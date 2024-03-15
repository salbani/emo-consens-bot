import socket
import struct
import cv2
import numpy as np

def client():

    def display_image(buffer, height, width):
        
        image = np.frombuffer(buffer, dtype=np.uint8).reshape((height, width, 3))
        
        # Display the image frame
        cv2.imshow('Pepper Video Stream', image)
        cv2.waitKey(1)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(('pepper.local', 40098))
        try:
            while True:
                header_format = '!I I I'  # Adjusted to include buffer_size
                header_size = struct.calcsize(header_format)
                header_data = client_socket.recv(header_size)
                if not header_data:
                    print("Server closed the connection.")
                    break

                image_width, image_height, buffer_size = struct.unpack(header_format, header_data)

                # Now receive the buffer based on the received size
                buffer = b''
                while len(buffer) < buffer_size:
                    chunk = client_socket.recv(buffer_size - len(buffer))
                    if not chunk:
                        print("Failed to receive all data.")
                        break
                    buffer += chunk

                display_image(buffer, image_height, image_width)


        except KeyboardInterrupt:
            print("Client shutting down.")
            client_socket.close()
            exit(0)

client()