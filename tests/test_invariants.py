"""Invariantes que debe cumplir cualquier planificación sobre datasets aleatorios."""

import pytest

from scheduling import metrics
from scheduling.datasets import SCENARIOS, generate_tasks, make_vms
from scheduling.schedulers import FCFS, MaxMin, MinMin

TOL = 1e-9
SCHEDULERS = [FCFS, MinMin, MaxMin]
SEEDS = range(5)

CASES = [
    pytest.param(cls, scenario, seed, id=f"{cls.name}-{scenario}-{seed}")
    for cls in SCHEDULERS
    for scenario in SCENARIOS
    for seed in SEEDS
]


@pytest.mark.parametrize("scheduler_cls, scenario, seed", CASES)
def test_each_task_assigned_exactly_once(scheduler_cls, scenario, seed):
    tasks = generate_tasks(scenario, seed)
    result = scheduler_cls().schedule(tasks, make_vms())
    assert sorted(a.task_id for a in result) == [t.id for t in tasks]


@pytest.mark.parametrize("scheduler_cls, scenario, seed", CASES)
def test_duration_equals_etc(scheduler_cls, scenario, seed):
    tasks = generate_tasks(scenario, seed)
    vms = make_vms()
    mi = {t.id: t.mi for t in tasks}
    mips = {v.id: v.mips for v in vms}
    for a in scheduler_cls().schedule(tasks, vms):
        assert a.finish - a.start == pytest.approx(mi[a.task_id] / mips[a.vm_id], abs=TOL)


@pytest.mark.parametrize("scheduler_cls, scenario, seed", CASES)
def test_no_overlap_within_vm(scheduler_cls, scenario, seed):
    vms = make_vms()
    result = scheduler_cls().schedule(generate_tasks(scenario, seed), vms)
    for vm in vms:
        intervals = sorted((a.start, a.finish) for a in result if a.vm_id == vm.id)
        for (_, previous_finish), (next_start, _) in zip(intervals, intervals[1:]):
            assert next_start >= previous_finish - TOL


@pytest.mark.parametrize("scheduler_cls, scenario, seed", CASES)
def test_makespan_respects_lower_bound(scheduler_cls, scenario, seed):
    tasks = generate_tasks(scenario, seed)
    vms = make_vms()
    result = scheduler_cls().schedule(tasks, vms)
    assert metrics.makespan(result) >= metrics.lower_bound(tasks, vms) - TOL


@pytest.mark.parametrize("scheduler_cls, scenario, seed", CASES)
def test_utilization_between_zero_and_one(scheduler_cls, scenario, seed):
    vms = make_vms()
    result = scheduler_cls().schedule(generate_tasks(scenario, seed), vms)
    for util in metrics.utilizations(result, vms):
        assert -TOL <= util <= 1 + TOL


@pytest.mark.parametrize("scheduler_cls, scenario, seed", CASES)
def test_same_seed_gives_identical_results(scheduler_cls, scenario, seed):
    vms = make_vms()
    first = scheduler_cls().schedule(generate_tasks(scenario, seed), vms)
    second = scheduler_cls().schedule(generate_tasks(scenario, seed), vms)
    assert first == second


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_different_seeds_give_different_datasets(scenario):
    assert generate_tasks(scenario, 0) != generate_tasks(scenario, 1)


def test_skewed_has_45_short_and_5_long_tasks():
    tasks = generate_tasks("skewed", 0)
    assert len(tasks) == 50
    assert sum(1000 <= t.mi <= 3000 for t in tasks) == 45
    assert sum(15000 <= t.mi <= 20000 for t in tasks) == 5


def test_mixed_range():
    tasks = generate_tasks("mixed", 0)
    assert len(tasks) == 50
    assert all(1000 <= t.mi <= 20000 for t in tasks)
