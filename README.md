# AgroSim — Research Edition

An educational, lightweight Agent-Based Model (ABM) of a hypothetical sugarcane farm. AgroSim keeps an article-inspired baseline simulation and provides a separate research mode that adds a simplified soil-water balance.

> **Research integrity note:** Loam soil parameters are initial literature-informed assumptions. Research-mode rainfall, evaporation and root-water-demand defaults are controlled experimental inputs, not calibrated measurements for a real farm. Do not interpret the outputs as validated agronomic predictions.

## Features

- 30 × 30 farm grid with 899 sugarcane agents and one mill cell.
- Baseline mode with the original project growth, rainfall-probability, harvest and cashflow rules.
- Research mode with per-cell loam soil-water storage.
- Rainfall input, saturation-limited storage and drainage.
- Soil evaporation and root-water uptake.
- A simple water-stress factor that scales plant growth.
- CSV exports and graphs.
- Integrated checks for rainfall, drainage, evaporation and root uptake.

## Project structure

```text
AgroSim_Research_Edition/
├── agrosim.py
├── README.md
├── requirements.txt
├── RESEARCH_REPORT.md
├── PRESENTATION.pptx
└── outputs/
    ├── baseline/
    └── research/
```

The simulation logic is intentionally consolidated in `agrosim.py`. Generated CSVs and graphs are placed under `outputs/` when you run it.

## Requirements

- Python 3.10 or newer (the original development environment used Python 3.12)
- Mesa 3.5.2
- NumPy
- Pandas
- Matplotlib

Install:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use the Python executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run integrated checks

```powershell
python agrosim.py --check
```

Expected message:

```text
All integrated soil-water checks passed.
```

## Run the baseline

```powershell
python agrosim.py --mode baseline --ticks 3240 --seed 100
```

This mode is intended to preserve the article-inspired baseline rules. The simulation records model data before agent activation each tick, matching the collection order used in the project baseline.

## Run the research extension

```powershell
python agrosim.py --mode research --ticks 3240 --seed 100
```

Research-mode defaults are illustrative experimental controls:
- Synthetic rainfall: 5 mm every 12 ticks
- Soil evaporation demand: 0.01 mm per tick per cell
- Root-water demand: 0.02 mm per tick per cell
- Soil layer: 0.30 m

You can change these inputs:

```powershell
python agrosim.py --mode research --ticks 3240 --rainfall-mm 8 --rain-interval 24 --evaporation-mm 0.015 --root-demand-mm 0.025
```

These values are not locally calibrated. Change one parameter at a time and document each experiment.

## Soil-water model

For each field cell, the simplified balance is:

\[
S_{t+1} = S_t + I_t - E_t - U_t - D_t
\]

where:
- \(S\): soil-water storage (mm)
- \(I\): rainfall added to the soil (mm)
- \(E\): soil evaporation (mm)
- \(U\): root-water uptake (mm)
- \(D\): drainage above the saturation storage limit (mm)

For a 0.30 m layer, volumetric water content is converted to water depth using:

\[
W\;(\mathrm{mm}) = \theta \times 0.30 \times 1000
\]

Initial parameter set:

| Parameter | Value |
|---|---:|
| Soil type | Loam |
| Saturation water content | 0.47 m³/m³ |
| Field capacity | 0.27 m³/m³ |
| Wilting point | 0.12 m³/m³ |
| Plant-available water content | 0.15 m³/m³ |
| Layer depth | 0.30 m |
| Water at field capacity | 81 mm |
| Water at wilting point | 36 mm |
| Plant-available water in layer | 45 mm |
| Saturation storage | 141 mm |

These are generic starting values, not site-specific soil test results.

## Outputs

After each run, see `outputs/baseline/` or `outputs/research/`:
- `model_results.csv`
- `agent_results.csv`
- `cashflow.png`
- `harvesting.png`
- Research mode also produces `soil_moisture.png` and `soil_water_distribution.png`.

The last recorded row is collected before agents act on that tick. Therefore it may differ slightly from the final state printed in the terminal. This is deliberate and documented.

## Scientific limitations

1. The model uses a single uniform 0.30 m soil layer per field cell; it does not yet represent layered soil profiles or dynamic root depth.
2. Rainfall is synthetic and periodic in research mode, not observed weather data.
3. Evaporation and root uptake are controlled input rates, not calculated from meteorological conditions or calibrated crop coefficients.
4. Water stress is a simple linear function between wilting point and field capacity.
5. Plant hormones (including abscisic acid), stomatal conductance, nutrient cycling, soil organic matter, pests and irrigation scheduling are not yet mechanistically represented.
6. The original baseline is a simplified hypothetical model and should not be treated as a farm forecast.

## Suggested research roadmap

1. Replace generic soil values with measured soil data from a clearly identified site.
2. Add observed daily rainfall and meteorological data, then choose and document the time-step conversion.
3. Add root depth and multiple soil layers.
4. Calibrate crop water demand and growth response against published or field observations.
5. Add ABA-mediated drought response and stomatal regulation only with defensible equations and parameters.
6. Add nutrient and soil-health processes, then validate against independent observations.

## GitHub publishing

1. Create a new public repository named `AgroSim`.
2. Extract this project ZIP.
3. Open the extracted folder in VS Code.
4. Run the integrated checks and at least one baseline and research simulation.
5. Review generated outputs and update the report with your actual run results.
6. Initialize Git and push:

```powershell
git init
git add .
git commit -m "Add integrated AgroSim research edition"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/AgroSim.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username. Do not upload virtual environments (`.venv/`) or unnecessary large files.
