import threading
import time

from PyQt6.QtCore import QThread, pyqtSignal

from main.simulation.simulation import Simulation

JOB_THREAD_WAIT_TIMEOUT = 0.016 # 16 milliseconds

class SimulationJob(QThread):
    frame_ready = pyqtSignal(float)

    def __init__(self, simulation: Simulation) -> None:
        super().__init__()

        self._simulation = simulation
        self._is_running = True
        self._previous_frame_processed_event = threading.Event()
        self._previous_frame_processed_event.set()

    def notify_frame_processed(self) -> None:
        self._previous_frame_processed_event.set()

    def stop(self) -> None:
        self._is_running = False

    def run(self) -> None:
        while self._is_running:
            if not self._previous_frame_processed_event.wait(JOB_THREAD_WAIT_TIMEOUT):
                continue

            start = time.perf_counter()
            self._simulation.simulate_frame()
            simulation_time = time.perf_counter() - start

            self.frame_ready.emit(simulation_time)

            self._previous_frame_processed_event.clear()
