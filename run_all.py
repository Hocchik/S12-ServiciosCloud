"""Genera data/, results/ y figures/ con un solo comando: python run_all.py"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from scheduling.experiment import run_experiments, write_results  # noqa: E402
from scheduling.plots import generate_figures  # noqa: E402


def main() -> None:
    data_dir = ROOT / "data"
    results_dir = ROOT / "results"
    figures_dir = ROOT / "figures"
    for directory in (data_dir, results_dir, figures_dir):
        directory.mkdir(exist_ok=True)

    metrics_frame = run_experiments(data_dir, results_dir)
    write_results(metrics_frame, results_dir)
    print(f"Resultados: {len(metrics_frame)} filas en {results_dir / 'metrics.csv'}")

    generate_figures(results_dir, figures_dir)
    print(f"Figuras en {figures_dir}")


if __name__ == "__main__":
    main()
