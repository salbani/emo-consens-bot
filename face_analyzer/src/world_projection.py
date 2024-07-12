import cv2
import numpy as np
import numpy.typing as npt
from cv2.typing import MatLike

from face_analyzer.src.camera_calibration import CameraCalibration


class WorldProjection:
    def __init__(self, calibration: CameraCalibration, image_points: npt.NDArray[np.float32], model_points: npt.NDArray[np.float32]) -> None:
        self.calibration = calibration
        self.image_points = image_points
        self.model_points = model_points
        self.calc_PnP_transformation()
        self.calc_affine_transformation()

    def calc_affine_transformation(self):
        image_points_3D = np.pad(self.image_points, ((0, 0), (0, 1)), "constant", constant_values=0)
        ret, self.affine_transformation, _ = cv2.estimateAffine3D(image_points_3D, self.model_points)
        if not ret:
            raise ValueError("Affine transformation not found")

    def calc_PnP_transformation(self):
        ret, self.rotation_vector, self.translation_vector = cv2.solvePnP(
            self.model_points,
            self.image_points,
            self.calibration.camera_matrix,
            self.calibration.dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not ret:
            raise ValueError("PnP solution not found")

    def image_basis(self):
        x = [1, 0, 0]
        y = [0, 1, 0]
        z = [0, 0, 1]

        rotation_matrix, _ = cv2.Rodrigues(self.rotation_vector)

        x = np.dot(rotation_matrix.T, x)
        x = x / np.linalg.norm(x) * 50

        y = np.dot(rotation_matrix.T, y)
        y = y / np.linalg.norm(y) * 50

        z = np.dot(rotation_matrix.T, z)
        z = z / np.linalg.norm(z) * 50

        return x, y, z

    def to_world_coord(self, image_coord: npt.NDArray[np.float32]):
        # convert to 3D coordinate and add a 1 for homogeneous coordinates
        image_coord = np.concatenate([image_coord[:3], [0, 0, 0, 1][min(len(image_coord), 3) :]])
        return (self.affine_transformation @ np.array([image_coord]).T).flatten()

    def to_image_coord(self, world_coord):
        (image_coord, _) = cv2.projectPoints(
            np.array(world_coord[:3], np.float32),
            self.rotation_vector,
            self.translation_vector,
            self.calibration.camera_matrix,
            self.calibration.dist_coeffs,
        )
        return image_coord[0][0]

    def direction(self, origin_world: npt.NDArray[np.float32], target_image: npt.NDArray[np.float32]):
        target_world_cord = self.to_world_coord(target_image)
        # 3D gaze point (10 is arbitrary value denoting gaze distance)
        gaze_world_dir = (target_world_cord - origin_world) * 10

        return gaze_world_dir, target_world_cord

    def draw_point(self, frame: MatLike, world_coord: npt.NDArray[np.float32], color=(255, 255, 0)):
        image_coord = self.to_image_coord(world_coord)
        cv2.circle(frame, (int(image_coord[0]), int(image_coord[1])), 3, color, -1)

    def draw_line(self, frame: MatLike, origin_image_coord: npt.NDArray[np.float32], origin_world_cord: npt.NDArray[np.float32], direction: npt.NDArray[np.float32], color=(0, 0, 255)):
        target_world_coord = origin_world_cord + direction

        projected_target_image_coord = self.to_image_coord(target_world_coord)
        projected_origin_image_coord = self.to_image_coord(origin_world_cord)

        corrected_target_image_coord = origin_image_coord + (projected_target_image_coord - origin_image_coord) - (projected_origin_image_coord - origin_image_coord)

        cv2.circle(frame, (int(corrected_target_image_coord[0]), int(corrected_target_image_coord[1])), 3, [255, 0, 0], -1)
        # Draw gaze line into screen
        # p1 = (int(pupil[0]), int(pupil[1]))
        # p2 = (int(gaze[0]), int(gaze[1]))
        p1 = (int(corrected_target_image_coord[0]), int(corrected_target_image_coord[1]))
        p2 = (int(origin_image_coord[0]), int(origin_image_coord[1]))
        cv2.line(frame, p1, p2, color, 2)
