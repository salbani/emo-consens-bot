from typing import Any, Callable

from bot_system.src.lib.core import Input, InputStreamHandler, InputStreamProvider, PromptInputData


class EmotionUtilities:
    def __init__(
        self,
        facial_expression_handler: InputStreamHandler,
        speech_emotion_handler: InputStreamHandler,
        emotion_threshold: float,
    ):
        self.facial_expression_handler = facial_expression_handler
        self.speech_emotion_handler = speech_emotion_handler
        self.emotion_threshold = emotion_threshold

    def facial_expressions_from_prompt_data(self, prompt_data: PromptInputData) -> str:
        facial_expressions = self._emotions_from_prompt_data(prompt_data, self.facial_expression_handler, self._facial_expression_to_string)
        return facial_expressions if facial_expressions else "Es konnte keine Emotionen im Gesicht erkannt werden."

    def speech_emotions_from_prompt_data(self, prompt_data: PromptInputData) -> str:
        speech_emotions = self._emotions_from_prompt_data(prompt_data, self.speech_emotion_handler, self._speech_emotion_to_string)
        return speech_emotions if speech_emotions else "Es konnte keine Emotionen in der Sprache erkannt werden."

    def _emotions_from_prompt_data(
        self,
        prompt_data: PromptInputData,
        provider: InputStreamProvider,
        to_string_fn: Callable[[str, float], str],
    ) -> str | None:
        emotions_buffer: list[dict[str, Any]] = [facial_expressions.value for facial_expressions in prompt_data.get_input(provider)]
        emotions = self._compute_average_emotions(emotions_buffer)

        if emotions is not None:
            emotions = {key: value for key, value in emotions.items() if value > self.emotion_threshold}
            emotions = "".join([to_string_fn(key, value) for key, value in emotions.items()])

        return emotions if emotions else None

    def _compute_average_emotions(self, emotions_buffer: list[dict[str, Any]]):
        if len(emotions_buffer) == 0:
            return None
        emotions_sum: dict[str, float] = {}
        for emotions in emotions_buffer:
            if "emotion" in emotions:
                emotions = emotions["emotion"]
            if emotions_sum == {}:
                emotions_sum = emotions
            else:
                for key, value in emotions.items():
                    emotions_sum[key] += value
        emotions_avg = {key: value / len(emotions_buffer) for key, value in emotions_sum.items()}
        return emotions_avg

    def _facial_expression_to_string(self, emotion_label: str, emotion_value: float):
        return f"Sieht ({self._translate_emotion_value(emotion_value)}) {self._translate_emotion_label(emotion_label)} aus."

    def _speech_emotion_to_string(self, emotion_label: str, emotion_value: float):
        return f"Klingt ({self._translate_emotion_value(emotion_value)}) {self._translate_emotion_label(emotion_label)}."

    def _translate_emotion_label(self, emotion: str):
        if emotion == "angry":
            return "Wütend"
        elif emotion == "disgust" or emotion == "disgusted":
            return "Ekel"
        elif emotion == "fear" or emotion == "fearful":
            return "Angst"
        elif emotion == "happy":
            return "Glücklich"
        elif emotion == "sad":
            return "Traurig"
        elif emotion == "surprise" or emotion == "surprised":
            return "Überrascht"
        elif emotion == "neutral":
            return "Neutral"
        elif emotion == "<unk>" or emotion == "other":
            return "Unbekannt"
        else:
            return emotion

    def _translate_emotion_value(self, value: float):
        if value > 0.95:
            return "sehr sicher"
        elif value > 0.85:
            return "sehr wahrscheinlich"
        elif value > 0.7:
            return "wahrscheinlich"
        elif value > 0.5:
            return "möglich"
        else:
            return "unwahrscheinlich"
