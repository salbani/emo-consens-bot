import cv2
import mediapipe as mp
from cv2.data import haarcascades
from mediapipe.python.solutions.face_mesh import FaceMesh
import numpy as np

from face_analyzer.src.face_analyzer import FaceAnalyzer
from pepper_data_reciever.video_reciever import VideoReceiver

face_cascade = cv2.CascadeClassifier(haarcascades + "haarcascade_frontalface_default.xml")
video_capture = VideoReceiver()
face_mesh = FaceMesh(
        max_num_faces=1,  # number of faces to track in each frame
        refine_landmarks=True,  # includes iris landmarks in the face mesh model
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5)
face_analyzer = FaceAnalyzer()

def process_frame(frame, w, h):
    try:
        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.
        frame = np.array(frame, copy=True)
        frame.flags.writeable = True
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        largest_face = max(faces, key=lambda x: x[2] * x[3], default=None)

        if largest_face is not None:
            

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # frame to RGB for the face-mesh model

            x, y, w, h = largest_face
            face_roi = rgb_frame[y : y + h, x : x + w]

            results = face_mesh.process(face_roi)

            if results.multi_face_landmarks:
                face_analyzer.analyze(frame, results.multi_face_landmarks[0].landmark, (x, y), (w, h), True)  # gaze estimation

        cv2.imshow('output window', frame)
        cv2.waitKey(1)
    except Exception as e:
        print(f"Error: {e}")

video_capture.start(process_frame)
