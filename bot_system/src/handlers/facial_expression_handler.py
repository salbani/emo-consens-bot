from typing import Any

import cv2
from cv2.data import haarcascades
from cv2.typing import MatLike
from deepface.DeepFace import analyze

from bot_system.src.lib.core import InputStreamHandler, InputStreamProvider
from bot_system.src.handlers.face_detection_handler import DetectedFace


class FacialExpressionHandler(InputStreamHandler[DetectedFace | MatLike, DetectedFace | MatLike, DetectedFace | MatLike, dict[str, Any]]):
    def __init__(self, image_provider: InputStreamProvider[DetectedFace | MatLike]):
        self.face_cascade = cv2.CascadeClassifier(haarcascades + "haarcascade_frontalface_default.xml")

        super().__init__(image_provider, blocking=True)

    def handle(self, input):
        if not isinstance(input.value, DetectedFace):
            return

        detected_face = input.value

        result = analyze(detected_face.face_roi, actions=["emotion"], enforce_detection=False)
        
        if result is not None and len(result) >= 0:
            for emotion, score in result[0]["emotion"].items():
                result[0]["emotion"][emotion] /= 100

            self.output(result[0])

    def dispose(self) -> None:
        super().dispose()
