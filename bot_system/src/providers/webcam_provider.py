from threading import Thread, Lock

from cv2 import VideoCapture
from cv2.typing import MatLike

from bot_system.src.lib.core import InputStreamProvider


class WebcamProvider(InputStreamProvider[MatLike]):

    def __init__(self):
        super().__init__()

        self.camera = VideoCapture(0)
        self.recording = True

        self.lock = Lock()
        self.capture_thread = Thread(target=self._capture)
        self.capture_thread.start()

    def dispose(self):
        self.recording = False
        self.camera.release()
        super().dispose()

    def _capture(self):
        with self.lock:
            while self.recording:
                ret, frame = self.camera.read()
                if not ret:
                    break

                self.output(frame)
