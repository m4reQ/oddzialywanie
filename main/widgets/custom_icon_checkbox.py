from PyQt6.QtWidgets import QCheckBox, QWidget

DEFAULT_CHECKBOX_SIZE = 16
VISIBLE_ICON_PATH = './ui/icons/visible_icon.svg'
NOT_VISIBLE_ICON_PATH = './ui/icons/not_visible_icon.svg'
STYLESHEET = f'QCheckBox::indicator:checked {{image: url({VISIBLE_ICON_PATH});}} QCheckBox::indicator:unchecked {{image: url({NOT_VISIBLE_ICON_PATH});}} QCheckBox::indicator {{width: {DEFAULT_CHECKBOX_SIZE}px;height: {DEFAULT_CHECKBOX_SIZE}px;}}'

class CustomIconCheckbox(QCheckBox):
    def __init__(self,
                 checked_icon_path: str,
                 unchecked_icon_path: str,
                 checkbox_size: int,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setStyleSheet(
            f'''
            QCheckBox::indicator:checked{{
                image: url({checked_icon_path});
            }}
            QCheckBox::indicator:unchecked{{
                image: url({unchecked_icon_path});
            }}
            QCheckBox::indicator{{
                width: {checkbox_size}px;
                height: {checkbox_size}px;
            }}''')
