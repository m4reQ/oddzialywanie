import abc
import dataclasses

import numpy as np


@dataclasses.dataclass
class SimulationSource(abc.ABC):
    pos_x: float
    pos_y: float
    frequency: float
    phase_shift: float
    amplitude: float
    data: np.ndarray = dataclasses.field(init=False)

    @abc.abstractmethod
    def calculate_data(self, time_array: np.ndarray) -> None:
        pass

    @property
    def pos_x_int(self) -> int:
        return int(self.pos_x)

    @property
    def pos_y_int(self) -> int:
        return int(self.pos_y)

    @property
    def pos(self) -> tuple[float, float]:
        return (self.pos_x, self.pos_y)

    @property
    def pos_int(self) -> tuple[int, int]:
        return (int(self.pos_x), int(self.pos_y))
