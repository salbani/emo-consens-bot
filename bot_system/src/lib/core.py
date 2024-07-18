from dataclasses import dataclass
from threading import Thread
import time
from typing import Any, Generic, TypeVar, overload

import reactivex as rx
from reactivex import Observable, operators as ops

OUT = TypeVar("OUT")

P1 = TypeVar("P1")
P2 = TypeVar("P2")
P3 = TypeVar("P3")


class InputStreamProvider(Generic[OUT]):
    def __init__(self):
        self._stream: rx.Subject[Input[OUT]] = rx.Subject()
        self.is_paused = False

    def output(self, value: OUT, capture_time: float | None = None) -> None:
        if not self.is_paused:
            self._stream.on_next(Input(self, value, capture_time if capture_time is not None else time.time()))

    def pause(self) -> None:
        self.is_paused = True

    def resume(self) -> None:
        self.is_paused = False

    def dispose(self) -> None:
        self._stream.on_completed()
        print(f"Disposed InputStreamProvider {self}!")


@dataclass
class Input(Generic[OUT]):
    source: InputStreamProvider[OUT]
    value: OUT
    capture_time: float


class InputStreamHandler(Generic[P1, P2, P3, OUT], InputStreamProvider[OUT]):
    @overload
    def __init__(self, providers: InputStreamProvider[P1], blocking=False) -> None: ...
    @overload
    def __init__(self, providers: tuple[InputStreamProvider[P1], InputStreamProvider[P2]], blocking=False) -> None: ...
    @overload
    def __init__(self, providers: tuple[InputStreamProvider[P1], InputStreamProvider[P2], InputStreamProvider[P3]], blocking=False) -> None: ...

    def __init__(
        self,
        providers: (
            InputStreamProvider[P1]
            | tuple[InputStreamProvider[P1]]
            | tuple[InputStreamProvider[P1], InputStreamProvider[P2]]
            | tuple[InputStreamProvider[P1], InputStreamProvider[P2], InputStreamProvider[P3]]
        ),
        blocking=False,
    ):
        super().__init__()
        if isinstance(providers, InputStreamProvider):
            providers = (providers,)
        self.blocking = blocking
        self.providers = providers
        self._setup_provider_stream(providers)
        self.is_handling = False
        self.is_paused = False

    def _setup_provider_stream(
        self, providers: tuple[InputStreamProvider[P1]] | tuple[InputStreamProvider[P1], InputStreamProvider[P2]] | tuple[InputStreamProvider[P1], InputStreamProvider[P2], InputStreamProvider[P3]]
    ) -> None:
        provider_streams = map(lambda x: (x._stream), list(providers))
        rx.merge(*provider_streams).subscribe(self._handle_on_thread)

    def _handle_on_thread(self, input: Input[P1] | Input[P2] | Input[P3]) -> None:
        Thread(target=self.handle, args=(input,)).start()

    def _handle_safe(self, input: Input[P1] | Input[P2] | Input[P3]) -> None:
        try:
            if not self.is_paused:
                self.is_handling = True
                self.handle(input)
        except Exception as e:
            print(f"Error in handler {type(self).__name__}: ", e)
        finally:
            self.is_handling = False

    def handle(self, input: Input[P1] | Input[P2] | Input[P3]) -> None:
        raise NotImplementedError

    def dispose(self) -> None:
        for provider in self.providers:
            provider.dispose()
        super().dispose()


class ChatAgent:

    def prompt(self, prompt: dict[str, str]) -> dict[str, Any]:
        raise NotImplementedError


class PromptInputData(Generic[P1, P2, P3]):
    def __init__(self, question: Input[str] | None = None) -> None:
        self.question: Input[str] | None = question
        self.input_buffers: dict[InputStreamProvider, list[Input[Any]]] = {}

    def has_input(self, provider: InputStreamProvider[P1] | InputStreamProvider[P2] | InputStreamProvider[P3]) -> bool:
        return provider in self.input_buffers

    def add_input(self, input: Input[P1] | Input[P2] | Input[P3]) -> None:
        if not self.has_input(input.source):
            self.input_buffers[input.source] = []

        self.input_buffers[input.source].append(input)

    @overload
    def get_input(self, provider: InputStreamProvider[P1]) -> list[Input[P1]]: ...
    @overload
    def get_input(self, provider: InputStreamProvider[P2]) -> list[Input[P2]]: ...
    @overload
    def get_input(self, provider: InputStreamProvider[P3]) -> list[Input[P3]]: ...

    def get_input(self, provider: InputStreamProvider[P1] | InputStreamProvider[P2] | InputStreamProvider[P3]) -> list[Input[P1]] | list[Input[P2]] | list[Input[P3]]:
        if provider in self.input_buffers:
            return self.input_buffers[provider]
        return []


class Message:
    def __init__(self, text: str, sender: str, from_chat=False, timestamp: float | None = None):
        self.text = text
        self.sender = sender
        self.from_chat = from_chat
        self.timestamp = time.time() if timestamp is None else timestamp

    def __str__(self):
        return f"{self.sender}: {self.text}"

    def __repr__(self):
        return f"Message({self.text}, {self.sender})"


class ChatServer:
    def __init__(self):
        self.messages = []
        self.message_stream = rx.Subject[Message]()
        self.message_stream.subscribe(self.send_message)

    def add_message(self, message: str, sender: str, from_chat=False) -> None:
        """ Add a message to the chat server. """
        self.message_stream.on_next(Message(message, sender, from_chat=from_chat))
        self.messages.append({"message": message, "sender": sender})

    def send_message(self, message: Message) -> None:
        """ Send a message to the chat clients. """
        raise NotImplementedError

    def get_messages(self):
        """ Get all messages. """
        return self.messages

    def stop(self) -> None:
        """ Stop the chat server. """
        self.message_stream.on_completed()


class RobotController:

    def __init__(self, robot: Any):
        self.robot = robot

    def execute_llm_response(self, response: dict[str, Any]) -> None:
        raise NotImplementedError

    def dispose(self) -> None:
        pass


class Prompter(Generic[P1, P2, P3]):

    @overload
    def __init__(
        self,
        text_input: InputStreamProvider[str],
        llm: ChatAgent,
        chat_server: ChatServer,
        robot_controller: RobotController,
        inputs: InputStreamProvider[P1],
    ): ...

    @overload
    def __init__(
        self,
        text_input: InputStreamProvider[str],
        llm: ChatAgent,
        chat_server: ChatServer,
        robot_controller: RobotController,
        inputs: tuple[InputStreamProvider[P1], InputStreamProvider[P2]],
    ): ...

    @overload
    def __init__(
        self,
        text_input: InputStreamProvider[str],
        llm: ChatAgent,
        chat_server: ChatServer,
        robot_controller: RobotController,
        inputs: tuple[InputStreamProvider[P1], InputStreamProvider[P2], InputStreamProvider[P3]],
    ): ...

    def __init__(
        self,
        text_input: InputStreamProvider[str],
        llm: ChatAgent,
        chat_server: ChatServer,
        robot_controller: RobotController,
        inputs: (
            None
            | InputStreamProvider[P1]
            | tuple[InputStreamProvider[P1]]
            | tuple[InputStreamProvider[P1], InputStreamProvider[P2]]
            | tuple[InputStreamProvider[P1], InputStreamProvider[P2], InputStreamProvider[P3]]
        ) = None,
    ):
        self.llm = llm

        if isinstance(inputs, InputStreamProvider):
            inputs = (inputs,)

        self.inputs = inputs
        self.text_input = text_input
        self.chat_server = chat_server
        self.robot_controller = robot_controller

        self.prompt_data = PromptInputData()

        text_input._stream.subscribe(lambda text: chat_server.add_message(text.value, "You"))

        user_messages_stream = chat_server.message_stream.pipe(
            ops.filter(lambda m: m.from_chat),
            ops.map(lambda m: Input(text_input, m.text, m.timestamp)),
        )
        text_input_stream: Observable[Input[str]] = rx.merge(text_input._stream, user_messages_stream)

        if isinstance(inputs, tuple):
            all_inputs: list[InputStreamProvider] = [*inputs, text_input]
            prompt_stream = rx.merge(*[input._stream for input in all_inputs])
        else:
            prompt_stream: Observable[Input] = text_input_stream

        self.prompt_stream_subscription = prompt_stream.pipe(
            ops.map(self._to_prompt_input_data),
            ops.filter(self.detect_prompt_ending),
            ops.map(self.create_prompt),
            ops.map(self.llm.prompt),
        ).subscribe(self.__handle_llm_response)

    def _to_prompt_input_data(self, input: Input) -> PromptInputData[P1, P2, P3]:

        if input.source == self.text_input:
            self.prompt_data.question = input
        else:
            self.prompt_data.add_input(input)

        return self.prompt_data

    def create_prompt(self, input_data: PromptInputData[P1, P2, P3]) -> dict[str, str]:
        raise NotImplementedError("create_prompt method must be implemented")

    def __handle_llm_response(self, response: dict[str, Any]) -> None:
        self.prompt_data = PromptInputData()
        answer = response.get("clean_answer") or response.get("answer", "There was a problem with the answer!")
        self.chat_server.add_message(answer, "ZeKI GPT")
        response = self.transform_llm_response(response)
        self.robot_controller.execute_llm_response(response)

    def transform_llm_response(self, response: dict[str, Any]) -> dict[str, Any]:
        return response

    def detect_prompt_ending(self, prompt_data: PromptInputData) -> bool:
        if prompt_data.question == None:
            return False
        return True

    def dispose(self) -> None:
        self.text_input.dispose()
        self.chat_server.stop()
        self.prompt_stream_subscription.dispose()
        if self.inputs is not None:
            for input in self.inputs:
                input.dispose()
