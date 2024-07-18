from collections import deque
from dataclasses import dataclass

import cv2
import numpy as np
from cv2.typing import MatLike

from face_analyzer.src.camera_calibration import CameraCalibration
from face_analyzer.src.face_model import FaceModel
from face_analyzer.src.math import calc_angle
from face_analyzer.src.mouth_angle_buffer import MouthAngleBuffer
from face_analyzer.src.world_projection import WorldProjection

@dataclass
class FaceAnalysisResult:
    angle_radians: np.float32
    mouth_angle_fluctuation: np.float32


class FaceAnalyzer:
    def __init__(self):
        self.frame_shape: tuple[int, int] = (0, 0)
        self.analyzed_frame_pos: tuple[int, int] = (0, 0)
        self.analyzed_frame_shape: tuple[int, int] = (0, 0)
        self.mouth_angle_buffer = MouthAngleBuffer(10)
        self.calibration: CameraCalibration | None = None

    def relative_pos(self, percent_coords):
        """
        Translate percentage coordinates from the analyzed frame to pixel coordinates in the original frame.

        Parameters:
        - percent_coords: Tuple of percentage coordinates (percent_x, percent_y).

        Returns:
        - pixel_coords: Tuple of pixel coordinates (x, y) in the original frame.
        """

        analyzed_width, analyzed_height = self.analyzed_frame_shape
        cutout_x, cutout_y = self.analyzed_frame_pos

        # Convert percentage coordinates to pixel coordinates in the analyzed frame
        pixel_x_in_analyzed = percent_coords.x * analyzed_width
        pixel_y_in_analyzed = percent_coords.y * analyzed_height

        # Translate pixel coordinates to the original frame
        pixel_x_in_original = cutout_x + pixel_x_in_analyzed
        pixel_y_in_original = cutout_y + pixel_y_in_analyzed

        return np.array([pixel_x_in_original, pixel_y_in_original], dtype=np.float32)

    def analyze(self, frame: MatLike, landmarks, analyzed_frame_pos: tuple[int, int], analyzed_frame_shape: tuple[int, int], draw_on_frame=False):
        if self.calibration == None or not self.calibration.is_same_camera(frame):
            self.calibration = CameraCalibration(frame.shape)

        self.analyzed_frame_pos = analyzed_frame_pos
        self.analyzed_frame_shape = analyzed_frame_shape

        face_model = FaceModel(landmarks, self.relative_pos)

        try:
            world = WorldProjection(self.calibration, face_model.face_points, face_model.model_points)
        except ValueError:
            return

        self.mouth_angle_buffer.add_angle(face_model.mouth_points)
        mouth_angle = self.mouth_angle_buffer.mean_angle()
        mouth_angle_fluctuation = self.mouth_angle_buffer.mean_fluctuation()

        # project pupil image point into 3d world point
        gaze_l, pupil_world_cord_l = world.direction(face_model.Eye_ball_center_left, face_model.pupil_points[0])
        gaze_r, pupil_world_cord_r = world.direction(face_model.Eye_ball_center_right, face_model.pupil_points[1])

        gaze_mid = (gaze_l + gaze_r) / 2
        # Transform gaze_mid to camera coordinates
        x, y, z = world.image_basis()

        # Berechnung des Winkels in Radiant
        angle_radians = calc_angle([0, 0, 0], gaze_mid, z)  # np.clip stellt sicher, dass der Wert im Bereich [-1, 1] liegt

        # rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
        # Combine rotation matrix and translation vector to form a 3x4 projection matrix
        # projection_matrix = np.hstack((rotation_matrix, translation_vector.reshape(-1, 1)))

        # # Decompose the projection matrix to extract Euler angles
        # _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(projection_matrix)
        # pitch, yaw, roll = euler_angles.flatten()[:3]

        # # Draw Euler angles on the frame
        # cv2.putText(frame, f"Pitch: {pitch:.2f}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        # cv2.putText(frame, f"Yaw: {yaw:.2f}", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        # cv2.putText(frame, f"Roll: {roll:.2f}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        if draw_on_frame:
            self.draw_mouth_debug_info(frame, mouth_angle, mouth_angle_fluctuation)

            for model_point in face_model.model_points:
                world.draw_point(frame, model_point, (0, 255, 255))

            for point in face_model.face_points:
                cv2.circle(frame, (int(point[0]), int(point[1])), 3, (0, 255), -1)

            for mouth_point in face_model.mouth_points:
                cv2.circle(frame, (int(mouth_point[0]), int(mouth_point[1])), 3, (0, 0, 255), -1)

            # for point in points.landmark:
            #     cv2.circle(frame, relative(point, frame.shape), 3, (0, 255, 0), -1)

            world.draw_point(frame, face_model.Eye_ball_center_right, (255, 255, 255))
            world.draw_point(frame, face_model.Eye_ball_center_left, (255, 255, 255))

            world.draw_line(frame, face_model.pupil_points[0], pupil_world_cord_l, gaze_l)
            world.draw_line(frame, face_model.pupil_points[1], pupil_world_cord_r, gaze_r)
            world.draw_line(frame, face_model.face_points[0], face_model.model_points[0], gaze_mid)

            world.draw_line(frame, face_model.face_points[0], face_model.model_points[0], x, color=(0, 0, 255))
            world.draw_line(frame, face_model.face_points[0], face_model.model_points[0], y, color=(0, 255, 0))
            world.draw_line(frame, face_model.face_points[0], face_model.model_points[0], z, color=(255, 0, 0))

            cv2.putText(frame, f"Angle: {angle_radians:.2f} rad", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        return FaceAnalysisResult(angle_radians, mouth_angle_fluctuation)

    def draw_mouth_debug_info(self, frame: MatLike, mouth_area, mouth_area_fluctuation):
        cv2.putText(frame, f"Mouth Angle: {mouth_area:.2f}", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.rectangle(frame, (20, 300), (20 + int(mouth_area / self.mouth_angle_buffer.max * 300), 300 + 50), (0, 0, 255), -1)
        cv2.rectangle(frame, (20, 300), (20 + 300, 300 + 50), (255, 255, 255), 2)

        cv2.putText(frame, f"Mouth Angle Fluctuation: {mouth_area_fluctuation:.2f}", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.rectangle(frame, (20, 350), (20 + int(mouth_area_fluctuation * 300), 350 + 50), (0, 0, 255), -1)
        cv2.rectangle(frame, (20, 350), (20 + 300, 350 + 50), (255, 255, 255), 2)
