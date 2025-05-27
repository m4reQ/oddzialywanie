import dataclasses


@dataclasses.dataclass(slots=True)
class SimulationParams:
    dt: float
    dx: float
    grid_size_x: int
    grid_size_y: int
    pml_reflectivity: float
    pml_layers: int
    pml_order: int

    @property
    def grid_size(self) -> tuple[int, int]:
        return (self.grid_size_x, self.grid_size_y)
