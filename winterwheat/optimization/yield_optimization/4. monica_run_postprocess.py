# -*- coding: utf-8 -*-
"""
Created on Fri Aug 29 12:15:18 2025

@author: Pandit
"""
# libraries

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

# 2. Update parameter files 
def update_parameter_files(param_update, parameter_dir, project_dir, cultivar_file, species_file,  crop_general_file, sim_file, sim_start, sim_end, i):
    """Updates parameter files based on generated parameter sets for Winter Wheat."""
    
    source_files = {
        "CultivarParameters": cultivar_file,
        "SpeciesParameters": species_file,
        "UserCropParameters": crop_general_file,
        "Simulation": sim_file
    }
    
    # folder names
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
            if not os.path.exists(file_path): continue
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
    
            if parameter_file == "UserCropParameters":
                scalar_keys = ["MaintenanceRespirationParameter1", "MaintenanceRespirationParameter2", "MaxCropNDemand"]
                for param in scalar_keys:
                    if param in updates: data[param] = updates[param]            
    
            elif parameter_file == "SpeciesParameters":
                scalar_keys_species = ['NConcentrationPN']
                for param in scalar_keys_species:
                    if param in updates: data[param] = updates[param]
                
                array_keys_species = ["BaseTemperature"]
                for param in array_keys_species:
                    if param in updates:
                        for idx, value in updates[param].items():
                            if idx < len(data[param]): data[param][idx] = value
    
            elif parameter_file == "CultivarParameters":
                
                if "LeafSenescenceRate_s5" in updates: data["OrganSenescenceRate"][4][1] = updates["LeafSenescenceRate_s5"]
                if "LeafSenescenceRate_s6" in updates: data["OrganSenescenceRate"][5][1] = updates["LeafSenescenceRate_s6"]

                cultivar_params = ["BeginSensitivePhaseHeatStress", "MaxAssimilationRate", "BaseDaylength", 
                                   "DaylengthRequirement", "SpecificLeafArea", "StageTemperatureSum"]
                
                for param in cultivar_params:
                    if param not in updates: continue 
                    if param in ["BeginSensitivePhaseHeatStress", "MaxAssimilationRate"]:
                        data[param] = updates[param]
                    elif param in ["BaseDaylength", "DaylengthRequirement", "SpecificLeafArea", "StageTemperatureSum"]:
                        target_list = data[param][0]
                        for idx, val in updates[param].items():
                            if idx < len(target_list): target_list[idx] = val

            elif parameter_file == "Simulation":
                if sim_start: data["climate.csv-options"]["start-date"] = sim_start
                if sim_end: data["climate.csv-options"]["end-date"] = sim_end

            # Wheat specific file mapping
            file_map = {
                "SpeciesParameters": "wheat.json",
                "CultivarParameters": "winter-wheat.json",
                "UserCropParameters": "crop.json",
                "Simulation": "sim.json"
            }

            output_file = os.path.join(sim_out_path if parameter_file == "Simulation" else para_out_path, file_map[parameter_file])
            with open(output_file, 'w', encoding='utf-8') as outfile:
                json.dump(data, outfile, ensure_ascii=False, indent=4)



def crop_worksteps(irr_data_path, fert_data_path, crp_data_path, sim_start, sim_end):
    """
    Generates a sorted list of agricultural work steps (Irrigation, 
    Fertilization, Sowing, Harvesting) between sim_start and sim_end.
    """
    sim_start = pd.to_datetime(sim_start)
    sim_end = pd.to_datetime(sim_end)
    worksteps = []

    # 1. Irrigation
    if irr_data_path and os.path.exists(irr_data_path):
        irr_df = pd.read_excel(irr_data_path)
        irr_df['date'] = pd.to_datetime(irr_df['date'])
        irr_df = irr_df[irr_df['date'].between(sim_start, sim_end)]
        for _, row in irr_df.iterrows():
            worksteps.append({
                "date": row["date"].strftime('%Y-%m-%d'),
                "type": "Irrigation",
                "amount": [float(row["amount"]), "mm"],
                "parameters": {"nitrateConcentration": [0.0, "mg dm-3"], "sulfateConcentration": [0.0, "mg dm-3"]}
            })

    # 2. Fertilization
    if fert_data_path and os.path.exists(fert_data_path):
        fert_df = pd.read_excel(fert_data_path)
        fert_df['date'] = pd.to_datetime(fert_df['date'])
        fert_df = fert_df[fert_df['date'].between(sim_start, sim_end)]
        for _, row in fert_df.iterrows():
            worksteps.append({
                "date": row["date"].strftime('%Y-%m-%d'),
                "type": "MineralFertilization",
                "amount": [float(row["amount"]), "kg N"],
                "partition": ["ref", "fert-params", "UAS"]
            })

    # 3. sowing and harvesting
    if crp_data_path and os.path.exists(crp_data_path):
        crp_df = pd.read_excel(crp_data_path)
        crp_df['sowing'] = pd.to_datetime(crp_df['sowing'])
        crp_df['harvesting'] = pd.to_datetime(crp_df['harvesting'])
        crp_df = crp_df[(crp_df['sowing'] >= sim_start) & (crp_df['harvesting'] <= sim_end)]
        for _, row in crp_df.iterrows():
            worksteps.append({
                "date": row["sowing"].strftime('%Y-%m-%d'),
                "type": "Sowing",
                "crop": ["ref", "crops", row['type']]
            })
            worksteps.append({
                "date": row["harvesting"].strftime('%Y-%m-%d'),
                "type": "Harvest",
                "crop": ["ref", "crops", row['type']]
            })

    # sorting
    return sorted(worksteps, key=lambda x: x['date'])


# 3. crop mgmt
def crop_json(irr_path, fert_path, crp_path, sim_start, sim_end, project_dir, parameter_dir, set_name, i):
    set_param_path = os.path.join(parameter_dir, f'wheat_run{i}', set_name)
    if not os.path.isdir(set_param_path): return
    base_monica = r'C:\Users\Pandit\Desktop\monica\monica-parameters'
    
    def get_rel(filename):
        return os.path.relpath(os.path.join(set_param_path, filename), base_monica).replace("\\", "/")

    worksteps = crop_worksteps(irr_path, fert_path, crp_path, sim_start, sim_end)
    
    crop_json_data = {
        'crops': {
            "WW": { # Changed to WW
                "is-winter-crop": True, # Winter crop set to True
                "cropParams": {
                    "species": ["include-from-file", get_rel("wheat.json")],
                    "cultivar": ["include-from-file", get_rel("winter-wheat.json")]
                },
                "residueParams": ["include-from-file", "crop-residues/wheat.json"]
            }
        },
        "fert-params": {
            "UAS": ["include-from-file", "mineral-fertilisers/UAS.json"],
            "CADLM": ["include-from-file", "organic-fertilisers/CADLM.json"]
        },
        "cropRotation": [{"worksteps": worksteps}],
        "CropParameters": ["include-from-file", get_rel("crop.json")]
    }
    
    save_path = os.path.join(project_dir, f'wheat_run{i}', set_name)
    os.makedirs(save_path, exist_ok=True)
    with open(os.path.join(save_path, "crop.json"), "w", encoding="utf-8") as f:
        json.dump(crop_json_data, f, ensure_ascii=False, indent=4)
        
        
def run_monica(project_dir, set_name, i):
    """
    Executes the MONICA simulation via subprocess.
    """
    monica_exe = r"C:\Users\Pandit\Desktop\monica\bin\monica-run.exe"
    
    # Construct paths consistent with your 'wheat_run{i}' folders
    subfolder = os.path.join(project_dir, f'wheat_run{i}')
    set_path = os.path.join(subfolder, set_name)
    sim_json = os.path.join(set_path, 'sim.json')
    sim_out_csv = os.path.join(set_path, 'sim-out.csv')

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
        print(f"Simulation failed for {set_name}: {e.stderr}")        
        



def process_yield_file(file_path):
    """
    Reads MONICA sim-out.csv (skipping 'daily' header).
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
    