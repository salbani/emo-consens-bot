import select
import sys
import time
from optparse import OptionParser

import qi


class PepperBridge():
    """
    The PepperBridge class represents a bridge between the Pepper robot and the application.
    It encapsulates the communication with the Pepper robot through the Naoqi API and provides the relevant functionality through IO communication.
    
    It provides methods to control the robot's tablet, speech, and memory.
    This encapsulation is needed because the qi framework runs on Python 2.7 only, while the application depends on python 3.12.
    """

    def __init__(self, session):
        """
        Create a new instance of the PepperBridge class.

        Args:
            session (qi.Session): The session object for connecting to the Pepper robot.
        """
        self.session = session

        self.tablet_service = session.service("ALTabletService")
        self.tablet_service.showWebview("http://10.42.0.38:4200")

        self.animated_speech = session.service("ALAnimatedSpeech")
        self.memory = session.service("ALMemory")

        self.sub = self.memory.subscriber("ALAnimatedSpeech/EndOfAnimatedSpeech")
        self.sub.signal.connect(self.on_speech_end)

    def on_speech_end(self):
        """Callback function called when the animated speech ends."""
        sys.stdout.write("event:speech_ended\n")
        sys.stdout.flush()

    def read_stdin_on_thread(self):
        """Start listen_stdin on a separate thread."""
        import threading
        threading.Thread(target=self.listen_stdin).start()

    def listen_stdin(self):
        """Listen to stdin and process the input."""
        self.is_running = True
        while self.is_running:
            if select.select([sys.stdin], [], [], 0)[0]:
                event = sys.stdin.readline().strip()
                if event and event.startswith("say:"):
                    self.say(event[4:])

    def say(self, text: str):
        """
        Make the robot say the specified text through the ALAnimatedSpeech Module.

        Args:
            text (str): The text to be spoken by the robot.

        """
        self.animated_speech.say(text)

    def start(self):
        """Start the PepperBridge."""
        self.read_stdin_on_thread()
        print("PepperBridge is running...")

    def stop(self):
        """Stop the PepperBridge."""
        self.is_running = False

    @staticmethod
    def setup(ip, port):
        """
        Set up the PepperBridge with a qi session.

        Args:
            ip (str): The IP address of the Pepper robot.
            port (int): The port number for connecting to the Pepper robot.

        Returns:
            PepperBridge: An instance of the PepperBridge class.

        """
        session = qi.Session()
        try:
            session.connect("tcp://" + ip + ":" + str(port))
        except RuntimeError:
            print ("Can't connect to Naoqi at ip \"" + ip + "\" on port " + str(port) +".\n"
                    "Please check your script arguments. Run with -h option for help.")
            sys.exit(1)
        module = PepperBridge(session)
        print("VideoTransmissionModule instance created")
        return module



if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--ip",
        help="Parent broker port. The IP address or your robot",
        dest="ip")
    parser.add_option("--port",
        help="Parent broker port. The port NAOqi is listening to",
        dest="port",
        type="int")
    parser.set_defaults(
        ip="pepper.local",
        port=9559)

    (opts, args_) = parser.parse_args()
    pepper_ip   = opts.ip
    pepper_port = opts.port

    pepperBridge = None
    try:
        pepperBridge = PepperBridge.setup(pepper_ip, pepper_port)
        pepperBridge.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        if pepperBridge is not None:
            pepperBridge.stop()
        sys.exit(0)
