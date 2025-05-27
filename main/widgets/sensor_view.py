import time

import numpy as np
from matplotlib.lines import Line2D
from PyQt6 import uic
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QGridLayout, QLabel, QSizePolicy, QWidget

from main.widgets.expand_checkbox import ExpandCheckbox
from main.widgets.mpl_canvas import MPLCanvas

_UI_FILEPATH = './ui/sensor_view.ui'

class SensorView(QWidget):
    def __init__(self, name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.render_area: MPLCanvas
        self.expand_checkbox: ExpandCheckbox
        self.name_label: QLabel

        uic.load_ui.loadUi(_UI_FILEPATH, self)

        self.expand_checkbox.checkStateChanged.connect(self._expand_state_changed_cb)
        self.name_label.setText(name)

        self.render_area.figure.tight_layout()

        self._axes = self.render_area.figure.add_subplot(1, 1, 1)
        self._axes.invert_xaxis()
        self._axes.set_xticks([])

        self._plot_line: Line2D | None = None
        self._draw_time = 0.0

    @property
    def draw_time(self) -> float:
        return self._draw_time

    @property
    def draw_time_ms(self) -> float:
        return self._draw_time * 1000.0

    def update_sensor_data(self, sensor_data: np.ndarray, time_data: np.ndarray) -> None:
        start = time.perf_counter()

        if self.expand_checkbox.isChecked():
            if self._plot_line is None:
                lines = self._axes.plot(time_data, sensor_data)
                assert len(lines) > 0

                self._plot_line = lines[0]
            else:
                self._plot_line.set_data(time_data, sensor_data)

            self._axes.relim()
            self._axes.autoscale_view(True, False, True)
            self.render_area.draw()

        self._draw_time = time.perf_counter() - start

    @pyqtSlot()
    def _expand_state_changed_cb(self) -> None:
        parent_layout = self._get_parent_layout()

        if self.expand_checkbox.isChecked():
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            QWidget.show(self.render_area)
        else:
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
            QWidget.hide(self.render_area)

        parent_layout.update()

    def _get_parent_layout(self) -> QGridLayout:
        parent_layout = self.layout()
        assert isinstance(parent_layout, QGridLayout)

        return parent_layout
