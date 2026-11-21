# AgroSim Research Report

## Title
**AgroSim: An Agent-Based Sugarcane Farm Simulation with a Simplified Soil-Water Balance**

## Abstract
AgroSim is an educational agent-based simulation of a hypothetical sugarcane farm. The project preserves an article-inspired baseline model and introduces a separate research mode that represents soil-water storage at each field cell. The extension includes synthetic rainfall input, saturation-limited storage, drainage, soil evaporation, root-water uptake and a simplified water-stress response affecting plant growth. The current implementation is a prototype for experimentation and software development; it is not a calibrated or validated crop model.

## 1. Objectives
- Represent a sugarcane farm as spatially distributed agents.
- Preserve a reproducible baseline for comparison.
- Add a transparent soil-water balance at field-cell level.
- Test water storage, drainage, evaporation and root uptake.
- Create an extensible foundation for future crop and soil research.

## 2. Model structure
The farm is represented by a 30 × 30 grid. The mill occupies one cell, leaving 899 sugarcane agents. Each agent represents one field cell and carries plant state (height and sugar content). In research mode, each agent also carries a soil-water state for a 0.30 m soil layer.

The simulation uses Mesa. Model and agent records are exported to CSV, and selected indicators are plotted with Matplotlib.

## 3. Baseline model
The baseline initializes sugar content uniformly between 0 and 0.112 and height between 0 and 2 m. Rainfall is represented as a random draw compared with a rainfall probability of 0.3. On a rainy tick, the model applies twice the dry-tick increments to height and sugar content. Dry ticks incur a cashflow cost per agent. The model selects a high-price patch for harvesting subject to the minimum-height threshold and per-tick harvesting capacity.

The baseline is a simplified hypothetical representation. Its equations and assumptions should be interpreted in the context of the source article and the code, not as a complete agronomic model.

## 4. Soil parameters and water-depth conversion
The research prototype starts with generic loam values:

| Parameter | Value |
|---|---:|
| Saturation water content | 0.47 m³/m³ |
| Field capacity | 0.27 m³/m³ |
| Wilting point | 0.12 m³/m³ |
| Soil depth | 0.30 m |
| Initial moisture | 0.27 m³/m³ |

Water depth is calculated as:

\[
W = \theta \times z \times 1000
\]

where \(W\) is water depth in mm, \(\theta\) is volumetric water content in m³/m³, and \(z\) is soil depth in metres.

For a 0.30 m layer:
- Field-capacity storage = 0.27 × 0.30 × 1000 = 81 mm.
- Wilting-point storage = 0.12 × 0.30 × 1000 = 36 mm.
- Plant-available water = 81 − 36 = 45 mm.
- Saturation storage = 0.47 × 0.30 × 1000 = 141 mm.

These values are generic literature-informed starting assumptions. They are not measurements from a specific farm.

## 5. Water-balance formulation
The simplified cell-level balance is:

\[
S_{t+1} = S_t + I_t - E_t - U_t - D_t
\]

where:
- \(S_t\): soil-water storage at the beginning of the step (mm)
- \(I_t\): rainfall added during the step (mm)
- \(E_t\): actual soil evaporation (mm)
- \(U_t\): actual root-water uptake (mm)
- \(D_t\): drainage when storage exceeds saturation (mm)

The implementation constrains drainage so storage does not exceed saturation, evaporation so storage cannot become negative, and root uptake so storage does not fall below the wilting-point threshold.

## 6. Plant-water stress
A deliberately simple stress factor is calculated between wilting point and field capacity:

\[
f_w = \max\left(0,\min\left(1,\frac{S-S_{WP}}{S_{FC}-S_{WP}}\right)\right)
\]

where \(S_{WP}\) is storage at wilting point and \(S_{FC}\) is storage at field capacity. The factor scales the baseline plant growth increments in research mode. This linear function is a prototype assumption and is not a validated sugarcane response function.

## 7. Experimental inputs
The research-mode defaults are controlled synthetic inputs:
- 5 mm rainfall pulse every 12 simulation ticks.
- 0.01 mm soil evaporation demand per tick per cell.
- 0.02 mm root-water demand per tick per cell.

They are selected to make the water-balance mechanisms testable, not to represent observed local weather or crop water use. The program exposes command-line options so users can vary them systematically.

## 8. Software verification
The integrated `--check` option verifies:
- Rainfall addition and drainage at saturation.
- Evaporation limited by stored water.
- Root uptake limited by water above wilting point.
- Rejection of negative rainfall, evaporation and root uptake.

These checks verify software rules. They do not validate the model against field observations.

## 9. Outputs and interpretation
The program writes model-level and agent-level CSV files and plots cashflow, cumulative harvest, average soil moisture and soil-water distribution. Data collection occurs before agent activation on each tick to preserve the baseline collection order. Consequently, the final recorded CSV row can differ from the terminal's post-step final state.

Before publishing scientific conclusions, run the model, retain the actual output files, report the exact parameters and seed, and compare outputs across controlled scenarios. Do not report expected or illustrative values as measured findings.

## 10. Limitations
- Single 0.30 m soil layer; no dynamic root profile.
- Synthetic rainfall; no historical weather input.
- Evaporation and root demand are fixed user inputs.
- Simplified linear water-stress response.
- No explicit ABA/hormone, stomatal, nutrient, organic-matter, pest or irrigation-control model.
- No site-specific calibration or independent validation.

## 11. Future work
1. Collect soil texture, field capacity, wilting point and bulk-density data for a named study site.
2. Use observed rainfall and meteorological data with documented units and time-step conversion.
3. Add multiple soil layers and root-depth dynamics.
4. Parameterize transpiration and crop response from published sugarcane studies.
5. Introduce plant-hormone mechanisms only when equations and parameters are supported by evidence.
6. Add soil organic matter and nutrient cycling.
7. Calibrate and validate against independent field observations.

## 12. Conclusion
AgroSim Research Edition provides a compact, transparent software foundation for exploring interactions between sugarcane agents and soil water. Its primary contribution at this stage is an extensible, testable prototype. Further parameterization, calibration and validation are required before drawing real-world agricultural conclusions.
