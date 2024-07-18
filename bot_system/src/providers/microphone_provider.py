from typing import Mapping
import pyaudio

from bot_system.src.lib.config import CHANNELS, CHUNK, FORMAT, RATE
from bot_system.src.lib.core import InputStreamProvider


class MicrophoneProvider(InputStreamProvider[bytes]):

    def __init__(self):
        super().__init__()

        self.audio = pyaudio.PyAudio()
        self.frames = []
        self.stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            stream_callback=self._on_audio,
        )

    def dispose(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        super().dispose()

    def _on_audio(
        self,
        input_data: bytes | None,
        frame_count: int,
        time_info: Mapping[str, float],
        flags: int,
    ) -> tuple[bytes | None, int]:
        if input_data:
            self.output(input_data)

        return input_data, pyaudio.paContinue
