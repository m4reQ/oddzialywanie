from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QDoubleSpinBox, QLabel, QWidget

from main.simulation.sensor import SimulationSensor

_SENSOR_INSPECTOR_UI_FILEPATH = './ui/sensor_inspector.ui'

class SensorInspector(QWidget):
    sensor_params_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        uic.load_ui.loadUi(_SENSOR_INSPECTOR_UI_FILEPATH, self)

        self._sensor: SimulationSensor | None = None

        self.sensor_x_input: QDoubleSpinBox
        self.sensor_x_input.valueChanged.connect(self._sensor_x_input_changed_cb)

        self.sensor_y_input: QDoubleSpinBox
        self.sensor_y_input.valueChanged.connect(self._sensor_y_input_changed_cb)

        self.sensor_name_label: QLabel

    def set_sensor_max_pos(self, x: float | None, y: float | None) -> None:
        self.sensor_x_input.setMaximum(x if (x is not None) else self.sensor_x_input.value())
        self.sensor_y_input.setMaximum(y if (y is not None) else self.sensor_y_input.value())

    def set_sensor(self, sensor: SimulationSensor | None) -> None:
        self._sensor = sensor

        if sensor is None:
            return

        self.sensor_name_label.setText(type(sensor).__name__)
        self.sensor_x_input.setValue(sensor.pos_x)
        self.sensor_y_input.setValue(sensor.pos_y)

    @pyqtSlot(float)
    def _sensor_x_input_changed_cb(self, new_value: float) -> None:
        if self._sensor is not None:
            self._sensor.pos_x = new_value
            self.sensor_params_changed.emit()

    @pyqtSlot(float)
    def _sensor_y_input_changed_cb(self, new_value: float) -> None:
        if self._sensor is not None:
            self._sensor.pos_y = new_value
            self.sensor_params_changed.emit()
