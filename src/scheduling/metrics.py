"""Métricas de una planificación, como funciones puras sobre listas de Assignment."""

from scheduling.models import VM, Assignment, Task


def makespan(assignments: list[Assignment]) -> float:
    """Instante en que termina la última tarea."""
    return max(a.finish for a in assignments)


def lower_bound(tasks: list[Task], vms: list[VM]) -> float:
    """Cota inferior del makespan: reparto perfecto o tarea más larga en la VM más rápida."""
    total_mi = sum(t.mi for t in tasks)
    total_mips = sum(v.mips for v in vms)
    return max(total_mi / total_mips, max(t.mi for t in tasks) / max(v.mips for v in vms))


def waits(assignments: list[Assignment], tasks: list[Task]) -> list[float]:
    """Espera de cada tarea: start − arrival.

    Con arrival = 0 la espera coincide con el instante de inicio; no es un error.
    """
    arrivals = {t.id: t.arrival for t in tasks}
    return [a.start - arrivals[a.task_id] for a in assignments]


def turnarounds(assignments: list[Assignment], tasks: list[Task]) -> list[float]:
    """Tiempo de retorno de cada tarea: finish − arrival."""
    arrivals = {t.id: t.arrival for t in tasks}
    return [a.finish - arrivals[a.task_id] for a in assignments]


def busy_times(assignments: list[Assignment], vms: list[VM]) -> list[float]:
    """Tiempo ocupado de cada VM: suma de los ETC de sus tareas (finish − start)."""
    busy = {v.id: 0.0 for v in vms}
    for a in assignments:
        busy[a.vm_id] += a.finish - a.start
    return [busy[v.id] for v in vms]


def utilizations(assignments: list[Assignment], vms: list[VM]) -> list[float]:
    """Utilización de cada VM: busy_j / makespan."""
    span = makespan(assignments)
    return [b / span for b in busy_times(assignments, vms)]


def arur(assignments: list[Assignment], vms: list[VM]) -> float:
    """Utilización media de los recursos (ARUR): media de util_j."""
    utils = utilizations(assignments, vms)
    return sum(utils) / len(utils)


def degree_of_imbalance(assignments: list[Assignment], vms: list[VM]) -> float:
    """Grado de desbalance (DI): (max(busy) − min(busy)) / mean(busy). Menor es mejor."""
    busy = busy_times(assignments, vms)
    return (max(busy) - min(busy)) / (sum(busy) / len(busy))


def compute_all(assignments: list[Assignment], tasks: list[Task], vms: list[VM]) -> dict[str, float]:
    """Calcula todas las métricas de una planificación; `util_vmN` usa la posición de la VM."""
    span = makespan(assignments)
    bound = lower_bound(tasks, vms)
    task_waits = waits(assignments, tasks)
    task_turnarounds = turnarounds(assignments, tasks)
    row = {
        "makespan": span,
        "lower_bound": bound,
        "makespan_ratio": span / bound,
        "avg_wait": sum(task_waits) / len(task_waits),
        "max_wait": max(task_waits),
        "avg_turnaround": sum(task_turnarounds) / len(task_turnarounds),
        "arur": arur(assignments, vms),
        "di": degree_of_imbalance(assignments, vms),
    }
    for j, util in enumerate(utilizations(assignments, vms)):
        row[f"util_vm{j}"] = util
    return row
