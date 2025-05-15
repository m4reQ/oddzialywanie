from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.uic import load_ui


class FrameInfoDisplay(QWidget):
    UI_PATH = './ui/status_bar_frame_info.ui'

    def __init__(self) -> None:
        super().__init__()
        load_ui.loadUi(self.UI_PATH, self)

        self.current_frame_label: QLabel
        self.render_time_label: QLabel
        self.simulation_time_label: QLabel

    def set_data(self,
                 frame_index: int | None = None,
                 render_time_seconds: float | None = None,
                 simulation_time_seconds: float | None = None) -> None:
        if frame_index is not None:
            self.current_frame_label.setText(str(frame_index))

        if render_time_seconds is not None:
            self.render_time_label.setText(f'{(render_time_seconds * 1000.0):.1f}')

        if simulation_time_seconds is not None:
            self.simulation_time_label.setText(f'{(simulation_time_seconds * 1000.0):.1f}')
