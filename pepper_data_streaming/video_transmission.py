from optparse import OptionParser
import struct
from data_streaming_server import DataStreamingServer
import qi
import argparse
import sys
import time
import vision_definitions

class VideoTransmissionModule(object):
    def __init__(self, session):
        self.session = session
        self.streaming_server = DataStreamingServer(40098)

        self.video_service = session.service("ALVideoDevice")

        # Register a Generic Video Module
        self.nameId = self.video_service.subscribeCamera(
            "python_GVM",
            vision_definitions.kTopCamera,
            vision_definitions.kQVGA,
            vision_definitions.kBGRColorSpace,
            20
        )
        self.streaming_server.listenAsync()
        self.is_running = False

    def start(self):
        print("Streaming video...")
        self.is_running = True
        
        while self.is_running:
            image = self.video_service.getImageRemote(self.nameId)
            image_width = image[0]
            image_height = image[1]
            buffer = image[6]
            buffer_size = len(buffer)

            # Include buffer_size in the header
            header_format = '!I I I'  # Adding an extra 'I' for buffer_size
            header_data = struct.pack(header_format, image_width, image_height, buffer_size)
            self.streaming_server.stream(header_data + buffer)
            time.sleep(0.05)

        self.video_service.unsubscribe(self.nameId)
        self.streaming_server.close()
        print("Video stream stopped")
    
    def stop(self):
        self.is_running = False

    @staticmethod
    def setup(ip, port):
        session = qi.Session()
        try:
            session.connect("tcp://" + ip + ":" + str(port))
        except RuntimeError:
            print ("Can't connect to Naoqi at ip \"" + ip + "\" on port " + str(port) +".\n"
                    "Please check your script arguments. Run with -h option for help.")
            sys.exit(1)
        module = VideoTransmissionModule(session)
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

    videoTransmissionModule = VideoTransmissionModule.setup(pepper_ip, pepper_port)
    videoTransmissionModule.start()
