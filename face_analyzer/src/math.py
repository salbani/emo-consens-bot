import numpy as np
import numpy.typing as npt


def calc_angle(root, p1: npt.NDArray[np.float32], p2: npt.NDArray[np.float32]):
    v1 = p1 - root
    v2 = p2 - root

    unit_v1 = v1 / np.linalg.norm(v1)
    unit_v2 = v2 / np.linalg.norm(v2)
    dot_product = np.dot(unit_v1, unit_v2)
    angle = np.arccos(np.clip(dot_product, -1.0, 1.0))
    return angle
