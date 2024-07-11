from bot_system.core import InputStreamProvider
from pepper_data_reciever.audio_reciever import AudioReceiver


class PepperAudioProvider(InputStreamProvider[bytes]):
    def __init__(self):
        super().__init__()
        self.audio_reciever = AudioReceiver()
        self.audio_reciever.start_async(self.on_audio)

    def on_audio(self, buffer: bytes, nbOfChannels: int, nbrOfSamplesByChannel: int, buffer_size: int, aTimeStamp: list[int]):
        self.output(buffer)

    def dispose(self):
        self.audio_reciever.dispose()
        super().dispose()
