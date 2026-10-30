"""Caso de 8 trabajos de la guía de evaluación, con valores exactos."""

import pytest

from scheduling import metrics
from scheduling.guide_case import (
    case_plans,
    idle_time,
    make_case_tasks,
    make_case_vms,
    make_vcpu_change_vms,
)
from scheduling.schedulers import FCFS, MaxMin

TASKS = make_case_tasks()
VMS = make_case_vms()
PLANS = case_plans(TASKS, VMS)

EXPECTED = {
    "Round Robin": {"busy": [17, 21, 14], "makespan": 21, "avg_wait": 6.625, "arur": 0.8254, "idle": 11, "di": 0.4038},
    "SJF": {"busy": [18, 22, 12], "makespan": 22, "avg_wait": 3.375, "arur": 0.7879, "idle": 14, "di": 0.5769},
    "LPT": {"busy": [18, 16, 18], "makespan": 18, "avg_wait": 7.625, "arur": 0.9630, "idle": 2, "di": 0.1154},
    "Propuesta": {"busy": [18, 17, 17], "makespan": 18, "avg_wait": 3.375, "arur": 0.9630, "idle": 2, "di": 0.0577},
    "Propuesta, largos primero": {"busy": [18, 17, 17], "makespan": 18, "avg_wait": 7.25, "arur": 0.9630, "idle": 2, "di": 0.0577},
}


@pytest.mark.parametrize("name", EXPECTED)
def test_strategy_values(name):
    plan = PLANS[name]
    row = metrics.compute_all(plan, TASKS, VMS)
    expected = EXPECTED[name]
    assert metrics.busy_times(plan, VMS) == pytest.approx(expected["busy"])
    assert row["makespan"] == pytest.approx(expected["makespan"])
    assert row["avg_wait"] == pytest.approx(expected["avg_wait"])
    assert row["arur"] == pytest.approx(expected["arur"], abs=1e-4)
    assert row["di"] == pytest.approx(expected["di"], abs=1e-4)
    assert idle_time(plan, VMS) == pytest.approx(expected["idle"])


@pytest.mark.parametrize("name", EXPECTED)
def test_each_job_runs_once(name):
    assert sorted(a.task_id for a in PLANS[name]) == [t.id for t in TASKS]


def test_lower_bound_is_total_over_vms():
    assert metrics.lower_bound(TASKS, VMS) == pytest.approx(52 / 3)


def test_vcpu_change():
    """Pregunta 3: con escalado lineal, Round Robin sube a 42 min y Max-Min sigue en 18."""
    vms = make_vcpu_change_vms()
    assert metrics.makespan(FCFS().schedule(TASKS, vms)) == pytest.approx(42)
    assert metrics.makespan(MaxMin().schedule(TASKS, vms)) == pytest.approx(18)
