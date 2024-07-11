from dataclasses import dataclass
from threading import Thread
import time
from typing import Any, Generic, TypeVar, overload

import reactivex as rx
from reactivex import operators as ops

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
    def __init__(self, providers: InputStreamProvider[P1]) -> None: ...
    @overload
    def __init__(self, providers: tuple[InputStreamProvider[P1], InputStreamProvider[P2]]) -> None: ...
    @overload
    def __init__(self, providers: tuple[InputStreamProvider[P1], InputStreamProvider[P2], InputStreamProvider[P3]]) -> None: ...

    def __init__(
        self,
        providers: (
            InputStreamProvider[P1]
            | tuple[InputStreamProvider[P1]]
            | tuple[InputStreamProvider[P1], InputStreamProvider[P2]]
            | tuple[InputStreamProvider[P1], InputStreamProvider[P2], InputStreamProvider[P3]]
        ),
    ):
        super().__init__()
        if isinstance(providers, InputStreamProvider):
            providers = (providers,)
        self.providers = providers
        self._setup_provider_stream(providers)
        self.is_paused = False

    def _setup_provider_stream(
        self, providers: tuple[InputStreamProvider[P1]] | tuple[InputStreamProvider[P1], InputStreamProvider[P2]] | tuple[InputStreamProvider[P1], InputStreamProvider[P2], InputStreamProvider[P3]]
    ) -> None:
        provider_streams = map(lambda x: (x._stream), list(providers))
        rx.merge(*provider_streams).subscribe(self._handle_on_thread)

    def _handle_on_thread(self, input: Input[P1] | Input[P2] | Input[P3]) -> None:
        Thread(target=self.handle, args=(input,)).start()

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
    def __init__(self, question: Input[str]) -> None:
        self.question = question
        self.input_buffers: dict[InputStreamProvider, list[Input[Any]]] = {}

    @overload
    def add_input(self, provider: InputStreamProvider[P1], value: Input[P1]) -> None: ...
    @overload
    def add_input(self, provider: InputStreamProvider[P2], value: Input[P2]) -> None: ...
    @overload
    def add_input(self, provider: InputStreamProvider[P3], value: Input[P3]) -> None: ...

    def add_input(self, provider: InputStreamProvider[P1] | InputStreamProvider[P2] | InputStreamProvider[P3], value: Input[P1] | Input[P2] | Input[P3]) -> None:
        if provider not in self.input_buffers:
            self.input_buffers[provider] = []

        self.input_buffers[provider].append(value)

    @overload
    def get_input(self, provider: type[InputStreamProvider[P1]]) -> list[Input[P1]]: ...
    @overload
    def get_input(self, provider: type[InputStreamProvider[P2]]) -> list[Input[P2]]: ...
    @overload
    def get_input(self, provider: type[InputStreamProvider[P3]]) -> list[Input[P3]]: ...

    def get_input(self, provider: type[InputStreamProvider[P1]] | type[InputStreamProvider[P2]] | type[InputStreamProvider[P3]]) -> list[Input[P1]] | list[Input[P2]] | list[Input[P3]]:
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
        self.message_stream.on_next(Message(message, sender, from_chat=from_chat))
        self.messages.append({"message": message, "sender": sender})

    def send_message(self, message: Message) -> None:
        raise NotImplementedError

    def get_messages(self):
        return self.messages

    def stop(self) -> None:
        self.message_stream.on_completed()


class RobotController:

    def __init__(self, robot: Any):
        self.robot = robot

    def execute_bot_response(self, response: dict[str, Any]) -> None:
        raise NotImplementedError


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

        text_input._stream.subscribe(lambda text: chat_server.add_message(text.value, "You"))

        user_messages_stream = chat_server.message_stream.pipe(
            ops.filter(lambda m: m.from_chat),
            ops.map(lambda m: Input(text_input, m.text, m.timestamp)),
        )
        text_input_stream = rx.merge(text_input._stream, user_messages_stream)

        if isinstance(inputs, tuple):
            input_streams = [input._stream.pipe(ops.map(lambda x: (input, x))) for input in inputs]

            prompt_stream = rx.merge(*input_streams).pipe(
                ops.buffer(text_input_stream),
                ops.with_latest_from(text_input_stream),
                ops.map(lambda x: self.__create_prompt_input_data(x[1], x[0])),
            )
        else:
            prompt_stream = text_input_stream.pipe(
                ops.map(lambda x: self.__create_prompt_input_data(x, [])),
            )


        prompt_stream.pipe(
            ops.map(self.create_prompt),
            ops.map(self.llm.prompt),
        ).subscribe(self.__handle_llm_response)

    def __create_prompt_input_data(self, question: Input[str], input_buffer: list[tuple[InputStreamProvider, Input[Any]]]) -> PromptInputData[P1, P2, P3]:
        data = PromptInputData(question)
        for provider, input in input_buffer:
            data.add_input(provider, input)
        return data

    def create_prompt(self, input_data: PromptInputData[P1, P2, P3]) -> dict[str, str]:
        raise NotImplementedError("create_prompt method must be implemented")
    
    def __handle_llm_response(self, response: dict[str, Any]) -> None:
        answer = response.get("clean_answer") or response.get("answer", "There was a problem with the answer!")
        self.chat_server.add_message(answer, "ZeKI GPT")
        response = self.transform_llm_response(response)
        self.robot_controller.execute_bot_response(response)

    def transform_llm_response(self, response: dict[str, Any]) -> dict[str, Any]:
        return response

    def dispose(self) -> None:
        self.text_input.dispose()
        if self.inputs is not None:
            for input in self.inputs:
                input.dispose()
