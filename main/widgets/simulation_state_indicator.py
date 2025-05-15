from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QBoxLayout, QFrame

from main.simulation import SimulationState


class SimulationStateIndicator(QFrame):
    def __init__(self, height: int, initial_state: SimulationState) -> None:
        super().__init__()

        self._simulation_state_icons = {
            SimulationState.OK: QSvgWidget('./ui/icons/simulation_ok_icon.svg'),
            SimulationState.ERROR: QSvgWidget('./ui/icons/simulation_error_icon.svg'),
            SimulationState.RUNNING: QSvgWidget('./ui/icons/simulation_running_icon.svg')}
        self._current_icon = self._simulation_state_icons[initial_state]
        self._layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)

        self._layout.addWidget(self._current_icon)

        self.setFixedSize(height, height)
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

    def set_state(self, state: SimulationState) -> None:
        new_icon = self._simulation_state_icons[state]
        new_icon.show()

        self._layout.replaceWidget(self._current_icon, new_icon)

        self._current_icon.hide()
        self._current_icon = new_icon
