from PyQt6 import QtCore, QtWidgets, uic

from main.simulation.objects.box import Box
from main.simulation.objects.simulation_object import SimulationObject

OBJECT_INSPECTOR_UI_FILEPATH = './ui/object_inspector.ui'

class ObjectInspector(QtWidgets.QWidget):
    object_params_changed = QtCore.pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self._object: SimulationObject | None = None

        self.width_input: QtWidgets.QDoubleSpinBox
        self.height_input: QtWidgets.QDoubleSpinBox
        self.object_name_label: QtWidgets.QLabel
        self.permeability_input: QtWidgets.QDoubleSpinBox
        self.permittivity_input: QtWidgets.QDoubleSpinBox
        self.x_input: QtWidgets.QDoubleSpinBox
        self.y_input: QtWidgets.QDoubleSpinBox

        uic.load_ui.loadUi(OBJECT_INSPECTOR_UI_FILEPATH, self)

        self.width_input.valueChanged.connect(self._width_changed_cb)
        self.height_input.valueChanged.connect(self._height_changed_cb)
        self.x_input.valueChanged.connect(self._x_input_changed_cb)
        self.y_input.valueChanged.connect(self._y_input_changed_cb)
        self.permittivity_input.valueChanged.connect(self._permittivity_input_changed_cb)
        self.permeability_input.valueChanged.connect(self._permeability_input_changed_cb)

    @QtCore.pyqtSlot()
    def _permittivity_input_changed_cb(self) -> None:
        assert isinstance(self._object, Box)

        self._object.permittivity = self.permittivity_input.value()
        self.object_params_changed.emit()

    @QtCore.pyqtSlot()
    def _permeability_input_changed_cb(self) -> None:
        assert isinstance(self._object, Box)

        self._object.permeability = self.permeability_input.value()
        self.object_params_changed.emit()

    @QtCore.pyqtSlot()
    def _x_input_changed_cb(self) -> None:
        assert isinstance(self._object, Box)

        self._object.pos_x = self.x_input.value()
        self.object_params_changed.emit()

    @QtCore.pyqtSlot()
    def _y_input_changed_cb(self) -> None:
        assert isinstance(self._object, Box)

        self._object.pos_y = self.y_input.value()
        self.object_params_changed.emit()

    @QtCore.pyqtSlot()
    def _width_changed_cb(self) -> None:
        if self._object is not None:
            assert isinstance(self._object, Box)

            self._object.width = self.width_input.value()
            self.object_params_changed.emit()

    @QtCore.pyqtSlot()
    def _height_changed_cb(self) -> None:
        if self._object is not None:
            assert isinstance(self._object, Box)

            self._object.height = self.height_input.value()
            self.object_params_changed.emit()

    def set_simulation_size(self, x: float, y: float) -> None:
        current_width = 0.0
        current_height = 0.0
        current_x = 0.0
        current_y = 0.0
        if self._object is not None:
            assert isinstance(self._object, Box)

            current_width = self._object.width
            current_height = self._object.height
            current_x = self._object.pos_x
            current_y = self._object.pos_y

        self.x_input.setMaximum(x - current_width)
        self.y_input.setMaximum(y - current_height)
        self.width_input.setMaximum(x - current_x)
        self.height_input.setMaximum(y - current_y)

    def set_object(self, object: SimulationObject | None) -> None:
        self._object = object

        if object is None:
            return

        assert isinstance(object, Box)
        self.object_name_label.setText('Object')
        self.width_input.setValue(object.width)
        self.height_input.setValue(object.height)
        self.permeability_input.setValue(object.permeability)
        self.permittivity_input.setValue(object.permittivity)
        self.x_input.setValue(object.pos_x)
        self.y_input.setValue(object.pos_y)
