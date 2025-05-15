from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QToolButton, QWidget


class SimulationControlButton(QToolButton):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._start_icon = QIcon('./ui/icons/simulation_start_icon.svg')
        self._stop_icon = QIcon('./ui/icons/simulation_stop_icon.svg')

        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        self.set_state(False)

    def set_state(self, is_simulation_running: bool) -> None:
        self.setIcon(self._stop_icon if is_simulation_running else self._start_icon)
        self.setText(' Stop simulation' if is_simulation_running else ' Start simulation')
