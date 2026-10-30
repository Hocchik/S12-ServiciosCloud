"""Caso de 4 tareas × 2 VMs con valores verificados a mano (tabla de CLAUDE.md)."""

import pytest

from scheduling import metrics
from scheduling.models import VM, Assignment, Task
from scheduling.schedulers import FCFS, MaxMin, MinMin

TASKS = [Task(0, 4000), Task(1, 1000), Task(2, 3000), Task(3, 2000)]
VMS = [VM(0, 1000), VM(1, 2000)]

EXPECTED = {
    FCFS: {
        "assignments": [(0, 0, 0, 4), (1, 1, 0, 0.5), (2, 0, 4, 7), (3, 1, 0.5, 1.5)],
        "makespan": 7.0,
        "avg_wait": 1.125,
        "max_wait": 4.0,
        "di": 1.2941,
    },
    MinMin: {
        "assignments": [(1, 1, 0, 0.5), (3, 1, 0.5, 1.5), (2, 0, 0, 3), (0, 1, 1.5, 3.5)],
        "makespan": 3.5,
        "avg_wait": 0.5,
        "max_wait": 1.5,
        "di": 0.1538,
    },
    MaxMin: {
        "assignments": [(0, 1, 0, 2), (2, 0, 0, 3), (3, 1, 2, 3), (1, 1, 3, 3.5)],
        "makespan": 3.5,
        "avg_wait": 1.25,
        "max_wait": 3.0,
        "di": 0.1538,
    },
}


@pytest.mark.parametrize("scheduler_cls", EXPECTED, ids=lambda cls: cls.name)
def test_assignments_in_decision_order(scheduler_cls):
    result = scheduler_cls().schedule(TASKS, VMS)
    expected = [Assignment(*row) for row in EXPECTED[scheduler_cls]["assignments"]]
    assert [(a.task_id, a.vm_id) for a in result] == [(e.task_id, e.vm_id) for e in expected]
    assert [a.start for a in result] == pytest.approx([e.start for e in expected])
    assert [a.finish for a in result] == pytest.approx([e.finish for e in expected])


@pytest.mark.parametrize("scheduler_cls", EXPECTED, ids=lambda cls: cls.name)
def test_metrics(scheduler_cls):
    result = scheduler_cls().schedule(TASKS, VMS)
    row = metrics.compute_all(result, TASKS, VMS)
    expected = EXPECTED[scheduler_cls]
    assert row["makespan"] == pytest.approx(expected["makespan"])
    assert row["avg_wait"] == pytest.approx(expected["avg_wait"])
    assert row["max_wait"] == pytest.approx(expected["max_wait"])
    assert row["di"] == pytest.approx(expected["di"], abs=1e-4)


def test_lower_bound():
    assert metrics.lower_bound(TASKS, VMS) == pytest.approx(10000 / 3000)


def test_min_min_vm_tie_goes_to_lowest_index():
    """Paso 3 de Min-Min: T2 da CT = 3.0 en VM0 y en VM1, y debe ganar VM0."""
    result = MinMin().schedule(TASKS, VMS)
    t2 = next(a for a in result if a.task_id == 2)
    assert t2.vm_id == 0
    assert t2.finish == pytest.approx(3.0)


@pytest.mark.parametrize("scheduler_cls", [MinMin, MaxMin], ids=lambda cls: cls.name)
def test_task_tie_goes_to_lowest_index(scheduler_cls):
    """Tareas idénticas empatan en todo: deben atenderse en orden de índice."""
    tasks = [Task(0, 1000), Task(1, 1000), Task(2, 1000)]
    vms = [VM(0, 1000)]
    assert [a.task_id for a in scheduler_cls().schedule(tasks, vms)] == [0, 1, 2]
