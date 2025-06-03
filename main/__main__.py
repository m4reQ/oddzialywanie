import math
import uuid

from PyQt6 import QtCore, QtGui, QtWidgets, uic

from main.simulation.objects.box import Box
from main.simulation.objects.simulation_object import SimulationObject
from main.simulation.sensor import SimulationSensor
from main.simulation.simulation import DEFAULT_DT, DEFAULT_DX, MU_0, Simulation
from main.simulation.simulation_params import SimulationParams
from main.simulation.sources.cosine_source import CosineSource
from main.simulation.sources.simulation_source import SimulationSource
from main.simulation.sources.sine_source import SineSource
from main.simulation_job import SimulationJob
from main.widgets.add_simulation_item_button import AddSimulationItemButton
from main.widgets.float_tooltip_spinbox import FloatTooltipSpinbox
from main.widgets.object_inspector import ObjectInspector
from main.widgets.sensor_inspector import SensorInspector
from main.widgets.sensor_view import SensorView
from main.widgets.simulation_control_button import SimulationControlButton
from main.widgets.simulation_render_area import SimulationRenderArea
from main.widgets.source_inspector import SourceInspector

MAIN_WINDOW_UI_FILEPATH = './ui/main_window.ui'
DATA_ROLE = QtCore.Qt.ItemDataRole.UserRole + 2137
DEFAULT_BOX_SIZE = 30.0

SOURCES_LIST_TAB_INDEX = 0
OBJECTS_LIST_TAB_INDEX = 1
SENSORS_LIST_TAB_INDEX = 2

SIMULATION_TAB_INDEX = 0
SENSORS_TAB_INDEX = 1

class UI(QtWidgets.QMainWindow):
    def __init__(self, simulation: Simulation) -> None:
        super().__init__()
        uic.load_ui.loadUi(MAIN_WINDOW_UI_FILEPATH, self)

        self._simulation = simulation
        self._simulation.params_changed.connect(self._sim_params_changed)
        self._simulation.emit_params_changed_signal()

        self._source_counter = 0
        self._object_counter = 0
        self._sensor_counter = 0
        self._sensor_widgets = dict[uuid.UUID, SensorView]()
        self._simulation_job: SimulationJob | None = None

        # widgets
        self.simulation_tab: QtWidgets.QTabWidget
        self.current_inspector_widget: QtWidgets.QWidget
        self.inspector_tab: QtWidgets.QWidget
        self.dt_auto_input: QtWidgets.QCheckBox
        self.inspectors_tab: QtWidgets.QTabWidget

        self.add_sensor_button: QtWidgets.QPushButton
        self.add_sensor_button.clicked.connect(self._add_sensor_button_clicked_cb)

        self.clear_button: QtWidgets.QPushButton
        self.clear_button.clicked.connect(self._clear_button_clicked_cb)

        self.simulate_button: SimulationControlButton
        self.simulate_button.clicked.connect(self._simulate_button_clicked_cb)

        self.add_button: AddSimulationItemButton
        self._register_add_source_callbacks()

        self.remove_button: QtWidgets.QPushButton
        self.remove_button.clicked.connect(self._remove_button_clicked_cb)

        self.simulation_render_area: SimulationRenderArea
        self.simulation_render_area.simulation = self._simulation

        self.sensors_list: QtWidgets.QListWidget
        self.sensors_list.itemSelectionChanged.connect(self._sensors_list_selection_changed_cb)

        self.sources_list: QtWidgets.QListWidget
        self.sources_list.itemSelectionChanged.connect(self._sources_list_selection_changed_cb)

        self.objects_list: QtWidgets.QListWidget
        self.objects_list.itemSelectionChanged.connect(self._objects_list_selection_changed_cb)

        self.lists_tab: QtWidgets.QTabWidget
        self.lists_tab.currentChanged.connect(self._simulation_items_list_changed_cb)

        self.dx_input: FloatTooltipSpinbox
        self.dx_input.validate_func = _input_greater_than_zero
        self.dx_input.valueChanged.connect(self._dx_input_changed)

        self.dt_input: FloatTooltipSpinbox
        self.dt_input.validate_func = _input_greater_than_zero
        self.dt_input.valueChanged.connect(self._dt_input_changed)

        self.grid_size_x_input: QtWidgets.QSpinBox
        self.grid_size_x_input.valueChanged.connect(self._grid_size_x_input_changed_cb)

        self.grid_size_y_input: QtWidgets.QSpinBox
        self.grid_size_y_input.valueChanged.connect(self._grid_size_y_input_changed_cb)

        self.pml_reflectivity_input: FloatTooltipSpinbox
        self.pml_reflectivity_input.validate_func = _input_greater_than_zero
        self.pml_reflectivity_input.valueChanged.connect(self._pml_reflectivity_input_changed_cb)

        self.pml_layers_input: QtWidgets.QSpinBox
        self.pml_layers_input.valueChanged.connect(self._pml_layers_input_changed_cb)

        self.pml_order_input: QtWidgets.QSpinBox
        self.pml_order_input.valueChanged.connect(self._pml_order_input_changed_cb)

        self.source_inspector = SourceInspector()
        self.source_inspector.source_params_changed.connect(self._source_params_changed_cb)
        self.source_inspector.set_max_source_pos(self._simulation._grid_size_x, self._simulation._grid_size_y)

        self.object_inspector = ObjectInspector()
        self.object_inspector.object_params_changed.connect(self._object_params_changed_cb)
        self.object_inspector.set_simulation_size(self._simulation._grid_size_x, self._simulation._grid_size_y)

        self.sensor_inspector = SensorInspector()
        self.sensor_inspector.sensor_params_changed.connect(self._sensor_params_changed_cb)

        self.show_objects_input: QtWidgets.QCheckBox
        self.show_objects_input.checkStateChanged.connect(self._show_objects_checkbox_changed_cb)

        self.show_sources_input: QtWidgets.QCheckBox
        self.show_sources_input.checkStateChanged.connect(self._show_sources_checkbox_changed_cb)

        self.show_pml_input: QtWidgets.QCheckBox
        self.show_pml_input.checkStateChanged.connect(self._show_pml_input_cb)

        self.show_sensors_input: QtWidgets.QCheckBox
        self.show_sensors_input.checkStateChanged.connect(self._show_sensors_checkbox_changed_cb)

        self.steps_per_render_input: QtWidgets.QSpinBox
        self.current_frame_label: QtWidgets.QLabel
        self.simulation_time_label: QtWidgets.QLabel
        self.render_time_label: QtWidgets.QLabel
        self.sensors_area_content: QtWidgets.QWidget

        self.sensors_area_layout = self.sensors_area_content.layout()
        assert isinstance(self.sensors_area_layout, QtWidgets.QVBoxLayout)
        self.sensors_area_layout.setDirection(QtWidgets.QBoxLayout.Direction.BottomToTop)

    def _set_dx_input_tooltip(self) -> None:
        self.dx_input.setToolTip(f'{self._simulation.dx:.2E}')

    def _set_dt_input_tooltip(self) -> None:
        self.dt_input.setToolTip(f'{self._simulation.dt:.2E}')

    def _create_simulation_object(self, object_type: str, pos_x: int, pos_y: int) -> SimulationObject:
        if object_type == 'box':
            return Box(1.0, MU_0, pos_x, pos_y, DEFAULT_BOX_SIZE, DEFAULT_BOX_SIZE)

        raise ValueError(f'Invalid simulation object type: {object_type}')

    def _add_simulation_object(self, object_type: str) -> None:
        obj_id = self._simulation.add_object(
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
        return (self._simulation.grid_size_x // 2,
                self._simulation.grid_size_y // 2)

    def _create_simulation_source(self, source_type: str, pos_x: int, pos_y: int) -> SimulationSource:
        if source_type == 'sine':
            return SineSource(pos_x, pos_y, 60e9, 0.0, 1.0)
        elif source_type == 'cosine':
            return CosineSource(pos_x, pos_y, 60e9, 0.0, 1.0)

        raise ValueError(f'Invalid simulation source type: {source_type}')

    def _add_simulation_source(self, source_type: str) -> None:
        pos_x, pos_y = self._get_simulation_center_pos()
        source = self._create_simulation_source(source_type, pos_x, pos_y)
        source_id = self._simulation.add_source(source)

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

    def _register_add_source_callbacks(self) -> None:
        self.add_button.register_add_callbacks((
            ('sine', self._add_simulation_source),
            ('cosine', self._add_simulation_source)))

    def _register_add_object_callbacks(self) -> None:
        self.add_button.register_add_callbacks((
            ('box', self._add_simulation_object),))

    def resizeEvent(self, event: QtGui.QResizeEvent | None) -> None:
        super().resizeEvent(event)

        if event is not None:
            self.simulation_render_area.figure.tight_layout(pad=1)

    @QtCore.pyqtSlot()
    def _add_sensor_button_clicked_cb(self) -> None:
        pos_x, pos_y = self._get_simulation_center_pos()
        sensor = SimulationSensor(pos_x, pos_y)
        sensor_id = self._simulation.add_sensor(sensor)

        item = QtWidgets.QListWidgetItem(f'Sensor {self._sensor_counter + 1}')
        item.setData(DATA_ROLE, sensor_id)
        self.sensors_list.addItem(item)

        self._sensor_counter += 1

        if self.simulation_render_area.show_sensors and self.simulation_render_area.draw_simulation:
            self.simulation_render_area.draw()

        widget = SensorView(f'Sensor {self._sensor_counter}')
        self._sensor_widgets[sensor_id] = widget

        assert self.sensors_area_layout is not None
        self.sensors_area_layout.addWidget(widget)
        widget.show()
        self.sensors_area_layout.update()

    @QtCore.pyqtSlot()
    def _show_sensors_checkbox_changed_cb(self) -> None:
        self.simulation_render_area.show_sensors = self.show_sensors_input.isChecked()
        self.simulation_render_area.draw(do_full_redraw=True)

    @QtCore.pyqtSlot()
    def _simulation_items_list_changed_cb(self) -> None:
        index = self.lists_tab.currentIndex()
        if index == SOURCES_LIST_TAB_INDEX:
            self._register_add_source_callbacks()
        elif index == OBJECTS_LIST_TAB_INDEX:
            self._register_add_object_callbacks()
        elif index == SENSORS_LIST_TAB_INDEX:
            self.add_button.register_single_add_callback(None, lambda _: self._add_sensor_button_clicked_cb())

    @QtCore.pyqtSlot()
    def _object_params_changed_cb(self) -> None:
        item = self.objects_list.currentItem()
        if item is not None:
            object_id: uuid.UUID = item.data(DATA_ROLE)
            self._simulation.update_object(object_id)

        if self.simulation_render_area.show_objects and self.simulation_render_area.draw_simulation:
            self.simulation_render_area.draw(do_full_redraw=True)

    @QtCore.pyqtSlot()
    def _sensor_params_changed_cb(self) -> None:
        if self.simulation_render_area.show_sensors and self.simulation_render_area.draw_simulation:
            self.simulation_render_area.draw(do_full_redraw=True)

    @QtCore.pyqtSlot()
    def _source_params_changed_cb(self) -> None:
        item = self.sources_list.currentItem()
        if item is not None:
            source_id: uuid.UUID = item.data(DATA_ROLE)
            self._simulation.update_source(source_id)

        if self.simulation_render_area.show_sources and self.simulation_render_area.draw_simulation:
            self.simulation_render_area.draw(do_full_redraw=True)

    @QtCore.pyqtSlot()
    def _sensors_list_selection_changed_cb(self) -> None:
        item = self.sensors_list.currentItem()
        if item is None:
            return

        item_id = item.data(DATA_ROLE)
        assert isinstance(item_id, uuid.UUID)

        self.sensor_inspector.set_sensor(self._simulation.sensors[item_id])
        self._change_inspector_widget(self.sensor_inspector)

    @QtCore.pyqtSlot()
    def _sources_list_selection_changed_cb(self) -> None:
        item = self.sources_list.currentItem()
        if item is None:
            return

        item_id = item.data(DATA_ROLE)
        assert isinstance(item_id, uuid.UUID)

        self.source_inspector.set_source(self._simulation.sources[item_id])
        self._change_inspector_widget(self.source_inspector)

    @QtCore.pyqtSlot()
    def _objects_list_selection_changed_cb(self) -> None:
        item = self.objects_list.currentItem()
        if item is None:
            return

        item_id = item.data(DATA_ROLE)
        assert isinstance(item_id, uuid.UUID)

        self.object_inspector.set_object(self._simulation.objects[item_id])
        self._change_inspector_widget(self.object_inspector)

    @QtCore.pyqtSlot()
    def _pml_reflectivity_input_changed_cb(self) -> None:
        self._simulation.set_pml_params(reflectivity=self.pml_reflectivity_input.value())

    @QtCore.pyqtSlot()
    def _pml_layers_input_changed_cb(self) -> None:
        self._simulation.set_pml_params(layers=self.pml_layers_input.value())

    @QtCore.pyqtSlot()
    def _pml_order_input_changed_cb(self) -> None:
        self._simulation.set_pml_params(order=self.pml_order_input.value())

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
        self._simulation.reset()
        self.simulation_render_area.draw()

    @QtCore.pyqtSlot()
    def _simulation_frame_ready_cb(self) -> None:
        current_tab = self.simulation_tab.currentIndex()

        draw_time = 0.0
        if current_tab == SIMULATION_TAB_INDEX:
            if self._simulation.current_frame % self.steps_per_render_input.value() == 0:
                self.simulation_render_area.draw()

            draw_time = self.simulation_render_area.draw_time_ms
        elif current_tab == SENSORS_TAB_INDEX:
            for (sensor_id, sensor) in self._simulation.sensors.items():
                widget = self._sensor_widgets[sensor_id]
                widget.update_sensor_data(sensor.data, self._simulation.time_array)

                draw_time += widget.draw_time_ms

        self.current_frame_label.setText(str(self._simulation.current_frame))
        self.simulation_time_label.setText(f'{self._simulation.simulation_time_ms:.1f}')
        self.render_time_label.setText(f'{draw_time:.1f}')

        if self._simulation_job is not None:
            self._simulation_job.notify_frame_processed()

    @QtCore.pyqtSlot()
    def _dx_input_changed(self) -> None:
        value = self.dx_input.value()
        if value <= 0.0:
            self.dx_input.setValue(self._simulation.dx)
            return

        self._simulation.set_dx(value, self.dt_auto_input.isChecked())

    @QtCore.pyqtSlot()
    def _dt_input_changed(self) -> None:
        value = self.dt_input.value()
        if value <= 0.0:
            self.dx_input.setValue(self._simulation._dt)
            return

        self._simulation.set_dt(value)

    @QtCore.pyqtSlot()
    def _grid_size_x_input_changed_cb(self) -> None:
        value = self.grid_size_x_input.value()
        if value <= 0:
            self.grid_size_x_input.setValue(self._simulation._grid_size_x)
            return

        self._simulation.set_grid_size(value, None)
        self.source_inspector.set_max_source_pos(self._simulation._grid_size_x, self._simulation._grid_size_y)
        self.object_inspector.set_simulation_size(self._simulation._grid_size_x, self._simulation._grid_size_y)

    @QtCore.pyqtSlot()
    def _grid_size_y_input_changed_cb(self) -> None:
        value = self.grid_size_y_input.value()
        if value <= 0:
            self.grid_size_y_input.setValue(self._simulation._grid_size_y)
            return

        self._simulation.set_grid_size(None, value)
        self.source_inspector.set_max_source_pos(self._simulation._grid_size_x, self._simulation._grid_size_y)
        self.object_inspector.set_simulation_size(self._simulation._grid_size_x, self._simulation._grid_size_y)

    @QtCore.pyqtSlot()
    def _simulate_button_clicked_cb(self) -> None:
        is_simulation_running = self._simulation_job is not None

        if is_simulation_running:
            self._simulation_job.stop() # type: ignore[union-attr]
            self._simulation_job = None
        else:
            self._simulation_job = SimulationJob(self._simulation)
            self._simulation_job.frame_ready.connect(self._simulation_frame_ready_cb)
            self._simulation_job.start()

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

                self._simulation.remove_source(item_id)
                self.sources_list.takeItem(self.sources_list.row(current_item))

                current_item = self.sources_list.currentItem()
                if current_item is not None:
                    new_source = self._simulation.sources[current_item.data(DATA_ROLE)] # type: ignore
                    self.source_inspector.set_source(new_source)
        elif current_tab == OBJECTS_LIST_TAB_INDEX:
            current_item = self.objects_list.currentItem()
            if current_item is not None:
                item_id = current_item.data(DATA_ROLE)
                assert isinstance(item_id, uuid.UUID)

                self._simulation.remove_object(item_id)
                self.objects_list.takeItem(self.objects_list.row(current_item))

                current_item = self.objects_list.currentItem()
                if current_item is not None:
                    new_object = self._simulation.objects[current_item.data(DATA_ROLE)] # type: ignore
                    self.object_inspector.set_object(new_object)

        self.simulation_render_area.draw()

    @QtCore.pyqtSlot(object)
    def _sim_params_changed(self, params: SimulationParams) -> None:
        self.dx_input.setValue(params.dx)
        self.dt_input.setValue(params.dt)

        self.grid_size_x_input.setValue(params.grid_size_x)
        self.grid_size_y_input.setValue(params.grid_size_y)

        self.pml_reflectivity_input.setValue(params.pml_reflectivity)

        self.pml_order_input.setValue(params.pml_order)

        self.pml_layers_input.setValue(params.pml_layers)
        self.pml_layers_input.setMaximum(math.floor(min(params.grid_size) / 2))

        self.simulation_render_area.draw()

def _input_greater_than_zero(_input: float | int) -> bool:
    return _input > 0

if __name__ == '__main__':
    simulation = Simulation(
            DEFAULT_DT,
            DEFAULT_DX,
            1500,
            500,
            500,
            1e-8,
            25,
            3)

    app = QtWidgets.QApplication([])
    ui = UI(simulation)

    ui.showMaximized()
    app.exec()
