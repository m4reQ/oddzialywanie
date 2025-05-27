import numpy as np
from PyQt6 import QtCore, QtWidgets, uic

from main.simulation.sources.simulation_source import SimulationSource
from main.widgets.float_tooltip_spinbox import FloatTooltipSpinbox

_SOURCE_INSPECTOR_UI_FILEPATH = './ui/source_inspector.ui'

class SourceInspector(QtWidgets.QWidget):
    source_params_changed = QtCore.pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        uic.load_ui.loadUi(_SOURCE_INSPECTOR_UI_FILEPATH, self)

        self._source: SimulationSource | None = None

        self.source_name_label: QtWidgets.QLabel

        self.source_frequency_input: FloatTooltipSpinbox
        self.source_frequency_input.valueChanged.connect(self._source_frequency_input_changed_cb)
        self.source_frequency_input.setMaximum(np.inf)

        self.source_x_input: QtWidgets.QDoubleSpinBox
        self.source_x_input.valueChanged.connect(self._source_x_input_changed_cb)

        self.source_y_input: QtWidgets.QDoubleSpinBox
        self.source_y_input.valueChanged.connect(self._source_y_input_changed_cb)

    def set_source(self, source: SimulationSource | None) -> None:
        self._source = source

        if source is None:
            return

        self.source_name_label.setText(type(source).__name__)
        self.source_frequency_input.setValue(source.frequency)
        self.source_x_input.setValue(source.pos_x)
        self.source_y_input.setValue(source.pos_y)

    def set_max_source_pos(self, x: float | None, y: float | None) -> None:
        self.source_x_input.setMaximum(x if (x is not None) else self.source_x_input.value())
        self.source_y_input.setMaximum(y if (y is not None) else self.source_y_input.value())

    @QtCore.pyqtSlot()
    def _source_frequency_input_changed_cb(self) -> None:
        if self._source is not None:
            self._source.frequency = self.source_frequency_input.value()
            self.source_params_changed.emit()

    @QtCore.pyqtSlot()
    def _source_x_input_changed_cb(self) -> None:
        if self._source is not None:
            self._source.pos_x = self.source_x_input.value()
            self.source_params_changed.emit()

    @QtCore.pyqtSlot()
    def _source_y_input_changed_cb(self) -> None:
        if self._source is not None:
            self._source.pos_y = self.source_y_input.value()
            self.source_params_changed.emit()
