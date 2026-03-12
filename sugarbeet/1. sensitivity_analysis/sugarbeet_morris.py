# -*- coding: utf-8 -*-
"""
Created on Fri Dec 19 12:10:51 2025

@author: Pandit
"""

from collections import defaultdict
import os
import json
import uuid
import pandas as pd
import numpy as np
import subprocess
import re

# Map the parameters
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


                
# change parameters values/ update parameter files
def update_parameter_files(param_update, parameter_dir, project_dir, cultivar_file, species_file,  crop_general_file, sim_file, sim_start, sim_end):
    """Updates parameter files based on generated parameter sets."""
    
    
    source_files = {
        "CultivarParameters": cultivar_file,
        "SpeciesParameters": species_file,
        "UserCropParameters": crop_general_file,
        "Simulation": sim_file
    }
    
    
    for set_name, updates in param_update.items():
        para_out_path = os.path.join(parameter_dir, set_name)
        sim_out_path = os.path.join(project_dir, set_name)
    
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
                # Scalar parameters
                scalar_keys_species = [
                    'AssimilateReallocation', 'DefaultRadiationUseEfficiency', 'InitialRootingDepth', 
                    'MaxNUptakeParam', 'LimitingTemperatureHeatStress', 'MinimumTemperatureForAssimilation',
                    'NConcentrationAbovegroundBiomass', 'NConcentrationPN', 'RootDistributionParam', 'RootFormFactor'
                ]
                for param in scalar_keys_species:
                    if param in updates:
                        data[param] = updates[param]
                
                # Array parameters
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


# crops dictionary
def crop_dict(species_file, cultivar_file,
             species_file_dry, cultivar_file_dry):
    return {
        "ZR": {
            "is-winter-crop": False,
            "cropParams": {
                "species": ["include-from-file", str(species_file)],
                "cultivar": ["include-from-file", str(cultivar_file)]
            },
            "residueParams": ["include-from-file", "crop-residues/beet.json"]
        }
    }
# determines crop type from the input file
def get_crop_type(worksteps):
    crop_types = set()
    for ws in worksteps:
        if ws.get('type') in ['Sowing', 'Harvesting']:
            crop = ws.get('crop')
            if isinstance(crop, list) and len(crop) > 2:
                crop_types.add(crop[2])
    return crop_types
        
        
# creates full crop json file
def crop_json_file(worksteps, species_file, cultivar_file, species_file_dry, cultivar_file_dry, generalcrop_file):
    crops = crop_dict(species_file, cultivar_file, species_file_dry, cultivar_file_dry)
    crop_type = get_crop_type(worksteps)

    # crop dict
    crops_in_file = {}
    for crop in crop_type:
        crops_in_file[crop] = crops[crop]
        general_crop_file_to_use = str(generalcrop_file)
   
    crop_json = {
        'crops': crops_in_file,
        "__user defined fertilizer parameteres section to be used via references": "",
        "fert-params": {
            "UAS": ["include-from-file", "mineral-fertilisers/UAS.json"],
            "CADLM": ["include-from-file", "organic-fertilisers/CADLM.json"]
        },
        "cropRotation": [{"worksteps": worksteps}],
        "__general crop parameters for the monica model": "",
        "CropParameters": ["include-from-file", general_crop_file_to_use]
    }

    return crop_json

def crop_worksteps(irr_data_path, fert_data_path, crp_data_path, sim_start, sim_end):
    """
    Generates a sorted list of agricultural work steps with date as string (YYYY-MM-DD) between the simulation period.

    """

    # Management files
    irrigation_data = pd.read_excel(irr_data_path)
    irrigation_data['date'] = pd.to_datetime(irrigation_data['date'])
    irrigation_data = irrigation_data[irrigation_data['date'].between(sim_start, sim_end)]
    
    fertilization_data = pd.read_excel(fert_data_path)
    fertilization_data['date'] = pd.to_datetime(fertilization_data['date'])
    fertilization_data = fertilization_data[fertilization_data['date'].between(sim_start, sim_end)]
    
    crop_data = pd.read_excel(crp_data_path)
    crop_data['sowing'] = pd.to_datetime(crop_data['sowing'])
    crop_data['harvesting'] = pd.to_datetime(crop_data['harvesting'])
    crop_data = crop_data[(crop_data['sowing'] >= sim_start) & (crop_data['harvesting'] <= sim_end)]
        
    worksteps = []

    if irrigation_data is not None and not irrigation_data.empty:
        for _, items in irrigation_data.iterrows():
            worksteps.append({
                "date": items["date"].strftime('%Y-%m-%d'),
                "type": "Irrigation",
                "amount": [float(items["amount"]), "mm"],
                "parameters": {
                    "nitrateConcentration": [0.0, "mg dm-3"],
                    "sulfateConcentration": [0.0, "mg dm-3"]
                }
            })

    for _, items in crop_data.iterrows():
        worksteps.append({
            "date": items["sowing"].strftime('%Y-%m-%d'),
            "type": "Sowing",
            "crop": ["ref", "crops", items['type']]
        })

    for _, items in crop_data.iterrows():
        worksteps.append({
            "date": items["harvesting"].strftime('%Y-%m-%d'),
            "type": "Harvesting",
            "crop": ["ref", "crops", items['type']]
        })

    for _, items in fertilization_data.iterrows():
        worksteps.append({
            "date": items["date"].strftime('%Y-%m-%d'),
            "type": "MineralFertilization",
            "amount": [float(items["amount"]), "kg N"],
            "partition": ["ref", "fert-params", "UAS"]
        })

    worksteps = sorted(worksteps, key=lambda x: x['date'])

    return worksteps   


def new_crop_json_files(irr_data_path, fert_data_path, crp_data_path, sim_start, sim_end, project_dir, parameter_dir, set_name):
   
    set_path = os.path.join(parameter_dir, set_name)   
    if not os.path.isdir(set_path):
        return
    
    till_monica = r'C:\Users\Pandit\Desktop\monica_win64_3.6.32.toth_ser_TUA\monica-parameters'
    species = os.path.join(set_path, "sugar-beet.json")
    species_dry = os.path.join(set_path, "dry_sugar-beet.json")
    species_file = os.path.relpath(species, till_monica).replace("\\", "/")
    species_file_dry = os.path.relpath(species_dry, till_monica).replace("\\", "/")
    
        
    cultivar = os.path.join(set_path, "sugarbeet.json")
    cultivar_dry = os.path.join(set_path, "dry_sugarbeet.json")
    cultivar_file = os.path.relpath(cultivar, till_monica).replace("\\", "/")
    cultivar_file_dry = os.path.relpath(cultivar_dry, till_monica).replace("\\", "/")
        
    general = os.path.join(set_path, "crop.json")
    generalcrop_file = os.path.relpath(general, till_monica).replace("\\", "/")
        
    worksteps = crop_worksteps(irr_data_path, fert_data_path, crp_data_path, sim_start, sim_end)
    crop_json = crop_json_file(worksteps, species_file, cultivar_file,species_file_dry, cultivar_file_dry, generalcrop_file)
    
    #saving files
    set_project_path = os.path.join(project_dir, set_name)
    os.makedirs(set_project_path, exist_ok=True)
    
    crop_json_path = os.path.join(set_project_path, "crop.json")
    with open(crop_json_path, "w", encoding="utf-8") as json_file:
        json.dump(crop_json, json_file, ensure_ascii=False, indent=4)

    #print(f"Saved crop.json for {set_name} in {set_project_path}")
    

# monica run
def run_monica(project_dir, set_name):
    monica_exe = r"C:\Users\Pandit\Desktop\monica_win64_3.6.32.toth_ser_TUA\bin\monica-run.exe"
    set_path = os.path.join(project_dir, set_name)
    sim_json = os.path.join(set_path, 'sim.json')
    sim_out_csv = os.path.join(set_path, 'sim-out.csv')

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
        
        
# simulated yearly yield value
def simulated_yield_data(sim_out_csv_path):
    
    sim_df = pd.read_csv(sim_out_csv_path, low_memory=False, sep=',', skiprows=1, header=[0,1])
    sim_df.columns = [
        col[0] if 'Unnamed' in col[1] else re.sub(r'[\[\]]', '', ' '.join(col)).strip()
        for col in sim_df.columns.values
    ]

    sim_df['Date'] = pd.to_datetime(sim_df['Date'])

    # only October 27
    date_filtered_df = sim_df[
        (sim_df['Date'].dt.month == 10) & (sim_df['Date'].dt.day == 27)
    ].copy()

    #  yield values for Oct 27 each year 
    simulated_yield = (
        date_filtered_df.groupby(date_filtered_df['Date'].dt.year)['Yield kgDM ha-1']
        .max()
        .reset_index()
    )

    # Convert to tDM/ha
    simulated_yield['Yield (tDM/ha)'] = simulated_yield['Yield kgDM ha-1'] / 1000
    simulated_yield = simulated_yield.drop(columns='Yield kgDM ha-1')
    simulated_yield.columns = ["Year", "Yield (tDM/ha)"]

    return simulated_yield


# function to extract the sim soil moisture data simulated
def extract_moist_data(sim_out_csv):
    moist_df = pd.read_csv(sim_out_csv, skiprows = 1, header = [0,1])
    moist_df.columns = [
                        col[0] if 'Unnamed' in col[1] else re.sub(r'\[\]', '', ' '.join(col)).strip()
                        for col in moist_df.columns.values]
        
    moist_df = moist_df.drop(columns = ['Yield [kgDM ha-1]', 'Irrig [mm]'])
    moist_df['avg_moist_30'] = moist_df[['Mois_1 [m3 m-3]', 'Mois_2 [m3 m-3]', 'Mois_3 [m3 m-3]']].mean(axis = 1)
        
    moist_data = moist_df[['Date', 'avg_moist_30']]
    moist_data = moist_data.copy()
    moist_data['Date'] = pd.to_datetime(moist_data['Date'])
    return moist_data


# function to extract the sim irrigation data simulated
def extract_irr_data(sim_out_csv):
    irr_df = pd.read_csv(sim_out_csv, skiprows = 1, header = [0,1])
    irr_df.columns = [
                        col[0] if 'Unnamed' in col[1] else re.sub(r'\[\]', '', ' '.join(col)).strip()
                        for col in irr_df.columns.values]
        
    irr_df = irr_df.drop(columns = ['Yield [kgDM ha-1]', 'Mois_1 [m3 m-3]', 'Mois_2 [m3 m-3]', 'Mois_3 [m3 m-3]'])
    irr_df["Date"] = pd.to_datetime(irr_df['Date'])
    irr_data = irr_df.groupby(irr_df['Date'].dt.year)['Irrig [mm]'].sum().reset_index()
    irr_data.columns = ['Year', 'sim_irr']
    return irr_data