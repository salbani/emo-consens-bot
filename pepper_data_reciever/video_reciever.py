import queue
import socket
import struct
import threading
from typing import Callable
import cv2
from cv2.typing import MatLike
import numpy as np

class VideoReceiver:
    def __init__(self, play_video: bool = False):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_running = False
        self.play_video = play_video

    def play(self, buffer: MatLike, height: int, width: int):
        cv2.imshow('Pepper Video Stream', buffer)
        cv2.waitKey(1)

    def start_async(self, receive_data: Callable[[MatLike, int, int], None]):
        threading.Thread(target=self.start, args=(receive_data,)).start()
    
    def start(self, receive_data: Callable[[MatLike, int, int], None]):
        try:
            self.client_socket.connect(("pepper.local", 40098))
            self.is_running = True
            while self.is_running:
                header_format = "!I I I"
                header_size = struct.calcsize(header_format)
                header_data = self.client_socket.recv(header_size)
                if not header_data:
                    print("VideoReceiver: Server closed the connection.")
                    break

                image_width, image_height, buffer_size = struct.unpack(header_format, header_data)

                buffer = b""
                while len(buffer) < buffer_size:
                    chunk = self.client_socket.recv(buffer_size - len(buffer))
                    if not chunk:
                        print("VideoReceiver: Failed to receive all data.")
                        break
                    buffer += chunk


                image = np.frombuffer(buffer, dtype=np.uint8).reshape((image_height, image_width, 3))
                receive_data(image, image_height, image_width)
                if self.play_video:
                    self.play(image, image_height, image_width)
        finally:
            self.is_running = False

    def dispose(self):
        self.is_running = False
        self.client_socket.close()

if __name__ == "__main__":
    receiver = VideoReceiver(play_video=True)
    receiver.start_async(lambda buffer, height, width: print(f"Received image: {height}x{width}"))

    try:
        while True:
            pass
    except KeyboardInterrupt:
        receiver.dispose()
        cv2.destroyAllWindows()
        exit(0)
        print("VideoReceiver stopped.")