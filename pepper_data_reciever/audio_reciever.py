import socket
import struct
import pyaudio
import numpy as np

def client():
    channels = 1
    sample_rate = 48000  # Hz, adjust this to match your audio stream's sample rate
    samples = 4096
    buffer_size = 32768  # This may refer to the byte size of your buffer

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open stream
    stream = p.open(format=pyaudio.paInt16,  # This assumes 16-bit samples; adjust as necessary
                    channels=channels,
                    rate=sample_rate,
                    output=True)
    
    def play(buffer):
        stream.write(buffer)

    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(('pepper.local', 40099))
        try:
            while True:
                header_format = '!I I I I I'  # Adjusted to include buffer_size
                header_size = struct.calcsize(header_format)
                header_data = client_socket.recv(header_size)
                if not header_data:
                    print("Server closed the connection.")
                    break

                nbOfChannels, nbrOfSamplesByChannel, timeStamp1, timeStamp2, buffer_size = struct.unpack(header_format, header_data)
                aTimeStamp = [timeStamp1, timeStamp2]

                # Now receive the buffer based on the received size
                buffer = b''
                while len(buffer) < buffer_size:
                    chunk = client_socket.recv(buffer_size - len(buffer))
                    if not chunk:
                        print("Failed to receive all data.")
                        break
                    buffer += chunk

                print(f"Data received: Channels={nbOfChannels}, Samples={nbrOfSamplesByChannel}, TimeStamps={aTimeStamp}, Buffer Size={len(buffer)}")
                play(buffer)

        except KeyboardInterrupt:
            print("Client shutting down.")

    stream.stop_stream()
    stream.close()
    
    p.terminate()

if __name__ == "__main__":
    client()