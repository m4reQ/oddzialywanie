import dataclasses

import numpy as np
from matplotlib.axes import Axes
from matplotlib.patches import Rectangle

from main.simulation.objects.simulation_object import SimulationObject


@dataclasses.dataclass
class Box(SimulationObject):
    width: float
    height: float

    def draw(self, axes: Axes) -> None:
        axes.add_patch(Rectangle((self.pos_x, self.pos_y), self.width, self.height, fill=False, edgecolor='black'))

    def place(self, permittivity_array: np.ndarray, permeability_array: np.ndarray) -> None:
        permittivity_array[self.pos_x_int:self.pos_x_int + self.width_int, self.pos_y_int:self.pos_y_int + self.height_int] = self.permittivity
        permeability_array[self.pos_x_int:self.pos_x_int + self.width_int, self.pos_y_int:self.pos_y_int + self.height_int] = self.permeability

    def erase(self,
              permittivity_array: np.ndarray,
              permeability_array: np.ndarray,
              default_permittivity: float,
              default_permeability: float) -> None:
        permittivity_array[self.pos_x_int:self.pos_x_int + self.width_int, self.pos_y_int:self.pos_y_int + self.height_int] = default_permittivity
        permeability_array[self.pos_x_int:self.pos_x_int + self.width_int, self.pos_y_int:self.pos_y_int + self.height_int] = default_permeability

    @property
    def width_int(self) -> int:
        return int(self.width)

    @property
    def height_int(self) -> int:
        return int(self.height)
