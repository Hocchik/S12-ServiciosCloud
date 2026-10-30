"""Algoritmos de planificación: FCFS cíclico, Min-Min y Max-Min.

Cada VM ejecuta una tarea a la vez, sin expropiación y en el orden de asignación
(space-shared). La lista devuelta respeta el orden en que se tomaron las decisiones.
"""

from abc import ABC, abstractmethod

from scheduling.models import VM, Assignment, Task

TOLERANCE = 1e-9


def _first_within_tolerance(values: list[float], target: float) -> int:
    """Devuelve el menor índice cuyo valor empata con `target` según la tolerancia."""
    return next(i for i, v in enumerate(values) if abs(v - target) <= TOLERANCE)


class Scheduler(ABC):
    """Interfaz común de los planificadores."""

    name: str
    slug: str

    @abstractmethod
    def schedule(self, tasks: list[Task], vms: list[VM]) -> list[Assignment]:
        """Asigna todas las tareas a las VMs y devuelve las asignaciones."""


class FCFS(Scheduler):
    """Asigna la tarea i a la VM `i % n_vms` sin mirar la velocidad de la VM.

    Es el comportamiento del broker por defecto de CloudSim. No es OLB: no busca la
    VM que se libera primero.
    """

    name = "FCFS"
    slug = "fcfs"

    def schedule(self, tasks: list[Task], vms: list[VM]) -> list[Assignment]:
        ready = [0.0] * len(vms)
        assignments = []
        for i, task in enumerate(tasks):
            j = i % len(vms)
            start = ready[j]
            finish = start + task.mi / vms[j].mips
            ready[j] = finish
            assignments.append(Assignment(task.id, vms[j].id, start, finish))
        return assignments


class _BestCompletionScheduler(Scheduler):
    """Esqueleto de Min-Min y Max-Min; solo difieren en qué tarea eligen en cada paso."""

    @staticmethod
    @abstractmethod
    def _select(completion_times: list[float]) -> float:
        """Elige, entre los CT mínimos de las tareas pendientes, el que se atiende."""

    def schedule(self, tasks: list[Task], vms: list[VM]) -> list[Assignment]:
        ready = [0.0] * len(vms)
        pending = list(tasks)
        assignments = []
        while pending:
            best_cts = []
            best_vms = []
            for task in pending:
                cts = [ready[j] + task.mi / vm.mips for j, vm in enumerate(vms)]
                # Empate entre VMs: gana la de menor índice.
                j = _first_within_tolerance(cts, min(cts))
                best_cts.append(cts[j])
                best_vms.append(j)

            # Empate entre tareas: gana la de menor índice, pues `pending` conserva el orden.
            k = _first_within_tolerance(best_cts, self._select(best_cts))
            task = pending.pop(k)
            j = best_vms[k]
            start = ready[j]
            finish = start + task.mi / vms[j].mips
            ready[j] = finish
            assignments.append(Assignment(task.id, vms[j].id, start, finish))
        return assignments


class MinMin(_BestCompletionScheduler):
    """En cada paso atiende la tarea con el menor de los CT mínimos."""

    name = "Min-Min"
    slug = "minmin"
    _select = staticmethod(min)


class MaxMin(_BestCompletionScheduler):
    """En cada paso atiende la tarea con el mayor de los CT mínimos."""

    name = "Max-Min"
    slug = "maxmin"
    _select = staticmethod(max)
