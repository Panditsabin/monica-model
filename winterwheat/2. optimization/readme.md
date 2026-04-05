# Optimization — Winter Wheat
### MONICA Agro-Ecosystem Model Calibration
 
> Two-stage optimization workflow calibrating MONICA crop parameters against field observations under both **optimal** and **reduced** irrigation management conditions.
 
## Management Conditions
 
Calibration is performed simultaneously under two irrigation scenarios to ensure parameters are robust across water availability conditions:
 
| Condition | Description |
|-----------|-------------|
| **Optimal (`opt`)** | Full irrigation — no water stress |
| **Reduced (`red`)** | Deficit irrigation — water-limited conditions |
 
## Yield Optimization
 
Single-objective calibration minimizing yield RMSE across both management conditions combined.
 
### File Descriptions
 
| File | Description |
|------|-------------|
| `1. monica_run_ww.py` | Core library — parameter mapping, JSON file updates, MONICA runner and objective function |
| `2. optimization_run_ww.py` | Defines the GA problem and runs the single-objective optimization loop |
| `3. post_process_ww.py` | Objective and parameter convergence analysis across generations |
| `4. monica_run_postprocess_ww.py` | Runs MONICA with the best calibrated parameters for both conditions over the full simulation period |
| `5. yield_optimization_result.py` | Simulated vs. observed yield plots for both conditions with RMSE |
 
### Simulation Settings
 
| Setting | Value |
|---------|-------|
| `sim_start` (calibration) | 2007-09-01 |
| `sim_end` (calibration) | 2018-12-31 |
| `sim_end` (full period) | 2020-12-31 |
| `excluded_years` | [2012] |
 
## Multi-Objective Optimization
 
Simultaneous calibration against three objectives using NSGA-II.
 
### Objectives
 
| Objective | Variable |
|-----------|----------|
| f₁ | Yield RMSE |
| f₂ | Soil Moisture RMSE |
| f₃ | Irrigation RMSE |
 
### File Descriptions
 
| File | Description |
|------|-------------|
| `1. monica_run_ww.py` | Core library — parameter mapping, JSON file updates, MONICA runner and three-objective function |
| `2. optimization_run_ww.py` | Defines the NSGA-II problem class with 3 objectives and runs the optimization |
| `3. post_process_ww.py` | Pareto front visualization, hypervolume, running metric and parameter convergence |
| `4. monica_run_postprocess_ww.py` | Runs MONICA for a given Pareto solution under both conditions over the full simulation period |
| `5. pareto_ensemble_ww.py` | Runs all Pareto-optimal solutions through MONICA and plots the ensemble spread (10–90% band) of yield and irrigation against observations |
 
### NSGA-II Settings
 
| Setting | Value |
|---------|-------|
| Population size | 150 |
| Generations | 30 |
| Sampling | Latin Hypercube Sampling |
| `sim_start` (calibration) | 2007-09-01 |
| `sim_end` (calibration) | 2018-12-31 |
| `sim_end` (full period) | 2020-12-31 |
| `excluded_years` | [2012] |
 
## Setting Up Paths
 
Set `base_path` to your local MONICA root directory and all other paths resolve automatically relative to it.
 
## Outputs
 
| File | Contents |
|------|----------|
| `optimization_result_set{i}.pkl` | Full optimization result object including history |
| `optimized_variables_set{i}.npy` | Decision variable values for Pareto front solutions |
| `objective_values_set{i}.npy` | Objective function values for Pareto front solutions |
