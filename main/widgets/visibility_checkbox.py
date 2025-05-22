from PyQt6.QtWidgets import QWidget

from main.widgets.custom_icon_checkbox import CustomIconCheckbox

DEFAULT_CHECKBOX_SIZE = 16
CHECKED_ICON_PATH = './ui/icons/visible_icon.svg'
UNCHECKED_ICON_PATH = './ui/icons/not_visible_icon.svg'
STYLESHEET = f'QCheckBox::indicator:checked {{image: url({CHECKED_ICON_PATH});}} QCheckBox::indicator:unchecked {{image: url({UNCHECKED_ICON_PATH});}} QCheckBox::indicator {{width: {DEFAULT_CHECKBOX_SIZE}px;height: {DEFAULT_CHECKBOX_SIZE}px;}}'

class VisibilityCheckbox(CustomIconCheckbox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            CHECKED_ICON_PATH,
            UNCHECKED_ICON_PATH,
            DEFAULT_CHECKBOX_SIZE,
            parent)
