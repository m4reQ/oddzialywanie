import typing as t

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QDoubleSpinBox, QWidget


class FloatTooltipSpinbox(QDoubleSpinBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.valueChanged.connect(self._value_changed_cb)
        self.validate_func: t.Callable[[float], bool] | None = None

        self._last_value = 0.0

    @pyqtSlot(float)
    def _value_changed_cb(self, new_value: float) -> None:
        if self.validate_func is not None and not self.validate_func(new_value):
            self.setValue(self._last_value)
            return

        self._last_value = new_value
        self.setToolTip(f'{new_value:.2E}')

