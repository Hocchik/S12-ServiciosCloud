# CLAUDE.md — Laboratorio Semana 12: Planificación (Scheduling) en Cloud Computing

## Contexto
Laboratorio del curso Cloud Computing (Ingeniería de Software, UTP). La guía pide:
simular y comparar **FCFS vs. Min-Min** con **50 tareas** de distintos tamaños y **5 VMs**
de distintas capacidades, medir **makespan** y **tiempo de espera**, graficar y responder:
1. ¿Cuál algoritmo terminó antes?
2. ¿Cuál aprovechó mejor la CPU?

Este repo implementa ese laboratorio y añade **Max-Min** como contraste, dos escenarios de
carga, 30 semillas y una validación con un caso hecho a mano. El informe final se escribe
aparte. Este repo produce los números, las tablas y las figuras para ese informe.

## Alcance (NO ampliar sin que el usuario lo pida)
- SÍ: FCFS (cíclico), Min-Min y Max-Min. Escenarios `mixed` y `skewed`. 30 semillas.
  Métricas, tests, CSV, figuras, notebook y README.
- NO: CloudSim, algoritmos genéticos o PSO, dashboards (Streamlit), llegadas dinámicas o
  Poisson, modelos de costo o energía, Round Robin con quantum. Si parece útil agregar algo,
  pregúntalo antes.

## Stack
- Python 3.11+, `numpy`, `pandas`, `matplotlib`, `scipy` (solo Wilcoxon), `pytest`, `jupyter`.
- Versiones fijadas en `requirements.txt`. Nada de dependencias extra sin preguntar.

## Estructura esperada
```
cloud-scheduling-sim/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── run_all.py                  # un solo comando: genera datos, corre experimentos, métricas y figuras
├── src/scheduling/
│   ├── models.py               # dataclasses Task(id, mi, arrival=0), VM(id, mips), Assignment(task_id, vm_id, start, finish)
│   ├── datasets.py             # generación de tareas por escenario + VMs fijas
│   ├── schedulers.py           # interfaz Scheduler + FCFS, MinMin, MaxMin
│   ├── metrics.py              # funciones puras sobre una lista de Assignment
│   └── experiment.py           # bucle escenarios × semillas × algoritmos → results/metrics.csv
├── tests/
│   ├── test_hand_case.py       # caso 4 tareas × 2 VMs con valores exactos (ver abajo)
│   └── test_invariants.py      # invariantes sobre datasets aleatorios
├── data/                       # tasks_<escenario>_seed<N>.csv, vms.csv
├── results/                    # metrics.csv, assignments_*.csv, summary.csv, wilcoxon.csv
├── figures/                    # PNG a 200 dpi, etiquetas en español
└── notebooks/analysis.ipynb    # lee results/ y reproduce tablas y figuras
```

## Modelo (definiciones fijas, no cambiarlas)
- **Tarea:** longitud en MI (millones de instrucciones). `arrival = 0` para todas (planificación estática por lotes).
- **VM:** capacidad en MIPS. Son fijas en todos los experimentos: `[500, 1000, 1500, 2000, 2500]`.
- **ETC[i][j] = MI_i / MIPS_j** (segundos).
- Cada VM ejecuta **una tarea a la vez**, sin expropiación, en el orden en que se le asignan
  (space-shared). `start = ready[vm]`, `finish = start + ETC`.
- **Orden de llegada** = orden del índice de la tarea en el dataset. El dataset se baraja al generarse.

## Algoritmos
Todos implementan `Scheduler.schedule(tasks, vms) -> list[Assignment]`.

- **FCFS (cíclico):** recorre las tareas en orden de llegada y asigna la tarea *i* a la VM `i % n_vms`.
  No mira la velocidad de la VM. Es el comportamiento del broker por defecto de CloudSim.
  ⚠️ NO implementarlo como "la VM que se libera primero": eso es OLB, un balanceador greedy,
  e inflaría el baseline.
- **Min-Min:** mientras queden tareas pendientes:
  1. Para cada una calcula su tiempo de finalización mínimo `CT = ready[j] + ETC[i][j]` y la VM que lo da.
  2. Elige la tarea con el **menor** de esos mínimos.
  3. La asigna a esa VM y actualiza `ready[j]`.
- **Max-Min:** igual que Min-Min, pero en el paso 2 elige la tarea con el **mayor** de esos mínimos
  y la asigna a la VM que le da su mínimo.

### Reglas de desempate (deterministas, obligatorias)
- Comparar tiempos con tolerancia `1e-9` (redondear a 9 decimales o usar `math.isclose`).
- Si dos VMs dan el mismo CT para una tarea, gana la **VM de menor índice**.
- Si dos tareas empatan en Min-Min o Max-Min, gana la **tarea de menor índice**.

## Escenarios de carga (50 tareas cada uno, `numpy.random.default_rng(seed)`)
- `mixed`: MI ~ Uniforme(1000, 20000). Es el escenario de la guía.
- `skewed`: 45 tareas ~ U(1000, 3000) + 5 tareas ~ U(15000, 20000), barajadas.
- Semillas `0..29`. Para cada escenario y semilla, los **tres algoritmos usan el mismo dataset**
  (diseño pareado).

## Métricas (en `metrics.py`, funciones puras)
- `makespan = max(finish)`
- `lower_bound = max(ΣMI / ΣMIPS, max(MI) / max(MIPS))`. Se reporta también `makespan / lower_bound`.
- `wait_i = start_i − arrival_i`. Se reportan `avg_wait` y `max_wait`.
  (Con `arrival = 0`, la espera es igual al instante de inicio. Documentarlo, no es un bug.)
- `turnaround_i = finish_i − arrival_i`. Se reporta `avg_turnaround`.
- `busy_j` = suma de los ETC de las tareas asignadas a la VM *j*.
- `util_j = busy_j / makespan` (utilización por VM), `ARUR = mean(util_j)`.
- `DI = (max(busy) − min(busy)) / mean(busy)` (grado de desbalance; menor es mejor).

## Experimentos y salidas
- `results/metrics.csv`: una fila por (escenario, semilla, algoritmo) con todas las métricas y `util_vm0..util_vm4`.
- `results/summary.csv`: media ± desviación por (escenario, algoritmo). Incluye el **% de mejora vs FCFS**
  y el **conteo de victorias** en makespan y en espera promedio.
- `results/wilcoxon.csv`: Wilcoxon pareado (`scipy.stats.wilcoxon`) Min-Min vs Max-Min y Min-Min vs FCFS,
  en makespan y avg_wait, por escenario. Reportar también la diferencia media (tamaño de efecto),
  no solo el p-valor.
- Guardar las asignaciones de la **semilla 0** (`assignments_<escenario>_<algoritmo>.csv`) para los Gantt.

## Figuras (`figures/`, matplotlib, etiquetas y títulos en español)
1. `barras_makespan_espera.png`: barras con error (desv. estándar) de makespan y espera promedio, por algoritmo y escenario. Línea punteada en la cota inferior.
2. `gantt_<escenario>.png`: un Gantt por algoritmo (semilla 0), mismo eje X para poder comparar, una fila por VM.
3. `utilizacion_vms.png`: utilización media por VM y algoritmo.
4. `boxplot_makespan.png`: distribución del makespan en las 30 semillas.
Colores consistentes por algoritmo en todas las figuras.

## Test obligatorio: caso a mano (`tests/test_hand_case.py`)
Tareas MI = `[4000, 1000, 3000, 2000]` (T0..T3), VMs MIPS = `[1000, 2000]` (VM0, VM1).
Valores esperados (verificados a mano, comparar con `pytest.approx`):

| Algoritmo | Asignación (tarea→VM: inicio–fin) | Makespan | Espera prom. | Espera máx. | DI |
|---|---|---|---|---|---|
| FCFS | T0→VM0 0–4, T1→VM1 0–0.5, T2→VM0 4–7, T3→VM1 0.5–1.5 | 7.0 | 1.125 | 4.0 | 1.2941 |
| Min-Min | T1→VM1 0–0.5, T3→VM1 0.5–1.5, T2→VM0 0–3, T0→VM1 1.5–3.5 | 3.5 | 0.5 | 1.5 | 0.1538 |
| Max-Min | T0→VM1 0–2, T2→VM0 0–3, T3→VM1 2–3, T1→VM1 3–3.5 | 3.5 | 1.25 | 3.0 | 0.1538 |

Cota inferior = 3.3333. El paso 3 de Min-Min tiene un **empate**: T2 da CT = 3.0 en VM0 y en VM1,
y gana VM0 por la regla de desempate. Si el test falla ahí, la regla está mal implementada.

## Invariantes (`tests/test_invariants.py`, varios datasets aleatorios)
- Cada tarea se asigna exactamente una vez.
- No hay solapamientos dentro de una VM, y `finish − start == ETC`.
- `makespan >= lower_bound − 1e-9` para todos los algoritmos.
- `0 <= util_j <= 1`.
- Resultados idénticos al repetir la misma semilla (determinismo).

## Comandos
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q                 # debe pasar antes de correr experimentos
python run_all.py         # genera data/, results/ y figures/
```

## Convenciones
- Identificadores en inglés. Docstrings, comentarios, README y figuras en **español**.
- Sin variables globales. La semilla siempre se pasa explícitamente.
- No inventes conclusiones: el README y el notebook reportan **lo que digan los datos**.
  Hipótesis a contrastar, no a confirmar: Min-Min suele dar menor espera promedio, Max-Min suele
  dar menor makespan y mejor balance (sobre todo en `skewed`), y FCFS cíclico sufre por ignorar la
  velocidad de las VMs.
- Antes de dar por terminada una tarea: `pytest -q` en verde y `python run_all.py` sin errores.
