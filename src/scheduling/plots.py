"""Figuras del laboratorio a partir de los archivos de results/. Etiquetas en español."""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from scheduling.datasets import SCENARIOS, make_vms
from scheduling.experiment import make_schedulers

DPI = 200
ALGORITHM_COLORS = {"FCFS": "#2a78d6", "Min-Min": "#eb6834", "Max-Min": "#1baf7a"}
SCENARIO_TITLES = {"mixed": "Escenario mixed", "skewed": "Escenario skewed"}
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
STYLE = {
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": INK_SECONDARY,
    "axes.titlecolor": INK,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.axisbelow": True,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "xtick.color": INK_SECONDARY,
    "ytick.color": INK_SECONDARY,
    "xtick.bottom": False,
    "legend.frameon": False,
    "text.color": INK,
}


def _algorithms() -> list[str]:
    return [scheduler.name for scheduler in make_schedulers()]


def _algorithm_handles() -> list[Patch]:
    return [Patch(color=ALGORITHM_COLORS[name], label=name) for name in _algorithms()]


@mpl.rc_context(STYLE)
def plot_makespan_wait_bars(metrics_frame: pd.DataFrame) -> Figure:
    """Barras con desviación estándar de makespan y espera promedio, por escenario."""
    panels = (("makespan", "Makespan (s)"), ("avg_wait", "Espera promedio (s)"))
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), layout="constrained")
    fig.suptitle("Makespan y espera promedio (media ± desv. estándar, 30 semillas)")
    algorithms = _algorithms()

    for col, scenario in enumerate(SCENARIOS):
        subset = metrics_frame[metrics_frame["scenario"] == scenario]
        for row, (metric, label) in enumerate(panels):
            ax = axes[row][col]
            stats = subset.groupby("algorithm")[metric].agg(["mean", "std"]).loc[algorithms]
            ax.bar(
                algorithms,
                stats["mean"],
                yerr=stats["std"],
                width=0.55,
                color=[ALGORITHM_COLORS[name] for name in algorithms],
                error_kw={"ecolor": INK_SECONDARY, "elinewidth": 1, "capsize": 4},
            )
            top = (stats["mean"] + stats["std"]).max()
            for i, name in enumerate(algorithms):
                ax.text(
                    i,
                    stats.loc[name, "mean"] + stats.loc[name, "std"] + top * 0.02,
                    f"{stats.loc[name, 'mean']:.1f}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )
            ax.set_ylim(0, top * 1.14)
            ax.set_ylabel(label)
            ax.set_title(SCENARIO_TITLES[scenario])
            if metric == "makespan":
                ax.axhline(subset["lower_bound"].mean(), color=INK, linestyle=":", linewidth=1.5)

    handles = _algorithm_handles() + [
        Line2D([], [], color=INK, linestyle=":", linewidth=1.5, label="Cota inferior (media)")
    ]
    fig.legend(handles=handles, loc="outside lower center", ncols=4)
    return fig


@mpl.rc_context(STYLE)
def plot_gantt(assignments: dict[str, pd.DataFrame], scenario: str) -> Figure:
    """Gantt de la semilla 0: un panel por algoritmo, mismo eje X, una fila por VM."""
    vms = make_vms()
    algorithms = _algorithms()
    fig, axes = plt.subplots(len(algorithms), 1, figsize=(11, 8), sharex=True, layout="constrained")
    fig.suptitle(f"Diagrama de Gantt, semilla 0 ({SCENARIO_TITLES[scenario]})")

    for ax, name in zip(axes, algorithms):
        frame = assignments[name]
        for row, vm in enumerate(vms):
            tasks = frame[frame["vm_id"] == vm.id]
            ax.broken_barh(
                list(zip(tasks["start"], tasks["finish"] - tasks["start"])),
                (row - 0.36, 0.72),
                facecolors=ALGORITHM_COLORS[name],
                edgecolors=SURFACE,
                linewidth=0.7,
            )
        span = frame["finish"].max()
        ax.axvline(span, color=INK, linewidth=1)
        ax.set_title(f"{name}: makespan = {span:.1f} s", loc="left")
        ax.set_yticks(range(len(vms)), [f"VM{vm.id} ({vm.mips} MIPS)" for vm in vms])
        ax.set_ylim(len(vms) - 0.5, -0.5)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", visible=True)
    axes[-1].set_xlabel("Tiempo (s)")
    axes[-1].set_xlim(left=0)
    return fig


@mpl.rc_context(STYLE)
def plot_vm_utilization(metrics_frame: pd.DataFrame) -> Figure:
    """Utilización media de cada VM por algoritmo y escenario."""
    vms = make_vms()
    algorithms = _algorithms()
    columns = [f"util_vm{j}" for j in range(len(vms))]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True, layout="constrained")
    fig.suptitle("Utilización media por VM (30 semillas)")
    width = 0.27

    for ax, scenario in zip(axes, SCENARIOS):
        subset = metrics_frame[metrics_frame["scenario"] == scenario]
        means = subset.groupby("algorithm")[columns].mean().loc[algorithms]
        for i, name in enumerate(algorithms):
            positions = [j + (i - 1) * width for j in range(len(vms))]
            ax.bar(
                positions,
                means.loc[name] * 100,
                width=width,
                color=ALGORITHM_COLORS[name],
                edgecolor=SURFACE,
                linewidth=1.2,
            )
        ax.set_xticks(range(len(vms)), [f"VM{vm.id}\n{vm.mips} MIPS" for vm in vms])
        ax.set_ylim(0, 105)
        ax.set_title(SCENARIO_TITLES[scenario])
    axes[0].set_ylabel("Utilización (%)")
    fig.legend(handles=_algorithm_handles(), loc="outside lower center", ncols=3)
    return fig


@mpl.rc_context(STYLE)
def plot_makespan_boxplot(metrics_frame: pd.DataFrame) -> Figure:
    """Distribución del makespan en las 30 semillas; cada escenario con su propia escala."""
    algorithms = _algorithms()
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), layout="constrained")
    fig.suptitle("Distribución del makespan en las 30 semillas")

    for ax, scenario in zip(axes, SCENARIOS):
        subset = metrics_frame[metrics_frame["scenario"] == scenario]
        groups = [subset.loc[subset["algorithm"] == name, "makespan"] for name in algorithms]
        boxes = ax.boxplot(
            groups,
            tick_labels=algorithms,
            widths=0.5,
            patch_artist=True,
            medianprops={"color": INK, "linewidth": 1.5},
        )
        for i, name in enumerate(algorithms):
            color = ALGORITHM_COLORS[name]
            boxes["boxes"][i].set(facecolor=color, edgecolor=color, alpha=0.75)
            for line in boxes["whiskers"][2 * i : 2 * i + 2] + boxes["caps"][2 * i : 2 * i + 2]:
                line.set(color=color, linewidth=1.2)
            boxes["fliers"][i].set(
                marker="o", markersize=4, markerfacecolor=color, markeredgecolor=SURFACE
            )
        ax.set_ylabel("Makespan (s)")
        ax.set_ylim(bottom=0)
        ax.set_title(SCENARIO_TITLES[scenario])
    fig.legend(handles=_algorithm_handles(), loc="outside lower center", ncols=3)
    return fig


def load_gantt_assignments(results_dir: Path, scenario: str) -> dict[str, pd.DataFrame]:
    """Lee las asignaciones de la semilla 0 de un escenario, por nombre de algoritmo."""
    return {
        scheduler.name: pd.read_csv(results_dir / f"assignments_{scenario}_{scheduler.slug}.csv")
        for scheduler in make_schedulers()
    }


def generate_figures(results_dir: Path, figures_dir: Path) -> None:
    """Genera todas las figuras en PNG a 200 dpi."""
    metrics_frame = pd.read_csv(results_dir / "metrics.csv")
    figures = {
        "barras_makespan_espera.png": plot_makespan_wait_bars(metrics_frame),
        "utilizacion_vms.png": plot_vm_utilization(metrics_frame),
        "boxplot_makespan.png": plot_makespan_boxplot(metrics_frame),
    }
    for scenario in SCENARIOS:
        assignments = load_gantt_assignments(results_dir, scenario)
        figures[f"gantt_{scenario}.png"] = plot_gantt(assignments, scenario)
    for filename, fig in figures.items():
        fig.savefig(figures_dir / filename, dpi=DPI)
        plt.close(fig)
