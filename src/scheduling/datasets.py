"""Generación de tareas por escenario y definición de las VMs fijas."""

from pathlib import Path

import numpy as np
import pandas as pd

from scheduling.models import VM, Task

VM_MIPS = (500, 1000, 1500, 2000, 2500)
SCENARIOS = ("mixed", "skewed")
SEEDS = tuple(range(30))
N_TASKS = 50


def make_vms() -> list[VM]:
    """Devuelve las 5 VMs fijas de todos los experimentos."""
    return [VM(id=i, mips=mips) for i, mips in enumerate(VM_MIPS)]


def generate_tasks(scenario: str, seed: int) -> list[Task]:
    """Genera las 50 tareas de un escenario; el orden resultante es el orden de llegada.

    - `mixed`: MI ~ U(1000, 20000).
    - `skewed`: 45 tareas ~ U(1000, 3000) y 5 tareas ~ U(15000, 20000).
    """
    rng = np.random.default_rng(seed)
    if scenario == "mixed":
        lengths = rng.uniform(1000, 20000, N_TASKS)
    elif scenario == "skewed":
        lengths = np.concatenate(
            [rng.uniform(1000, 3000, 45), rng.uniform(15000, 20000, 5)]
        )
    else:
        raise ValueError(f"Escenario desconocido: {scenario}")
    rng.shuffle(lengths)
    return [Task(id=i, mi=float(mi)) for i, mi in enumerate(lengths)]


def save_tasks(tasks: list[Task], path: Path) -> None:
    """Guarda las tareas en CSV."""
    frame = pd.DataFrame(
        {
            "id": [t.id for t in tasks],
            "mi": [t.mi for t in tasks],
            "arrival": [t.arrival for t in tasks],
        }
    )
    frame.to_csv(path, index=False)


def save_vms(vms: list[VM], path: Path) -> None:
    """Guarda las VMs en CSV."""
    frame = pd.DataFrame({"id": [v.id for v in vms], "mips": [v.mips for v in vms]})
    frame.to_csv(path, index=False)
