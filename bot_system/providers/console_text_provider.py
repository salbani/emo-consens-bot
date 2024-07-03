from threading import Lock, Thread
import time

from bot_system.core import InputStreamProvider


class ConsoleTextProvider(InputStreamProvider[str]):

    def __init__(self):
        super().__init__()

        self.words_per_second = 0.5
        self.recording = True

        self.lock = Lock()
        self.capture_thread = Thread(target=self._get_input)
        self.capture_thread.start()

    def dispose(self):
        self.recording = False
        super().dispose()

    def _get_input(self):
        with self.lock:
            while self.recording:
                user_input = input("Enter something: ")
                captured_time = time.time() - user_input.count(" ") / self.words_per_second
                self.output(user_input, captured_time)
