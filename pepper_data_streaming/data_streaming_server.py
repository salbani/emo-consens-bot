import socket
import threading
import Queue

# This is a thread-safe queue where we'll put the data chunks received from the service

class DataStreamingServer:
    def __init__(self, port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = '0.0.0.0'  # Listen on all network interfaces
        self.port = port
        self.is_listening = False
        self.is_connected = False
        self.reset_queue()

    def reset_queue(self):
        self.data_queue = Queue.Queue()
        
        
    def handle_client_connection(self, client_socket):
        print("Server: New client connected with address " + str(client_socket.getpeername()))
        try:
            while self.is_listening:
                # Wait for data to be available in the queue and send it to the client
                self.is_connected = True
                data_chunk = self.data_queue.get()
                if data_chunk is None:
                    break  # Use None as a signal to close the connection
                client_socket.sendall(data_chunk)
        except socket.error as e:
            print("Server: Client connection error: " + str(e))
        finally:
            client_socket.close()
            self.is_connected = False
            self.reset_queue()
            print("Server: Client connection closed")

    def listen(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.server_socket.settimeout(1)
        self.is_listening = True

        print("Server listening on " + str(self.host) + ":" + str(self.port))

        try:
            while self.is_listening:
                try:
                    client_socket, _ = self.server_socket.accept()
                    client_thread = threading.Thread(target=self.handle_client_connection, args=(client_socket,))
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    print("Error: " + str(e))
                    break
        finally:
            self.is_listening = False
            self.data_queue = Queue.Queue()
            self.server_socket.close()
            print("Server: Stopped listening")

    def listenAsync(self):
        # Start the server in a new thread
        self.server_thread = threading.Thread(target=self.listen)
        self.server_thread.start()

    def close(self):
        print("Server: Stopping...")
        self.data_queue.put(None)
        self.is_listening = False

    # Example function that simulates receiving data from another service and putting it into the queue
    def stream(self, data):
        if self.is_connected:
            self.data_queue.put(data)  # Signal to close the client connection
            return True
        else:
            return False