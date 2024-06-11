from typing import Any

import cv2
from cv2.data import haarcascades
from cv2.typing import MatLike
from deepface.DeepFace import analyze

from bot_system.core import InputStreamHandler, InputStreamProvider


class EmotionHandler(InputStreamHandler[MatLike, MatLike, MatLike, dict[str, Any]]):
    def __init__(self, image_provider: InputStreamProvider[MatLike]):
        self.face_cascade = cv2.CascadeClassifier(haarcascades + "haarcascade_frontalface_default.xml")
        self.is_detecting_emotion = False

        super().__init__(image_provider)

    def handle(self, input):
        if self.is_detecting_emotion:
            return

        self.is_detecting_emotion = True
        frame = input.value
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Convert grayscale frame to RGB format
        rgb_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2RGB)

        # Detect faces in the frame
        faces = self.face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        largest_face = max(faces, key=lambda x: x[2] * x[3] if len(faces) else 0, default=None)

        if largest_face is not None:
            x, y, w, h = largest_face
            face_roi = rgb_frame[y : y + h, x : x + w]

            result = analyze(face_roi, actions=["emotion"], enforce_detection=False)

            emotion = result[0]["dominant_emotion"]
            self.output(result[0])

        self.is_detecting_emotion = False

    def dispose(self) -> None:
        super().dispose()
