# -*- coding: utf-8 -*-
"""
Created on Wed Aug 20 14:53:28 2025

@author: Pandit
"""

from monica_run_sb import (
    map_parameters, update_parameter_files, site_json, crop_json, run_monica, process_yield_file, simulated_yield_data,
    calculate_objective)

# Libraries import from post_process.py
from post_process_sb import(variable_convergance, converg)
    

import os
import json
import uuid
import pandas as pd
import numpy as np
import subprocess
import re
import sys
import time
from multiprocessing import Pool
import dill as pickle

from pymoo.operators.sampling.lhs import LHS
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.termination import get_termination
from pymoo.optimize import minimize
from pymoo.core.problem import Problem
from pymoo.algorithms.soo.nonconvex.ga import GA 

# 1. worker func
def run_simulation_worker(base_path, x_params, param_names, project_dir_opt, project_dir_red, 
                          parameter_dir, cultivar_file, species_file, crop_general_file, 
                          sim_file, 
                          irr_data_path_opt, fert_data_path_opt, crp_data_path_opt, 
                          irr_data_path_red, fert_data_path_red, crp_data_path_red, 
                          obs_yield_path_opt, obs_yield_path_red, 
                          sheet_name, sim_start, sim_end, i):
    
    # set name
    set_name = f"set_{uuid.uuid4().hex[:10]}"
    
    try:
       
        param_update = map_parameters(x_params, param_names, set_name)
        
        
        update_parameter_files(base_path, param_update, parameter_dir, project_dir_opt, 
                               cultivar_file, species_file, crop_general_file, 
                               sim_file, sim_start, sim_end, i)
        
        update_parameter_files(base_path, param_update, parameter_dir, project_dir_red, 
                               cultivar_file, species_file, crop_general_file, 
                               sim_file, sim_start, sim_end, i)
        
        
        # optimal condn management file
        crop_json(base_path, irr_data_path_opt, fert_data_path_opt, crp_data_path_opt, sim_start, sim_end, 
                  project_dir_opt, parameter_dir, set_name, i)
        site_json(base_path, project_dir_opt, set_name, i)
        
        # reduced condn management file
        crop_json(base_path, irr_data_path_red, fert_data_path_red, crp_data_path_red, sim_start, sim_end, 
                  project_dir_red, parameter_dir, set_name, i)
        site_json(base_path, project_dir_red, set_name, i)
            
        # monica run for opt and red condition
        run_monica(base_path, project_dir_opt, set_name, i)
        run_monica(base_path, project_dir_red, set_name, i)

        # objective
        combined_rmse = calculate_objective(
            set_name = set_name, 
            project_dir_opt = project_dir_opt, 
            project_dir_red = project_dir_red, 
            obs_yield_path_opt = obs_yield_path_opt, 
            obs_yield_path_red = obs_yield_path_red, 
            sheet_name = sheet_name, 
            i=i
        )
        
        return combined_rmse

    except Exception as e:
        print(f"Worker Error in run {i} for {set_name}: {e}")
        return 1e6

# 2. problem defn
class MonicaSingleObjectiveProblem(Problem):
    def __init__(self, base_path, n_cores, parameter_dir, project_dir_opt, project_dir_red, para_df_x, 
                 cultivar_file, species_file, crop_general_file, sim_file, 
                 irr_data_path_opt, fert_data_path_opt, crp_data_path_opt, obs_yield_path_opt,
                 irr_data_path_red, fert_data_path_red, crp_data_path_red, obs_yield_path_red,
                 sheet_name, sim_start, sim_end, i):
        
        self.base_path = base_path
        
        self.n_cores = n_cores
        self.parameter_dir = parameter_dir
        self.project_dir_opt = project_dir_opt
        self.project_dir_red = project_dir_red
        self.para_df_x = para_df_x
        self.param_names = para_df_x["parameter_name"].str.strip().tolist()
        
        self.cultivar_file = cultivar_file      
        self.species_file = species_file        
        self.crop_general_file = crop_general_file 
        self.sim_file = sim_file
        
        self.irr_opt = irr_data_path_opt
        self.fert_opt = fert_data_path_opt
        self.crp_opt = crp_data_path_opt
        self.obs_opt = obs_yield_path_opt
        
        self.irr_red = irr_data_path_red
        self.fert_red = fert_data_path_red
        self.crp_red = crp_data_path_red
        self.obs_red = obs_yield_path_red
        
        self.sheet_name = sheet_name
        self.sim_start = sim_start             
        self.sim_end = sim_end                 
        self.i = i
        
        super().__init__(
            n_var=len(para_df_x),
            n_obj=1, 
            n_ieq_constr=0,
            xl=para_df_x["lower_limit"].values,
            xu=para_df_x["upper_limit"].values
        )

    def _evaluate(self, X, out, *args, **kwargs):
        tasks = []
        for row in range(len(X)):
            x_params = X[row, :] 
            
            
            task_args = (
                self.base_path,         
                x_params, 
                self.param_names, 
                self.project_dir_opt, 
                self.project_dir_red,
                self.parameter_dir, 
                self.cultivar_file, 
                self.species_file, 
                self.crop_general_file, 
                self.sim_file, 
                self.irr_opt, 
                self.fert_opt, 
                self.crp_opt,
                self.irr_red, 
                self.fert_red, 
                self.crp_red, 
                self.obs_opt, 
                self.obs_red,
                self.sheet_name, 
                self.sim_start, 
                self.sim_end, 
                self.i
            )
            tasks.append(task_args)

        # execution in parallel run
        
        with Pool(processes=self.n_cores) as pool:
            results = pool.starmap(run_simulation_worker, tasks)
 
        # 
        out["F"] = np.array(results, dtype=np.float64).reshape(-1, 1)
        
if __name__ == '__main__':
    
    base_path = r'C:\Users\Pandit\Desktop\monica'
    
    # Management paths
    irr_opt = os.path.join(base_path, r'magagement_data\sugarbeet_optimal\optimal_irrigation.xlsx')
    fert_opt = os.path.join(base_path, r'magagement_data\sugarbeet_optimal\fertilizer.xlsx')
    crp_opt = os.path.join(base_path, r'magagement_data\sugarbeet_optimal\crop_mgmt_ZR.xlsx')
    
    irr_red = os.path.join(base_path, r'magagement_data\sugarbeet_reduced\reduced_irrigation.xlsx')
    fert_red = os.path.join(base_path, r'magagement_data\sugarbeet_reduced\fertilizer.xlsx')
    crp_red = os.path.join(base_path, r'magagement_data\sugarbeet_reduced\crop_mgmt_ZR.xlsx')
    
    # Sim period and Observed Yield
    sim_start, sim_end = '2009-01-01', '2015-12-31'
    
    obs_opt = os.path.join(base_path, r"field_obs_data\obs_yield_opt_condition.xlsx")
    obs_red = os.path.join(base_path, r"field_obs_data\obs_yield_red_condition.xlsx")
    
    # Parameter JSONs
    cult_f = os.path.join(base_path, r"monica-parameters\crops\sugar-beet\sugarbeet.json")
    spec_f = os.path.join(base_path, r"monica-parameters\crops\sugar-beet.json")
    gen_f = os.path.join(base_path, r"monica-parameters\general\crop.json")
    sim_f = os.path.join(base_path, r'projects\calibration\sim.json')

    # sensitive paras
    para_df = pd.read_excel(os.path.join(base_path, r'sensitive_paras\sugarbeet_sens_main_paras.xlsx'))
    default_params = para_df["default_value"].values
    
    # Target folders
    proj_opt = os.path.join(base_path, r'projects\sugarbeet_opt')
    proj_red = os.path.join(base_path, r'projects\sugarbeet_red')
    param_dir = os.path.join(base_path, r'monica-parameters\sugarbeet_yield_cal')

    for i in range(1, 2):
        print(f"Starting Yield Optimization for Set {i}...")
        
        problem = MonicaSingleObjectiveProblem(base_path,
            15, param_dir, proj_opt, proj_red, para_df,        # here 15 means the number of the pc cores used 
            cult_f, spec_f, gen_f, sim_f,
            irr_opt, fert_opt, crp_opt, obs_opt,
            irr_red, fert_red, crp_red, obs_red,
            "Sugarbeet", sim_start, sim_end, i
        )
        
        # lhs sampling
        sampling_obj = LHS()
        X_random = sampling_obj._do(problem, 150)
        
        # initialization with the default params
        X_random[0, :] = default_params
        
        algorithm = GA(
            pop_size=150,
            sampling=X_random,
            crossover=SBX(prob=0.9, eta=10),
            mutation=PM(prob=0.25, eta=3),
            eliminate_duplicates=True
        )
    
        res = minimize(problem, algorithm, get_termination("n_gen", 25),         # no of generations as termination criteria
                        seed=int(time.time()), save_history=True, verbose=True)
        
        result_path = os.path.join(base_path, r'projects\sugarbeet_yield_results')
        os.makedirs(result_path, exist_ok=True)
        
        # save file
        np.save(os.path.join(result_path, f'optimized_variables_set{i}.npy'), res.X)
        with open(os.path.join(result_path, f'optimization_result_set{i}.pkl'), 'wb') as f:
            pickle.dump(res, f)
            
        converg(result_path, i)
        variable_convergance(result_path, i, para_df)
    
    
        