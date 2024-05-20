from optparse import OptionParser
import threading
import time

from audio_transmission import AudioTransmissionModule
from video_transmission import VideoTransmissionModule


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
        ip="127.0.0.1",
        port=9559)

    (opts, args_) = parser.parse_args()
    pepper_ip   = opts.ip
    pepper_port = opts.port

    audioTransmissionModule = AudioTransmissionModule.setup(pepper_ip, pepper_port)
    videoTransmissionModule = VideoTransmissionModule.setup(pepper_ip, pepper_port)

    audio_thread = threading.Thread(target=audioTransmissionModule.start)
    video_thread = threading.Thread(target=videoTransmissionModule.start)

    audio_thread.start()
    video_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        audioTransmissionModule.stop()
        videoTransmissionModule.stop()
        exit(0)