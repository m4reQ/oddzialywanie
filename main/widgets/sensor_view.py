from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PyQt6 import uic
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QSizePolicy, QWidget

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
