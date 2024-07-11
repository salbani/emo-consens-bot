import socket
import struct
import threading
from typing import Callable
import pyaudio
import numpy as np


class AudioReceiver:
    def __init__(self, play_audio: bool = False):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_running = False

        self.play_audio = play_audio
        if play_audio:
            channels = 1
            sample_rate = 48000  # Hz, adjust this to match your audio stream's sample rate
            samples = 4096
            buffer_size = 32768  # This may refer to the byte size of your buffer

            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(format=pyaudio.paInt16, channels=channels, rate=sample_rate, output=True)  # This assumes 16-bit samples; adjust as necessary

    def play(self, buffer):
        self.stream.write(buffer)

    def start_async(self, receive_data: Callable[[bytes, int, int, int, list[int]], None]):
        threading.Thread(target=self.start, args=(receive_data,)).start()

    def start(self, receive_data: Callable[[bytes, int, int, int, list[int]], None]):
        try:
            self.client_socket.connect(("pepper.local", 40099))
            self.is_running = True
            while self.is_running:
                header_format = "!I I I I I"
                header_size = struct.calcsize(header_format)
                header_data = self.client_socket.recv(header_size)
                if not header_data:
                    print("AudioReceiver: Server closed the connection.")
                    break

                nbOfChannels, nbrOfSamplesByChannel, timeStamp1, timeStamp2, buffer_size = struct.unpack(header_format, header_data)
                aTimeStamp = [timeStamp1, timeStamp2]

                buffer = b""
                while len(buffer) < buffer_size:
                    chunk = self.client_socket.recv(buffer_size - len(buffer))
                    if not chunk:
                        print("AudioReceiver: Failed to receive all data.")
                        break
                    buffer += chunk

                receive_data(buffer, nbOfChannels, nbrOfSamplesByChannel, buffer_size, aTimeStamp)
                if self.play_audio:
                    self.play(buffer)
        finally:
            self.is_running = False

    def dispose(self):
        self.is_running = False
        self.client_socket.close()
        if self.play_audio:
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()


if __name__ == "__main__":
    receiver = AudioReceiver(True)
    receiver.start_async(
        lambda buffer, nbOfChannels, nbrOfSamplesByChannel, buffer_size, aTimeStamp: print(
            f"Received audio data: Channels={nbOfChannels}, Samples={nbrOfSamplesByChannel}, TimeStamps={aTimeStamp}, Buffer Size={buffer_size}"
        )
    )

    try:
        while True:
            pass
    except KeyboardInterrupt:
        receiver.dispose()
        print("AudioReceiver stopped.")
