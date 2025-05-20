from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QCheckBox, QWidget

DEFAULT_CHECKBOX_SIZE = 16
VISIBLE_ICON_PATH = './ui/icons/visible_icon.svg'
NOT_VISIBLE_ICON_PATH = './ui/icons/not_visible_icon.svg'
STYLESHEET = f'QCheckBox::indicator:checked {{image: url({VISIBLE_ICON_PATH});}} QCheckBox::indicator:unchecked {{image: url({NOT_VISIBLE_ICON_PATH});}} QCheckBox::indicator {{width: {DEFAULT_CHECKBOX_SIZE}px;height: {DEFAULT_CHECKBOX_SIZE}px;}}'

class VisibilityCheckbox(QCheckBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setStyleSheet(STYLESHEET)

        font_height = self.fontMetrics().height()
        self.setIconSize(QSize(font_height, font_height))
