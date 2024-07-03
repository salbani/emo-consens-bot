import math
import wave
import webrtcvad
from openai import OpenAI
from collections import deque

from bot_system.config import CHANNELS, CHUNK, FORMAT, OPENAI_API_KEY, RATE, WAVE_OUTPUT_FILENAME
from bot_system.core import InputStreamHandler, InputStreamProvider
import os


openai_client = OpenAI(api_key=OPENAI_API_KEY)


class SpeechRecognitionHandler(InputStreamHandler[bytes, bytes, bytes, str]):
    def __init__(self, speech_provider: InputStreamProvider[bytes], mock: bool = False):
        self.mock = mock
        self.vad = webrtcvad.Vad(0)
        self.vad_frame_duration = 30  # ms
        self.vad_frame_len = int(RATE / 1000 * self.vad_frame_duration * FORMAT / 4)
        self.frames: list[bytes] = []
        self.is_speech_sliding_window = deque(maxlen=int(RATE / CHUNK) * math.floor(CHUNK * 2 / self.vad_frame_len))
        self.frames_sliding_window: deque[bytes] = deque(maxlen=int(RATE / CHUNK))
        self.is_detecting_speech = False
        self.min_speech_duration = 1

        super().__init__(speech_provider)

    def handle(self, input):
        audio = input.value

        speech_probability = self.speech_probability(audio)
        # print(f"Speech probability: {speech_probability:.2f}")
        self.frames_sliding_window.append(audio)

        if not self.is_detecting_speech and speech_probability > 0.9:
            print(f"Detecting speech... {speech_probability:.2f}")
            self.is_detecting_speech = True
            self.frames = list(self.frames_sliding_window)

        if self.is_detecting_speech:
            self.frames.append(audio)

        if self.is_detecting_speech and speech_probability < 0.85:
            self.is_detecting_speech = False
            speech_duration = len(self.frames) / (RATE / CHUNK)
            print(f"Speech ended... {speech_probability:.2f}")
            print(f"Speech duration: {speech_duration:.2f}")

            if speech_duration > self.min_speech_duration:
                waveFile = wave.open(WAVE_OUTPUT_FILENAME, "wb")
                waveFile.setnchannels(CHANNELS)
                waveFile.setsampwidth(2)
                waveFile.setframerate(RATE)
                waveFile.writeframes(b"".join(self.frames))
                waveFile.close()
                transcription = self.transcribe()
                self.output(transcription, input.capture_time - speech_duration)

            print(f"Speech too short... {len(self.frames) / RATE:.2f}")

    def transcribe(self) -> str:
        if self.mock:
            return "Hallo, wie geht es dir?. Ich bin kein chatbot. Ich bin ein Mensch."

        audio_file = open(WAVE_OUTPUT_FILENAME, "rb")
        transcription = openai_client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        return transcription.text

    def speech_probability(self, audio: bytes) -> float:
        vad_frame_count = 1
        while self.vad_frame_len * vad_frame_count < len(audio):
            vad_frame_start = self.vad_frame_len * (vad_frame_count - 1)
            vad_frame_end = self.vad_frame_len * vad_frame_count
            vad_frame = audio[vad_frame_start:vad_frame_end]

            self.is_speech_sliding_window.append(self.vad.is_speech(vad_frame, RATE))
            vad_frame_count += 1
        speech_probability = sum(self.is_speech_sliding_window) / len(self.is_speech_sliding_window)
        return speech_probability

    def dispose(self) -> None:
        super().dispose()
        if os.path.exists(WAVE_OUTPUT_FILENAME):
            os.remove(WAVE_OUTPUT_FILENAME)
