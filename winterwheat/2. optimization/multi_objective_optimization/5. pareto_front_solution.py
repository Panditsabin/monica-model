import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import dill as pickle


from monica_run_postprocess import (
    map_parameters, update_parameter_files, site_json, crop_json, run_monica, 
    simulated_yield_data, extract_irr_data, extract_moist_data)

from post_process import read_optimization_result

def run_pareto_simulations(X_pareto, param_names,
    base_path, parameter_dir,
    project_dir_opt, project_dir_red,
    cultivar_file, species_file, crop_general_file, sim_file,
    irr_opt, fert_opt, crp_opt,
    irr_red, fert_red, crp_red,
    sim_start, sim_end,
    set_name,
    excluded_yrs):

    # store data
    all_yield_opt, all_yield_red = [], []
    all_irr_opt, all_irr_red = [], []

    for idx, x_params in enumerate(X_pareto):

        run_set_name = f"run_{idx}" 

        try:
            
            param_update = map_parameters(x_params, param_names, run_set_name)

            update_parameter_files(
                base_path, param_update, parameter_dir, project_dir_opt,
                cultivar_file, species_file, crop_general_file,
                sim_file, sim_start, sim_end, condition="opt"
            )

            update_parameter_files(
                base_path, param_update, parameter_dir, project_dir_red,
                cultivar_file, species_file, crop_general_file,
                sim_file, sim_start, sim_end, condition="red"
            )

            # opt mgmt
            crop_json(base_path, irr_opt, fert_opt, crp_opt,
                      sim_start, sim_end, project_dir_opt, parameter_dir, run_set_name)
            site_json(base_path, project_dir_opt, run_set_name)

            
            # RED MGMT
            crop_json(base_path, irr_red, fert_red, crp_red,
                      sim_start, sim_end, project_dir_red, parameter_dir, run_set_name)
            site_json(base_path, project_dir_red, run_set_name)

           # monica run
            run_monica(base_path, project_dir_opt, run_set_name)
            run_monica(base_path, project_dir_red, run_set_name)

        
            for condition, project_dir in zip(
                ["opt", "red"], [project_dir_opt, project_dir_red]
            ):

                sim_out_csv = os.path.join(
                                    project_dir, run_set_name, "sim-out.csv"
                                    )

                if not os.path.exists(sim_out_csv):
                    continue

                # YLD
                df_yield = simulated_yield_data(sim_out_csv)
                df_yield = df_yield[~df_yield['Year'].isin(excluded_yrs)]
                series_yield = df_yield.set_index('Year')['Sim_yield']
                series_yield.name = f"run_{idx}"

                # irr
                df_irr = extract_irr_data(sim_out_csv)
                df_irr = df_irr[~df_irr['Year'].isin(excluded_yrs)]
                series_irr = df_irr.set_index('Year')['Sim_irrig']
                series_irr.name = f"run_{idx}"

                
                if condition == "opt":
                    all_yield_opt.append(series_yield)
                    all_irr_opt.append(series_irr)
                else:
                    all_yield_red.append(series_yield)
                    all_irr_red.append(series_irr)

        except Exception as e:
            print(f"Error in Pareto run {idx}: {e}")
            continue

    
    yield_opt_df = pd.concat(all_yield_opt, axis=1) if all_yield_opt else pd.DataFrame()
    yield_red_df = pd.concat(all_yield_red, axis=1) if all_yield_red else pd.DataFrame()

    irr_opt_df = pd.concat(all_irr_opt, axis=1) if all_irr_opt else pd.DataFrame()
    irr_red_df = pd.concat(all_irr_red, axis=1) if all_irr_red else pd.DataFrame()

    return yield_opt_df, yield_red_df, irr_opt_df, irr_red_df

# plotting function
def plot_ensemble_condition(ax, df_sim, df_obs, color, title, split_year=2018):

    # mean
    mean_series = df_sim.mean(axis=1)

    # merge
    merged = pd.concat(
        [mean_series.rename("Sim"), df_obs.iloc[:, 0].rename("Obs")],
        axis=1
    ).dropna()

    
    df_sim = df_sim.loc[merged.index]

    # band
    lower = df_sim.quantile(0.1, axis=1)
    upper = df_sim.quantile(0.9, axis=1)

    ax.fill_between(merged.index, lower, upper,
                    color=color, alpha=0.25, label='10–90% range')

    # pareto mean
    ax.plot(merged.index, merged["Sim"],
            color=color, linewidth=3, marker='s',
            label='Simulated (Mean)')

    # obs
    ax.plot(merged.index, merged["Obs"],
            color='black', linewidth=2, marker='o',
            label='Observed')

    # val
    if split_year is not None:
        ax.axvline(x=split_year, color='magenta', linestyle='--', linewidth=2)

    # rmse
    rmse = np.sqrt(np.mean((merged["Sim"] - merged["Obs"])**2)) if not merged.empty else np.nan

    # title
    ax.set_title(f"{title} | RMSE: {rmse:.3f}", fontsize=13)
    ax.set_ylabel(ax.get_ylabel() or "")
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper left')
    

# plotting
if __name__ == '__main__':

    base_path = r'C:\Users\Pandit\Desktop\monica'

    # opt mgmt
    irr_opt = os.path.join(base_path, r'magagement_data\winterwheat_optimal\optimal_irrigation.xlsx')
    crop_rot_opt = os.path.join(base_path, r'magagement_data\winterwheat_optimal\crop_mgmt_WW.xlsx')
    fert_opt = os.path.join(base_path, r'magagement_data\winterwheat_optimal\fertilizer.xlsx')
    
    # red mgmt
    irr_red = os.path.join(base_path, r'magagement_data\winterwheat_reduced\reduced_irrigation.xlsx')
    crop_rot_red = os.path.join(base_path, r'magagement_data\winterwheat_reduced\crop_mgmt_WW.xlsx')
    fert_red = os.path.join(base_path, r'magagement_data\winterwheat_reduced\fertilizer.xlsx')

    # obs
    obs_yield_opt  = os.path.join(base_path, r"field_obs_data\obs_yield_opt_condition.xlsx")
    obs_yield_red  = os.path.join(base_path, r"field_obs_data\obs_yield_red_condition.xlsx")

    man_irr_opt = os.path.join(base_path, r"field_obs_data\wheat_irr_opt_condition.xlsx")
    man_irr_red = os.path.join(base_path, r"field_obs_data\wheat_irr_red_condition.xlsx")

    # param
    para_df = pd.read_excel(
        os.path.join(base_path, r'sensitive_paras\wheat_yld_sm_sens_para.xlsx')
    )
    param_names = para_df["parameter_name"].str.strip().tolist()

    # params file
    cult_f = os.path.join(base_path, r"monica-parameters\crops\wheat\winter-wheat.json")
    spec_f = os.path.join(base_path, r"monica-parameters\crops\wheat.json")
    gen_f  = os.path.join(base_path, r"monica-parameters\general\crop.json")
    sim_f  = os.path.join(base_path, r'projects\calibration\sim.json')

    # sim period
    sim_start, sim_end = '2007-09-01', '2020-12-31'
    
    # parameters and simulation file will be saved inside this folder
    set_name = "pareto_eval"

    parameter_dir = os.path.join(base_path, r'monica-parameters\wheat_3objs', set_name)
    project_dir_opt = os.path.join(base_path, r'projects\wheat_3objs_opt', set_name)
    project_dir_red = os.path.join(base_path, r'projects\wheat_3objs_red', set_name)

    result_path = os.path.join(base_path, r'projects\wheat_3objs_result')

    
    i = 0
    result_data = read_optimization_result(result_path, i)

    X_pareto = result_data.X
    
    excluded_yrs = [2007,2012]

    
    yield_opt, yield_red, irr_opt_df, irr_red_df = run_pareto_simulations(
        X_pareto=X_pareto,
        param_names=param_names,
        base_path=base_path,
        parameter_dir=parameter_dir,
        project_dir_opt=project_dir_opt,
        project_dir_red=project_dir_red,
        cultivar_file=cult_f,
        species_file=spec_f,
        crop_general_file=gen_f,
        sim_file=sim_f,
        irr_opt=irr_opt,
        fert_opt=fert_opt,
        crp_opt=crop_rot_opt,
        irr_red=irr_red,
        fert_red=fert_red,
        crp_red=crop_rot_red,
        sim_start=sim_start,
        sim_end=sim_end,
        set_name=set_name,
        excluded_yrs=excluded_yrs)

    
    # yld
    df_obs_yield_opt = pd.read_excel(obs_yield_opt, sheet_name="WinterWheat")
    df_obs_yield_opt.columns = ["Year", "Obs"]
    df_obs_yield_opt = df_obs_yield_opt.set_index("Year")

    df_obs_yield_red = pd.read_excel(obs_yield_red, sheet_name="WinterWheat")
    df_obs_yield_red.columns = ["Year", "Obs"]
    df_obs_yield_red = df_obs_yield_red.set_index("Year")

    # irr
    df_obs_irr_opt = pd.read_excel(man_irr_opt)
    df_obs_irr_opt.columns = ["Year", "Obs"]
    df_obs_irr_opt = df_obs_irr_opt.set_index("Year")

    df_obs_irr_red = pd.read_excel(man_irr_red)
    df_obs_irr_red.columns = ["Year", "Obs"]
    df_obs_irr_red = df_obs_irr_red.set_index("Year")

    
    fig, axes = plt.subplots(4, 1, figsize=(12, 18))

    # yld opt
    axes[0].set_ylabel("Yield (tDM/ha)")
    plot_ensemble_condition(
        axes[0], yield_opt, df_obs_yield_opt,
        "blue", "Optimal Condition - Yield"
    )

    # yld red
    axes[1].set_ylabel("Yield (tDM/ha)")
    plot_ensemble_condition(
        axes[1], yield_red, df_obs_yield_red,
        "red", "Reduced Condition - Yield"
    )

    # irr opt
    axes[2].set_ylabel("Irrigation (mm)")
    plot_ensemble_condition(
        axes[2], irr_opt_df, df_obs_irr_opt,
        "blue", "Optimal Condition - Irrigation"
    )

    # irr red 
    axes[3].set_ylabel("Irrigation (mm)")
    plot_ensemble_condition(
        axes[3], irr_red_df, df_obs_irr_red,
        "red", "Reduced Condition - Irrigation"
    )

    axes[3].set_xlabel("Year")

    plt.suptitle(
        "Pareto Ensemble Analysis\nWinter Wheat (Yield & Irrigation)",
        fontsize=14, fontweight='bold'
    )

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    plt.show()