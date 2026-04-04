# -*- coding: utf-8 -*-
"""
Created on Wed Aug 20 14:53:28 2025

@author: Pandit
"""
from monica_run import (
    map_parameters, update_parameter_files, site_json, crop_json, run_monica, 
    simulated_yield_data, calculate_objectives  
    )

# Libraries import from post_process.py
from post_process import(
    read_optimization_result, analyze_pareto, hypervolume_analysis, running_metric, variable_convergance
    )

import os
import json
import uuid
import time
import pandas as pd
import numpy as np
import dill as pickle
from multiprocessing import Pool

# Pymoo imports
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.sampling.lhs import LatinHypercubeSampling
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.termination import get_termination
from pymoo.optimize import minimize
from pymoo.core.problem import Problem

# 1. worker func
def run_simulation_worker(base_path, x_params, param_names, project_dir_opt, project_dir_red, 
                          parameter_dir, cultivar_file, species_file, crop_general_file, 
                          sim_file, 
                          irr_opt, fert_opt, crp_opt, 
                          irr_red, fert_red, crp_red, 
                          obs_yield_opt, obs_yield_red, 
                          obs_moist_opt, obs_moist_red,   
                          man_irr_opt, man_irr_red,       
                          sheet_name, sim_start, sim_end,
                         i): 
    
    set_name = f"set_{uuid.uuid4().hex[:10]}"
    
    try:
        # map params
        param_update = map_parameters(x_params, param_names, set_name)
        
        # update json files
        update_parameter_files(base_path, param_update, parameter_dir, project_dir_opt, 
                               cultivar_file, species_file, crop_general_file, 
                               sim_file, sim_start, sim_end, i, condition="opt")
        
        update_parameter_files(base_path, param_update, parameter_dir, project_dir_red, 
                               cultivar_file, species_file, crop_general_file, 
                               sim_file, sim_start, sim_end, i, condition="red")
        
        # opt mgmt
        crop_json(base_path, irr_opt, fert_opt, crp_opt, sim_start, sim_end, project_dir_opt, parameter_dir, set_name, i)
        site_json(base_path, project_dir_opt, set_name, i)
        
        # red mgmt
        crop_json(base_path, irr_red, fert_red, crp_red, sim_start, sim_end, project_dir_red, parameter_dir, set_name, i)
        site_json(base_path, project_dir_red, set_name, i)
            
        # monica run
        run_monica(base_path, project_dir_opt, set_name, i)
        run_monica(base_path, project_dir_red, set_name, i)

        # rmse (both opt and red condn combined)
        combined_rmse = calculate_objectives(
            set_name           = set_name, 
            project_dir_opt    = project_dir_opt, 
            project_dir_red    = project_dir_red, 
            obs_yield_path_opt = obs_yield_opt, 
            obs_yield_path_red = obs_yield_red, 
            obs_moist_path_opt = obs_moist_opt,  
            obs_moist_path_red = obs_moist_red,  
            manual_irr_path_opt   = man_irr_opt,      
            manual_irr_path_red   = man_irr_red,      
            sheet_name         = sheet_name, 
            sim_start = sim_start,   
            sim_end = sim_end,
            i = i
        )
        
        return combined_rmse 

    except Exception as e:
        print(f"Worker Error in run {i}: {e}")
        return (1e6, 1e6, 1e6)

# 2. problem defn
class MonicaManualParallelProblem(Problem):
    def __init__(self, n_cores, parameter_dir, project_dir_opt, project_dir_red, para_df_x, 
                 cultivar_file, species_file, crop_general_file, sim_file, 
                 sim_start, sim_end, irrigation_data_opt, fertilization_data_opt, crop_data_opt,
                 irrigation_data_red, fertilization_data_red, crop_data_red,
                 obs_yield_path_opt, obs_yield_path_red, sheet_name,
                 obs_moist_path_opt, obs_moist_path_red, manual_irr_path_opt, manual_irr_path_red,
                 i, base_path):
        
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
        
        # mgmt and obs data path
        self.paths = {
            "irr_opt": irrigation_data_opt, "fert_opt": fertilization_data_opt, "crp_opt": crop_data_opt,
            "irr_red": irrigation_data_red, "fert_red": fertilization_data_red, "crp_red": crop_data_red,
            "yield_opt": obs_yield_path_opt, "yield_red": obs_yield_path_red,
            "moist_opt": obs_moist_path_opt, "moist_red": obs_moist_path_red,
            "man_opt": manual_irr_path_opt, "man_red": manual_irr_path_red
        }
        
        self.sheet_name = sheet_name
        self.sim_start, self.sim_end = sim_start, sim_end                 
        self.i = i
        
        super().__init__(
            n_var = len(para_df_x),
            n_obj = 3 , 
            xl = para_df_x["lower_limit"].values,
            xu = para_df_x["upper_limit"].values
        )

    def _evaluate(self, X, out, *args, **kwargs):
        tasks = []
        for row in range(len(X)):
            task_args = (
                self.base_path, X[row, :], self.param_names, self.project_dir_opt, self.project_dir_red,
                self.parameter_dir, self.cultivar_file, self.species_file, self.crop_general_file, self.sim_file, 
                self.paths["irr_opt"], self.paths["fert_opt"], self.paths["crp_opt"],
                self.paths["irr_red"], self.paths["fert_red"], self.paths["crp_red"], 
                self.paths["yield_opt"], self.paths["yield_red"],
                self.paths["moist_opt"], self.paths["moist_red"],
                self.paths["man_opt"], self.paths["man_red"],
                self.sheet_name, self.sim_start, self.sim_end, self.i
            )
            tasks.append(task_args)

        with Pool(processes=self.n_cores) as pool:
            results = pool.starmap(run_simulation_worker, tasks)
 
        out["F"] = np.array(results, dtype=np.float64)

if __name__ == '__main__':
    base_path = r'C:\Users\Pandit\Desktop\monica'

    # opt mgmt paths
    irr_opt = os.path.join(base_path, r'magagement_data\winterwheat_optimal\optimal_irrigation.xlsx')
    crop_rot_opt = os.path.join(base_path, r'magagement_data\winterwheat_optimal\crop_mgmt_WW.xlsx')
    fert_opt = os.path.join(base_path, r'magagement_data\winterwheat_optimal\fertilizer.xlsx')
    
    # red mgmt paths
    irr_red = os.path.join(base_path, r'magagement_data\winterwheat_reduced\reduced_irrigation.xlsx')
    crop_rot_red = os.path.join(base_path, r'magagement_data\winterwheat_reduced\crop_mgmt_WW.xlsx')
    fert_red = os.path.join(base_path, r'magagement_data\winterwheat_reduced\fertilizer.xlsx')

    # opt obs data
    obs_yield_opt  = os.path.join(base_path, r"field_obs_data\obs_yield_opt_condition.xlsx")
    obs_yield_red  = os.path.join(base_path, r"field_obs_data\obs_yield_red_condition.xlsx")
    
    obs_moist_opt  = os.path.join(base_path, r"field_obs_data\wheat_sm_opt_condition.xlsx")
    obs_moist_red  = os.path.join(base_path, r"field_obs_data\wheat_sm_red_condition.xlsx")
    
    man_irr_opt    = os.path.join(base_path, r"field_obs_data\wheat_irr_opt_condition.xlsx")
    man_irr_red    = os.path.join(base_path, r"field_obs_data\wheat_irr_red_condition.xlsx")
    
    # sens para df
    para_df = pd.read_excel(r'C:\Users\Pandit\Desktop\monica\sensitive_paras\wheat_yld_sm_sens_para.xlsx')
    
    # json parameters 
    cult_f = os.path.join(base_path, r"monica-parameters\crops\wheat\winter-wheat.json")
    spec_f = os.path.join(base_path, r"monica-parameters\crops\wheat.json")
    gen_f = os.path.join(base_path, r"monica-parameters\general\crop.json")
    sim_f = os.path.join(base_path, r'projects\calibration\sim.json')
    
    # simulation period
    sim_start, sim_end = '2007-09-01', '2018-12-31'
    
    # param dir
    parameter_dir  = r'C:\Users\Pandit\Desktop\monica\monica-parameters\wheat_3objs'
    
    # project dir
    project_dir_opt = r'C:\Users\Pandit\Desktop\monica\projects\wheat_3objs_opt'
    project_dir_red = r'C:\Users\Pandit\Desktop\monica\projects\wheat_3objs_red'
    
    # optimization result save
    result_path = r'C:\Users\Pandit\Desktop\monica\projects\wheat_3objs_result'
    os.makedirs(result_path, exist_ok=True)

    no_cores = 15 # no of cores

    for i in range(0, 1):
        print(f"Analysis Starting for set{i}.....")

        # problem = MonicaManualParallelProblem(
        #     n_cores              = no_cores,
        #     parameter_dir        = parameter_dir,
        #     project_dir_opt      = project_dir_opt,
        #     project_dir_red      = project_dir_red,
        #     para_df_x            = para_df,
        #     cultivar_file        = cult_f,         
        #     species_file         = spec_f,         
        #     crop_general_file    = gen_f,          
        #     sim_file             = sim_f,          
        #     sim_start            = sim_start,       
        #     sim_end              = sim_end,         
        #     irrigation_data_opt  = irr_opt,
        #     fertilization_data_opt = fert_opt,
        #     crop_data_opt        = crop_rot_opt,
        #     irrigation_data_red  = irr_red,
        #     fertilization_data_red = fert_red,
        #     crop_data_red        = crop_rot_red,
        #     obs_yield_path_opt   = obs_yield_opt,
        #     obs_yield_path_red   = obs_yield_red,
        #     sheet_name           = 'WinterWheat',
        #     obs_moist_path_opt   = obs_moist_opt,
        #     obs_moist_path_red   = obs_moist_red,
        #     manual_irr_path_opt  = man_irr_opt,
        #     manual_irr_path_red  = man_irr_red,
        #     i                    = i,
        #     base_path            = base_path 
        # )

        # algorithm = NSGA2(
        #     pop_size= 150,
        #     sampling=LatinHypercubeSampling(),
        #     crossover=SBX(prob=0.9, eta=15),   
        #     mutation=PM(eta=20),
        #     eliminate_duplicates=True
        #     )

        # res = minimize(
        #     problem, 
        #     algorithm, 
        #     get_termination("n_gen", 30), 
        #     seed=int(time.time()),
        #     save_history=True, 
        #     verbose=True)

        # # Save results
        # np.save(os.path.join(result_path, f'optimized_variables_set{i}.npy'), res.X)
        # np.save(os.path.join(result_path, f'objective_values_set{i}.npy'), res.F)

        # with open(os.path.join(result_path, f'optimization_result_set{i}.pkl'), 'wb') as f:
        #     pickle.dump(res, f)

        # print(f"Analysis for set {i} is complete.")
        
        #plots
        analyze_pareto(result_path, i)
        
        hypervolume_analysis(result_path, i)
        running_metric(result_path, i)
        variable_convergance(result_path, i, para_df)