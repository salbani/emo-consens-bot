from optparse import OptionParser
import struct
from data_streaming_server import DataStreamingServer
import qi
import argparse
import sys
import time
import vision_definitions


def main(session):
    """
    """
    server = DataStreamingServer(40098)

    video_service = session.service("ALVideoDevice")

    # Register a Generic Video Module
    nameId = video_service.subscribeCamera(
        "python_GVM",
        vision_definitions.kTopCamera,
        vision_definitions.kVGA,
        vision_definitions.kBGRColorSpace,
        20
    )
    server.listenAsync()

    print("Streaming video...")
    try:
        while True:
            image = video_service.getImageRemote(nameId)
            image_width = image[0]
            image_height = image[1]
            buffer = image[6]
            buffer_size = len(buffer)

            # Include buffer_size in the header
            header_format = '!I I I'  # Adding an extra 'I' for buffer_size
            header_data = struct.pack(header_format, image_width, image_height, buffer_size)
            server.stream(header_data + buffer)
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("Interrupted by user, shutting down")
        server.close()

    video_service.unsubscribe(nameId)


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

    session = qi.Session()
    try:
        session.connect("tcp://" + pepper_ip + ":" + str(pepper_port))
    except RuntimeError:
        print ("Can't connect to Naoqi at ip \"" + pepper_ip + "\" on port " + str(pepper_port) +".\n"
                "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)
    main(session)