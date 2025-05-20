import typing as t

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QToolButton, QWidget


class AddSimulationItemButton(QToolButton):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setMenu(QMenu(self))

    def register_add_callbacks[T](self, callbacks: t.Iterable[tuple[T, t.Callable[[T], t.Any]]]) -> None:
        # NOTE This removes existing actions (along with their callbacks)
        menu = self.menu()
        assert menu is not None

        for action in menu.actions():
            menu.removeAction(action)

        for (callback_arg, callback) in callbacks:
            self._add_action_with_callback(callback_arg, callback)

    def _add_action_with_callback[T](self, callback_arg: T, callback: t.Callable[[T], t.Any]) -> None:
        action = QAction(str(callback_arg), self)
        action.triggered.connect(pyqtSlot(object)(lambda: callback(callback_arg)))

        menu = self.menu()
        assert menu is not None

        menu.addAction(action)
