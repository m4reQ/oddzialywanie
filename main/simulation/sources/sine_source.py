import dataclasses

import numpy as np

from main.simulation.sources.simulation_source import SimulationSource


@dataclasses.dataclass
class SineSource(SimulationSource):
    length: float = 30.0

    def calculate_data(self, dt: float, time_steps: int) -> None:
        self.data = np.sin(2 * np.pi * self.frequency * SimulationSource.generate_time_array(self.length, dt, time_steps))
