# Morris Sensitivity Analysis (SA) for Sugar Beet
### MONICA Agro-Ecosystem Model Integration
 
> An automated workflow to perform **Global Sensitivity Analysis** using the **Morris Method (Elementary Effects)**. This analysis quantifies the impact of crop parameters on **Yield**, **Irrigation**, and **Soil Moisture** under optimal growing conditions.
 
---
 
## Project Structure
 
| File | Type | Description |
|------|------|-------------|
| `sugarbeet_morris.py` | Core library for JSON mapping, parameter file updates, and MONICA output parsing |
| `morris_run_sb_sa.py`| The execution script. Automates the simulation loop for the Morris trajectories |
| `morris_sa_sugarbeet_optimal_condn.ipynb` | For Parameter Generation, Objective Function Calculation, and Statistical Analysis |
 
---
 
## The Workflow
 
The analysis is structured into **three distinct phases**:
 
---
 
### Phase 1 — Pre-Processing (Parameter Sampling)
 
**Module:** `morris_sa_sugarbeet_optimal_condn.ipynb`
 
- Defines the **"Problem"** — parameter names and their min/max ranges
- Uses the **SALib** library to generate an optimized Morris trajectory set
 
**Output:** `sugarbeet_morris.xlsx` — the input file for the simulation runner
 
---
 
### Phase 2 — Automated Simulation
 
**Module:** `morris_run_sb_sa.py`
 
**Steps executed automatically:**
 
1. Reads the parameter trajectories from `sugarbeet_morris.xlsx`
2. Dynamically updates MONICA `.json` files (Species, Cultivar, and Management)
3. Executes `monica-run.exe` for each parameter set
4. Extracts time-series data for soil moisture and yearly totals for yield and irrigation
 
**Output:** Consolidated `.txt` result files ready for post-processing
 
---
 
### Phase 3 — Post-Processing & Sensitivity Analysis
 
**Module:** `morris_sa_sugarbeet_optimal_condn.ipynb`
 
#### Objective Functions
Sensitivity is calculated not just on raw outputs, but on **error metrics** comparing simulation vs. observation:
 
| Metric | Description |
|--------|-------------|
| **RMSE** | Root Mean Square Error |
| **MAE** | Mean Absolute Error |
| **PBIAS** | Percent Bias |
 
#### Statistical Sensitivity Metrics
 
| Metric | Description |
|--------|-------------|
| **μ\*** (Mu Star) | Overall parameter importance and influence on output |
| **σ** (Sigma) | Parameter interactions or non-linear effects |
 
#### Visualizations
 
- **Covariance Plots** — Identify sensitive parameters based on Elementary Effects (EE)
- **Yearly SI Boxplots** — Analyse how parameter sensitivity fluctuates across growing seasons (2009–2020)
 
---

 
### Setting Up Paths
 
Configure the following variables in `morris_run_sb_sa.py` before running:
 
```python
monica_exe    = "path/to/monica-run.exe"   # Path to your MONICA binary
project_dir   = "path/to/project/"         # Working directory for simulation outputs
parameter_dir = "path/to/json/params/"     # Location of the base MONICA .json parameter files
```
 
---
 
## Output Interpretation
 
Use the Morris plots to classify parameters.
 


