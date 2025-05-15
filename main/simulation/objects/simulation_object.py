import abc
import dataclasses

import numpy as np
from matplotlib.axes import Axes


@dataclasses.dataclass
class SimulationObject(abc.ABC):
    permittivity: float
    permeability: float
    pos_x: float
    pos_y: float

    @abc.abstractmethod
    def draw(self, axes: Axes) -> None:
        pass

    @abc.abstractmethod
    def place(self, permittivity_array: np.ndarray, permeability_array: np.ndarray) -> None:
        pass

    @property
    def pos_x_int(self) -> int:
        return int(self.pos_x)

    @property
    def pos_y_int(self) -> int:
        return int(self.pos_y)
