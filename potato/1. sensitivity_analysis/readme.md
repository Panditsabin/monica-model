# Morris Sensitivity Analysis — Potato
### MONICA Agro-Ecosystem Model Integration
 
> An automated workflow to perform **Global Sensitivity Analysis** using the **Morris Method (Elementary Effects)**. This analysis quantifies the impact of crop parameters on **Yield**, **Irrigation**, and **Soil Moisture** under optimal growing conditions.
 
## Project Structure
 
| File | Description |
|------|-------------|
| `potato_morris_multiprocess.py` | Core library for JSON mapping, parameter file updates, MONICA runner, and output parsers |
| `moris_run_potato_multiprocess.py` | Execution script that runs parallel Morris simulations and saves consolidated results |
| `morris_sa_potato.ipynb` | Parameter generation, objective function calculation, statistical analysis and visualizations |
 
## The Workflow
 
The analysis is structured into **three phases**:
 
### Phase 1 — Pre-Processing (Parameter Sampling)
 
**Module:** `morris_sa_potato.ipynb`
 
- Defines the **"Problem"** — parameter names and their min/max ranges
- Uses **SALib** to generate an optimized Morris trajectory set
 
**Output:** `potato_morris.xlsx` — input sample file for the simulation runner
 
### Phase 2 — Automated Simulation
 
**Module:** `moris_run_potato_multiprocess.py`
 
Reads trajectories from `potato_morris.xlsx`, distributes simulations across `n_cores` parallel workers, and for each trajectory updates the MONICA `.json` parameter files, executes `monica-run.exe`, and extracts yield, irrigation and soil moisture outputs.
 
**Output:** Three consolidated `.txt` result files saved to `results_morris/`
 
### Phase 3 — Post-Processing & Sensitivity Analysis
 
**Module:** `morris_sa_potato.ipynb`
 
#### Objective Functions
 
| Metric | Description |
|--------|-------------|
| **RMSE** | Root Mean Square Error |
| **MAE** | Mean Absolute Error |
| **PBIAS** | Percent Bias |
 
#### Sensitivity Metrics
 
| Metric | Description |
|--------|-------------|
| **μ\*** | Overall parameter importance |
| **σ** | Parameter interactions and non-linear effects |
 
#### Visualizations
- **Covariance Plots** — parameter ranking based on Elementary Effects
- **Yearly SI Boxplots** — sensitivity fluctuation across growing seasons (2006–2015)
 
## Simulation Settings
 
| Setting | Value | Description |
|---------|-------|-------------|
| `sim_start` | 2006-01-01 | Start of simulation period |
| `sim_end` | 2015-12-31 | End of simulation period |
| `excluded_years` | [2016] | No-crop years excluded from results |
| `n_cores` | 15 | Parallel workers — adjust to available CPU cores |
 
## Setting Up Paths
 
All paths are configured at the top of `moris_run_potato_multiprocess.py`. Set `base_path` to your local MONICA root directory and all other paths resolve automatically relative to it.
 
## Outputs
 
All results are saved to `projects\potato_morris_sa_reduced\results_morris\`:
 
| File | Contents |
|------|----------|
| `potato_yld.txt` | Simulated yearly yield per trajectory |
| `potato_irr.txt` | Simulated yearly irrigation totals per trajectory |
| `potato_sm.txt` | Simulated soil moisture matched to observed measurement dates |
 
## Output Interpretation
 
Use the Morris plots to classify parameters into three groups:
 
- **High μ\*, low σ** — linearly influential; prioritize for calibration
- **High μ\*, high σ** — influential with non-linear effects or interactions
- **Low μ\*, low σ** — negligible influence; fix at default values
 
Parameters identified as influential are carried forward into the yield optimization and multi-objective calibration stages.
