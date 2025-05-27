import time

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.image import AxesImage
from matplotlib.patches import Circle, Rectangle
from PyQt6.QtWidgets import QWidget

from main.simulation.simulation import Simulation


class SimulationRenderArea(FigureCanvasQTAgg):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__()

        self.show_sources = True
        self.show_objects = True
        self.show_sensors = True
        self.draw_pml = False
        self.simulation: Simulation | None = None
        self.cmap = 'jet'
        self.source_radius = 2.0
        self.source_color = 'red'
        self.sensor_color = 'blue'

        self._axes = self.figure.add_subplot(1, 1, 1)
        self._axes_image: AxesImage | None = None
        self._draw_time = 0.0

    def draw(self, do_full_redraw: bool = False) -> None:
        start = time.perf_counter()
        if self.simulation is not None:
            cmap = self.cmap
            vmin: float | None = -1.0
            vmax: float | None = 1.0
            if self.draw_pml:
                sim_data = self.simulation.get_pml_data()
                cmap = 'viridis'
                vmin = None
                vmax = None
            else:
                sim_data = self.simulation.get_simulation_data()

            if self._axes_image is None or do_full_redraw:
                self._axes.clear()
                self._axes_image = self._axes.imshow(
                    sim_data,
                    origin='lower',
                    vmin=vmin,
                    vmax=vmax,
                    cmap=cmap)
            else:
                self._axes_image.set_data(sim_data)

            if self.show_sources:
                for source in self.simulation.sources.values():
                    self._axes.add_patch(
                        Circle(
                            source.pos,
                            self.source_radius,
                            color=self.source_color))

            if self.show_sensors:
                for sensor in self.simulation.sensors.values():
                    self._axes.add_patch(
                        Rectangle(
                            sensor.pos,
                            4,
                            4,
                            color=self.sensor_color))

            if self.show_objects:
                for obj in self.simulation.objects.values():
                    obj.draw(self._axes)

        super().draw()

        self._draw_time = time.perf_counter() - start

    @property
    def draw_time(self) -> float:
        return self._draw_time

    @property
    def draw_time_ms(self) -> float:
        return self._draw_time * 1000.0

    @property
    def draw_simulation(self) -> bool:
        return not self.draw_pml
