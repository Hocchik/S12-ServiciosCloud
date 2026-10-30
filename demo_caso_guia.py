"""Muestra el caso de 8 trabajos de la guía de evaluación: python demo_caso_guia.py"""

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from scheduling import metrics  # noqa: E402
from scheduling.guide_case import (  # noqa: E402
    DURATIONS,
    case_plans,
    idle_time,
    make_case_tasks,
    make_case_vms,
    make_vcpu_change_vms,
)
from scheduling.models import VM, Assignment, Task  # noqa: E402
from scheduling.schedulers import FCFS, MaxMin  # noqa: E402


def print_plan(name: str, plan: list[Assignment], tasks: list[Task], vms: list[VM]) -> None:
    """Imprime los trabajos y el uso de cada VM, y las métricas de la estrategia."""
    print(f"\n{name}")
    utils = metrics.utilizations(plan, vms)
    busy = metrics.busy_times(plan, vms)
    for j, vm in enumerate(vms):
        steps = sorted((a for a in plan if a.vm_id == vm.id), key=lambda a: a.start)
        jobs = ", ".join(f"J{a.task_id + 1} ({a.start:g}-{a.finish:g})" for a in steps)
        print(f"  VM{j + 1}: {jobs} | carga {busy[j]:g} min | uso {utils[j] * 100:.1f} %")
    row = metrics.compute_all(plan, tasks, vms)
    print(
        f"  Makespan: {row['makespan']:g} min | Espera promedio: {row['avg_wait']:.3f} min | "
        f"Ocioso total: {idle_time(plan, vms):g} min | DI: {row['di']:.2f}"
    )


def main() -> None:
    tasks = make_case_tasks()
    vms = make_case_vms()
    bound = metrics.lower_bound(tasks, vms)

    print("Caso de la guía: 8 trabajos en 3 VMs iguales (tiempos en minutos)")
    print("Duraciones:", ", ".join(f"J{i + 1}={d}" for i, d in enumerate(DURATIONS)))
    print(f"Total: {sum(DURATIONS)} | Cota inferior: {bound:.2f}, que con duraciones enteras es {math.ceil(bound)}")

    plans = case_plans(tasks, vms)
    for name, plan in plans.items():
        print_plan(name, plan, tasks, vms)

    print("\nComparación")
    print(f"  {'Estrategia':<27}{'Makespan':>9}{'Espera prom.':>14}{'Uso medio':>11}{'Ocioso':>8}{'DI':>7}")
    for name, plan in plans.items():
        row = metrics.compute_all(plan, tasks, vms)
        print(
            f"  {name:<27}{row['makespan']:>9g}{row['avg_wait']:>14.3f}"
            f"{row['arur'] * 100:>10.1f}%{idle_time(plan, vms):>8g}{row['di']:>7.2f}"
        )

    print("\nPregunta 3: VM1 con 8 vCPU, VM2 y VM3 con 2 vCPU (supone escalado lineal)")
    changed_vms = make_vcpu_change_vms()
    print_plan("Round Robin", FCFS().schedule(tasks, changed_vms), tasks, changed_vms)
    print_plan("Considerando la capacidad (Max-Min)", MaxMin().schedule(tasks, changed_vms), tasks, changed_vms)


if __name__ == "__main__":
    main()
