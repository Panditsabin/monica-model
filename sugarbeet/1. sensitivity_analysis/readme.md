# Morris Sensitivity Analysis (SA) for Sugar Beet
### MONICA Agro-Ecosystem Model Integration
 
> An automated workflow to perform **Global Sensitivity Analysis** using the **Morris Method (Elementary Effects)**. This analysis quantifies the impact of crop parameters on **Yield**, **Irrigation**, and **Soil Moisture** under optimal growing conditions.
 
## Project Structure
 
| File | Description |
|------|-------------|
| `sugarbeet_morris_multiprocess.py` | Core library — JSON mapping, parameter file updates, MONICA runner, and output parsers for yield, irrigation and soil moisture |
| `morris_run_sb_sa.py` | Execution script — builds the task list, runs parallel Morris simulations across CPU cores, and saves consolidated results |
| `morris_sa_sugarbeet_optimal_condn.ipynb` | Parameter generation, objective function calculation, statistical sensitivity analysis and visualizations |
 
## The Workflow
 
The analysis is structured into **three phases**:
 
### Phase 1 — Pre-Processing (Parameter Sampling)
 
**Module:** `morris_sa_sugarbeet_optimal_condn.ipynb`
 
- Defines the **"Problem"** — parameter names and their min/max ranges
- Uses the **SALib** library to generate an optimized Morris trajectory set
 
**Output:** `sugarbeet_morris.xlsx` — the input sample file consumed by the simulation runner
 
### Phase 2 — Automated Simulation
 
**Module:** `morris_run_sb_sa.py`
 
**Steps executed automatically:**
 
1. Reads the parameter trajectories from `sugarbeet_morris.xlsx`
2. Builds one simulation task per Morris row and distributes them across `n_cores` parallel workers using `multiprocessing.Pool`
3. For each task, calls `sugarbeet_morris_multiprocess.py` to dynamically update MONICA `.json` files (Species, Cultivar, and Management)
4. Executes `monica-run.exe` for each parameter set
5. Extracts time-series soil moisture and yearly totals for yield and irrigation
6. Merges soil moisture results against observed measurement dates before saving
 
**Output:** Three consolidated `.txt` result files saved to `results_morris/`
 
### Phase 3 — Post-Processing & Sensitivity Analysis
 
**Module:** `morris_sa_sugarbeet_optimal_condn.ipynb`
 
#### Objective Functions
Sensitivity is calculated on **error metrics** comparing simulation vs. observation:
 
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
 
## Simulation Settings
 
| Setting | Value | Description |
|---------|-------|-------------|
| `sim_start` | 2009-01-01 | Start of simulation period |
| `sim_end` | 2015-12-31 | End of simulation period |
| `excluded_years` | [2017] | Years with no crop grown — excluded from result aggregation |
| `n_cores` | 15 | Parallel workers — adjust to your available CPU cores |
 
## Setting Up Paths
 
All paths are configured at the top of `morris_run_sb_sa.py`. Set `base_path` to your local MONICA root directory and the remaining paths resolve automatically:
 
```python
# --- Core Path ---
base_path = r'C:\Users\YourName\Desktop\monica'   # Root MONICA installation directory
 
# --- Management Data ---
irr_data_path  = os.path.join(base_path, r'management_data\sugarbeet_reduced\reduced_irrigation.xlsx')
fert_data_path = os.path.join(base_path, r'management_data\sugarbeet_reduced\fertilizer.xlsx')
crp_data_path  = os.path.join(base_path, r'management_data\sugarbeet_reduced\crop_mgmt_ZR.xlsx')
 
# --- MONICA Parameter Files ---
cultivar_file     = os.path.join(base_path, r'monica-parameters\crops\sugar-beet\sugarbeet.json')
species_file      = os.path.join(base_path, r'monica-parameters\crops\sugar-beet.json')
crop_general_file = os.path.join(base_path, r'monica-parameters\general\crop.json')
sim_file          = os.path.join(base_path, r'projects\calibration\sim.json')
 
# --- Observed Data ---
obs_moist_path = os.path.join(base_path, r'field_obs_data\sugarbeet_sm_red_condition.xlsx')
 
# --- Morris Sample File ---
morris_df = pd.read_excel(os.path.join(base_path, r'sa_analysis\sugarbeet_morris.xlsx'))
 
# --- Simulation Period ---
sim_start = '2009-01-01'
sim_end   = '2015-12-31'
 
# --- Parallelization ---
n_cores = 15   # Set based on your machine's available CPU cores
```
 
## Parallelization
 
Each Morris trajectory is an independent MONICA simulation. The script uses Python's `multiprocessing.Pool` to distribute tasks across `n_cores` workers simultaneously, reducing total runtime from hours to minutes on a multi-core machine. It is recommended to set `n_cores` to 1–2 fewer than your total available cores to keep the system responsive during long runs.
 
## Outputs
 
All results are saved to `projects\sugarbeet_morris_sa_reduced\results_morris\`:
 
| File | Contents |
|------|----------|
| `sugarbeet_yld.txt` | Simulated yearly yield for each Morris trajectory |
| `sugarbeet_irr.txt` | Simulated yearly irrigation totals per trajectory |
| `sugarbeet_sm.txt` | Simulated soil moisture matched to observed measurement dates |
 
## Output Interpretation
 
Use the Morris plots to classify parameters into three groups:
 
- **High μ\*, low σ** — linearly influential parameters; prioritize these for calibration
- **High μ\*, high σ** — influential but with strong interactions or non-linear effects
- **Low μ\*, low σ** — negligible influence; can be fixed at default values
 
Parameters identified as influential here are carried forward into the yield optimization and multi-objective calibration stages.
