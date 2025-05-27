import dataclasses

import numpy as np


@dataclasses.dataclass(slots=True)
class SimulationSensor:
    pos_x: float
    pos_y: float
    data: np.ndarray | None = dataclasses.field(init=False, default=None)

    @property
    def pos(self) -> tuple[float, float]:
        return (self.pos_x, self.pos_y)

    @property
    def pos_x_int(self) -> int:
        return int(self.pos_x)

    @property
    def pos_y_int(self) -> int:
        return int(self.pos_y)

    @property
    def pos_int(self) -> tuple[int, int]:
        return (self.pos_x_int, self.pos_y_int)
