from io import BufferedReader
from openai import OpenAI

from bot_system.src.lib.config import OPENAI_API_KEY, WAVE_OUTPUT_FILENAME
from bot_system.src.lib.core import Input, InputStreamHandler, InputStreamProvider
from bot_system.src.handlers.speech_intent_detection_handler import SpeechIntent

openai_client = OpenAI(api_key=OPENAI_API_KEY)


class TranskriptionHandler(InputStreamHandler[BufferedReader, bytes, bytes, str]):
    def __init__(
        self,
        audio_file_provider: InputStreamProvider[BufferedReader],
        mock: bool = False,
    ):
        self.mock = mock

        super().__init__(audio_file_provider)

    def handle(self, input):
        if self.mock:
            self.output("Hallo, wie geht es dir?. Ich bin kein chatbot. Ich bin ein Mensch.")
            return
        
        audio_file = input.value

        transcription = openai_client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        self.output(transcription.text)

