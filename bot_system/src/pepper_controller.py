import subprocess
from threading import Thread
from typing import Any

from reactivex import Subject
from bot_system.src.lib.core import InputStreamProvider, RobotController

import pyaudio
from bot_system.src.lib.config import CHANNELS, FORMAT, openai_client


class PepperController(RobotController):
    """
    Controller class for interacting with the Pepper robot. Extends the RobotController class.

    Enables animated messages to be sent to the Pepper robot.
    """

    def __init__(self, audio_provider: InputStreamProvider, mute: bool = False, no_pepper: bool = False):
        """
        Create a new instance of the PepperController class.

        Args:
            audio_provider (InputStreamProvider): The audio provider for bot system.
            mute (bool, optional): Whether to only print the answer to the console without playing the audio. Defaults to False.
            no_pepper (bool, optional): Whether to play the text from the llm response locally. For testing without Pepper. Defaults to False.
        """
        self.audio_provider = audio_provider
        self.mute = mute
        self.no_pepper = no_pepper
        self.on_speech_end = Subject[bool]()
        if not no_pepper:
            self.start_pepper_bridge()
            self.listen_to_bridge_output_on_thread()

    def start_pepper_bridge(self):
        """Starts the Pepper bridge subprocess."""
        self.process = subprocess.Popen(
            ["/usr/local/bin/python", "/Users/simonprivat/Workspace/Projects/emo-consens-bot/bot_system/pepper_bridge.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )  # Line-buffered

    def listen_to_bridge_output_on_thread(self):
        """Runs the listen_to_bridge_output method on a separate thread."""
        thread = Thread(target=self.listen_to_bridge_output)
        thread.start()

    def listen_to_bridge_output(self):
        """Listens to the output from the Pepper bridge subprocess and handles the events."""
        if self.process.stdout is None:
            raise ValueError("Subprocess stdout is None")

        while True:
            output = self.process.stdout.readline()
            if output:
                text = output.strip()
                print(f"Output from Python 2.7 script: {text}")
                if text == "event:speech_ended":
                    self.on_speech_end.on_next(True)
            else:
                break

    def send_event_to_bridge(self, event):
        """
        Sends an event to the Pepper bridge subprocess.

        Args:
            event (str): The event to send.
        """
        if self.process.stdin is None:
            raise ValueError("Subprocess stdin is None")

        self.process.stdin.write(event + "\n")
        self.process.stdin.flush()
        print(f"Sent event to Python 2.7 script: {event}")

    # Override
    def execute_llm_response(self, response: dict[str, Any]) -> None:
        if self.mute:
            print(response["answer"])
            self.on_speech_end.on_next(True)
            return

        if self.no_pepper:
            self.tts_locally(response)
        else:
            self.send_event_to_bridge(f"say:{response['answer']}")

    def tts_locally(self, response: dict[str, Any]) -> None:
        """
        Performs text-to-speech locally.

        Args:
            response (dict[str, Any]): The response from the bot.
        """

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
                input=response["clean_answer"] or response["answer"],
                response_format="pcm",
            )

            y = x.read()
            stream.write(y[int(24000 / 10) : -int(24000 / 10)])
            stream.stop_stream()
            stream.close()
            audio.terminate()
            self.on_speech_end.on_next(True)

        Thread(target=tts).start()

    # Override
    def dispose(self):
        self.process.terminate()
        self.on_speech_end.on_completed()
        super().dispose()


if __name__ == "__main__":
    audio_provider = InputStreamProvider()
    pepper_controller = PepperController(audio_provider)
    pepper_controller.execute_llm_response({"answer": "Hello! ^start(animations/Stand/Gestures/Hey_1) Nice to meet you ^wait(animations/Stand/Gestures/Hey_1)"})

    try:
        while True:
            pass
    except KeyboardInterrupt:
        pepper_controller.dispose()
        audio_provider.dispose()
        print("PepperController disposed")
