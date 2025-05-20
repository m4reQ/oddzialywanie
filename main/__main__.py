import math
import time
import uuid

import numpy as np
from matplotlib.patches import Circle
from PyQt6 import QtCore, QtGui, QtWidgets, uic

from main.simulation.objects.box import Box
from main.simulation.objects.simulation_object import SimulationObject
from main.simulation.simulation import DEFAULT_DT, DEFAULT_DX, MU_0, Simulation
from main.simulation.simulation_state import SimulationState
from main.simulation.sources.cosine_source import CosineSource
from main.simulation.sources.simulation_source import SimulationSource
from main.simulation.sources.sine_source import SineSource
from main.simulation_job import SimulationJob
from main.widgets import mpl_canvas
from main.widgets.add_simulation_item_button import AddSimulationItemButton
from main.widgets.frame_info_display import FrameInfoDisplay
from main.widgets.simulation_control_button import SimulationControlButton
from main.widgets.simulation_state_indicator import SimulationStateIndicator

MAIN_WINDOW_UI_FILEPATH = './ui/main_window.ui'
SOURCE_INSPECTOR_UI_FILEPATH = './ui/source_inspector.ui'
OBJECT_INSPECTOR_UI_FILEPATH = './ui/object_inspector.ui'
DATA_ROLE = QtCore.Qt.ItemDataRole.UserRole + 2137

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

class SourceInspector(QtWidgets.QWidget):
    source_params_changed = QtCore.pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self._source: SimulationSource | None = None

        self.source_name_label: QtWidgets.QLabel
        self.source_frequency_input: QtWidgets.QDoubleSpinBox
        self.source_x_input: QtWidgets.QDoubleSpinBox
        self.source_y_input: QtWidgets.QDoubleSpinBox

        uic.load_ui.loadUi(SOURCE_INSPECTOR_UI_FILEPATH, self)

        self.source_x_input.valueChanged.connect(self._source_x_input_changed_cb)
        self.source_y_input.valueChanged.connect(self._source_y_input_changed_cb)
        self.source_frequency_input.valueChanged.connect(self._source_frequency_input_changed_cb)

        self.source_frequency_input.setMaximum(np.inf)

    @QtCore.pyqtSlot()
    def _source_frequency_input_changed_cb(self) -> None:
        if self._source is not None:
            self._source.frequency = self.source_frequency_input.value()
            self.source_params_changed.emit()

    @QtCore.pyqtSlot()
    def _source_x_input_changed_cb(self) -> None:
        if self._source is not None:
            self._source.pos_x = self.source_x_input.value()
            self.source_params_changed.emit()

    @QtCore.pyqtSlot()
    def _source_y_input_changed_cb(self) -> None:
        if self._source is not None:
            self._source.pos_y = self.source_y_input.value()
            self.source_params_changed.emit()

    def set_source(self, source: SimulationSource | None) -> None:
        self._source = source

        if source is None:
            return

        self.source_name_label.setText(f'{type(source).__name__}')
        self.source_frequency_input.setValue(source.frequency)
        self.source_x_input.setValue(source.pos_x)
        self.source_y_input.setValue(source.pos_y)

    def set_max_source_pos(self, x: float | None, y: float | None) -> None:
        if x is None:
            x = self.source_x_input.value()

        if y is None:
            y = self.source_y_input.value()

        self.source_x_input.setMaximum(x)
        self.source_y_input.setMaximum(y)

class UI(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        uic.load_ui.loadUi(MAIN_WINDOW_UI_FILEPATH, self)

        self.simulation_tab: QtWidgets.QTabWidget
        self.clear_button: QtWidgets.QPushButton
        self.simulate_button: SimulationControlButton
        self.add_button: AddSimulationItemButton
        self.remove_button: QtWidgets.QPushButton
        self.figure_canvas: mpl_canvas.MPLCanvas
        self.current_inspector_widget: QtWidgets.QWidget
        self.inspector_tab: QtWidgets.QWidget
        self.sources_list: QtWidgets.QListWidget
        self.objects_list: QtWidgets.QListWidget
        self.lists_tab: QtWidgets.QTabWidget
        self.dx_input: QtWidgets.QDoubleSpinBox
        self.dt_input: QtWidgets.QDoubleSpinBox
        self.grid_size_x_input: QtWidgets.QSpinBox
        self.grid_size_y_input: QtWidgets.QSpinBox
        self.dt_auto_input: QtWidgets.QCheckBox
        self.pml_reflectivity_input: QtWidgets.QDoubleSpinBox
        self.pml_layers_input: QtWidgets.QSpinBox
        self.pml_order_input: QtWidgets.QSpinBox
        self.status_bar: QtWidgets.QStatusBar
        self.show_objects_input: QtWidgets.QCheckBox
        self.show_sources_input: QtWidgets.QCheckBox
        self.show_pml_input: QtWidgets.QCheckBox
        self.inspectors_tab: QtWidgets.QTabWidget
        self.steps_per_render_input: QtWidgets.QSpinBox
        self.source_inspector_widget = SourceInspector()
        self.object_inspector_widget = ObjectInspector()
        self.status_bar_frame_info = FrameInfoDisplay()
        self.simulation_state_indicator = SimulationStateIndicator(self.status_bar.height(), SimulationState.OK)

        self.status_bar.addWidget(self.simulation_state_indicator)
        self.status_bar.addWidget(self.status_bar_frame_info)

        self.current_selected_simulation_item_id: uuid.UUID | None = None

        self._source_counter = 0
        self._object_counter = 0
        self._frame_render_time = 0.0

        self.axes = self.figure_canvas.figure.add_subplot(1, 1, 1)
        self.simulation = Simulation(
            DEFAULT_DT,
            DEFAULT_DX,
            500,
            500,
            1e-8,
            25,
            3)

        self.add_button.register_add_callbacks((
            ('sine', self._add_simulation_source),
            ('cosine', self._add_simulation_source),
            ('broadband', self._add_simulation_source),
            ('gaussian', self._add_simulation_source)))

        self.object_inspector_widget.set_simulation_size(self.simulation._grid_size_x, self.simulation._grid_size_y)
        self.source_inspector_widget.set_max_source_pos(self.simulation._grid_size_x, self.simulation._grid_size_y)

        self.simulation.deltas_changed.connect(self._sim_deltas_changed_cb)
        self.simulation.grid_size_changed.connect(self._sim_grid_size_changed_cb)
        self.simulation.pml_params_changed.connect(self._sim_pml_params_changed)
        self.simulation.emit_params_changed_signal()

        self.simulation_job: SimulationJob | None = None

        self.remove_button.clicked.connect(self._remove_button_clicked_cb)
        self.simulate_button.clicked.connect(self._simulate_button_clicked_cb)
        self.clear_button.clicked.connect(self._clear_button_clicked_cb)
        self.dx_input.valueChanged.connect(self._dx_input_changed)
        self.dt_input.valueChanged.connect(self._dt_input_changed)
        self.pml_reflectivity_input.valueChanged.connect(self._pml_reflectivity_input_changed_cb)
        self.pml_layers_input.valueChanged.connect(self._pml_layers_input_changed_cb)
        self.pml_order_input.valueChanged.connect(self._pml_order_input_changed_cb)
        self.grid_size_x_input.valueChanged.connect(self._grid_size_x_input_changed_cb)
        self.grid_size_y_input.valueChanged.connect(self._grid_size_y_input_changed_cb)
        self.show_objects_input.checkStateChanged.connect(self._show_checkbox_changed_cb)
        self.show_sources_input.checkStateChanged.connect(self._show_checkbox_changed_cb)
        self.show_pml_input.checkStateChanged.connect(self._show_pml_input_cb)
        self.sources_list.itemSelectionChanged.connect(self._sources_list_selection_changed_cb)
        self.objects_list.itemSelectionChanged.connect(self._objects_list_selection_changed_cb)
        self.source_inspector_widget.source_params_changed.connect(self._source_params_changed_cb)
        self.object_inspector_widget.object_params_changed.connect(self._object_params_changed_cb)

    def _add_simulation_source(self, source_type: str) -> None:
        source_pos_x = self.simulation.grid_size_x // 2
        source_pos_y = self.simulation.grid_size_y // 2
        source_id = uuid.uuid4()

        source: SimulationSource
        if source_type == 'sine':
            source = SineSource(source_pos_x, source_pos_y, 60e9)
        elif source_type == 'cosine':
            source = CosineSource(source_pos_x, source_pos_y, 60e9)
        else:
            print('Invalid source type.')
            return

        source_id = self.simulation.add_source(source)

        item = QtWidgets.QListWidgetItem(f'Source {self._source_counter + 1}')
        item.setData(DATA_ROLE, source_id)
        self.sources_list.addItem(item)

        self._source_counter += 1

        if self.show_sources_input.isChecked():
            self._redraw_simulation_canvas()

    def _stop_current_simulation_job(self) -> None:
        if self.simulation_job is not None:
            self.simulation_job.stop()
            self.simulation_job = None

    def _redraw_pml_canvas(self) -> None:
        self.axes.imshow(self.simulation.get_pml_data(), origin='lower', cmap='viridis', aspect='auto')

        self.figure_canvas.draw()

    def _change_inspector_widget(self, new_widget: QtWidgets.QWidget) -> None:
        tab_layout = self.inspector_tab.layout()
        assert tab_layout is not None

        tab_layout.replaceWidget(self.current_inspector_widget, new_widget)
        tab_layout.update()

        self.current_inspector_widget.hide()
        new_widget.show()

        self.current_inspector_widget = new_widget

    def _redraw_simulation_canvas(self) -> float:
        start = time.perf_counter()

        if self.simulation_tab.currentIndex() == 0:
            self.axes.clear()
            self.axes.imshow(
                self.simulation.get_simulation_data(),
                origin='lower',
                vmin=-1,
                vmax=1,
                cmap='jet')

            # TODO Use axes_image.set_data() with cached axesimage to speed up rendering

            if self.show_sources_input.isChecked():
                for source in self.simulation.sources.values():
                    self.axes.add_patch(Circle((source.pos_x, source.pos_y), 2.0, color='red'))

            if self.show_objects_input.isChecked():
                for object in self.simulation.objects.values():
                    object.draw(self.axes)

            self.figure_canvas.draw()

        return time.perf_counter() - start

    def _select_list_item_by_id(self, _list: QtWidgets.QListWidget, object_id: uuid.UUID) -> None:
        for i in range(_list.count()):
            item = _list.item(i)
            assert item is not None

            if item.data(DATA_ROLE) == object_id:
                _list.setCurrentItem(item)

    def _get_item_name(self, tab_index: int) -> str:
        if tab_index == 0:
            self._source_counter += 1
            return f'Source {self._source_counter}'

        self._object_counter += 1
        return f'Object {self._object_counter}'

    def _get_current_tab_list(self) -> QtWidgets.QListWidget:
        if self.lists_tab.currentIndex() == 0:
            return self.sources_list

        return self.objects_list

    def resizeEvent(self, event: QtGui.QResizeEvent | None) -> None:
        super().resizeEvent(event)

        if event is not None:
            self.figure_canvas.figure.tight_layout(pad=1)

    @QtCore.pyqtSlot()
    def _object_params_changed_cb(self) -> None:
        if not self.show_pml_input.isChecked() and self.show_objects_input.isChecked():
            self._redraw_simulation_canvas()

    @QtCore.pyqtSlot()
    def _source_params_changed_cb(self) -> None:
        if not self.show_pml_input.isChecked() and self.show_sources_input.isChecked():
            self._redraw_simulation_canvas()

    @QtCore.pyqtSlot()
    def _sources_list_selection_changed_cb(self) -> None:
        item = self.sources_list.currentItem()
        if item is None:
            return

        self.current_selected_simulation_item_id = item.data(DATA_ROLE)
        assert isinstance(self.current_selected_simulation_item_id, uuid.UUID)

        self.source_inspector_widget.set_source(self.simulation.sources[self.current_selected_simulation_item_id])

        self._change_inspector_widget(self.source_inspector_widget)

    @QtCore.pyqtSlot()
    def _objects_list_selection_changed_cb(self) -> None:
        item = self.objects_list.currentItem()
        if item is None:
            return

        self.current_selected_simulation_item_id = item.data(DATA_ROLE)
        assert isinstance(self.current_selected_simulation_item_id, uuid.UUID)

        self.object_inspector_widget.set_object(self.simulation.objects[self.current_selected_simulation_item_id])

        self._change_inspector_widget(self.object_inspector_widget)

    @QtCore.pyqtSlot()
    def _pml_reflectivity_input_changed_cb(self) -> None:
        self.simulation.set_pml_params(reflectivity=self.pml_reflectivity_input.value())

    @QtCore.pyqtSlot()
    def _pml_layers_input_changed_cb(self) -> None:
        self.simulation.set_pml_params(layers=self.pml_layers_input.value())

    @QtCore.pyqtSlot()
    def _pml_order_input_changed_cb(self) -> None:
        self.simulation.set_pml_params(order=self.pml_order_input.value())

    @QtCore.pyqtSlot()
    def _show_pml_input_cb(self) -> None:
        self.axes.clear()

        if self.show_pml_input.isChecked():
            self._redraw_pml_canvas()
        else:
            self._redraw_simulation_canvas()

    @QtCore.pyqtSlot()
    def _show_checkbox_changed_cb(self) -> None:
        self._redraw_simulation_canvas()

    @QtCore.pyqtSlot()
    def _clear_button_clicked_cb(self) -> None:
        self._stop_current_simulation_job()
        self.simulation.reset()
        self._redraw_simulation_canvas()

    @QtCore.pyqtSlot(float)
    def _simulation_frame_ready_cb(self, simulation_time: float) -> None:
        if self.simulation.current_frame % self.steps_per_render_input.value() == 0:
            self._frame_render_time = self._redraw_simulation_canvas()

        self.status_bar_frame_info.set_data(
            self.simulation.current_frame,
            self._frame_render_time,
            simulation_time)

        if self.simulation_job is not None:
            self.simulation_job.notify_frame_processed()

    @QtCore.pyqtSlot(float, float)
    def _sim_deltas_changed_cb(self, dx: float, dt: float) -> None:
        self.dx_input.setValue(dx)
        self.dt_input.setValue(dt)

    @QtCore.pyqtSlot(int, int)
    def _sim_grid_size_changed_cb(self, x: int, y: int) -> None:
        self.grid_size_x_input.setValue(x)
        self.grid_size_y_input.setValue(y)
        self.pml_layers_input.setMaximum(math.floor(min(x, y) / 2))

        self._redraw_simulation_canvas()

    @QtCore.pyqtSlot(float, int, int)
    def _sim_pml_params_changed(self, reflectivity: float, layers: int, order: int) -> None:
        self.pml_reflectivity_input.setValue(reflectivity)
        self.pml_layers_input.setValue(layers)
        self.pml_order_input.setValue(order)

        if self.show_pml_input.isChecked():
            self._redraw_pml_canvas()

    @QtCore.pyqtSlot()
    def _dx_input_changed(self) -> None:
        value = self.dx_input.value()
        if value <= 0.0:
            self.dx_input.setValue(self.simulation._dx)
            return

        self.simulation.set_dx(value, self.dt_auto_input.isChecked())

    @QtCore.pyqtSlot()
    def _dt_input_changed(self) -> None:
        value = self.dt_input.value()
        if value <= 0.0:
            self.dx_input.setValue(self.simulation._dt)
            return

        self.simulation.set_dt(value)

    @QtCore.pyqtSlot()
    def _grid_size_x_input_changed_cb(self) -> None:
        value = self.grid_size_x_input.value()
        if value <= 0:
            self.grid_size_x_input.setValue(self.simulation._grid_size_x)
            return

        self.simulation.set_grid_size(value, None)
        self.source_inspector_widget.set_max_source_pos(self.simulation._grid_size_x, self.simulation._grid_size_y)
        self.object_inspector_widget.set_simulation_size(self.simulation._grid_size_x, self.simulation._grid_size_y)

    @QtCore.pyqtSlot()
    def _grid_size_y_input_changed_cb(self) -> None:
        value = self.grid_size_y_input.value()
        if value <= 0:
            self.grid_size_y_input.setValue(self.simulation._grid_size_y)
            return

        self.simulation.set_grid_size(None, value)
        self.source_inspector_widget.set_max_source_pos(self.simulation._grid_size_x, self.simulation._grid_size_y)
        self.object_inspector_widget.set_simulation_size(self.simulation._grid_size_x, self.simulation._grid_size_y)

    @QtCore.pyqtSlot()
    def _simulate_button_clicked_cb(self) -> None:
        is_simulation_running = self.simulation_job is not None

        if is_simulation_running:
            self.simulation_job.stop() # type: ignore[union-attr]
            self.simulation_job = None
        else:
            self.simulation_job = SimulationJob(self.simulation)
            self.simulation_job.frame_ready.connect(self._simulation_frame_ready_cb)
            self.simulation_job.start()

            self.show_pml_input.setChecked(False)

        self.steps_per_render_input.setEnabled(is_simulation_running)
        self.show_pml_input.setEnabled(is_simulation_running)
        self.simulate_button.set_state(not is_simulation_running)
        self.simulation_state_indicator.set_state(SimulationState.RUNNING if not is_simulation_running else SimulationState.OK)

    @QtCore.pyqtSlot(uuid.UUID)
    def _simulation_scene_selection_cb(self, object_id: uuid.UUID) -> None:
        self._select_list_item_by_id(self.sources_list, object_id)
        self._select_list_item_by_id(self.objects_list, object_id)

    @QtCore.pyqtSlot()
    def _remove_button_clicked_cb(self) -> None:
        current_tab = self.lists_tab.currentIndex()
        if current_tab == 0:
            current_item = self.sources_list.currentItem()
            if current_item is not None:
                item_id = current_item.data(DATA_ROLE)
                assert isinstance(item_id, uuid.UUID)

                self.simulation.remove_source(item_id)
        elif current_tab == 1:
            current_item = self.objects_list.currentItem()
            if current_item is not None:
                item_id = current_item.data(DATA_ROLE)
                assert isinstance(item_id, uuid.UUID)

                self.simulation.remove_object(item_id)

        self._redraw_simulation_canvas()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    ui = UI()

    ui.show()
    app.exec()
