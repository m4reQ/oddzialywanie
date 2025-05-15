import enum


class SimulationState(enum.Enum):
    OK = enum.auto()
    ERROR = enum.auto()
    RUNNING = enum.auto()
