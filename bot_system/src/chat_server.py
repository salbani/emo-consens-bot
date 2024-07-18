from flask import Flask, render_template
from flask_socketio import SocketIO
import threading

from bot_system.src.lib.core import ChatServer
from bot_system.src.handlers.speech_intent_detection_handler import SpeechIntent, SpeechIntentDetectionHandler


class PepperChatServer(ChatServer):
    """
    A class representing a chat server for Pepper robot. Extends the ChatServer class.
    """

    def __init__(self, speech_intent_handler: SpeechIntentDetectionHandler | None = None, start=True):
        """
        Create a new instance of the PepperChatServer class.

        Args:
            speech_intent_handler (SpeechIntentDetectionHandler | None, optional): The speech intent handler. If provided, the chat server will send speech intents to the client to be displayed. Defaults to None.
            start (bool, optional): Whether to start the server automatically. Defaults to True.
        """
        super().__init__()
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app)

        if speech_intent_handler is not None:
            speech_intent_handler._stream.subscribe(lambda input: self.send_intent(input.value))

        self.setup_routes()
        self.setup_socketio_events()
        self.server_thread = None

        if start:
            self.run()

    def setup_routes(self):
        """ Set up the routes for the flask server. """
        @self.app.route("/")
        def index():
            return render_template("chat.html", messages=self.get_messages())

    def setup_socketio_events(self):
        """ Set up the SocketIO events for the chat server. Enables the server to receive messages from the chat UI. """
        @self.socketio.on("send_message")
        def handle_send_message(data):
            message = data["message"]
            sender = data["sender"]
            self.add_message(message, sender, from_chat=True)
            print(f"Received message from {sender}: {message}")

    # Override
    def send_message(self, message):
        self.socketio.emit("message", {"message": message.text, "sender": message.sender})

    def send_intent(self, intent: SpeechIntent):
        """
        Send a speech intent to the chat clients.

        Args:
            intent (SpeechIntent): The speech intent to send.
        """
        self.socketio.emit(
            "intent",
            {
                "is_moving_mouth": intent.is_moving_mouth,
                "has_eye_contact": intent.has_eye_contact,
                "is_speech": intent.is_speech,
            },
        )

    def run(self, host="0.0.0.0", port=4200):
        """
        Run the chat server.

        Args:
            host (str, optional): The host address to bind the server to. Defaults to "0.0.0.0".
            port (int, optional): The port number to bind the server to. Defaults to 4200.
        """
        self.server_thread = threading.Thread(target=self.socketio.run, args=(self.app,), kwargs={"host": host, "port": port, "debug": False, "use_reloader": False})
        self.server_thread.start()

    def run_unthreaded(self, host="0.0.0.0", port=4200):
        """
        Run the chat server in a single-threaded mode.

        Args:
            host (str, optional): The host address to bind the server to. Defaults to "0.0.0.0".
            port (int, optional): The port number to bind the server to. Defaults to 4200.
        """
        self.socketio.run(self.app, host=host, port=port, debug=False, use_reloader=True, log_output=True)


if __name__ == "__main__":
    chat_server = PepperChatServer(start=False)
    chat_server.run_unthreaded()
