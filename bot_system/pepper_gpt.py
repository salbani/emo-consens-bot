import csv
from typing import Any


from bot_system.chat_agents.chat_gpt_agent import ChatGPTAgent
from bot_system.chat_server import PepperChatServer
from bot_system.config import CHANNELS, FORMAT, openai_client
from bot_system.core import Prompter, PromptInputData
from bot_system.handlers.emotion_handler import EmotionHandler
from bot_system.handlers.speech_recognition_handler import \
    SpeechRecognitionHandler
from bot_system.pepper_controller import PepperController
from bot_system.providers.console_input_provider import ConsoleInputProvider
from bot_system.providers.microphone_provider import MicrophoneProvider
from bot_system.providers.webcam_provider import WebcamProvider


class PepperGPT(Prompter[dict[str, Any], None, None]):
    def __init__(self, no_cost: bool = False, mute: bool = False, data_path: str | None = None):
        self.voice_provider = MicrophoneProvider()
        self.webcam_provider = WebcamProvider()

        if data_path is not None:
            self.chat_agent = ChatGPTAgent(no_cost, data_path)
        else:
            self.chat_agent = ChatGPTAgent(no_cost)

        animation_csv = open("bot_system/animations.csv", "r")
        animation_dict = csv.DictReader(animation_csv, fieldnames=["animation", "path", "labels"])
        self.animation_dict = {row["animation"]: (row["path"], row["labels"]) for row in animation_dict}

        super().__init__(
            # text_input=SpeechRecognitionHandler(self.voice_provider, mock=no_cost),
            text_input=ConsoleInputProvider(),
            llm=self.chat_agent,
            chat_server= PepperChatServer(),
            robot_controller=PepperController(self.voice_provider, mute),
            inputs=EmotionHandler(self.webcam_provider),
        )
        print("PepperGPT initialized")

    def _create_animation_list(self) -> str:
        return "\n".join([f"{key}: {value[1]}" for key, value in self.animation_dict.items()])

    def create_prompt(self, input_data):
        self.voice_provider.pause()
        face_results = [face_result.value for face_result in input_data.get_input(EmotionHandler) if face_result.capture_time > input_data.question.capture_time]
        primary_emotion, secondary_emotion = self.calculate_emotion_stats(face_results)

        print(f"Question:                   {input_data.question.value}")
        print(f"Detected primary emotion:   {primary_emotion}")
        print(f"Detected secondary emotion: {secondary_emotion}")
        return {
            "question": input_data.question.value,
            "animations": self._create_animation_list(),
            "facial_emotion_primary": f"{primary_emotion[0]} - Sicherheit: {primary_emotion[1]}" if primary_emotion is not None else "None",
            "facial_emotion_secondary": f"{secondary_emotion[0]} - Sicherheit: {secondary_emotion[1]}" if secondary_emotion is not None else "None",
        }

    def calculate_emotion_stats(self, face_results):
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
        return primary_emotion,secondary_emotion
        


from deepface.DeepFace import analyze

if __name__ == "__main__":
    prompter = PepperGPT(mute=False, no_cost=False, data_path="bot_system/data")

    try:
        analyze("bot_system/test_images/img1.jpg", actions=["emotion"], enforce_detection=False)
        print("Emotion Detection Initialized")
        while True:
            pass
    except KeyboardInterrupt:
        prompter.dispose()
        print("Exiting")
