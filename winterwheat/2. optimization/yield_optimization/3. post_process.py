# -*- coding: utf-8 -*-
"""
Created on Wed Aug 20 15:00:55 2025

@author: Pandit
"""
import dill as pickle
import os
import matplotlib.pyplot as plt
import numpy as np

import pandas as pd

# pareto parameters 
def pareto_parameter(para_df, result_path, i):
    """
    Returns Pareto front parameter sets as a DataFrame.
    """
    result = read_optimization_result(result_path, i)
    var = result.X
    params_name = para_df['parameter_name'].to_list()
    
    df_opt_para = pd.DataFrame(var, columns=params_name)
    df_opt_para['set_name'] = [f"set_" + str(i) for i in range(len(df_opt_para))]
    
    return df_opt_para

# load opt result
def read_optimization_result(result_path, i):
    """
    Loads and returns the saved optimization result from a pickle file.
    """
    out_file_path = os.path.join(result_path, f'optimization_result_set{i}.pkl')
    with open(out_file_path, 'rb') as file:
        result = pickle.load(file)
        
    return result

# objective convergence plot
def converg(result_path, i):
    res = read_optimization_result(result_path, i)
    n_gen = len(res.history)
    fitness = [h.opt.get("F")[0] for h in res.history]
    plt.plot(range(n_gen), fitness)
    plt.title(f"Convergence Set {i}")
    plt.xlabel("Generation")
    plt.ylabel("RMSE")
    plt.show()

# parameter convergance
def variable_convergance(result_path, i, para_df):
    """Plots mean and standard deviation of each parameter across generations to assess convergence."""
    result = read_optimization_result(result_path, i)
    his_x = [gen.pop.get('X') for gen in result.history]
    n_gen = len(his_x)
    
    # para names
    vars_name = para_df['parameter_name'].to_list()
    n_vars = len(para_df)
    
    mean_values = []
    std_values = []
    
    for gen_data in his_x:
        mean_values.append(np.mean(gen_data, axis=0))
        std_values.append(np.std(gen_data, axis=0))
    
    mean_values = np.array(mean_values)  # Shape: (n_gen, n_var)
    std_values = np.array(std_values)    # Shape: (n_gen, n_var)
    
    n_cols = 5
    n_rows = int(np.ceil(n_vars / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 6, n_rows * 4), constrained_layout=True)
    
    axes = axes.flatten()
    
    for var_idx in range(n_vars):
        ax = axes[var_idx]
    
        means       = mean_values[:, var_idx]
        stds        = std_values[:, var_idx]
        generations = np.arange(1, n_gen + 1)
    
        ax.plot(generations, means, color='blue', lw=2, label='Population Mean')
        ax.fill_between(generations, means - stds, means + stds, color='lightblue', alpha=0.4, label='Mean ± 1 std. dev.')
    
        ax.set_title(f"Parameter: {vars_name[var_idx]}", fontsize=12)
        ax.set_ylabel("Value", fontsize=10)
        ax.set_xlabel("Generation", fontsize=10)
        ax.set_xticks(np.insert(np.arange(5, n_gen + 1, 5), 0, 1))
        ax.tick_params(axis='x')
    
        lower_bound = para_df['lower_limit'].values[var_idx]
        upper_bound = para_df['upper_limit'].values[var_idx]
        ax.axhline(y=lower_bound, color='gray', linestyle='--', label=f'Lower ({lower_bound:.2f})')
        ax.axhline(y=upper_bound, color='gray', linestyle='--', label=f'Upper ({upper_bound:.2f})')
    
        ax.legend(fontsize=8)
        ax.grid(True, linestyle='--', alpha=0.6)

    # hide unused subplots
    for ax_idx in range(n_vars, len(axes)):
        axes[ax_idx].set_visible(False)
    
    plt.suptitle("Parameter Convergence Across Generations", fontsize=14)
    plt.show()