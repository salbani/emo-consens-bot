import inspect
import math
from collections import deque
from dataclasses import dataclass
from typing import cast

import cv2
from cv2.typing import MatLike
import numpy as np
import webrtcvad
from mediapipe.python.solutions.face_mesh import FaceMesh

from bot_system.src.lib.config import CHANNELS, CHUNK, FORMAT, OPENAI_API_KEY, RATE, WAVE_OUTPUT_FILENAME
from bot_system.src.lib.core import Input, InputStreamHandler, InputStreamProvider
from bot_system.src.handlers.face_detection_handler import DetectedFace
from bot_system.src.lib.run_on_main import RunOnMainThread
from face_analyzer import FaceAnalyzer

import matplotlib.pyplot as plt

# Set up the plot
plt.ion()
fig, ax = plt.subplots()
ax.set_ylim(-0.5, 2.5)
ax.set_xlim(0, 100)

# Line objects for each attribute
lines = {
    "is_moving_mouth": ax.plot([], [], label="is_moving_mouth")[0],
    "has_eye_contact": ax.plot([], [], label="has_eye_contact")[0],
    "is_speech": ax.plot([], [], label="is_speech")[0],
}
ax.legend(loc="upper left")


@dataclass
class SpeechIntent:
    is_moving_mouth: bool
    has_eye_contact: bool
    is_speech: bool

    def intents_speaking(self) -> bool:
        return self.is_moving_mouth and self.has_eye_contact and self.is_speech


class SpeechIntentDetectionHandler(InputStreamHandler[DetectedFace | MatLike, bytes, bytes, SpeechIntent]):
    def __init__(
        self,
        face_provider: InputStreamProvider[DetectedFace | MatLike],
        audio_provider: InputStreamProvider[bytes],
        mouth_angle_fluctuation_threshold: float = 0.005,
        gaze_angle_threshold: float = 0.7,
        probability_threshold: float = 0.75,
        intent_start_buffer_len: int = 20,
        intent_end_buffer_len: int = 20,
        debug: bool = False,
    ):
        """
        Initializes a SpeechIntentHandler object.

        Args:
            face_provider (InputStreamProvider[DetectedFace]): The provider for detected faces.
            audio_provider (InputStreamProvider[bytes]): The provider for audio data.
            mouth_angle_fluctuation_threshold (float): The threshold for mouth angle fluctuation.
            gaze_angle_threshold (float): The threshold for gaze angle in radians.
            probability_threshold (float): The threshold for the probability of the speech intent detection in the sliding window.
            buffer_length (int): The length of the buffer for the sliding window of the speech intent detection

        Returns:
            None
        """
        self.audio_provider = audio_provider
        self.face_provider = face_provider
        self.mouth_angle_fluctuation_threshold = mouth_angle_fluctuation_threshold
        self.gaze_angle_threshold = gaze_angle_threshold
        self.probability_threshold = probability_threshold
        self.debug = debug

        self.speech_intent = SpeechIntent(False, False, False)

        self.intent_start_buffer_len = intent_start_buffer_len
        self.intent_end_buffer_len = intent_end_buffer_len

        self.intent_queue = deque[SpeechIntent](maxlen=100)

        self.vad_frame_duration = 30  # ms
        self.vad_frame_len = int(RATE / 1000 * self.vad_frame_duration * FORMAT / 4)

        self.has_eye_contact_buffer = deque[bool](maxlen=max(intent_start_buffer_len, intent_end_buffer_len))
        self.is_moving_mouth_buffer = deque[bool](maxlen=max(intent_start_buffer_len, intent_end_buffer_len))
        self.is_speech_buffer = deque(maxlen=max(intent_start_buffer_len, intent_end_buffer_len))

        self.vad = webrtcvad.Vad(1)
        self.face_analyzer = FaceAnalyzer()
        self.face_mesh = FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        super().__init__((face_provider, audio_provider), blocking=True)

    def handle(self, input):
        if input.source == self.audio_provider:
            self._handle_audio(cast(Input[bytes], input))

        if input.source == self.face_provider:
            self._handle_face(cast(Input[DetectedFace | MatLike], input))

    def _handle_audio(self, input: Input[bytes]):
        audio = input.value

        vad_frame_count = 1
        while self.vad_frame_len * vad_frame_count < len(audio):
            vad_frame_start = self.vad_frame_len * (vad_frame_count - 1)
            vad_frame_end = self.vad_frame_len * vad_frame_count
            vad_frame = audio[vad_frame_start:vad_frame_end]

            self.is_speech_buffer.append(self.vad.is_speech(vad_frame, RATE))
            vad_frame_count += 1

        self._update_speech_intent()

    def _handle_face(self, input: Input[DetectedFace | MatLike]):
        if not isinstance(input.value, DetectedFace):
            frame = input.value
            self.has_eye_contact_buffer.append(False)
            self.is_moving_mouth_buffer.append(False)

        else:
            frame = input.value.frame
            detected_face = input.value

            results = self.face_mesh.process(detected_face.face_roi)

            if results.multi_face_landmarks:  # type: ignore
                face_analysis = self.face_analyzer.analyze(
                    detected_face.frame,
                    results.multi_face_landmarks[0].landmark,  # type: ignore
                    detected_face.position,
                    detected_face.dimensions,
                    True,
                )


                if face_analysis:
                    is_moving_mouth = bool(face_analysis.mouth_angle_fluctuation > self.mouth_angle_fluctuation_threshold)
                    is_gazing = bool(face_analysis.angle_radians < self.gaze_angle_threshold)

                    self.has_eye_contact_buffer.append(is_gazing)
                    self.is_moving_mouth_buffer.append(is_moving_mouth)

            else:
                self.has_eye_contact_buffer.append(False)
                self.is_moving_mouth_buffer.append(False)

        self._update_speech_intent()

        if self.debug:
            RunOnMainThread.schedule(lambda: self._show_frame(frame))

    def _estimate_probability(self, buffer: deque):
        return bool(np.mean(buffer) > self.probability_threshold)

    def _check_buffer_maxlen(self):
        if self.speech_intent.intents_speaking():
            if self.has_eye_contact_buffer.maxlen != self.intent_end_buffer_len:
                self.has_eye_contact_buffer = deque[bool](self.has_eye_contact_buffer, maxlen=self.intent_end_buffer_len)
            if self.is_moving_mouth_buffer.maxlen != self.intent_end_buffer_len:
                self.is_moving_mouth_buffer = deque[bool](self.is_moving_mouth_buffer, maxlen=self.intent_end_buffer_len)
            if self.is_speech_buffer.maxlen != self.intent_end_buffer_len:
                self.is_speech_buffer = deque(self.is_speech_buffer, maxlen=self.intent_end_buffer_len)
        else:
            if self.has_eye_contact_buffer.maxlen != self.intent_start_buffer_len:
                self.has_eye_contact_buffer = deque[bool](self.has_eye_contact_buffer, maxlen=self.intent_start_buffer_len)
            if self.is_moving_mouth_buffer.maxlen != self.intent_start_buffer_len:
                self.is_moving_mouth_buffer = deque[bool](self.is_moving_mouth_buffer, maxlen=self.intent_start_buffer_len)
            if self.is_speech_buffer.maxlen != self.intent_start_buffer_len:
                self.is_speech_buffer = deque(self.is_speech_buffer, maxlen=self.intent_start_buffer_len)

    def _update_speech_intent(self):
        self._check_buffer_maxlen()
        self.speech_intent = SpeechIntent(
            is_speech=self._estimate_probability(self.is_speech_buffer),
            is_moving_mouth=self._estimate_probability(self.is_moving_mouth_buffer),
            has_eye_contact=self._estimate_probability(self.has_eye_contact_buffer),
        )
        self.output(self.speech_intent)

        self.intent_queue.append(self.speech_intent)
        if self.debug:
            RunOnMainThread.schedule(self._plot_intent)

    def _show_frame(self, frame):
        cv2.imshow("output window", frame)
        cv2.waitKey(1)

    def _plot_intent(self):

        # plot the speech intent
        x_data = list(range(len(self.intent_queue)))
        y_data = {
            "is_moving_mouth": [int(intent.is_moving_mouth) for intent in self.intent_queue],
            "has_eye_contact": [int(intent.has_eye_contact) for intent in self.intent_queue],
            "is_speech": [int(intent.is_speech) for intent in self.intent_queue],
        }
        for key, line in lines.items():
            line.set_data(x_data, y_data[key])
        fig.canvas.draw()
        fig.canvas.flush_events()
