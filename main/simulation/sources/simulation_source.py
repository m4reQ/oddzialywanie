import abc
import dataclasses

import numpy as np


@dataclasses.dataclass
class SimulationSource(abc.ABC):
    pos_x: float
    pos_y: float
    frequency: float
    data: np.ndarray = dataclasses.field(init=False)

    @staticmethod
    def generate_time_array(l: float, dt: float, time_steps: int) -> np.ndarray:
        return -np.linspace(-l * dt, l * dt, time_steps)

    @abc.abstractmethod
    def calculate_data(self, dt: float, time_steps: int) -> None:
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
