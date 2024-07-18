from collections import deque
from bot_system.src.lib.config import RATE
from bot_system.src.lib.core import InputStreamProvider
from pepper_data_reciever.audio_reciever import AudioReceiver


import matplotlib.pyplot as plt
import numpy as np


plt.ion()
fig, ax = plt.subplots()
ax.set_ylim(-3000, 3000)
ax.set_xlim(0, 10)
x = ax.plot([], [], label="audio")[0]
class PepperAudioProvider(InputStreamProvider[bytes]):
    def __init__(self):
        super().__init__()
        self.audio_reciever = AudioReceiver()
        self.audio_reciever.start_async(self.on_audio)
        self.audio_buffer = deque(maxlen=50)

    def on_audio(self, buffer: bytes, nbOfChannels: int, nbrOfSamplesByChannel: int, buffer_size: int, aTimeStamp: list[int]):
        self.output(buffer)
        # self.audio_buffer.append(buffer)
        # from_dummy_thread(self.plot_audio)

    def plot_audio(self):
        buffer = b"".join(self.audio_buffer)

        if not buffer:
            print("Buffer is empty")
            return
        
        y = np.frombuffer(buffer, dtype=np.int16)
        t = np.linspace(0, len(buffer) / (RATE), num=len(y))
        x.set_data(t, y)
        fig.canvas.draw()
        fig.canvas.flush_events()

    def dispose(self):
        self.audio_reciever.dispose()
        super().dispose()
