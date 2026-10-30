"""Entidades del modelo de planificación."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    """Tarea de longitud `mi` (millones de instrucciones) disponible desde `arrival`."""

    id: int
    mi: float
    arrival: float = 0.0


@dataclass(frozen=True)
class VM:
    """Máquina virtual con capacidad `mips` (millones de instrucciones por segundo)."""

    id: int
    mips: float


@dataclass(frozen=True)
class Assignment:
    """Ejecución de una tarea en una VM durante el intervalo [start, finish], en segundos."""

    task_id: int
    vm_id: int
    start: float
    finish: float
