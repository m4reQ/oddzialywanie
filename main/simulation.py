import abc
import dataclasses
import typing as t

import numpy as np
from matplotlib import axes, patches
from PyQt6 import QtCore

MU_0 = 4.0 * np.pi * 1.0e-7
EPS_0 = 8.854 * 1e-12
ETA = np.sqrt(MU_0 / EPS_0)
C = 1 / np.sqrt(EPS_0 * MU_0)
S = 1 / np.sqrt(2)

DEFAULT_DX = 3e-3
DEFAULT_DT = S * DEFAULT_DX / C

@dataclasses.dataclass
class PMLProfile:
    data: np.ndarray
    a: np.ndarray
    b: np.ndarray
    c: np.ndarray
    d: np.ndarray

@dataclasses.dataclass
class SimulationObject(abc.ABC):
    permittivity: float
    permeability: float
    pos_x: float
    pos_y: float

    @abc.abstractmethod
    def draw(self, axes: axes.Axes) -> None:
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

@dataclasses.dataclass
class Box(SimulationObject):
    width: float
    height: float

    def draw(self, axes: axes.Axes) -> None:
        axes.add_patch(patches.Rectangle((self.pos_x, self.pos_y), self.width, self.height, fill=False, edgecolor='black'))

    def place(self, permittivity_array: np.ndarray, permeability_array: np.ndarray) -> None:
        permittivity_array[self.pos_x_int:self.pos_x_int + int(self.width), self.pos_y_int:self.pos_y_int + int(self.height)] = self.permittivity
        permeability_array[self.pos_x_int:self.pos_x_int + int(self.width), self.pos_y_int:self.pos_y_int + int(self.height)] = self.permeability

    @property
    def width_int(self) -> int:
        return int(self.width)

    @property
    def height_int(self) -> int:
        return int(self.height)

@dataclasses.dataclass
class Source(abc.ABC):
    pos_x: float
    pos_y: float
    frequency: float
    data: np.ndarray = dataclasses.field(init=False)

    @abc.abstractmethod
    def calculate_data(self, dt: float, time_steps: int) -> None:
        pass

    @property
    def pos_x_int(self) -> int:
        return int(self.pos_x)

    @property
    def pos_y_int(self) -> int:
        return int(self.pos_y)

@dataclasses.dataclass
class SourceSine(Source):
    length: float = 30.0

    def calculate_data(self, dt: float, time_steps: int) -> None:
        self.data = np.sin(2 * np.pi * self.frequency * _generate_time_array(self.length, dt, time_steps))

@dataclasses.dataclass
class SourceCosine(Source):
    length: float = 30.0

    def calculate_data(self, dt: float, time_steps: int) -> None:
        self.data = np.sin(2 * np.pi * self.frequency * _generate_time_array(self.length, dt, time_steps))

class Simulation(QtCore.QObject):
    deltas_changed = QtCore.pyqtSignal(float, float)
    grid_size_changed = QtCore.pyqtSignal(int, int)
    pml_params_changed = QtCore.pyqtSignal(float, int, int)

    def __init__(self,
                 dt: float,
                 dx: float,
                 grid_size_x: int,
                 grid_size_y: int,
                 pml_reflectivity: float,
                 pml_layers: int,
                 pml_order: int) -> None:
        super().__init__()

        self._dt = dt
        self._dx = dx
        self._grid_size_x = grid_size_x
        self._grid_size_y = grid_size_y
        self._pml_reflectivity = pml_reflectivity
        self._pml_layers = pml_layers
        self._pml_order = pml_order

        self._current_frame = 0

        self._ez: np.ndarray
        self._hx: np.ndarray
        self._hy: np.ndarray
        self._ae: np.ndarray
        self._am: np.ndarray
        self._pml_profile = self._generate_pml_profile()

        self.reset()

    @property
    def current_frame(self) -> float:
        return self._current_frame

    def emit_params_changed_signal(self) -> None:
        self._emit_pml_params_changed()
        self._emit_deltas_changed()
        self._emit_grid_size_changed()

    def set_dx(self, dx: float, use_auto_dt: bool = False) -> None:
        self._dx = dx

        if use_auto_dt:
            self._dt = S * self._dx / C

        self._pml_profile = self._generate_pml_profile()
        self._update_allowance_arrays()
        self._emit_deltas_changed()

    def set_dt(self, dt: float) -> None:
        self._dt = dt

        self._pml_profile = self._generate_pml_profile()
        self._update_allowance_arrays()
        self._emit_deltas_changed()

    def set_grid_size(self, x: int | None, y: int | None) -> None:
        if x is None:
            x = self._grid_size_x

        if y is None:
            y = self._grid_size_y

        self._grid_size_x = x
        self._grid_size_y = y

        grid_size = (self._grid_size_x, self._grid_size_y)
        self._ez.resize(grid_size)
        self._hx.resize(grid_size)
        self._hy.resize(grid_size)
        self._ae.resize(grid_size)
        self._am.resize(grid_size)

        self._update_allowance_arrays()
        self._emit_grid_size_changed()

    def set_pml_params(self,
                       reflectivity: float | None = None,
                       layers: int | None = None,
                       order: int | None = None) -> None:
        params_changed = False

        if reflectivity is not None:
            self._pml_reflectivity = reflectivity
            params_changed = True

        if layers is not None:
            self._pml_layers = layers
            params_changed = True

        if order is not None:
            self._pml_order = order
            params_changed = True

        if params_changed:
            self._pml_profile = self._generate_pml_profile()
            self._emit_pml_params_changed()

    def reset(self) -> None:
        self._current_frame = 0

        grid_size = (self._grid_size_x, self._grid_size_y)
        self._ez = np.zeros(grid_size)
        self._hx = np.zeros(grid_size)
        self._hy = np.zeros(grid_size)
        self._ae = np.ones(grid_size) * self._dt / (self._dx * EPS_0)
        self._am = np.ones(grid_size) * self._dt / (self._dx * MU_0)

    def simulate_frame(self, sources: t.Iterable[Source], objects: t.Iterable[SimulationObject]) -> None:
        n1 = 1
        n11 = 1
        n2 = self._grid_size_y - 1
        n21 = self._grid_size_x - 1

        self._hy[n1:n2, n11:n21] = self._pml_profile.a[n1:n2, n11:n21] * self._hy[n1:n2, n11:n21] + self._pml_profile.b[n1:n2, n11:n21] * self._am[n1:n2, n11:n21] * (self._ez[n1 + 1:n2 + 1, n11:n21] - self._ez[n1:n2, n11:n21])
        self._hx[n1:n2, n11:n21] = self._pml_profile.a[n1:n2, n11:n21] * self._hx[n1:n2, n11:n21] - self._pml_profile.b[n1:n2, n11:n21] * self._am[n1:n2, n11:n21] * (self._ez[n1:n2, n11 + 1:n21 + 1] - self._ez[n1:n2, n11:n21])
        self._ez[n1 + 1:n2 + 1, n11 + 1:n21 + 1] = self._pml_profile.c[n1 + 1:n2 + 1, n11 + 1:n21 + 1] * self._ez[n1 + 1:n2 + 1, n11 + 1:n21 + 1] + self._pml_profile.d[n1 + 1:n2 + 1, n11 + 1:n21 + 1] * self._ae[n1 + 1:n2 + 1, n11 + 1:n21 + 1] * (self._hy[n1 + 1:n2 + 1, n11 + 1:n21 + 1] - self._hy[n1:n2, n11 + 1:n21 + 1] - self._hx[n1 + 1:n2 + 1, n11 + 1:n21 + 1] + self._hx[n1 + 1:n2 + 1, n11:n21])

        for source in sources:
            self._ez[source.pos_x_int, source.pos_y_int] = source.data[self._current_frame]

        for obj in objects:
            obj.place(self._ae, self._am)

        self._current_frame += 1

    def get_simulation_data(self) -> np.ndarray:
        return self._ez.T

    def get_pml_data(self) -> np.ndarray:
        return self._pml_profile.data.T

    def _emit_deltas_changed(self) -> None:
        self.deltas_changed.emit(self._dx, self._dt)

    def _emit_grid_size_changed(self) -> None:
        self.grid_size_changed.emit(self._grid_size_x, self._grid_size_y)

    def _emit_pml_params_changed(self) -> None:
        self.pml_params_changed.emit(self._pml_reflectivity, self._pml_layers, self._pml_order)

    def _generate_pml_profile(self) -> PMLProfile:
        sigma = 4e-4 * np.ones((self._grid_size_x, self._grid_size_y))
        sigma_max = -(self._pml_order + 1) * np.log(self._pml_reflectivity) / (2 * ETA * self._pml_layers * self._dx)
        lcp = ((np.arange(1, self._pml_layers + 1) / self._pml_layers) ** self._pml_order) * sigma_max
        lcp_rev = np.flip(lcp)

        sigma[1:self._pml_layers + 1, :] += lcp_rev[:, None]
        sigma[-self._pml_layers:, :] += lcp[:, None]
        sigma[:, 1:self._pml_layers + 1] += lcp_rev[None, :]
        sigma[:, -self._pml_layers:] += lcp[None, :]

        return PMLProfile(
            sigma.T,
            np.ones(sigma.shape) * ((MU_0 - 0.5 * self._dt * 4e-4) / (MU_0 + 0.5 * self._dt * 4e-4)),
            np.ones(sigma.shape) * ((self._dt / self._dx) / (MU_0 + 0.5 * self._dt * 4e-4)),
            (EPS_0 - 0.5 * self._dt * sigma) / (EPS_0 + 0.5 * self._dt * sigma),
            (self._dt / self._dx) / (EPS_0 + 0.5 * self._dt * sigma))

    def _update_allowance_arrays(self) -> None:
        self._ae.fill(self._dt / (self._dx * EPS_0))
        self._am.fill(self._dt / (self._dx * MU_0))

def _generate_time_array(l: float, dt: float, time_steps: int) -> np.ndarray:
    return -np.linspace(-l * dt, l * dt, time_steps)
