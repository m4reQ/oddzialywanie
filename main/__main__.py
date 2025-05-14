import math
import typing as t
import uuid

import numpy as np
from matplotlib.patches import Circle
from PyQt6 import QtCore, QtGui, QtWidgets, uic

from main import mpl_canvas, simulation

MAIN_WINDOW_UI_FILEPATH = './ui/main_window.ui'
SIMULATION_ITEM_ROLE = QtCore.Qt.ItemDataRole.UserRole + 2137

class SimulationJob(QtCore.QThread):
    frame_ready = QtCore.pyqtSignal()

    def __init__(self, simulation: simulation.Simulation, sources: t.Iterable[simulation.Source]) -> None:
        super().__init__()

        self.simulation = simulation
        self.sources = sources
        self.is_running = True
        self.previous_frame_processed = True

    def notify_frame_processed(self) -> None:
        self.previous_frame_processed = True

    def stop(self) -> None:
        self.is_running = False

    def run(self) -> None:
        while self.is_running:
            if not self.previous_frame_processed:
                continue

            self.simulation.simulate_frame(self.sources)
            self.frame_ready.emit()

            self.previous_frame_processed = False

class UI(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        uic.load_ui.loadUi(MAIN_WINDOW_UI_FILEPATH, self)

        self.clear_button: QtWidgets.QPushButton
        self.simulate_button: QtWidgets.QPushButton
        self.add_button: QtWidgets.QPushButton
        self.remove_button: QtWidgets.QPushButton
        self.figure_canvas: mpl_canvas.MPLCanvas
        self.inspector_widget: QtWidgets.QWidget
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

        self.status_bar_frame_index = QtWidgets.QLabel('Current frame: 0')
        self.status_bar.addWidget(self.status_bar_frame_index)

        self._simulation_sources = dict[uuid.UUID, simulation.Source]()
        self._source_counter = 0
        self._simulation_objects = dict[uuid.UUID, simulation.SimulationObject]()
        self._object_counter = 0

        self.axes = self.figure_canvas.figure.add_subplot(1, 1, 1)
        self.simulation = simulation.Simulation(
            simulation.DEFAULT_DT,
            simulation.DEFAULT_DX,
            500,
            500,
            1e-8,
            25,
            3)
        self.simulation.deltas_changed.connect(self._sim_deltas_changed_cb)
        self.simulation.grid_size_changed.connect(self._sim_grid_size_changed_cb)
        self.simulation.pml_params_changed.connect(self._sim_pml_params_changed)
        self.simulation.emit_params_changed_signal()

        self.simulation_job: SimulationJob | None = None

        self.add_button.clicked.connect(self._add_button_clicked_cb)
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

    def resizeEvent(self, event: QtGui.QResizeEvent | None) -> None:
        super().resizeEvent(event)

        if event is not None:
            self.figure_canvas.figure.tight_layout(pad=1)

    def _stop_current_simulation_job(self) -> None:
        if self.simulation_job is not None:
            self.simulation_job.stop()
            self.simulation_job = None

    def _redraw_pml_canvas(self) -> None:
        self.axes.imshow(self.simulation.get_pml_data(), origin='lower', cmap='viridis', aspect='auto')
        self.axes.set_xlabel('x')
        self.axes.set_ylabel('y')

        self.figure_canvas.draw()

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

    @QtCore.pyqtSlot()
    def _show_checkbox_changed_cb(self) -> None:
        self._redraw_simulation_canvas()

    @QtCore.pyqtSlot()
    def _clear_button_clicked_cb(self) -> None:
        self._stop_current_simulation_job()
        self.simulation.reset()

    @QtCore.pyqtSlot()
    def _simulation_frame_ready_cb(self) -> None:
        self._redraw_simulation_canvas()
        self.status_bar_frame_index.setText(f'Current frame: {self.simulation.current_frame}')

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

        self.simulation.set_grid_size(value, self.simulation._grid_size_y)

    @QtCore.pyqtSlot()
    def _grid_size_y_input_changed_cb(self) -> None:
        value = self.grid_size_y_input.value()
        if value <= 0:
            self.grid_size_y_input.setValue(self.simulation._grid_size_y)
            return

        self.simulation.set_grid_size(self.simulation._grid_size_x, value)

    @QtCore.pyqtSlot()
    def _simulate_button_clicked_cb(self) -> None:
        self.simulate_button.setText('Start Simulation' if self.simulation_job is not None else 'Stop Simulation')

        if self.simulation_job is not None:
            self.simulation_job.stop()
            self.simulation_job = None
        else:
            self.simulation_job = SimulationJob(self.simulation, self._simulation_sources.values())
            self.simulation_job.frame_ready.connect(self._simulation_frame_ready_cb)
            self.simulation_job.start()

    @QtCore.pyqtSlot(uuid.UUID)
    def _simulation_scene_selection_cb(self, object_id: uuid.UUID) -> None:
        self._select_list_item_by_id(self.sources_list, object_id)
        self._select_list_item_by_id(self.objects_list, object_id)

    @QtCore.pyqtSlot()
    def _add_button_clicked_cb(self) -> None:
        current_tab = self.lists_tab.currentIndex()
        item_id = uuid.uuid4()
        if current_tab == 1:
            self._simulation_objects[item_id] = simulation.Box(0.0, 0.0, 250.0, 250.0, 30.0, 30.0)

            list_item = QtWidgets.QListWidgetItem(f'Object {self._object_counter}')
            list_item.setData(SIMULATION_ITEM_ROLE, item_id)
            self.objects_list.addItem(list_item)

            self._object_counter += 1
        elif current_tab == 0:
            item = simulation.SourceSine(250.0, 250.0, 1000.0)
            item.calculate_data(self.simulation._dt, 1000)

            self._simulation_sources[item_id] = item

            list_item = QtWidgets.QListWidgetItem(f'Source {self._source_counter}')
            list_item.setData(SIMULATION_ITEM_ROLE, item_id)
            self.sources_list.addItem(list_item)

            self._source_counter += 1

        self._redraw_simulation_canvas()

    @QtCore.pyqtSlot()
    def _remove_button_clicked_cb(self) -> None:
        current_tab = self.lists_tab.currentIndex()
        if current_tab == 0:
            current_item = self.sources_list.currentItem()
            if current_item is not None:
                item_id = current_item.data(SIMULATION_ITEM_ROLE)
                assert isinstance(item_id, uuid.UUID)

                self.sources_list.takeItem(self.sources_list.row(current_item))
                self._simulation_sources.pop(item_id)
        elif current_tab == 1:
            current_item = self.objects_list.currentItem()
            if current_item is not None:
                item_id = current_item.data(SIMULATION_ITEM_ROLE)
                assert isinstance(item_id, uuid.UUID)

                self.objects_list.takeItem(self.objects_list.row(current_item))
                self._simulation_objects.pop(item_id)

        self._redraw_simulation_canvas()

    def _redraw_simulation_canvas(self) -> None:
        self.axes.clear()
        self.axes.set_xlabel('X')
        self.axes.set_ylabel('Y')
        self.axes.imshow(
            self.simulation.get_simulation_data(),
            origin='lower',
            vmin=-1,
            vmax=1,
            cmap='jet')

        if self.show_sources_input.isChecked():
            for source in self._simulation_sources.values():
                self.axes.add_patch(Circle((source.pos_x, source.pos_y), 2.0, color='red'))

        if self.show_objects_input.isChecked():
            for object in self._simulation_objects.values():
                object.draw(self.axes)

        self.figure_canvas.draw()

    def _select_list_item_by_id(self, _list: QtWidgets.QListWidget, object_id: uuid.UUID) -> None:
        for i in range(_list.count()):
            item = _list.item(i)
            assert item is not None

            if item.data(SIMULATION_ITEM_ROLE) == object_id:
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

def _apply_jet_colormap(data: np.ndarray) -> np.ndarray:
    data_min = np.min(data)
    data_max = np.max(data)
    normalized = np.zeros_like(data) if data_max == data_min else (data - data_min) / (data_max - data_min)

    r = np.clip(1.5 - np.abs(4.0 * normalized - 3.0), 0, 1)
    g = np.clip(1.5 - np.abs(4.0 * normalized - 2.0), 0, 1)
    b = np.clip(1.5 - np.abs(4.0 * normalized - 1.0), 0, 1)
    return (np.stack((r, g, b), axis=-1) * 255).astype(np.uint8)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    ui = UI()

    ui.show()
    app.exec()
