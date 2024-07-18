from io import BufferedReader
from typing import Any, cast

from funasr.auto.auto_model import AutoModel

from bot_system.src.lib.config import CHUNK, RATE
from bot_system.src.lib.core import Input, InputStreamHandler, InputStreamProvider
from bot_system.src.handlers.face_detection_handler import DetectedFace
from bot_system.src.handlers.speech_intent_detection_handler import SpeechIntent


class SpeechEmotionHandler(InputStreamHandler[BufferedReader, BufferedReader, BufferedReader, dict[str, Any]]):
    def __init__(self, audio_provider: InputStreamProvider[BufferedReader]):
        self.model = AutoModel(model="iic/emotion2vec_plus_large")
        self.is_analyzing = False

        self.audio_provider = audio_provider

        super().__init__(audio_provider)

    def handle(self, input):
        audio_file = input.value
        frames = audio_file.read()
        res = self.model.generate(input=frames)
        labels = [str(label).split("/")[-1] for label in res[0]["labels"]]
        speech_emotions = dict(zip(labels, res[0]["scores"]))
        self.output(speech_emotions)

    def dispose(self) -> None:
        super().dispose()
