# MONICA Model Calibration & Validation Framework
### Crop Yield, Soil Moisture and Irrigation Demand Simulation
 
> Scripts for MONICA agro-ecosystem model setup, Morris sensitivity analysis, single-objective yield calibration using a Genetic Algorithm, and multi-objective calibration of crop yield, soil moisture and irrigation demand using NSGA-II. Calibration is performed for three crops — **Potato**, **Sugar Beet**, and **Winter Wheat**.
 
## Repository Structure
 
```
monica-model/
│
├── sa_morris_def_parameters.xlsx          # Morris screening parameter definitions for all three crops
│
├── potato/
│   ├── 1. sensitivity_analysis/           # Morris SA
│   └── 2. optimization/
│       ├── yield_optimization/            # Single-objective GA calibration
│       └── multi_objective_optimization/  # NSGA-II three-objective calibration
│
├── sugarbeet/
│   ├── 1. sensitivity_analysis/
│   └── 2. optimization/
│       ├── yield_optimization/
│       └── multi_objective_optimization/
│
└── winterwheat/
    ├── 1. sensitivity_analysis/
    └── 2. optimization/
        ├── yield_optimization/
        └── multi_objective_optimization/
```
 
## Methodology
 
The calibration follows a systematic three-stage workflow applied consistently across all three crops:
 
**Stage 1 — Morris Sensitivity Analysis**
Global sensitivity screening using the Morris Elementary Effects method to identify the most influential crop parameters for yield, soil moisture and irrigation. Only parameters identified as sensitive are carried forward into calibration.
 
**Stage 2 — Single-Objective Yield Calibration**
A Genetic Algorithm minimizes yield RMSE under both optimal and reduced irrigation management conditions simultaneously, ensuring calibrated parameters are robust across water availability scenarios.
 
**Stage 3 — Multi-Objective Calibration (NSGA-II)**
NSGA-II simultaneously optimizes three objectives — yield RMSE, soil moisture RMSE, and irrigation RMSE — under both management conditions, producing a Pareto front of non-dominated solutions that represent trade-offs across the three targets.
 
## Morris Parameter Definitions
 
`sa_morris_def_parameters.xlsx` contains the parameter definitions used for Morris screening for all three crops, including parameter names, default values, and lower and upper bounds. Each crop has its own sheet.
 
### Vector Parameter Indexing
 
Several MONICA crop parameters are vectors with values defined per development stage (e.g. `StageKcFactor`, `SpecificLeafArea`, `StageTemperatureSum`). In all scripts, these vector parameters are indexed using **Python-based (zero-based) indexing**, where stage 0 corresponds to the first development stage. For example, `StageKcFactor 0` through `StageKcFactor 5` refer to the six development stages indexed from 0 to 5.
 
MONICA must be installed separately. See the [MONICA GitHub repository](https://github.com/zalf-rpm/monica) for installation instructions.
 
