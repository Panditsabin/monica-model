# -*- coding: utf-8 -*-
"""
Created on Wed Aug 20 14:48:01 2025

@author: Pandit
"""
# libraries for changing the parameters
import os
import json
import uuid
import pandas as pd
import numpy as np
import subprocess
import re
from collections import defaultdict



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

def update_parameter_files(base_path, param_update, parameter_dir, project_dir, cultivar_file, species_file,  crop_general_file, sim_file, sim_start, sim_end, i):
    """Updates parameter files based on generated parameter sets."""
    
    
    source_files = {
        "CultivarParameters": cultivar_file,
        "SpeciesParameters": species_file,
        "UserCropParameters": crop_general_file,
        "Simulation": sim_file
    }
    
    #  directories 
    subfolder_project = os.path.join(project_dir, f'sugarbeet_run{i}')
    subfoler_parameter = os.path.join(parameter_dir, f'sugarbeet_run{i}')
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
                # Partitioning and Senescence
                senescence_map = {
                    "LeafSenescenceRate_s5": (4, 0),
                    "LeafSenescenceRate_s6": (5, 0),
                    "StemSenescenceRate_s4": (3, 1),
                    "StemSenescenceRate_s5": (4, 1),
                    "StemSenescenceRate_s6": (5, 1)
                }
                
                if "OrganSenescenceRate" in data:
                    for key, (row, col) in senescence_map.items():
                        if key in updates:
                            
                            if row < len(data["OrganSenescenceRate"]) and col < len(data["OrganSenescenceRate"][row]):
                                data["OrganSenescenceRate"][row][col] = updates[key]

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
                
                monica_params_abs = os.path.join(base_path, "monica-parameters").replace("\\", "/")
                if not monica_params_abs.endswith("/"):
                    monica_params_abs += "/"
                    
                data["include-file-base-path"] = monica_params_abs
                
                if "threshold" in updates:
                    data["AutoIrrigationParams"]["trigger_if_nFC_below_%"][0] = int(updates["threshold"])
                    
                if sim_start:
                    data["climate.csv-options"]["start-date"] = sim_start
                if sim_end:
                    data["climate.csv-options"]["end-date"] = sim_end
                

            # 5. Save Files
            file_map = {
                "SpeciesParameters": "sugar-beet.json",
                "CultivarParameters": "sugarbeet.json",
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

            

# input files

# 1. site json
def site_json(base_path, project_dir, set_name, i):
    """
    Creates site.json and saves it in the project folder alongside crop.json.
   
    """
    # path to save the site json
    save_path = os.path.join(project_dir, f'sugarbeet_run{i}', set_name)
    os.makedirs(save_path, exist_ok=True)
    
   # reference to the parameters
    general_prefix = "general/"

     # soil Profile
    soil_profile = [
     {"Thickness": 0.30, "Sand": 0.82, "Clay": 0.02, "SoilOrganicCarbon": [2.99, "%"], "SoilBulkDensity": 1274, "FieldCapacity": 0.209, "PermanentWiltingPoint": 0.042, "Lambda": 0.83},
     {"Thickness": 0.20, "Sand": 0.82, "Clay": 0.02, "SoilOrganicCarbon": [0.49, "%"], "SoilBulkDensity": 1624, "FieldCapacity": 0.142, "PermanentWiltingPoint": 0.038, "Lambda": 0.83},
     {"Thickness": 0.10, "Sand": 0.75, "Clay": 0.07, "SoilOrganicCarbon": [0.0, "%"], "SoilBulkDensity": 1597, "FieldCapacity": 0.210, "PermanentWiltingPoint": 0.048, "Lambda": 0.72},
     {"Thickness": 0.35, "Sand": 0.65, "Clay": 0.10, "SoilOrganicCarbon": [0.0, "%"], "SoilBulkDensity": 1575, "FieldCapacity": 0.254, "PermanentWiltingPoint": 0.063, "Lambda": 0.58},
     {"Thickness": 1.05, "Sand": 0.94, "Clay": 0.01, "SoilOrganicCarbon": [0.0, "%"], "SoilBulkDensity": 1640, "FieldCapacity": 0.093, "PermanentWiltingPoint": 0.047, "Lambda": 1.03}
     ]


    # json str
    site_data = {
        "SiteParameters": {
            "Latitude": 52.5333333,
            "Slope": 0,
            "HeightNN": [65, "m"],
            "NDeposition": [5, "kg N ha-1 y-1"],
            "SoilProfileParameters": soil_profile
        },
        "SoilTemperatureParameters": ["include-from-file", general_prefix + "soil-temperature.json"],
        "EnvironmentParameters": ["include-from-file", general_prefix + "environment.json"],
        "SoilOrganicParameters": ["include-from-file", general_prefix + "soil-organic.json"],
        "SoilTransportParameters": ["include-from-file", general_prefix + "soil-transport.json"],
        "SoilMoistureParameters": ["include-from-file", general_prefix + "soil-moisture.json"]
    }

    # save file
    output_file = os.path.join(save_path, "site.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(site_data, f, indent=4)
    

# 2. crop worksteps
def crop_worksteps(irr_data_path, fert_data_path, crp_data_path, sim_start, sim_end):
    """
    Generates a sorted list of worksteps for a specific scenario.
    """
    # datetime 
    sim_start = pd.to_datetime(sim_start)
    sim_end = pd.to_datetime(sim_end)
    
    worksteps = []

    # irrigation
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

    # fertilization
    if fert_data_path and os.path.exists(fert_data_path):
        fert_df = pd.read_excel(fert_data_path)
        fert_df['date'] = pd.to_datetime(fert_df['date'])
        fert_df = fert_df[fert_df['date'].between(sim_start, sim_end)]
        
        for _, row in fert_df.iterrows():
            worksteps.append({
                "date": row["date"].strftime('%Y-%m-%d'),
                "type": "MineralFertilization",
                "amount": [float(row["amount"]), "kg N ha-1"],
                "partition": ["ref", "fert-params", "UAS"]
            })

    # Sowing and Harvest
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



# 3. crop json
def crop_json(base_path, irr_path, fert_path, crp_path, sim_start, sim_end, 
              project_dir, parameter_dir, set_name, i):
    """
    Creates crop.json by referencing parameters inside base_path/monica-parameters
    and saving the output to the project_dir.
    """
    
    # reference to monica parameter path
    base_monica = os.path.join(base_path, 'monica-parameters')

    set_param_path = os.path.join(base_monica, parameter_dir, f'sugarbeet_run{i}', set_name)
    
    # check
    if not os.path.isdir(set_param_path):
        print(f"Directory not found: {set_param_path}")
        return

    # relative path to monica-parameters
    def get_rel(filename):
        full_path = os.path.join(set_param_path, filename)
    
        return os.path.relpath(full_path, base_monica).replace("\\", "/")

    # worksteps
    worksteps = crop_worksteps(irr_path, fert_path, crp_path, sim_start, sim_end)

    # crop json str
    crop_json_data = {
        'crops': {
            "ZR": {
                "is-winter-crop": False,
                "cropParams": {
                    "species": ["include-from-file", get_rel("sugar-beet.json")],
                    "cultivar": ["include-from-file", get_rel("sugarbeet.json")]
                },
                "residueParams": ["include-from-file", "crop-residues/beet.json"]
            }
        },
        "fert-params": {
            "UAS": ["include-from-file", "mineral-fertilisers/UAS.json"],
            "CADLM": ["include-from-file", "organic-fertilisers/CADLM.json"]
        },
        "cropRotation": [{"worksteps": worksteps}],
        "CropParameters": ["include-from-file", get_rel("crop.json")]
    }
    
   # save file
    save_path = os.path.join(project_dir, f'sugarbeet_run{i}', set_name)
    os.makedirs(save_path, exist_ok=True)
    
    output_file = os.path.join(save_path, "crop.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(crop_json_data, f, ensure_ascii=False, indent=4)
        
    # print(f"Crop JSON saved to: {output_file}")

# run monica
def run_monica(base_path, project_dir, set_name, i):
    
    monica_exe = os.path.join(base_path, "bin", "monica-run.exe")
    monica_params = os.path.join(base_path, "monica-parameters")  

    set_path = os.path.join(project_dir, f"sugarbeet_run{i}", set_name)
    sim_json = "sim.json"
    sim_out_csv = os.path.join(set_path, "sim-out.csv")

    if not os.path.exists(os.path.join(set_path, sim_json)):
        print(f"Error: sim.json not found in {set_path}")
        return

    # monica parameters environment
    env = os.environ.copy()
    env["MONICA_PARAMETERS"] = monica_params

    try:
        result = subprocess.run(
            [monica_exe, "-o", sim_out_csv, sim_json],
            check=True,
            capture_output=True,
            text=True,
            cwd=set_path,
            env=env 
        )
        # print(f"STDOUT: {result.stdout}")
        # print(f"STDERR: {result.stderr}")

    except subprocess.CalledProcessError as e:
        print(f"Simulation failed for {set_name} in Run {i}")
        # print(f"STDOUT: {e.stdout}")
        # print(f"STDERR: {e.stderr}")

     
#2) Objective function part

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
    
    sub_opt = os.path.join(project_dir_opt, f'sugarbeet_run{i}', set_name, 'sim-out.csv')
    sub_red = os.path.join(project_dir_red, f'sugarbeet_run{i}', set_name, 'sim-out.csv')

    try:
        
        sim_yld_opt, sim_yld_red = simulated_yield_data(sub_opt, sub_red)
        
       
        excluded_years = [2017] 

       
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