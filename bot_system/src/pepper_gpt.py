import csv
from typing import Any

from bot_system.src.lib.core import Prompter, PromptInputData
from bot_system.src.lib.emotion_utilities import EmotionUtilities
from bot_system.src.providers.pepper_audio_provider import PepperAudioProvider
from bot_system.src.providers.pepper_video_provider import PepperVideoProvider
from bot_system.src.providers.console_input_provider import ConsoleInputProvider
from bot_system.src.providers.microphone_provider import MicrophoneProvider
from bot_system.src.providers.webcam_provider import WebcamProvider
from bot_system.src.handlers.face_detection_handler import FaceDetectionHandler
from bot_system.src.handlers.facial_expression_handler import FacialExpressionHandler
from bot_system.src.handlers.speech_buffer_handler import SpeechBufferHandler
from bot_system.src.handlers.speech_emotion_handler import SpeechEmotionHandler
from bot_system.src.handlers.speech_intent_detection_handler import SpeechIntentDetectionHandler
from bot_system.src.handlers.transkription_handler import TranskriptionHandler
from bot_system.src.pepper_controller import PepperController
from bot_system.src.chat_gpt_agent import ChatGPTAgent
from bot_system.src.chat_server import PepperChatServer

from bot_system.src.lib.run_on_main import RunOnMainThread


class PepperGPT(Prompter[dict[str, Any], dict[str, Any], None]):
    """PepperGPT is the main class that represents the Pepper GPT chatbot system. Extends the Prompter class."""

    def __init__(
        self,
        context_data_path: str | None = None,
        emotion_threshold: float = 0.5,
        no_cost: bool = False,
        mute: bool = False,
        no_pepper: bool = False,
        debug: bool = False,
        use_console_input: bool = False,
    ):
        """
        Create a new instance of the PepperGPT class.

        Args:
            data_path (str | None, optional): The path to the data for training the chatbot. Defaults to None.
            emotion_threshold (float, optional): The threshold for detecting emotions. Defaults to 0.5.
            no_cost (bool, optional): Whether to simulate no cost for generating responses. Defaults to False.
            mute (bool, optional): Whether to mute the audio. Defaults to False.
            no_pepper (bool, optional): Whether to simulate running without Pepper robot. Defaults to False.
            use_console_input (bool, optional): Whether to use console input. Defaults to False.
        """
        print("Initializing PepperGPT...")
        # Initialize animation dictionary
        animation_csv = open("bot_system/animations.csv", "r")
        self.animation_dict = {row["animation"]: (row["path"], row["labels"]) for row in csv.DictReader(animation_csv, fieldnames=["animation", "path", "labels"])}
        self.animation_list = "\n".join([f"{key}: {value[1]}" for key, value in self.animation_dict.items()])
        self.emotion_threshold = emotion_threshold

        # Initialize audio and video providers based on no_pepper flag
        if no_pepper:
            self.audio_provider = MicrophoneProvider()
            self.video_provider = WebcamProvider()
        else:
            self.audio_provider = PepperAudioProvider()
            self.video_provider = PepperVideoProvider()

        # Initialize chat GPT agent
        if context_data_path is not None:
            chat_gpt_agent = ChatGPTAgent(no_cost, context_data_path)
        else:
            chat_gpt_agent = ChatGPTAgent(no_cost)

        # Initialize various handlers and providers
        self.face_detection_handler = FaceDetectionHandler(self.video_provider)
        self.speech_intent_detection_handler = SpeechIntentDetectionHandler(self.face_detection_handler, self.audio_provider, debug=debug)
        self.facial_expression_handler = FacialExpressionHandler(self.face_detection_handler)
        self.speech_buffer_handler = SpeechBufferHandler(self.audio_provider, self.speech_intent_detection_handler)
        self.speech_emotion_handler = SpeechEmotionHandler(self.speech_buffer_handler)

        # Initialize text input and Pepper controller
        text_input = TranskriptionHandler(self.speech_buffer_handler, mock=no_cost) if not use_console_input else ConsoleInputProvider()
        pepper_controller = PepperController(self.audio_provider, mute, no_pepper=no_pepper)
        pepper_chat_server = PepperChatServer(self.speech_intent_detection_handler)

        self.emotion_utilities = EmotionUtilities(self.facial_expression_handler, self.speech_emotion_handler, emotion_threshold)

        # Call the super constructor to initialize the Prompter
        super().__init__(
            text_input=text_input,
            llm=chat_gpt_agent,
            chat_server=pepper_chat_server,
            robot_controller=pepper_controller,
            inputs=(self.facial_expression_handler, self.speech_emotion_handler),
        )

        # Pause the audio provider when speech is detected and resume when robot speech ends
        self.speech_buffer_handler._stream.subscribe(lambda _: self.audio_provider.pause())
        pepper_controller.on_speech_end.subscribe(lambda _: self.audio_provider.resume())
        print("PepperGPT initialized")

    # Override
    def create_prompt(self, input_data):
        if input_data.question is None:
            raise ValueError("Question is None")

        facial_expressions = self.emotion_utilities.facial_expressions_from_prompt_data(input_data)
        speech_emotions = self.emotion_utilities.speech_emotions_from_prompt_data(input_data)

        print(f"Question:                    {input_data.question.value}")
        print(f"Detected facial expressions: {facial_expressions}")
        print(f"Detected speech emotions:    {speech_emotions}")
        return {
            "question": input_data.question.value,
            "animations": self.animation_list,
            "facial_expressions": facial_expressions if facial_expressions is not None else "None",
            "speech_emotions": speech_emotions if speech_emotions is not None else "None",
        }

    # Override
    def transform_llm_response(self, response):
        for animation, (path, _) in self.animation_dict.items():
            response["answer"] = response["answer"].replace(animation, path)

        print(f"Answer: {response['answer']}")
        return response

    # Override
    def detect_prompt_ending(self, prompt_data):
        return prompt_data.question is not None and prompt_data.has_input(self.speech_emotion_handler)
