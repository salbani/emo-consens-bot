from dataclasses import dataclass
from typing import Sequence

import cv2
from cv2.data import haarcascades
from cv2.typing import MatLike

from bot_system.src.lib.core import InputStreamHandler, InputStreamProvider


@dataclass
class DetectedFace:
    frame: MatLike
    face_roi: MatLike
    position: tuple[int, int]
    dimensions: tuple[int, int]


class FaceDetectionHandler(InputStreamHandler[MatLike, MatLike, MatLike, DetectedFace | MatLike]):
    def __init__(self, image_provider: InputStreamProvider[MatLike]):
        self.face_cascade = cv2.CascadeClassifier(haarcascades + "haarcascade_frontalface_default.xml")
        self.is_detecting = False

        super().__init__(image_provider)

    def handle(self, input):
        if self.is_detecting:
            return
        self.is_detecting = True

        frame = input.value
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces in the frame
        faces = self.face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        largest_face = max(faces, key=lambda x: x[2] * x[3] if len(faces) else 0, default=None)

        if largest_face is not None:
            rgb_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2RGB)
            x, y, w, h = largest_face
            face_roi = rgb_frame[y : y + h, x : x + w]

            self.output(DetectedFace(frame, face_roi, (x, y), (w, h)))
        else:
            self.output(frame)
        
        self.is_detecting = False
