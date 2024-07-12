from collections import deque

import numpy as np
import numpy.typing as npt

from face_analyzer.src.math import calc_angle


class MouthAngleBuffer:
    def __init__(self, maxlen):
        self.buffer: deque[np.float32] = deque(maxlen=maxlen)
        self.max = np.pi * 0.7

    def append(self, value: np.float32):
        self.buffer.append(value)

    def add_angle(self, mouth_points: npt.NDArray[np.float32]):
        angle_left = calc_angle(mouth_points[2], mouth_points[0], mouth_points[1])
        angle_right = calc_angle(mouth_points[3], mouth_points[0], mouth_points[1])
        angle_mean = np.mean([angle_left, angle_right])
        self.append(angle_mean)
        return angle_mean

    def fluctuations(self):
        if len(self.buffer) < 2:
            return [0]
        absolute_changes = np.diff(self.buffer)

        # Compute the fluctuations
        fluctuations = np.abs(absolute_changes) / self.max
        return fluctuations

    def mean_fluctuation(self):
        return np.mean(self.fluctuations())

    def mean_angle(self):
        return np.mean(self.buffer)
