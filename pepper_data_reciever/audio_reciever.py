import socket
import struct

def client():
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

        except KeyboardInterrupt:
            print("Client shutting down.")

client()