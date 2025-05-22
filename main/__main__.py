import math
import uuid

from PyQt6 import QtCore, QtGui, QtWidgets, uic

from main.simulation.objects.box import Box
from main.simulation.objects.simulation_object import SimulationObject
from main.simulation.simulation import DEFAULT_DT, DEFAULT_DX, MU_0, Simulation
from main.simulation.sources.cosine_source import CosineSource
from main.simulation.sources.simulation_source import SimulationSource
from main.simulation.sources.sine_source import SineSource
from main.simulation_job import SimulationJob
from main.widgets.add_simulation_item_button import AddSimulationItemButton
from main.widgets.object_inspector import ObjectInspector
from main.widgets.sensor_view import SensorView
from main.widgets.simulation_control_button import SimulationControlButton
from main.widgets.simulation_render_area import SimulationRenderArea
from main.widgets.source_inspector import SourceInspector

MAIN_WINDOW_UI_FILEPATH = './ui/main_window.ui'
DATA_ROLE = QtCore.Qt.ItemDataRole.UserRole + 2137
DEFAULT_BOX_SIZE = 30.0
SOURCES_LIST_TAB_INDEX = 0
OBJECTS_LIST_TAB_INDEX = 1

class UI(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        uic.load_ui.loadUi(MAIN_WINDOW_UI_FILEPATH, self)

        self.add_sensor_button: QtWidgets.QPushButton
        self.simulation_tab: QtWidgets.QTabWidget
        self.clear_button: QtWidgets.QPushButton
        self.simulate_button: SimulationControlButton
        self.add_button: AddSimulationItemButton
        self.remove_button: QtWidgets.QPushButton
        self.simulation_render_area: SimulationRenderArea
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
        self.show_objects_input: QtWidgets.QCheckBox
        self.show_sources_input: QtWidgets.QCheckBox
        self.show_pml_input: QtWidgets.QCheckBox
        self.inspectors_tab: QtWidgets.QTabWidget
        self.steps_per_render_input: QtWidgets.QSpinBox
        self.current_frame_label: QtWidgets.QLabel
        self.simulation_time_label: QtWidgets.QLabel
        self.render_time_label: QtWidgets.QLabel
        self.sensors_area_content: QtWidgets.QWidget
        self.show_sensors_input: QtWidgets.QCheckBox
        self.source_inspector_widget = SourceInspector()
        self.object_inspector_widget = ObjectInspector()

        self.sensors_area_layout = self.sensors_area_content.layout()
        assert isinstance(self.sensors_area_layout, QtWidgets.QVBoxLayout)
        self.sensors_area_layout.setDirection(QtWidgets.QBoxLayout.Direction.BottomToTop)

        self.current_selected_simulation_item_id: uuid.UUID | None = None

        self._source_counter = 0
        self._object_counter = 0
        self._sensor_counter = 0

        self._sensors = list[SensorView]()

        self.simulation = Simulation(
            DEFAULT_DT,
            DEFAULT_DX,
            500,
            500,
            1e-8,
            25,
            3)
        self.simulation_render_area.simulation = self.simulation

        self._register_add_source_callbacks()

        self.object_inspector_widget.set_simulation_size(self.simulation._grid_size_x, self.simulation._grid_size_y)
        self.source_inspector_widget.set_max_source_pos(self.simulation._grid_size_x, self.simulation._grid_size_y)

        self.simulation.deltas_changed.connect(self._sim_deltas_changed_cb)
        self.simulation.grid_size_changed.connect(self._sim_grid_size_changed_cb)
        self.simulation.pml_params_changed.connect(self._sim_pml_params_changed)
        self.simulation.emit_params_changed_signal()

        self.simulation_job: SimulationJob | None = None

        self.add_sensor_button.clicked.connect(self._add_sensor_button_clicked_cb)
        self.lists_tab.currentChanged.connect(self._simulation_items_list_changed_cb)
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
        self.show_objects_input.checkStateChanged.connect(self._show_objects_checkbox_changed_cb)
        self.show_sources_input.checkStateChanged.connect(self._show_sources_checkbox_changed_cb)
        self.show_pml_input.checkStateChanged.connect(self._show_pml_input_cb)
        self.sources_list.itemSelectionChanged.connect(self._sources_list_selection_changed_cb)
        self.objects_list.itemSelectionChanged.connect(self._objects_list_selection_changed_cb)
        self.source_inspector_widget.source_params_changed.connect(self._source_params_changed_cb)
        self.object_inspector_widget.object_params_changed.connect(self._object_params_changed_cb)

    def _register_add_source_callbacks(self) -> None:
        self.add_button.register_add_callbacks((
            ('sine', self._add_simulation_source),
            ('cosine', self._add_simulation_source)))

    def _register_add_object_callbacks(self) -> None:
        self.add_button.register_add_callbacks((
            ('box', self._add_simulation_object),))

    def _create_simulation_object(self, object_type: str, pos_x: int, pos_y: int) -> SimulationObject:
        if object_type == 'box':
            return Box(1.0, MU_0, pos_x, pos_y, DEFAULT_BOX_SIZE, DEFAULT_BOX_SIZE)

        raise ValueError(f'Invalid simulation object type: {object_type}')

    def _add_simulation_object(self, object_type: str) -> None:
        obj_id = self.simulation.add_object(
            self._create_simulation_object(
                object_type,
                *self._get_simulation_center_pos()))

        item = QtWidgets.QListWidgetItem(f'Object {self._object_counter + 1}')
        item.setData(DATA_ROLE, obj_id)
        self.objects_list.addItem(item)

        self._object_counter += 1

        if self.simulation_render_area.show_objects and self.simulation_render_area.draw_simulation:
            self.simulation_render_area.draw()

    def _get_simulation_center_pos(self) -> tuple[int, int]:
        return (self.simulation.grid_size_x // 2,
                self.simulation.grid_size_y // 2)

    def _create_simulation_source(self, source_type: str, pos_x: int, pos_y: int) -> SimulationSource:
        if source_type == 'sine':
            return SineSource(pos_x, pos_y, 60e9)
        elif source_type == 'cosine':
            return CosineSource(pos_x, pos_y, 60e9)

        raise ValueError(f'Invalid simulation source type: {source_type}')

    def _add_simulation_source(self, source_type: str) -> None:
        pos_x, pos_y = self._get_simulation_center_pos()
        source = self._create_simulation_source(source_type, pos_x, pos_y)
        source_id = self.simulation.add_source(source)

        item = QtWidgets.QListWidgetItem(f'Source {self._source_counter + 1}')
        item.setData(DATA_ROLE, source_id)
        self.sources_list.addItem(item)

        self._source_counter += 1

        if self.simulation_render_area.show_sources and self.simulation_render_area.draw_simulation:
            self.simulation_render_area.draw()

    def _change_inspector_widget(self, new_widget: QtWidgets.QWidget) -> None:
        tab_layout = self.inspector_tab.layout()
        assert tab_layout is not None

        tab_layout.replaceWidget(self.current_inspector_widget, new_widget)
        tab_layout.update()

        self.current_inspector_widget.hide()
        new_widget.show()

        self.current_inspector_widget = new_widget

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
            self.simulation_render_area.figure.tight_layout(pad=1)

    @QtCore.pyqtSlot()
    def _add_sensor_button_clicked_cb(self) -> None:
        assert self.sensors_area_layout is not None

        widget = SensorView(f'Sensor {self._sensor_counter}')
        self.sensors_area_layout.addWidget(widget)
        widget.show()
        self.sensors_area_layout.update()

        self._sensor_counter += 1

    @QtCore.pyqtSlot()
    def _simulation_items_list_changed_cb(self) -> None:
        index = self.lists_tab.currentIndex()
        if index == SOURCES_LIST_TAB_INDEX:
            self._register_add_source_callbacks()
        elif index == OBJECTS_LIST_TAB_INDEX:
            self._register_add_object_callbacks()

    @QtCore.pyqtSlot()
    def _object_params_changed_cb(self) -> None:
        item = self.objects_list.currentItem()
        if item is not None:
            object_id: uuid.UUID = item.data(DATA_ROLE)
            self.simulation.update_object(object_id)

        if self.simulation_render_area.show_objects and self.simulation_render_area.draw_simulation:
            self.simulation_render_area.draw(do_full_redraw=True)

    @QtCore.pyqtSlot()
    def _source_params_changed_cb(self) -> None:
        item = self.sources_list.currentItem()
        if item is not None:
            source_id: uuid.UUID = item.data(DATA_ROLE)
            self.simulation.update_source(source_id)

        if self.simulation_render_area.show_sources and self.simulation_render_area.draw_simulation:
            self.simulation_render_area.draw(do_full_redraw=True)

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
        self.simulation_render_area.draw_pml = self.show_pml_input.isChecked()
        self.simulation_render_area.draw(do_full_redraw=True)

    @QtCore.pyqtSlot()
    def _show_sources_checkbox_changed_cb(self) -> None:
        self.simulation_render_area.show_sources = self.show_sources_input.isChecked()
        self.simulation_render_area.draw(do_full_redraw=True)

    @QtCore.pyqtSlot()
    def _show_objects_checkbox_changed_cb(self) -> None:
        self.simulation_render_area.show_objects = self.show_objects_input.isChecked()
        self.simulation_render_area.draw(do_full_redraw=True)

    @QtCore.pyqtSlot()
    def _clear_button_clicked_cb(self) -> None:
        self.simulation.reset()
        self.simulation_render_area.draw()

    @QtCore.pyqtSlot()
    def _simulation_frame_ready_cb(self) -> None:
        if self.simulation.current_frame % self.steps_per_render_input.value() == 0:
            self.simulation_render_area.draw()

        self.current_frame_label.setText(str(self.simulation.current_frame))
        self.simulation_time_label.setText(f'{self.simulation.simulation_time_ms:.1f}')
        self.render_time_label.setText(f'{self.simulation_render_area.draw_time_ms:.1f}')

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

        self.simulation_render_area.draw()

    @QtCore.pyqtSlot(float, int, int)
    def _sim_pml_params_changed(self, reflectivity: float, layers: int, order: int) -> None:
        self.pml_reflectivity_input.setValue(reflectivity)
        self.pml_layers_input.setValue(layers)
        self.pml_order_input.setValue(order)

        self.simulation_render_area.draw()

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

        self.clear_button.setEnabled(is_simulation_running)
        self.steps_per_render_input.setEnabled(is_simulation_running)
        self.show_pml_input.setEnabled(is_simulation_running)
        self.simulate_button.set_state(not is_simulation_running)

    @QtCore.pyqtSlot(uuid.UUID)
    def _simulation_scene_selection_cb(self, object_id: uuid.UUID) -> None:
        self._select_list_item_by_id(self.sources_list, object_id)
        self._select_list_item_by_id(self.objects_list, object_id)

    @QtCore.pyqtSlot()
    def _remove_button_clicked_cb(self) -> None:
        current_tab = self.lists_tab.currentIndex()
        if current_tab == SOURCES_LIST_TAB_INDEX:
            current_item = self.sources_list.currentItem()
            if current_item is not None:
                item_id = current_item.data(DATA_ROLE)
                assert isinstance(item_id, uuid.UUID)

                self.simulation.remove_source(item_id)
                self.sources_list.takeItem(self.sources_list.row(current_item))
        elif current_tab == OBJECTS_LIST_TAB_INDEX:
            current_item = self.objects_list.currentItem()
            if current_item is not None:
                item_id = current_item.data(DATA_ROLE)
                assert isinstance(item_id, uuid.UUID)

                self.simulation.remove_object(item_id)
                self.objects_list.takeItem(self.objects_list.row(current_item))

        self.simulation_render_area.draw()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    ui = UI()

    ui.show()
    app.exec()
