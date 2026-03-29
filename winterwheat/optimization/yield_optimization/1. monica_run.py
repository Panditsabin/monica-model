# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 15:07:31 2026

@author: Pandit
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Aug 20 14:48:01 2025

@author: Pandit
"""
# libraries for changing the parameters
from collections import defaultdict
import os
import json
import uuid
import pandas as pd
import numpy as np
import subprocess
import re

# param update
def map_parameters(x, param_names, set_name):
   
    updates = defaultdict(dict)
    for i, name in enumerate(param_names):
        name = str(name).strip() 
        parts = name.split()
        
        if len(parts) > 1 and parts[-1].isdigit():
            base_name = " ".join(parts[:-1])
            index = int(parts[-1])
            
            updates[base_name][index] = x[i]
        else:
            
            updates[name] = x[i]
            
    return {set_name: dict(updates)}

# changing the parameters values in monica json format 

def update_parameter_files(param_update, parameter_dir, project_dir, cultivar_file, species_file,  crop_general_file, sim_file, sim_start, sim_end, i):
    """Updates parameter files based on generated parameter sets."""
    
    
    source_files = {
        "CultivarParameters": cultivar_file,
        "SpeciesParameters": species_file,
        "UserCropParameters": crop_general_file,
        "Simulation": sim_file
    }
    
    #  directories 
    subfolder_project = os.path.join(project_dir, f'wheat_run{i}')
    subfoler_parameter = os.path.join(parameter_dir, f'wheat_run{i}')
    os.makedirs(subfoler_parameter, exist_ok=True)
    os.makedirs(subfolder_project, exist_ok=True)
    
    for set_name, updates in param_update.items():
        para_out_path = os.path.join(subfoler_parameter, set_name)
        sim_out_path = os.path.join(subfolder_project, set_name)
    
        os.makedirs(para_out_path, exist_ok=True)
        os.makedirs(sim_out_path, exist_ok=True)
    
        for parameter_file, file_path in source_files.items():
            if not os.path.exists(file_path):
                print(f"Warning: Source file not found: {file_path}")
                continue
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
    
            # 1. Update UserCropParameters
            if parameter_file == "UserCropParameters":
                scalar_keys = [
                    "CanopyReflectionCoefficient", "GrowthRespirationParameter1", "GrowthRespirationParameter2",
                    "MaintenanceRespirationParameter1", "MaintenanceRespirationParameter2", "MaxCropNDemand",
                    "ReferenceAlbedo", "ReferenceLeafAreaIndex", "SaturationBeta", "StomataConductanceAlpha"
                ]
                for param in scalar_keys:
                    if param in updates:
                        data[param] = updates[param]            
    
            # 2. Update SpeciesParameters
            elif parameter_file == "SpeciesParameters":
                # scalar params
                scalar_keys_species = [
                    'AssimilateReallocation', 'DefaultRadiationUseEfficiency', 'InitialRootingDepth', 
                    'MaxNUptakeParam', 'OptimumTemperatureForAssimilation', 'MaximumTemperatureForAssimilation',
                    'NConcentrationAbovegroundBiomass', 'NConcentrationPN', 'RootDistributionParam', 'RootFormFactor'
                ]
                for param in scalar_keys_species:
                    if param in updates:
                        data[param] = updates[param]
                
                # arrays
                array_keys_species = [
                    "BaseTemperature", "InitialOrganBiomass", "OrganGrowthRespiration", "OrganMaintenanceRespiration"
                ]
                for param in array_keys_species:
                    if param in updates:
                        for idx, value in updates[param].items():
                            if idx < len(data[param]):
                                data[param][idx] = value
    
            # 3. Update CultivarParameters
            elif parameter_file == "CultivarParameters":

                if "LeafSenescenceRate_s5" in updates: data["OrganSenescenceRate"][4][1] = updates["LeafSenescenceRate_s5"]
                if "LeafSenescenceRate_s6" in updates: data["OrganSenescenceRate"][5][1] = updates["LeafSenescenceRate_s6"]

                # Other parameters
                cultivar_params = [
                    "BeginSensitivePhaseHeatStress", "CriticalTemperatureHeatStress", "CropHeightP1", "CropHeightP2",
                    "CropSpecificMaxRootingDepth", "EndSensitivePhaseHeatStress", "HeatSumIrrigationEnd",
                    "HeatSumIrrigationStart", "MaxAssimilationRate", "MaxCropHeight", "ResidueNRatio", "RespiratoryStress",
                    "BaseDaylength", "DaylengthRequirement", "DroughtStressThreshold", "OptimumTemperature",
                    "SpecificLeafArea", "StageKcFactor", "StageTemperatureSum", "VernalisationRequirement"
                ]
                
                for param in cultivar_params:
                    if param not in updates:
                        continue 
                    
                    if param in ["CropHeightP1", "CropHeightP2", "CropSpecificMaxRootingDepth", "HeatSumIrrigationEnd",
                                 "HeatSumIrrigationStart", "MaxAssimilationRate", "ResidueNRatio", "RespiratoryStress"]:
                        data[param] = updates[param]
                    
                    elif param in ["BeginSensitivePhaseHeatStress", "CriticalTemperatureHeatStress", "EndSensitivePhaseHeatStress", "MaxCropHeight"]:
                        data[param][0] = updates[param]
                    
                    elif param in ["BaseDaylength", "DaylengthRequirement", "OptimumTemperature", "SpecificLeafArea", "StageKcFactor", "StageTemperatureSum"]:
                        target_list = data[param][0]
                        for idx, val in updates[param].items():
                            if idx < len(target_list):
                                target_list[idx] = val
                                
                    elif param == "DroughtStressThreshold":
                        target_list = data[param]
                        for idx, val in updates[param].items():
                            if idx < len(target_list):
                                target_list[idx] = val
                    
                    elif param == "VernalisationRequirement":
                        target_list = data[param]
                        for idx, val in updates[param].items():
                            if idx < len(target_list):
                                target_list[idx] = val

            # 4. Simulation Parameters Update 
            elif parameter_file == "Simulation":
                if "threshold" in updates:
                    data["AutoIrrigationParams"]["trigger_if_nFC_below_%"][0] = int(updates["threshold"])
                    
                if sim_start:
                    data["climate.csv-options"]["start-date"] = sim_start
                if sim_end:
                    data["climate.csv-options"]["end-date"] = sim_end
                

            # 5. Save Files
            file_map = {
                "SpeciesParameters": "wheat.json",
                "CultivarParameters": "winter-wheat.json",
                "UserCropParameters": "crop.json",
                "Simulation": "sim.json"
            }

            # save path
            if parameter_file == "Simulation":
                output_file = os.path.join(sim_out_path, file_map[parameter_file])
            else:
                output_file = os.path.join(para_out_path, file_map[parameter_file])
    
            with open(output_file, 'w', encoding='utf-8') as outfile:
                json.dump(data, outfile, ensure_ascii=False, indent=4)

            

# crop worksteps
def crop_worksteps(irr_data_path, fert_data_path, crp_data_path, sim_start, sim_end):
    """
    Generates a sorted list of worksteps for a specific scenario.
    """
    # Ensure simulation dates are datetime objects
    sim_start = pd.to_datetime(sim_start)
    sim_end = pd.to_datetime(sim_end)
    
    worksteps = []

    # 1. Process Irrigation
    if irr_data_path and os.path.exists(irr_data_path):
        irr_df = pd.read_excel(irr_data_path)
        irr_df['date'] = pd.to_datetime(irr_df['date'])
        irr_df = irr_df[irr_df['date'].between(sim_start, sim_end)]
        
        for _, row in irr_df.iterrows():
            worksteps.append({
                "date": row["date"].strftime('%Y-%m-%d'),
                "type": "Irrigation",
                "amount": [float(row["amount"]), "mm"],
                "parameters": {
                    "nitrateConcentration": [0.0, "mg dm-3"],
                    "sulfateConcentration": [0.0, "mg dm-3"]
                }
            })

    # 2. Process Fertilization
    if fert_data_path and os.path.exists(fert_data_path):
        fert_df = pd.read_excel(fert_data_path)
        fert_df['date'] = pd.to_datetime(fert_df['date'])
        fert_df = fert_df[fert_df['date'].between(sim_start, sim_end)]
        
        for _, row in fert_df.iterrows():
            worksteps.append({
                "date": row["date"].strftime('%Y-%m-%d'),
                "type": "MineralFertilization",
                "amount": [float(row["amount"]), "kg N"],
                "partition": ["ref", "fert-params", "UAN"]
            })

    # 3. Process Crops (Sowing and Harvest)
    if crp_data_path and os.path.exists(crp_data_path):
        crp_df = pd.read_excel(crp_data_path)
        crp_df['sowing'] = pd.to_datetime(crp_df['sowing'])
        crp_df['harvesting'] = pd.to_datetime(crp_df['harvesting'])
        
        # within the crop simulation period
        crp_df = crp_df[(crp_df['sowing'] >= sim_start) & (crp_df['harvesting'] <= sim_end)]
        
        for _, row in crp_df.iterrows():
            # sowing
            worksteps.append({
                "date": row["sowing"].strftime('%Y-%m-%d'),
                "type": "Sowing",
                "crop": ["ref", "crops", row['type']]
            })
            # harvest
            worksteps.append({
                "date": row["harvesting"].strftime('%Y-%m-%d'),
                "type": "Harvest",
                "crop": ["ref", "crops", row['type']]
            })

    # sorting
    worksteps = sorted(worksteps, key=lambda x: x['date'])

    return worksteps


# crop json
def crop_json(irr_path, fert_path, crp_path, sim_start, sim_end, 
                             project_dir, parameter_dir, set_name, i):
    
    set_param_path = os.path.join(parameter_dir, f'wheat_run{i}', set_name)
    if not os.path.isdir(set_param_path): return

    base_monica = r'C:\Users\Pandit\Desktop\monica\monica-parameters'
    
    def get_rel(filename):
        return os.path.relpath(os.path.join(set_param_path, filename), base_monica).replace("\\", "/")

    #  worksteps
    worksteps = crop_worksteps(irr_path, fert_path, crp_path, sim_start, sim_end)
    

    crop_json_data = {
        'crops': {
            "WW": {
                "is-winter-crop": True,
                "cropParams": {
                    "species": ["include-from-file", get_rel("wheat.json")],
                    "cultivar": ["include-from-file", get_rel("winter-wheat.json")]
                },
                "residueParams": ["include-from-file", "crop-residues/wheat.json"]
            }
        },
        "fert-params": {
            "UAN": ["include-from-file", "mineral-fertilisers/UAN.json"],
            "CADLM": ["include-from-file", "organic-fertilisers/CADLM.json"]
        },
        "cropRotation": [{"worksteps": worksteps}],
        "CropParameters": ["include-from-file", get_rel("crop.json")]
    }
    
    # Saving
    save_path = os.path.join(project_dir, f'wheat_run{i}', set_name)
    os.makedirs(save_path, exist_ok=True)
    with open(os.path.join(save_path, "crop.json"), "w", encoding="utf-8") as f:
        json.dump(crop_json_data, f, ensure_ascii=False, indent=4)


# Monica run optimal
def run_monica(project_dir, set_name, i):
    """
    function to run Monica simulation for a given directory and run index.
    """
    monica_exe = r"C:\Users\Pandit\Desktop\monica\bin\monica-run.exe"
    
    # Construct paths
    subfolder = os.path.join(project_dir, f'wheat_run{i}')
    set_path = os.path.join(subfolder, set_name)
    sim_json = os.path.join(set_path, 'sim.json')
    sim_out_csv = os.path.join(set_path, 'sim-out.csv')

    # check 
    if not os.path.exists(sim_json):
        print(f"Error: sim.json not found in {set_path}")
        return

    try:
        subprocess.run(
            [monica_exe, "-o", sim_out_csv, sim_json],
            check=True,
            capture_output=True,
            text=True,
            cwd=set_path
        )
    except subprocess.CalledProcessError as e:
        print(f"Simulation failed for {set_name} in {project_dir}: {e.stderr}")   

        
#2) Objective function part

def process_phenology_file(file_path):
    """
    Extracts the first DOY where Stage reaches 6.0 for each year.
    Returns a DataFrame with [Year, Sim_DOY].
    """
    try:
        
        df = pd.read_csv(file_path, low_memory=False, skiprows=1)

        
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        df['Stage'] = pd.to_numeric(df['Stage'], errors='coerce')
        df['DOY'] = pd.to_numeric(df['DOY'], errors='coerce')
        df = df.dropna(subset=['Year', 'Stage', 'DOY'])

        
        maturity = df[df['Stage'] >= 6.0].sort_values(['Year', 'DOY'])
        maturity = maturity.groupby('Year').first().reset_index()
        
        return maturity[['Year', 'DOY']].rename(columns={'DOY': 'Sim_DOY'})

    except Exception as e:
        return pd.DataFrame(columns=["Year", "Sim_DOY"])
    
def simulated_phenology_data(sim_out_csv_opt, sim_out_csv_red):
    """
    Reads the TWO output files generated for the SAME parameter set.
    """
    
    df_opt = process_phenology_file(sim_out_csv_opt)
    df_red = process_phenology_file(sim_out_csv_red)
    
    return df_opt, df_red

def process_yield_file(file_path):
    """
    Reads MONICA sim-out.csv
    Extracts max yield per year and converts kgDM/ha to tDM/ha.
    """
    try:
        
        df = pd.read_csv(file_path, low_memory=False, skiprows=1, sep=',')

        
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        df['Yield'] = pd.to_numeric(df['Yield'], errors='coerce')
        df = df.dropna(subset=['Year', 'Yield'])

        
        yield_df = df.groupby('Year')['Yield'].max().reset_index()

        
        yield_df['Sim_yield'] = yield_df['Yield'] / 1000.0
        
        return yield_df[['Year', 'Sim_yield']]

    except Exception as e:
        print(f"Error reading simulation file {file_path}: {e}")
        return pd.DataFrame(columns=["Year", "Sim_yield"])


def simulated_yield_data(sim_out_csv_opt, sim_out_csv_red):
    """
    Processes the simulated files for both Optimal and Reduced scenarios.
    """
    df_opt = process_yield_file(sim_out_csv_opt)
    df_red = process_yield_file(sim_out_csv_red)
    
    return df_opt, df_red


def calculate_objective(set_name, project_dir_opt, project_dir_red, 
                        obs_yield_path_opt, obs_yield_path_red, sheet_name, i): 
    
    sub_opt = os.path.join(project_dir_opt, f'wheat_run{i}', set_name, 'sim-out.csv')
    sub_red = os.path.join(project_dir_red, f'wheat_run{i}', set_name, 'sim-out.csv')

    try:
        
        sim_yld_opt, sim_yld_red = simulated_yield_data(sub_opt, sub_red)
        
       
        excluded_years = [2006, 2007, 2012] 

       
        obs_opt = pd.read_excel(obs_yield_path_opt, sheet_name=sheet_name)
        obs_red = pd.read_excel(obs_yield_path_red, sheet_name=sheet_name)
        
        def get_clean_merge(sim_df, obs_df):
            
            merged = pd.merge(obs_df, sim_df, on="Year", how="inner")
            merged = merged[~merged['Year'].isin(excluded_years)]
            return merged

        m_opt = get_clean_merge(sim_yld_opt, obs_opt)
        m_red = get_clean_merge(sim_yld_red, obs_red)
            
        combined = pd.concat([m_opt, m_red], ignore_index=True)

        if combined.empty:
            return 1e6

        # error metric
        yield_rmse = np.sqrt(np.mean((combined["Sim_yield"] - combined["Obs_yield"])**2)) 
        
        return yield_rmse
    
    except Exception as e:
          print(f'Yield Optimization Error for {set_name}: {e}')
          return 1e6

# def calculate_objective(set_name, project_dir_opt, project_dir_red, 
#                         obs_yield_path_opt, obs_yield_path_red, sheet_name, i): 
    
#     sub_opt = os.path.join(project_dir_opt, f'wheat_run{i}', set_name, 'sim-out.csv')
#     sub_red = os.path.join(project_dir_red, f'wheat_run{i}', set_name, 'sim-out.csv')

#     try:
#         # 1. READ SIMULATED DATA (Stage 6 DOY)
#         sim_mat_opt, sim_mat_red = simulated_phenology_data(sub_opt, sub_red)
        
#         # 2. CALIBRATION PERIOD DEFINITION
#         # 2008 is REMOVED from this list so it is now INCLUDED in calibration
#         excluded_years = [2006, 2007, 2012, 2019, 2020, 2021, 2022]

#         # 3. READ OBSERVED DATA
#         obs_opt = pd.read_excel(obs_yield_path_opt, sheet_name=sheet_name)
#         obs_red = pd.read_excel(obs_yield_path_red, sheet_name=sheet_name)
        
#         def get_clean_merge(sim_df, obs_df, scenario_name):
#             # Merge sim and obs on Year
#             merged = pd.merge(obs_df, sim_df, on="Year", how="left")
            
#             # Filter: Keep only the years we want to calibrate
#             merged = merged[~merged['Year'].isin(excluded_years)]
            
#             # # --- DEBUG CHECK FOR FAILURES ---
#             # # If 2008 fails to reach Stage 6, it will appear here
#             # nans = merged[merged['Sim_DOY'].isna()]['Year'].tolist()
#             # if len(nans) > 0:
#             #     # This prints to console if n_cores=1
#             #     print(f"DEBUG [{set_name}]: {scenario_name} failed in: {nans}")
            
#             # Fill NaNs with 365 penalty (Forces GA to fix these years)
#             merged['Sim_DOY'] = merged['Sim_DOY'].fillna(365.0)
#             return merged

#         # Process both scenarios
#         merged_opt = get_clean_merge(sim_mat_opt, obs_opt, "OPTIMAL")
#         merged_red = get_clean_merge(sim_mat_red, obs_red, "REDUCED")
            
#         # Combine scenarios into one flat list of errors
#         combined = pd.concat([merged_opt, merged_red], ignore_index=True)

#         if combined.empty:
#             print(f"Set {set_name}: No data remains after filtering!")
#             return 1e6

#         # 4. CALCULATE RMSE (Targeting 'harvest_doy' from your Excel)
#         # diff = (Simulated Day - Observed Day)
#         pheno_rmse = np.sqrt(np.mean((combined["Sim_DOY"] - combined["harvest_doy"])**2)) 
        
#         return pheno_rmse
    
#     except Exception as e:
#           print(f'Error in calculation for {set_name}: {e}')
#           return 1e6