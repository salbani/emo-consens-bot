from threading import Thread
from typing import Any

import pyaudio

from bot_system.chat_agents.chat_gpt_agent import ChatGPTAgent
from bot_system.config import CHANNELS, FORMAT, openai_client
from bot_system.core import Prompter, PromptInputData
from bot_system.handlers.emotion_handler import EmotionHandler
from bot_system.providers.microphone_provider import MicrophoneProvider
from bot_system.handlers.speech_recognition_handler import SpeechRecognitionHandler
from bot_system.providers.webcam_provider import WebcamProvider


class PepperGPT(Prompter[dict[str, Any], None, None]):
    def __init__(self, no_cost: bool = False, mute: bool = False, data_path: str | None = None):
        self.mute = mute
        self.voice_provider = MicrophoneProvider()
        self.webcam_provider = WebcamProvider()

        if data_path is not None:
            self.chat_agent = ChatGPTAgent(no_cost, data_path)
        else:
            self.chat_agent = ChatGPTAgent(no_cost)

        self.voice_handler = SpeechRecognitionHandler(self.voice_provider, mock=no_cost)
        self.emotion_handler = EmotionHandler(self.webcam_provider)

        super().__init__(
            text_input=self.voice_handler,
            llm=self.chat_agent,
            inputs=self.emotion_handler,
        )
        print("PepperGPT initialized")

    def create_prompt(self, input_data):
        self.voice_provider.pause()
        face_results = [face_result.value for face_result in input_data.get_input(self.emotion_handler) if face_result.capture_time > input_data.question.capture_time]
        primary_emotion: tuple[str, float] | None = None
        secondary_emotion: tuple[str, float] | None = None
        if len(face_results) > 0:
            emotion: dict[str, float] | None = None
            for face_result in face_results:
                if emotion is None:
                    emotion = face_result["emotion"]
                else:
                    for key, value in face_result["emotion"].items():
                        emotion[key] += value
            if emotion is not None:
                emotion = {key: value / len(face_results) for key, value in emotion.items()}
                primary_emotion = max(emotion.items(), key=lambda x: x[1])
                secondary_emotion = max(emotion.items(), key=lambda x: x[1] if x[0] != primary_emotion[0] else 0)

        print(f"Question:                   {input_data.question}")
        print(f"Detected primary emotion:   {primary_emotion}")
        print(f"Detected secondary emotion: {secondary_emotion}")
        return {
            "question": input_data.question,
            "facial_emotion_primary": f"{primary_emotion[0]} - Sicherheit: {primary_emotion[1]}" if primary_emotion is not None else "None",
            "facial_emotion_secondary": f"{secondary_emotion[0]} - Sicherheit: {secondary_emotion[1]}" if secondary_emotion is not None else "None",
        }

    def handle_llm_response(self, response: str) -> None:
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
                input=response,
                response_format="pcm",
            )

            y = x.read()
            stream.write(y[int(24000 / 10) : -int(24000 / 10)])
            stream.stop_stream()
            stream.close()
            audio.terminate()
            self.voice_provider.resume()

        Thread(target=tts).start()


from deepface.DeepFace import analyze

if __name__ == "__main__":
    prompter = PepperGPT(mute=True, no_cost=True, data_path="bot_system/data")

    try:
        analyze("bot_system/test_images/img1.jpg", actions=["emotion"], enforce_detection=False)
        print("Emotion Detection Initialized")
        while True:
            pass
    except KeyboardInterrupt:
        prompter.dispose()
        print("Exiting")
