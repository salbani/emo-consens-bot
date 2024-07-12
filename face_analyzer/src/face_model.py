from typing import Any, Callable

import numpy as np
import numpy.typing as npt

FACE_MODEL_INDICES = [
    4,  # Nose tip
    152,  # Chin
    263,  # Left eye, left corner
    33,  # Right eye, right corner
    287,  # Left Mouth corner
    57,  # Right mouth corner
]

MOUTH_MODEL_INDICES = [
    13,  # upper inner Lip
    14,  # lower inner Lip
    78,  # left inner Lip
    308,  # right inner Lip
]

PUPIL_MODEL_INDICES = [
    468,  # Left pupil
    473,  # Right pupil
]


class FaceModel:

    model_points = np.array(
        [
            (0.0, 0.0, 0.0),  # Nose tip
            (0, -63.6, -12.5),  # Chin
            (-43.3, 32.7, -26),  # Left eye, left corner
            (43.3, 32.7, -26),  # Right eye, right corner
            (-28.9, -28.9, -24.1),  # Left Mouth corner
            (28.9, -28.9, -24.1),  # Right mouth corner
        ],
        dtype=np.float32,
    )

    # 3D model eye points
    Eye_ball_center_right = np.array([-29.05, 32.7, -35.5], dtype=np.float32)
    Eye_ball_center_left = np.array([29.05, 32.7, -35.5], dtype=np.float32)

    def __init__(self, landmarks, projection_func: Callable[[Any], npt.NDArray[np.float32]]):
        self.face_points = np.array([projection_func(landmarks[i]) for i in FACE_MODEL_INDICES], dtype=np.float32)
        self.mouth_points = np.array([projection_func(landmarks[i]) for i in MOUTH_MODEL_INDICES], dtype=np.float32)
        self.pupil_points = np.array([projection_func(landmarks[i]) for i in PUPIL_MODEL_INDICES], dtype=np.float32)
