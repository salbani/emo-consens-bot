from threading import Thread
from typing import Any
from bot_system.core import InputStreamProvider, RobotController

import pyaudio
from bot_system.config import CHANNELS, FORMAT, openai_client

class PepperController(RobotController):
    def __init__(self, voice_provider: InputStreamProvider, mute: bool = False):
        self.voice_provider = voice_provider
        self.mute = mute

    def execute_bot_response(self, response: dict[str, Any]) -> None:
        print("ChatAgent Answered: ")
        print(response)
        if self.mute:
            self.voice_provider.resume()
            return

        def tts():
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=24000,
                output=True,
            )
            x = openai_client.audio.speech.create(
                model="tts-1",
                voice="fable",
                speed=1.1,
                input=response["answer"],
                response_format="pcm",
            )

            y = x.read()
            stream.write(y[int(24000 / 10) : -int(24000 / 10)])
            stream.stop_stream()
            stream.close()
            audio.terminate()
            self.voice_provider.resume()

        Thread(target=tts).start()
        