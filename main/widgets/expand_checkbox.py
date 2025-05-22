from PyQt6.QtWidgets import QWidget

from main.widgets.custom_icon_checkbox import CustomIconCheckbox

DEFAULT_CHECKBOX_SIZE = 16
CHECKED_ICON_PATH = './ui/icons/sensor_hide_icon.svg'
UNCHECKED_ICON_PATH = './ui/icons/sensor_show_icon.svg'

class ExpandCheckbox(CustomIconCheckbox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            CHECKED_ICON_PATH,
            UNCHECKED_ICON_PATH,
            DEFAULT_CHECKBOX_SIZE,
            parent)
