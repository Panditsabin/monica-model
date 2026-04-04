# -*- coding: utf-8 -*-
"""
Created on Wed Aug 20 15:00:55 2025

@author: Pandit
"""
import dill as pickle
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pymoo.indicators.hv import Hypervolume
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

# 3d and 2d plot
def analyze_pareto(result_path, i):
    """
    Plots the Pareto front in 3D and 2D for the three objectives: yield, soil moisture, and irrigation RMSE.
    """
    result = read_optimization_result(result_path, i)
    
    obj = result.F
    var = result.X
    
    # three objectives
    x = obj[:,0]
    y = obj[:,1]
    z = obj[:,2]
    

    # 1. 3D plot
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot
    scatter = ax.scatter(x, y*100, z, marker = "o", color = "blue", label = "Pareto Front")
    
    ax.set_title('Pareto Front - Yield vs Soil Moisture vs Irrigation RMSE')
    ax.set_xlabel('Yield RMSE (tDM/ha)')
    ax.set_ylabel('Soil Moisture RMSE (%)')
    ax.set_zlabel('Irrigation RMSE (mm)')
    plt.legend()
    plt.tight_layout()
    #plt.savefig(r'C:\Users\Pandit\Desktop\wheat new\sameparametersthrought\3dpareto_plot.png', dpi = 300)
    plt.show()
    
    # 2D plot
    fig, ax = plt.subplots(nrows = 2, ncols = 1, figsize=(12, 6))

    ax[0].scatter(x, y*100, facecolors='none', edgecolors='blue', label = 'Pareto Front')
    ax[0].set_title('Optimal Solutions Yield vs Soil Moisture')
    ax[0].set_xlabel('Yield RMSE (tDM/ha)')
    ax[0].set_ylabel('Soil Moisture RMSE (%)')
    ax[0].legend(loc='best')
    
    # Second subplot 
    ax[1].scatter(z, y*100, facecolors='none', edgecolors='green',label = 'Pareto Front')
    ax[1].set_title('Optimal Solutions Soil Moisture vs Irrigation)')
    ax[1].set_xlabel('Irrigation RMSE (mm)')
    ax[1].set_ylabel('Soil Moisture RMSE (%)')
    ax[1].legend(loc='best')
    
    
    plt.tight_layout()
    #plt.savefig(r'C:\Users\Pandit\Desktop\wheat new\sameparametersthrought\2dpareto_plot.png', dpi = 300)
    plt.show()  

# hyper volume
def hypervolume_analysis(result_path, i):
    """ 
    Plots hypervolume convergence across generations.
    """
    result = read_optimization_result(result_path, i)
        
    n_evals = np.array([e.evaluator.n_eval for e in result.history])
    obj = result.F

    # objs result in each gen
    hist_F = []
    for gen in result.history:
        f = gen.opt.get('F')
        hist_F.append(f)
    
    # worst and best result
    ideal_F = obj.min(axis = 0)
    nadir_F = obj.max(axis = 0)
    
    # hyper volume calculation
    metrics = Hypervolume(
        ref_point = np.array([1.0, 1.0, 1.0]),
        norm_ref_point = False,
        ideal = ideal_F,
        nadir = nadir_F,
        zero_to_one = True 
    )
    
    hvs = [metrics.do(_F) for _F in hist_F if len(_F) > 0]
    
    # plot
    plt.figure(figsize=(12, 5))
    plt.plot(n_evals, hvs,  color='black', lw=0.7, label="Algorithm Performance")
    plt.scatter(n_evals, hvs,  facecolor="none", edgecolor='black', marker="p")
    plt.title(f"Convergence Set_{i}")
    plt.xlabel("Function Evaluations")
    plt.ylabel("Hypervolume")
    plt.tight_layout()
    #plt.savefig(r'C:\Users\Pandit\Desktop\wheat new\sameparametersthrought\Convergence_Hypervolume_Plot.png', dpi = 300)
    plt.show()


def running_metric(result_path, i):
    """ 
    Plots the running metric to visualize objective improvement across generations.
    """
    result = read_optimization_result(result_path, i)
    from pymoo.util.running_metric import RunningMetricAnimation

    running = RunningMetricAnimation(delta_gen=5,
                            n_plots=5,
                            key_press=False,
                            do_show=True)
    
    for algorithm in result.history:
        running.update(algorithm)
        
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