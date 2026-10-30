"""Caso de 8 trabajos y 3 VMs de la guía de evaluación práctica.

Reutiliza los planificadores y las métricas del laboratorio. Una VM con `mips = 1` hace que
los MI de una tarea equivalgan a sus minutos, y sus resultados se leen en minutos.
"""

from scheduling import metrics
from scheduling.models import VM, Assignment, Task
from scheduling.schedulers import FCFS, MaxMin, MinMin

DURATIONS = (12, 4, 8, 3, 10, 6, 2, 7)
PROPOSED_LOADS = ((5, 0), (3, 1, 4), (6, 7, 2))
PROPOSED_LONG_FIRST = ((0, 5), (4, 3, 1), (2, 7, 6))


def make_case_tasks() -> list[Task]:
    """Devuelve los trabajos J1..J8; el `id` de cada tarea es su número menos uno."""
    return [Task(i, duration) for i, duration in enumerate(DURATIONS)]


def make_case_vms() -> list[VM]:
    """Devuelve las 3 VMs homogéneas del caso."""
    return [VM(j, 1) for j in range(3)]


def make_vcpu_change_vms() -> list[VM]:
    """Devuelve las VMs de la pregunta 3: 8, 2 y 2 vCPU.

    Supone que la duración escala de forma lineal con las vCPU, con 4 vCPU como referencia.
    """
    return [VM(0, 2.0), VM(1, 0.5), VM(2, 0.5)]


def manual_plan(tasks: list[Task], vms: list[VM], groups: tuple[tuple[int, ...], ...]) -> list[Assignment]:
    """Construye una asignación a mano: `groups[j]` lista, en orden, las tareas de la VM j."""
    plan = []
    for vm, group in zip(vms, groups):
        ready = 0.0
        for task_id in group:
            finish = ready + tasks[task_id].mi / vm.mips
            plan.append(Assignment(task_id, vm.id, ready, finish))
            ready = finish
    return plan


def case_plans(tasks: list[Task], vms: list[VM]) -> dict[str, list[Assignment]]:
    """Calcula cada estrategia del caso.

    Con VMs iguales, Min-Min equivale a SJF con la VM que se libera primero, y Max-Min a LPT.
    """
    return {
        "Round Robin": FCFS().schedule(tasks, vms),
        "SJF": MinMin().schedule(tasks, vms),
        "LPT": MaxMin().schedule(tasks, vms),
        "Propuesta": manual_plan(tasks, vms, PROPOSED_LOADS),
        "Propuesta, largos primero": manual_plan(tasks, vms, PROPOSED_LONG_FIRST),
    }


def idle_time(assignments: list[Assignment], vms: list[VM]) -> float:
    """Suma, en todas las VMs, el tiempo libre hasta el makespan."""
    span = metrics.makespan(assignments)
    return sum(span - busy for busy in metrics.busy_times(assignments, vms))
