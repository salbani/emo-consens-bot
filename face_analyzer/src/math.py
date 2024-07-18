import numpy as np
import numpy.typing as npt


def calc_angle(root: npt.ArrayLike, p1: npt.ArrayLike, p2: npt.ArrayLike):
    v1 = np.array(p1, dtype=np.float32) - np.array(root, dtype=np.float32)
    v2 = np.array(p2, dtype=np.float32) - np.array(root, dtype=np.float32)

    unit_v1 = v1 / np.linalg.norm(v1)
    unit_v2 = v2 / np.linalg.norm(v2)
    dot_product: np.float32 = np.dot(unit_v1, unit_v2)
    angle: np.float32 = np.arccos(np.clip(dot_product, -1.0, 1.0), dtype=np.float32)
    return angle
