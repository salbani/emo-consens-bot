from cv2.typing import MatLike

from bot_system.src.lib.core import InputStreamProvider
from pepper_data_reciever.video_reciever import VideoReceiver


class PepperVideoProvider(InputStreamProvider[MatLike]):
    def __init__(self):
        super().__init__()
        self.video_receiver = VideoReceiver()
        self.video_receiver.start_async(self.on_video)

    def on_video(self, buffer: MatLike, height: int, width: int):
        self.output(buffer)