from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import threading
import reactivex as rx

from bot_system.core import ChatServer


class PepperChatServer(ChatServer):
    def __init__(self, start=True):
        super().__init__()
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app)

        self.setup_routes()
        self.setup_socketio_events()
        self.server_thread = None

        if start:
            self.run()

    def setup_routes(self):
        @self.app.route("/")
        def index():
            return render_template("chat.html", messages=self.get_messages())

    def setup_socketio_events(self):
        @self.socketio.on("send_message")
        def handle_send_message(data):
            message = data["message"]
            sender = data["sender"]
            self.add_message(message, sender, from_chat=True)
            print(f"Received message from {sender}: {message}")

    def send_message(self, message):
        self.socketio.emit("message", {"message": message.text, "sender": message.sender})

    def run(self, host="0.0.0.0", port=4200):
        self.server_thread = threading.Thread(target=self.socketio.run, args=(self.app,), kwargs={"host": host, "port": port, "debug": False, "use_reloader": False})
        self.server_thread.start()

    def run_unthreaded(self, host="0.0.0.0", port=4200):
        self.socketio.run(self.app, host=host, port=port, debug=False, use_reloader=True, log_output=True)


if __name__ == "__main__":
    chat_server = PepperChatServer(False)
    chat_server.run_unthreaded()
