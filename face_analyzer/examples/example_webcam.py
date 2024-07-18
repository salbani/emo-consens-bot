import cv2
import mediapipe as mp
from cv2.data import haarcascades
from mediapipe.python.solutions.face_mesh import FaceMesh

import face_analyzer.src.face_analyzer as face_analyzer
from pepper_data_reciever.video_reciever import VideoReceiver

face_cascade = cv2.CascadeClassifier(haarcascades + "haarcascade_frontalface_default.xml")
video_capture = VideoReceiver()
# camera stream:
cap = cv2.VideoCapture(0)  # chose camera index (try 1, 2, 3)
face_mesh = FaceMesh(
        max_num_faces=1,  # number of faces to track in each frame
        refine_landmarks=True,  # includes iris landmarks in the face mesh model
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5)

face_analyzer = face_analyzer.FaceAnalyzer()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:  # no frame input
        print("Ignoring empty camera frame.")
        continue
    # To improve performance, optionally mark the image as not writeable to
    # pass by reference.
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    largest_face = max(faces, key=lambda x: x[2] * x[3], default=None)

    if largest_face is None:
        continue

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # frame to RGB for the face-mesh model

    x, y, w, h = largest_face
    face_roi = rgb_frame[y : y + h, x : x + w]

    results = face_mesh.process(face_roi)

    if results.multi_face_landmarks:
        face_analyzer.analyze(frame, results.multi_face_landmarks[0].landmark, (x, y), (w, h), True)  # gaze estimation

    cv2.imshow('output window', frame)
    if cv2.waitKey(2) & 0xFF == 27:
        break
cap.release()
