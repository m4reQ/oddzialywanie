import time
import uuid

import numpy as np
from PyQt6 import QtCore

from main.simulation.objects.simulation_object import SimulationObject
from main.simulation.pml_profile import PMLProfile
from main.simulation.sensor import SimulationSensor
from main.simulation.simulation_params import SimulationParams
from main.simulation.sources.simulation_source import SimulationSource

MU_0 = 4.0 * np.pi * 1.0e-7
EPS_0 = 8.854 * 1e-12
ETA = np.sqrt(MU_0 / EPS_0)
C = 1 / np.sqrt(EPS_0 * MU_0)
S = 1 / np.sqrt(2)

DEFAULT_DX = 3e-3
DEFAULT_DT = S * DEFAULT_DX / C

class Simulation(QtCore.QObject):
    params_changed = QtCore.pyqtSignal(object)

    def __init__(self,
                 dt: float,
                 dx: float,
                 max_time_steps: int,
                 grid_size_x: int,
                 grid_size_y: int,
                 pml_reflectivity: float,
                 pml_layers: int,
                 pml_order: int) -> None:
        super().__init__()

        self._dt = dt
        self._dx = dx
        self._max_time_steps = max_time_steps
        self._grid_size_x = grid_size_x
        self._grid_size_y = grid_size_y
        self._pml_reflectivity = pml_reflectivity
        self._pml_layers = pml_layers
        self._pml_order = pml_order

        self._current_frame = 0
        self._simulation_time = 0.0

        self._ez: np.ndarray
        self._hx: np.ndarray
        self._hy: np.ndarray
        self._ae: np.ndarray
        self._am: np.ndarray
        self._time_array: np.ndarray
        self._pml_profile: PMLProfile

        self._sources = dict[uuid.UUID, SimulationSource]()
        self._objects = dict[uuid.UUID, SimulationObject]()
        self._sensors = dict[uuid.UUID, SimulationSensor]()

        self.reset()
        self._regenerate_pml_profile()
        self._regenerate_time_array()

    @property
    def dx(self) -> float:
        return self._dx

    @property
    def dt(self) -> float:
        return self._dt

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

    @property
    def sensors(self) -> dict[uuid.UUID, SimulationSensor]:
        return self._sensors

    @property
    def simulation_time(self) -> float:
        return self._simulation_time

    @property
    def simulation_time_ms(self) -> float:
        return self._simulation_time * 1000.0

    @property
    def time_array(self) -> np.ndarray:
        return self._time_array

    def set_dx(self, dx: float, use_auto_dt: bool = False) -> None:
        self._dx = dx

        self._regenerate_pml_profile()
        self._update_allowance_arrays()
        self._update_objects(erase_old=False)

        if use_auto_dt:
            self._set_dt(_calculate_auto_dt(self._dx), regenerate_pml=False)

        self.emit_params_changed_signal()

    def set_dt(self, dt: float) -> None:
        self._set_dt(dt, regenerate_pml=True)
        self.emit_params_changed_signal()

    def set_grid_size(self, x: int | None, y: int | None) -> None:
        if x is None:
            x = self._grid_size_x

        if y is None:
            y = self._grid_size_y

        self._grid_size_x = x
        self._grid_size_y = y

        grid_size = self.grid_size
        self._hx.resize(grid_size)
        self._hy.resize(grid_size)
        self._ae.resize(grid_size)
        self._am.resize(grid_size)

        self._needs_allowance_arrays_update = True
        self.emit_params_changed_signal()

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
            self._regenerate_pml_profile()
            self.emit_params_changed_signal()

    def reset(self) -> None:
        self._current_frame = 0

        grid_size = self.grid_size
        self._ez = np.zeros(grid_size)
        self._hx = np.zeros(grid_size)
        self._hy = np.zeros(grid_size)
        # we need to immediately update allowance to allow user to see changes after clicking reset
        self._update_allowance_arrays()
        self._update_objects(erase_old=False)

    def add_source(self, source: SimulationSource) -> uuid.UUID:
        source.calculate_data(self._time_array)

        source_id = uuid.uuid4()
        self._sources[source_id] = source

        return source_id

    def add_sensor(self, sensor: SimulationSensor) -> uuid.UUID:
        sensor.data = np.zeros((self._max_time_steps, ))

        sensor_id = uuid.uuid4()
        self._sensors[sensor_id] = sensor

        return sensor_id

    def update_source(self, source_id: uuid.UUID) -> None:
        source = self._sources.get(source_id, None)
        if source is not None:
            source.calculate_data(self._time_array)

    def update_object(self, object_id: uuid.UUID) -> None:
        obj = self._objects.get(object_id, None)
        if obj is not None:
            self._update_object(obj, erase_old=True)

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
        start = time.perf_counter()

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

        # update sources
        for source in self._sources.values():
            self._ez[source.pos_y_int, source.pos_x_int] = source.data[self._current_frame]

        # update sensors
        for sensor in self._sensors.values():
            assert sensor.data is not None
            sensor.data[self._current_frame] = self._ez[sensor.pos_int]

        self._current_frame += 1
        self._simulation_time = time.perf_counter() - start

    def get_simulation_data(self) -> np.ndarray:
        return self._ez

    def get_pml_data(self) -> np.ndarray:
        return self._pml_profile.data

    def _regenerate_time_array(self) -> None:
        self._time_array = -np.linspace(-30 * self._dt, 30 * self._dt, self._max_time_steps)

    def _regenerate_pml_profile(self) -> None:
        sigma = 4e-4 * np.ones(self.grid_size)
        sigma_max = -(self._pml_order + 1) * np.log(self._pml_reflectivity) / (2 * ETA * self._pml_layers * self._dx)
        lcp = ((np.arange(1, self._pml_layers + 1) / self._pml_layers) ** self._pml_order) * sigma_max
        lcp_rev = np.flip(lcp)

        sigma[1:self._pml_layers + 1, :] += lcp_rev[:, None]
        sigma[-self._pml_layers:, :] += lcp[:, None]
        sigma[:, 1:self._pml_layers + 1] += lcp_rev[None, :]
        sigma[:, -self._pml_layers:] += lcp[None, :]

        self._pml_profile = PMLProfile(
            sigma.T,
            np.ones(sigma.shape) * ((MU_0 - 0.5 * self._dt * 4e-4) / (MU_0 + 0.5 * self._dt * 4e-4)),
            np.ones(sigma.shape) * ((self._dt / self._dx) / (MU_0 + 0.5 * self._dt * 4e-4)),
            (EPS_0 - 0.5 * self._dt * sigma) / (EPS_0 + 0.5 * self._dt * sigma),
            (self._dt / self._dx) / (EPS_0 + 0.5 * self._dt * sigma))

    def _update_allowance_arrays(self) -> None:
        self._ae = np.ones(self.grid_size) * (self._dt / (self._dx * EPS_0))
        self._am = np.ones(self.grid_size) * (self._dt / (self._dx * MU_0))

    def emit_params_changed_signal(self) -> None:
        self.params_changed.emit(
            SimulationParams(
                self._dt,
                self._dx,
                self._grid_size_x,
                self._grid_size_y,
                self._pml_reflectivity,
                self._pml_layers,
                self._pml_order))

    def _update_objects(self, erase_old: bool) -> None:
        for obj in self._objects.values():
            self._update_object(obj, erase_old)

    def _update_object(self, obj: SimulationObject, erase_old: bool) -> None:
        if erase_old:
            obj.erase(
                self._ae,
                self._am,
                self._dt / (self._dx * EPS_0),
                self._dt / (self._dx * MU_0))

        obj.place(self._ae, self._am)

    def _set_dt(self, dt: float, regenerate_pml: bool) -> None:
        self._dt = dt

        if regenerate_pml:
            self._regenerate_pml_profile()

        self._regenerate_time_array()
        self._recalculate_sources_data()

    def _recalculate_sources_data(self) -> None:
        for source in self._sources.values():
            source.calculate_data(self._time_array)

def _calculate_auto_dt(dx: float) -> float:
    return S * dx / C
