
import numpy as np
from cv2.typing import MatLike


class CameraCalibration:
    def __init__(self, frame_shape: tuple[int, ...]):
        self.calibrate_camera(frame_shape)

    def calibrate_camera(self, frame_shape: tuple[int, ...]):
        # Camera matrix estimation
        self.frame_shape = frame_shape
        self.focal_length = self.frame_shape[1]
        self.center = (self.frame_shape[1] / 2, self.frame_shape[0] / 2)
        self.camera_matrix = np.array([[self.focal_length, 0, self.center[0]], [0, self.focal_length, self.center[1]], [0, 0, 1]], dtype="double")
        self.dist_coeffs = np.zeros((4, 1))  # Assuming no lens distortion

    def is_same_camera(self, frame: MatLike):
        return self.frame_shape == frame.shape