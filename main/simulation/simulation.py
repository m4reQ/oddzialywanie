import typing as t
import uuid

import numpy as np
from PyQt6 import QtCore

from main.simulation.objects.simulation_object import SimulationObject
from main.simulation.pml_profile import PMLProfile
from main.simulation.sources.simulation_source import SimulationSource

MU_0 = 4.0 * np.pi * 1.0e-7
EPS_0 = 8.854 * 1e-12
ETA = np.sqrt(MU_0 / EPS_0)
C = 1 / np.sqrt(EPS_0 * MU_0)
S = 1 / np.sqrt(2)

DEFAULT_DX = 3e-3
DEFAULT_DT = S * DEFAULT_DX / C

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
        self._needs_allowance_arrays_update = True
        self._sources_to_update = set[uuid.UUID]()
        self._objects_to_update = set[uuid.UUID]()

        self._sources = dict[uuid.UUID, SimulationSource]()
        self._objects = dict[uuid.UUID, SimulationObject]()

        self.reset()

    @property
    def current_frame(self) -> int:
        return self._current_frame

    @property
    def grid_size_x(self) -> int:
        return self._grid_size_x

    @property
    def grid_size_y(self) -> int:
        return self._grid_size_y

    @property
    def grid_size(self) -> tuple[int, int]:
        return (self._grid_size_x, self._grid_size_y)

    @property
    def sources(self) -> dict[uuid.UUID, SimulationSource]:
        return self._sources

    @property
    def objects(self) -> dict[uuid.UUID, SimulationObject]:
        return self._objects

    def emit_params_changed_signal(self) -> None:
        self._emit_pml_params_changed()
        self._emit_deltas_changed()
        self._emit_grid_size_changed()

    def set_dx(self, dx: float, use_auto_dt: bool = False) -> None:
        self._dx = dx

        if use_auto_dt:
            self._dt = S * self._dx / C

        self._pml_profile = self._generate_pml_profile()
        self._needs_allowance_arrays_update = True
        self._emit_deltas_changed()

    def set_dt(self, dt: float) -> None:
        self._dt = dt

        self._pml_profile = self._generate_pml_profile()
        self._needs_allowance_arrays_update = True
        self._emit_deltas_changed()
        self._update_simulation_sources()

        for obj in self._objects.values():
            obj.place(self._ae, self._am)

    def set_grid_size(self, x: int | None, y: int | None) -> None:
        if x is None:
            x = self._grid_size_x

        if y is None:
            y = self._grid_size_y

        self._grid_size_x = x
        self._grid_size_y = y

        grid_size = self.grid_size
        self._ez.resize(grid_size)
        self._hx.resize(grid_size)
        self._hy.resize(grid_size)
        self._ae.resize(grid_size)
        self._am.resize(grid_size)

        self._needs_allowance_arrays_update = True
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

        grid_size = self.grid_size
        self._ez = np.zeros(grid_size)
        self._hx = np.zeros(grid_size)
        self._hy = np.zeros(grid_size)
        # we need to immediately update allowance to allow user to see changes after clicking reset
        self._update_allowance_arrays()

    def add_source(self, source: SimulationSource) -> uuid.UUID:
        source.calculate_data(self._dt, 1000)

        source_id = uuid.uuid4()
        self._sources[source_id] = source

        return source_id

    def update_source(self, source_id: uuid.UUID) -> None:
        self._sources_to_update.add(source_id)

    def update_object(self, object_id: uuid.UUID) -> None:
        self._objects_to_update.add(object_id)

    def remove_source(self, source_id: uuid.UUID) -> None:
        self._sources.pop(source_id, None)

    def remove_object(self, object_id: uuid.UUID) -> None:
        obj = self._objects.pop(object_id, None)
        if obj is not None:
            obj.erase(self._ae, self._am, self._dt / (self._dx * EPS_0), self._dt / (self._dx * MU_0))

    def add_object(self, obj: SimulationObject) -> uuid.UUID:
        self._needs_allowance_arrays_update = True

        object_id = uuid.uuid4()
        self._objects[object_id] = obj

        return object_id

    def simulate_frame(self) -> None:
        if self._needs_allowance_arrays_update:
            self._update_allowance_arrays()
            self._needs_allowance_arrays_update = False

        for source_id in self._sources_to_update:
            source = self._sources.get(source_id, None)
            if source is not None:
                source.calculate_data(self._dt, 1000)

        for object_id in self._objects_to_update:
            object = self._objects.get(object_id, None)
            if object is not None:
                object.erase(self._ae, self._am, self._dt / (self._dx * EPS_0), self._dt / (self._dx * MU_0))
                object.place(self._ae, self._am)

        self._sources_to_update.clear()
        self._objects_to_update.clear()

        n1 = 1
        n11 = 1
        n2 = self._grid_size_y - 1
        n21 = self._grid_size_x - 1

        idx1 = (slice(n1, n2), slice(n11, n21))
        idx2 = (slice(n1 + 1, n2 + 1), slice(n11 + 1, n21 + 1))

        pml_a = self._pml_profile.a[idx1]
        pml_b = self._pml_profile.b[idx1]

        self._hy[idx1] = pml_a * self._hy[idx1] + pml_b * self._am[idx1] * (self._ez[n1 + 1:n2 + 1, n11:n21] - self._ez[idx1])
        self._hx[idx1] = pml_a * self._hx[idx1] - pml_b * self._am[idx1] * (self._ez[n1:n2, n11 + 1:n21 + 1] - self._ez[idx1])
        self._ez[idx2] = self._pml_profile.c[idx2] * self._ez[idx2] + self._pml_profile.d[idx2] * self._ae[idx2] * (self._hy[idx2] - self._hy[n1:n2, n11 + 1:n21 + 1] - self._hx[idx2] + self._hx[n1 + 1:n2 + 1, n11:n21])

        for source in self._sources.values():
            self._ez[source.pos_y_int, source.pos_x_int] = source.data[self._current_frame]

        self._current_frame += 1

    def get_simulation_data(self) -> np.ndarray:
        return self._ez

    def get_pml_data(self) -> np.ndarray:
        return self._pml_profile.data

    def _update_simulation_sources(self) -> None:
        for source in self._sources.values():
            source.calculate_data(self._dt, 1000)

    def _emit_deltas_changed(self) -> None:
        self.deltas_changed.emit(self._dx, self._dt)

    def _emit_grid_size_changed(self) -> None:
        self.grid_size_changed.emit(self._grid_size_x, self._grid_size_y)

    def _emit_pml_params_changed(self) -> None:
        self.pml_params_changed.emit(self._pml_reflectivity, self._pml_layers, self._pml_order)

    def _generate_pml_profile(self) -> PMLProfile:
        sigma = 4e-4 * np.ones(self.grid_size)
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
        grid_size = self.grid_size
        self._ae = np.ones(grid_size) * (self._dt / (self._dx * EPS_0))
        self._am = np.ones(grid_size) * (self._dt / (self._dx * MU_0))

        for obj in self._objects.values():
            obj.place(self._ae, self._am)
