import time
import audio_reciever as ar
import video_reciever as vr
import threading
import queue


if __name__ == "__main__":
    callback_queue = queue.Queue(1)

    video_thread = threading.Thread(target=vr.VideoReceiver, args=[callback_queue])
    audio_thread = threading.Thread(target=ar.AudioReceiver)

    video_thread.start()
    audio_thread.start()

    try:
        while True:
            try:
                callback = callback_queue.get(False) #doesn't block
                callback()
            except queue.Empty: #raised when queue is empty
                continue
    except KeyboardInterrupt:
        print("Shutting down...")
        exit(0)