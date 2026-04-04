# -*- coding: utf-8 -*-
"""
Created on Sat Mar 28 21:24:49 2026

@author: Pandit
"""

import pandas as pd
import os
from monica_run_postprocess import(map_parameters, update_parameter_files, site_json, crop_json, run_monica, process_yield_file)
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta

from post_process import (pareto_parameter, read_optimization_result)
import dill as pickle

from optimization_run import MonicaSingleObjectiveProblem


def process_and_plot_condition(ax, color, best_x, param_names, proj_dir, parameter_dir, 
                               irr_path, fert_path, crp_path, obs_path, 
                               cultivar_file, species_file, crop_general_file, sim_file,
                               sim_start, sim_end, set_name, sheet_name, i):
    """
    Runs the model for the optimal parameter and generates plot of sim vs obs.
    """
    # parameter file update
    param_update = map_parameters(best_x, param_names, set_name)
    update_parameter_files(base_path, param_update, parameter_dir, proj_dir, 
                           cultivar_file, species_file, crop_general_file, 
                           sim_file, sim_start, sim_end, i)

    # crop json
    crop_json(base_path, irr_path, fert_path, crp_path, sim_start, sim_end, 
              proj_dir, parameter_dir, set_name, i)
    
    # site json
    site_json(base_path, proj_dir, set_name, i)

    # monica run
    run_monica(base_path, proj_dir, set_name, i)

    # read sim file
    sim_out_csv = os.path.join(proj_dir, f'wheat_run{i}', set_name, 'sim-out.csv')
    if not os.path.exists(sim_out_csv):
        return None

    df_sim = process_yield_file(sim_out_csv)
    excluded_years = [2007, 2012]
    df_sim = df_sim[~df_sim['Year'].isin(excluded_years)]

    df_obs = pd.read_excel(obs_path, sheet_name = sheet_name)
    if "Obs_yield" not in df_obs.columns:
        df_obs.columns = ["Year", "Obs_yield"]

    # merge sim and obs file
    merged = pd.merge(df_sim, df_obs, on="Year", how="inner")
    
    if not merged.empty:

        rmse_val = np.sqrt(np.mean((merged['Sim_yield'] - merged['Obs_yield'])**2))

        # plot
        # sim
        ax.plot(merged['Year'], merged['Sim_yield'], label='Simulated Yield', 
                color=color, linestyle='-', linewidth=2.5, marker='s', markersize=5)
        
        # obs
        ax.plot(merged['Year'], merged['Obs_yield'], label='Observed Yield', 
                color='black', linestyle='-', linewidth=2, marker='o', markersize=6)

        ax.axvline( x = 2018, color = "magenta", linestyle = "--", linewidth=2)
        
        ax.set_title(f'Scenario rmse_val: {rmse_val:.3f}', fontsize=14, fontweight='bold')
        ax.set_ylabel('Yield (tDM/ha)', fontsize=12)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(loc='upper left')
        ax.set_xticks(sorted(merged['Year'].unique()))
        
        return merged
    return None

if __name__ == '__main__':
    base_path = r'C:\Users\Pandit\Desktop\monica'
    
    # Management paths
    irr_opt = os.path.join(base_path, r'magagement_data\winterwheat_optimal\optimal_irrigation.xlsx')
    fert_opt = os.path.join(base_path, r'magagement_data\winterwheat_optimal\fertilizer.xlsx')
    crp_opt = os.path.join(base_path, r'magagement_data\winterwheat_optimal\crop_mgmt_WW.xlsx')
    
    irr_red = os.path.join(base_path, r'magagement_data\winterwheat_reduced\reduced_irrigation.xlsx')
    fert_red = os.path.join(base_path, r'magagement_data\winterwheat_reduced\fertilizer.xlsx')
    crp_red = os.path.join(base_path, r'magagement_data\winterwheat_reduced\crop_mgmt_WW.xlsx')
    
    # Sim period and Observed Yield
    sim_start, sim_end = '2007-09-01', '2022-12-31'
    
    obs_opt = os.path.join(base_path, r"field_obs_data\obs_yield_opt_condition.xlsx")
    obs_red = os.path.join(base_path, r"field_obs_data\obs_yield_red_condition.xlsx")
    
    # Parameter JSONs
    cult_f = os.path.join(base_path, r"monica-parameters\crops\wheat\winter-wheat.json")
    spec_f = os.path.join(base_path, r"monica-parameters\crops\wheat.json")
    gen_f = os.path.join(base_path, r"monica-parameters\general\crop.json")
    sim_f = os.path.join(base_path, r'projects\calibration\sim.json')
    
    # Parameters value
    sens_df = pd.read_excel(os.path.join(base_path, r'sensitive_paras\wheat_sens_main_paras.xlsx'))
    param_names = sens_df["parameter_name"].str.strip().tolist()
    
    # project dir
    proj_opt = os.path.join(base_path, r'projects\wheat_opt')
    proj_red = os.path.join(base_path, r'projects\wheat_red')
    param_dir = os.path.join(base_path, r'monica-parameters\wheat_yield_cal')
    
    # pareto result
    result_path = r'C:\Users\Pandit\Desktop\monica\projects\wheat_yield_results'
    
    i = 1
    result_data = read_optimization_result(result_path, i)
    best_x = result_data.X 
    
    set_name = "final_validation_run"
    sheet_name = 'WinterWheat'
    
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))

    # opt plot
    df_opt = process_and_plot_condition(
        ax1, "blue", best_x, param_names, proj_opt, param_dir, 
        irr_opt, fert_opt, crp_opt, obs_opt,
        cult_f, spec_f, gen_f, sim_f,
        sim_start, sim_end, set_name, sheet_name, i
    )

    # red plot
    df_red = process_and_plot_condition(
        ax2, "red", best_x, param_names, proj_red, param_dir, 
        irr_red, fert_red, crp_red, obs_red,
        cult_f, spec_f, gen_f, sim_f,
        sim_start, sim_end, set_name, sheet_name, i
    )

    # plot format
    ax2.set_xlabel('Year', fontsize=12)

    #combined rmse value
    valid_dfs = [df for df in [df_opt, df_red] if df is not None]
    if valid_dfs:
        all_data = pd.concat(valid_dfs)
        total_rmse = np.sqrt(np.mean((all_data['Sim_yield'] - all_data['Obs_yield'])**2))
        
        fig.suptitle(f'Run: Winterwheat Yield\nOverall Combined RMSE: {total_rmse:.3f}', 
                     fontsize=18, fontweight='bold', y=0.98)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.show()