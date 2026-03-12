# -*- coding: utf-8 -*-
"""
Created on Fri Dec 19 14:36:38 2025

@author: Pandit
"""

import pandas as pd
import os

from sugarbeet_morris import ( map_parameters, update_parameter_files, new_crop_json_files, run_monica, simulated_yield_data, extract_moist_data, extract_irr_data)

if __name__ == '__main__':

    # Management file Path
    irr_data_path = r'C:\Users\Pandit\Desktop\monica_win64_3.6.32.toth_ser_TUA\magagement_data\sugarbeet_reduced\reduced_irrigation.xlsx'

    fert_data_path = r'C:\Users\Pandit\Desktop\monica_win64_3.6.32.toth_ser_TUA\magagement_data\sugarbeet_reduced\fertilizer.xlsx'
    
    crp_data_path = r'C:\Users\Pandit\Desktop\monica_win64_3.6.32.toth_ser_TUA\magagement_data\sugarbeet_reduced\crop_mgmt_ZR.xlsx'
    
    # simulation period
    
    sim_start = '2009-01-01'
    sim_end = '2015-12-31'
    
    # parameter json files
    cultivar_file = r"C:\Users\Pandit\Desktop\monica_win64_3.6.32.toth_ser_TUA\monica-parameters\crops\sugar-beet\sugarbeet.json"
    species_file = r"C:\Users\Pandit\Desktop\monica_win64_3.6.32.toth_ser_TUA\monica-parameters\crops\sugar-beet.json"
    crop_general_file = r"C:\Users\Pandit\Desktop\monica_win64_3.6.32.toth_ser_TUA\monica-parameters\general\crop.json"
    sim_file = r'C:\Users\Pandit\Desktop\monica_win64_3.6.32.toth_ser_TUA\projects\calibration\sim.json'
    
    # morris parameter set
    morris_df = pd.read_excel(r'C:\Users\Pandit\Desktop\sa_analysis\sugarbeet_morris.xlsx')
    param_names = morris_df.columns.to_list()
    
    # directory
    parameter_dir = r'C:\Users\Pandit\Desktop\monica_win64_3.6.32.toth_ser_TUA\monica-parameters\sugarbeet_morris_sa_reduced'
    project_dir = r'C:\Users\Pandit\Desktop\monica_win64_3.6.32.toth_ser_TUA\projects\sugarbeet_morris_sa_reduced'
    results_dir = os.path.join(project_dir, r'results_morris')
    os.makedirs(results_dir, exist_ok=True)
   
    # output save
    yield_results = []
    irrigation_results = []
    moisture_results = []
    
    for i, row in morris_df.iterrows():
        x = row.values
        set_name = f'set_{i}'
        param_update = map_parameters(x, param_names, set_name)
        update_parameter_files(param_update, parameter_dir, project_dir, cultivar_file, species_file,  crop_general_file, sim_file, sim_start, sim_end)
        new_crop_json_files(irr_data_path, fert_data_path, crp_data_path, 
                            sim_start, sim_end, project_dir, parameter_dir, set_name)
        
        # 2. MONICA simulation
        
        run_monica(project_dir, set_name)
        sim_csv_path = os.path.join(project_dir, set_name, 'sim-out.csv')
         
        
        # 3. saving the files in the txt format
        if os.path.exists(sim_csv_path):
            # 1. yield
            df_yld = simulated_yield_data(sim_csv_path)
            df_yldt = df_yld.set_index('Year').T
            #df_yldt.index = [0] 
            yield_results.append(df_yldt)

            # 2. IRRIGATION
            df_irr = extract_irr_data(sim_csv_path)
            df_irrt = df_irr.set_index('Year').T 
            #df_irrt.index = [0]
            irrigation_results.append(df_irrt)

            # 3. MOISTURE
            df_moist = extract_moist_data(sim_csv_path)
            df_moistt = df_moist.set_index('Date').T 
            #df_moistt.index = [0]
            moisture_results.append(df_moistt)
            
            
    def save_to_txt(results_list, file_name):
        if results_list:
            final_df = pd.concat(results_list, ignore_index=True)
            
            # Save path
            out_path = os.path.join(results_dir, file_name)
            
            
            final_df.to_csv(out_path, index=True, float_format="%.4f")
            print(f"Saved: {out_path}")

    # saving text files
    save_to_txt(yield_results, 'sugarbeet_yld.txt' )
    save_to_txt(irrigation_results, 'sugarbeet_irr.txt')
    save_to_txt(moisture_results, 'sugarbeet_sm.txt')