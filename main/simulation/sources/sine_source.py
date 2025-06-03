import dataclasses

import numpy as np

from main.simulation.sources.simulation_source import SimulationSource


@dataclasses.dataclass
class SineSource(SimulationSource):
    def calculate_data(self, time_array: np.ndarray) -> None:
        self.data = np.sin(2 * np.pi * self.frequency * time_array + self.phase_shift) * self.amplitude
