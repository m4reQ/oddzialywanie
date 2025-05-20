from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QBoxLayout, QFrame, QWidget

from main.simulation.simulation_state import SimulationState


class SimulationStateIndicator(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._simulation_state_icons = {
            SimulationState.OK: QSvgWidget('./ui/icons/simulation_ok_icon.svg'),
            SimulationState.ERROR: QSvgWidget('./ui/icons/simulation_error_icon.svg'),
            SimulationState.RUNNING: QSvgWidget('./ui/icons/simulation_running_icon.svg')}
        self._current_icon = self._simulation_state_icons[SimulationState.OK]
        self._layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._layout.addWidget(self._current_icon)

        self.setFixedSize(16, 16)
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)
        self.setToolTip(_get_tooltip_text(SimulationState.OK))
        self.show()

    def set_state(self, state: SimulationState) -> None:
        self.setToolTip(_get_tooltip_text(state))

        new_icon = self._simulation_state_icons[state]
        new_icon.show()

        self._layout.replaceWidget(self._current_icon, new_icon)

        self._current_icon.hide()
        self._current_icon = new_icon

def _get_tooltip_text(state: SimulationState) -> str:
    match state:
        case SimulationState.OK:
            return 'Simulation ready'
        case SimulationState.RUNNING:
            return 'Simulation running'
        case SimulationState.ERROR:
            return 'Simulation error occurred'

    return ''
