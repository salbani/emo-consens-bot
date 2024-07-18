from io import BufferedReader
import os
import wave
from collections import deque
from typing import cast

from bot_system.src.lib.config import CHANNELS, CHUNK, RATE, WAVE_OUTPUT_FILENAME
from bot_system.src.lib.core import Input, InputStreamHandler, InputStreamProvider
from bot_system.src.handlers.speech_intent_detection_handler import SpeechIntent


class SpeechBufferHandler(InputStreamHandler[bytes, SpeechIntent, bytes, BufferedReader]):
    def __init__(
        self,
        speech_provider: InputStreamProvider[bytes],
        speech_intent_handler: InputStreamProvider[SpeechIntent],
        mock: bool = False,
    ):
        self.mock = mock
        self.min_speech_duration = 2.3
        self.is_detecting_speech = False

        self.speech_intent = SpeechIntent(False, False, False)
        self.audio_frames_sliding_window: deque[bytes] = deque(maxlen=int(RATE / CHUNK) * 2)

        self.speech_intent_handler = speech_intent_handler
        self.speech_provider = speech_provider

        super().__init__((speech_provider, speech_intent_handler))

    def handle(self, input):
        if input.source == self.speech_intent_handler:
            self._handle_speech_intent(cast(Input[SpeechIntent], input))

        if input.source == self.speech_provider:
            self._handle_audio(cast(Input[bytes], input))

    def _handle_speech_intent(self, input: Input[SpeechIntent]):
        self.speech_intent = input.value

    def _handle_audio(self, input: Input[bytes]):
        audio = input.value

        self._add_to_buffer(audio)

        if not self.is_detecting_speech and self.speech_intent.intents_speaking():
            self.is_detecting_speech = True
            self._start_buffer()

        if self.is_detecting_speech and not self.speech_intent.intents_speaking():
            self.is_detecting_speech = False
            self._end_buffer()

    def _start_buffer(self):
        print(f"Detecting speech...")
        self.frames = list(self.audio_frames_sliding_window)
        self._buffer_to_audio(self.frames, "test.wav")
        print(f"{len(self.frames)} frames")

    def _add_to_buffer(self, audio: bytes):
        self.audio_frames_sliding_window.append(audio)
        if self.is_detecting_speech:
            self.frames.append(audio)

    def _end_buffer(self):
        speech_duration = len(self.frames) / (RATE / CHUNK)
        print(f"Speech ended...")
        print(f"Speech duration: {speech_duration:.2f}")

        if speech_duration > self.min_speech_duration:
            audio_file = self._buffer_to_audio(self.frames)
            self.output(audio_file, speech_duration)
        else:
            print(f"Speech too short, must be at least {self.min_speech_duration} seconds!")

    def _buffer_to_audio(self, audio: list[bytes], filename: str = WAVE_OUTPUT_FILENAME) -> BufferedReader:
        waveFile = wave.open(filename, "wb")
        waveFile.setnchannels(CHANNELS)
        waveFile.setsampwidth(2)
        waveFile.setframerate(RATE)
        waveFile.writeframes(b"".join(audio))
        waveFile.close()
        audio_file = open(filename, "rb")
        return audio_file

    def dispose(self) -> None:
        super().dispose()
        if os.path.exists(WAVE_OUTPUT_FILENAME):
            os.remove(WAVE_OUTPUT_FILENAME)
