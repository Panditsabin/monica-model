# -*- coding: utf-8 -*-
"""
Created on Sun Nov 30 13:49:46 2025

@author: Pandit
"""

import pandas as pd
import numpy as np
import os
import multiprocessing as mp

from wheat_morris_multiprocess import (map_parameters, update_parameter_files, crop_json, site_json,
                           run_monica, simulated_yield_data, extract_moist_data, extract_irr_data)

def save_to_txt(results_list, file_name, results_dir):
    """saves the result as the txt"""
    if results_list:
        final_df = pd.concat(results_list, ignore_index=True)
        out_path = os.path.join(results_dir, file_name)
        final_df.to_csv(out_path, index=True, float_format="%.4f")
        print(f"Saved: {out_path}")


def run_morris_worker(args):
    """
    Worker function to process one Morris row (one simulation task).
    """
    (base_path, x, param_names, i, set_name, run_name,
     parameter_dir, project_dir,
     cultivar_file, species_file, crop_general_file, sim_file,
     irr_data_path, fert_data_path, crp_data_path,
     sim_start, sim_end) = args

    try:
        
        param_update = map_parameters(x, param_names, set_name)

        update_parameter_files(base_path, param_update, parameter_dir, project_dir,
                               cultivar_file, species_file, crop_general_file,
                               sim_file, sim_start, sim_end, run_name)

        crop_json(base_path, irr_data_path, fert_data_path, crp_data_path,
                  sim_start, sim_end, project_dir, parameter_dir, set_name, run_name)
        
        site_json(base_path, project_dir, set_name, run_name)

        
        run_monica(base_path, project_dir, set_name, run_name)

        
        sim_csv_path = os.path.join(project_dir, run_name, set_name, 'sim-out.csv')

        if os.path.exists(sim_csv_path):
            df_yld   = simulated_yield_data(sim_csv_path)
            df_irr   = extract_irr_data(sim_csv_path)
            df_moist = extract_moist_data(sim_csv_path)
            return (i, df_yld, df_irr, df_moist)
        else:
            return (i, None, None, None)

    except Exception as e:
        print(f"Worker Error in index {i} for {set_name}: {e}")
        return (i, None, None, None)



if __name__ == '__main__':

    base_path = r'C:\Users\Pandit\Desktop\monica'

    # management files
    irr_data_path  = os.path.join(base_path, r'magagement_data\winterwheat_reduced\reduced_irrigation.xlsx')
    fert_data_path = os.path.join(base_path, r'magagement_data\winterwheat_reduced\fertilizer.xlsx')
    crp_data_path  = os.path.join(base_path, r'magagement_data\winterwheat_reduced\crop_mgmt_WW.xlsx')

    # simulation period
    sim_start = '2007-07-01'
    sim_end   = '2018-12-31'

    # parameter files
    cultivar_file     = os.path.join(base_path, r'monica-parameters\crops\wheat\winter-wheat.json')
    species_file      = os.path.join(base_path, r'monica-parameters\crops\wheat.json')
    crop_general_file = os.path.join(base_path, r'monica-parameters\general\crop.json')
    sim_file          = os.path.join(base_path, r'projects\calibration\sim.json')

    # morris parameter sets
    morris_df   = pd.read_excel(os.path.join(base_path, r'sa_analysis\winterwheat_morris.xlsx'))
    param_names = morris_df.columns.to_list()

    # folders
    parameter_dir = os.path.join(base_path, r'monica-parameters\wheat_morris_sa_reduced')
    project_dir   = os.path.join(base_path, r'projects\wheat_morris_sa_reduced')
    results_dir   = os.path.join(project_dir, 'results_morris')
    os.makedirs(results_dir, exist_ok=True)

    # no crop period
    excluded_years = [2007, 2012]
    run_name = "wheat_run" 
    n_cores = 15      

    # observed soil moisture
    obs_moist_path = os.path.join(base_path, r'field_obs_data\wheat_sm_red_condition.xlsx')
    obs_moist_df   = pd.read_excel(obs_moist_path)
    obs_moist_df['Date'] = pd.to_datetime(obs_moist_df['Date'])

    # task
    tasks = []
    for i, row in morris_df.iterrows():
        x        = row.values
        set_name = f'set_{i}'
        tasks.append((
            base_path, x, param_names, i, set_name, run_name,
            parameter_dir, project_dir,
            cultivar_file, species_file, crop_general_file, sim_file,
            irr_data_path, fert_data_path, crp_data_path,
            sim_start, sim_end
        ))
        
    # parallel run
    print(f"Starting {len(tasks)} Morris simulations on {n_cores} cores...")
    with mp.Pool(processes=n_cores) as pool:
        all_results = pool.map(run_morris_worker, tasks)

    # sorting
    all_results.sort(key=lambda x: x[0])

    
    yield_results      = []
    irrigation_results = []
    moisture_results   = []

    for (i, df_yld, df_irr, df_moist) in all_results:
        if df_yld is not None:
            
            df_yld = df_yld[~df_yld['Year'].isin(excluded_years)]
            yield_results.append(df_yld.set_index('Year').T)
            
        if df_irr is not None:
            
            df_irr = df_irr[~df_irr['Year'].isin(excluded_years)]
            irrigation_results.append(df_irr.set_index('Year').T)
            
        if df_moist is not None:
            
            df_merged = pd.merge(obs_moist_df[['Date']], df_moist, on='Date', how='inner')
            moisture_results.append(df_merged.set_index('Date').T)

    # text files
    save_to_txt(yield_results,      'wheat_yld.txt', results_dir)
    save_to_txt(irrigation_results, 'wheat_irr.txt', results_dir)
    save_to_txt(moisture_results,   'wheat_sm.txt',  results_dir)
    
    print("processing complete.")
    