import dataclasses

import numpy as np


@dataclasses.dataclass
class PMLProfile:
    data: np.ndarray
    a: np.ndarray
    b: np.ndarray
    c: np.ndarray
    d: np.ndarray
