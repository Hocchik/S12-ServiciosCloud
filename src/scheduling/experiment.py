"""Bucle escenarios × semillas × algoritmos y construcción de las tablas de resultados."""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from scheduling import metrics
from scheduling.datasets import SCENARIOS, SEEDS, generate_tasks, make_vms, save_tasks, save_vms
from scheduling.models import Assignment
from scheduling.schedulers import FCFS, MaxMin, MinMin, Scheduler

TOLERANCE = 1e-9
GANTT_SEED = 0
SUMMARY_METRICS = (
    "makespan",
    "lower_bound",
    "makespan_ratio",
    "avg_wait",
    "max_wait",
    "avg_turnaround",
    "arur",
    "di",
    "util_vm0",
    "util_vm1",
    "util_vm2",
    "util_vm3",
    "util_vm4",
)
COMPARED_METRICS = ("makespan", "avg_wait")
WILCOXON_PAIRS = (("Min-Min", "Max-Min"), ("Min-Min", "FCFS"))


def make_schedulers() -> list[Scheduler]:
    """Devuelve los algoritmos en el orden en que se reportan."""
    return [FCFS(), MinMin(), MaxMin()]


def run_experiments(data_dir: Path, results_dir: Path) -> pd.DataFrame:
    """Corre todas las combinaciones, guarda datasets y asignaciones, y devuelve las métricas.

    El diseño es pareado: para cada escenario y semilla, los tres algoritmos reciben el
    mismo dataset.
    """
    vms = make_vms()
    save_vms(vms, data_dir / "vms.csv")
    rows = []
    for scenario in SCENARIOS:
        for seed in SEEDS:
            tasks = generate_tasks(scenario, seed)
            save_tasks(tasks, data_dir / f"tasks_{scenario}_seed{seed}.csv")
            for scheduler in make_schedulers():
                assignments = scheduler.schedule(tasks, vms)
                rows.append(
                    {
                        "scenario": scenario,
                        "seed": seed,
                        "algorithm": scheduler.name,
                        **metrics.compute_all(assignments, tasks, vms),
                    }
                )
                if seed == GANTT_SEED:
                    path = results_dir / f"assignments_{scenario}_{scheduler.slug}.csv"
                    _save_assignments(assignments, path)
    return pd.DataFrame(rows)


def _save_assignments(assignments: list[Assignment], path: Path) -> None:
    """Guarda las asignaciones en el orden en que se decidieron."""
    frame = pd.DataFrame(
        {
            "task_id": [a.task_id for a in assignments],
            "vm_id": [a.vm_id for a in assignments],
            "start": [a.start for a in assignments],
            "finish": [a.finish for a in assignments],
        }
    )
    frame.to_csv(path, index=False)


def build_summary(metrics_frame: pd.DataFrame) -> pd.DataFrame:
    """Resume cada (escenario, algoritmo): media, desviación, % de mejora y victorias.

    - La desviación es la muestral (ddof = 1).
    - El % de mejora compara medias: (FCFS − algoritmo) / FCFS × 100. Positivo = mejor que FCFS.
    - Una victoria es tener el menor valor de los tres en una semilla. Los empates (tolerancia
      1e-9) cuentan para todos los empatados, así que la suma puede superar 30.
    """
    keys = ["scenario", "algorithm"]
    grouped = metrics_frame.groupby(keys, sort=False)[list(SUMMARY_METRICS)]
    summary = grouped.agg(["mean", "std"])
    summary.columns = [f"{metric}_{stat}" for metric, stat in summary.columns]
    summary = summary.reset_index()

    for metric in COMPARED_METRICS:
        means = summary.set_index(keys)[f"{metric}_mean"]
        baseline = summary["scenario"].map(means.xs("FCFS", level="algorithm"))
        summary[f"{metric}_improvement_pct"] = (baseline - summary[f"{metric}_mean"]) / baseline * 100

        best = metrics_frame.groupby(["scenario", "seed"])[metric].transform("min")
        is_win = metrics_frame[metric] <= best + TOLERANCE
        wins = is_win.groupby([metrics_frame["scenario"], metrics_frame["algorithm"]]).sum()
        summary[f"{metric}_wins"] = [
            int(wins[(scenario, algorithm)])
            for scenario, algorithm in zip(summary["scenario"], summary["algorithm"])
        ]
    return summary


def build_wilcoxon(metrics_frame: pd.DataFrame) -> pd.DataFrame:
    """Aplica Wilcoxon pareado por escenario y reporta la diferencia media como tamaño de efecto.

    `mean_diff` es la media de (A − B): negativa significa que A obtuvo valores menores.
    """
    rows = []
    for scenario in metrics_frame["scenario"].unique():
        subset = metrics_frame[metrics_frame["scenario"] == scenario]
        for metric in COMPARED_METRICS:
            table = subset.pivot(index="seed", columns="algorithm", values=metric)
            for algorithm_a, algorithm_b in WILCOXON_PAIRS:
                a = table[algorithm_a].to_numpy()
                b = table[algorithm_b].to_numpy()
                diff = a - b
                # Wilcoxon no está definido si todas las diferencias son nulas.
                if np.all(np.abs(diff) <= TOLERANCE):
                    statistic, p_value = np.nan, 1.0
                else:
                    result = wilcoxon(a, b)
                    statistic, p_value = float(result.statistic), float(result.pvalue)
                rows.append(
                    {
                        "scenario": scenario,
                        "metric": metric,
                        "algorithm_a": algorithm_a,
                        "algorithm_b": algorithm_b,
                        "n": len(diff),
                        "mean_a": a.mean(),
                        "mean_b": b.mean(),
                        "mean_diff": diff.mean(),
                        "std_diff": diff.std(ddof=1),
                        "statistic": statistic,
                        "p_value": p_value,
                    }
                )
    return pd.DataFrame(rows)


def write_results(metrics_frame: pd.DataFrame, results_dir: Path) -> None:
    """Escribe metrics.csv, summary.csv y wilcoxon.csv."""
    metrics_frame.to_csv(results_dir / "metrics.csv", index=False)
    build_summary(metrics_frame).to_csv(results_dir / "summary.csv", index=False)
    build_wilcoxon(metrics_frame).to_csv(results_dir / "wilcoxon.csv", index=False)
