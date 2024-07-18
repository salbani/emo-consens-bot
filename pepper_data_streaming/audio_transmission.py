from optparse import OptionParser
import struct
import sys
import time
from data_streaming_server import DataStreamingServer
# from naoqi import ALProxy, ALModule, ALBroker
import qi

SAMPLE_RATE = 16000         # Hz, be careful changing this, both google and Naoqi have requirements!

class AudioTransmissionModule(object):
    moduleName = "AudioTransmission"

    def __init__(self, app):
        super(AudioTransmissionModule, self).__init__()
        
        app.start()
        self.streaming_server = DataStreamingServer(40099)
        self.audio = app.session.service("ALAudioDevice")

        self.nNbrChannelFlag = 3 # ALL_Channels: 0,  AL::LEFTCHANNEL: 1, AL::RIGHTCHANNEL: 2 AL::FRONTCHANNEL: 3  or AL::REARCHANNEL: 4.
        self.nDeinterleave = 0
        self.is_running = False
        
    
    def processRemote(self, nbOfChannels, nbrOfSamplesByChannel, aTimeStamp, buffer):
        ''' 
        This is the function that will be called by the audio module.
        It will be called every time a new buffer is received.
        
        | Keyword arguments:
        | nbOfChannels: long - number of channels in the buffer
        | nbrOfSamplesByChannel: long - number of samples in one channel
        | aTimeStamp: list<long> - [[seconds since start], [milliseconds]]
        | buffer: bytearray - the audio buffer
        ''' 
        buffer_size = len(buffer)

        # Include buffer_size in the header
        header_format = '!I I I I I'  # Adding an extra 'I' for buffer_size
        header_data = struct.pack(header_format, nbOfChannels, nbrOfSamplesByChannel, aTimeStamp[0], aTimeStamp[1], buffer_size)
        
        # Send header and buffer
        self.streaming_server.stream(header_data + buffer)

    def start(self):
        print("Streaming audio...")
        self.is_running = True
        self.audio.setClientPreferences(self.moduleName, SAMPLE_RATE, self.nNbrChannelFlag, self.nDeinterleave) # setting same as default generate a bug !?!
        self.audio.subscribe(self.moduleName)
        self.streaming_server.listenAsync()

        while self.is_running:
            time.sleep(1)
        self.audio.unsubscribe(self.moduleName)
        self.streaming_server.close()
        print("Audio stream stopped")

    def stop(self):
        self.is_running = False

    @staticmethod
    def setup(ip, port):
        try:
            print("Initializing module " + AudioTransmissionModule.moduleName + " with ip \"" + ip + "\" on port " + str(port))
            # Initialize qi framework.
            connection_url = "tcp://" + ip + ":" + str(port)
            app = qi.Application([AudioTransmissionModule.moduleName, "--qi-url=" + connection_url])
        except RuntimeError:
            print ("Can't connect to Naoqi at ip \"" + ip + "\" on port " + str(port) +".\n"
                    "Please check your script arguments. Run with -h option for help.")
            sys.exit(1)

        module = AudioTransmissionModule(app)
        app.session.registerService(module.moduleName, module)
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
        ip="127.0.0.1",
        port=9559)

    (opts, args_) = parser.parse_args()
    pepper_ip   = opts.ip
    pepper_port = opts.port

    audioTransmissionModule = AudioTransmissionModule.setup(pepper_ip, pepper_port)
    audioTransmissionModule.start()
    
    