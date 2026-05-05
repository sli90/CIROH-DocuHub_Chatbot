# File: nextgen_calibration_utils.py

import os
import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import spotpy
from spotpy.parameter import Uniform

# Ensure dataretrieval is installed
try:
    from dataretrieval import nwis
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "dataretrieval"])
    from dataretrieval import nwis

from update_parameters import update_cfe_parameters  # user-defined module
from pyngiab import PyNGIAB  # model wrapper

# === Utility Function to Retrieve and Preprocess USGS Streamflow ===
def process_usgs_streamflow(site, start, end, output_path=None):
    start = pd.to_datetime(start) - pd.Timedelta(days=1)
    end = pd.to_datetime(end) + pd.Timedelta(days=1)
    adjusted_start = start.strftime('%Y-%m-%d')
    adjusted_end = end.strftime('%Y-%m-%d')

    dfo_usgs = nwis.get_record(sites=site, service='iv', start=adjusted_start, end=adjusted_end)
    dfo_usgs.index = pd.to_datetime(dfo_usgs.index)
    dfo_usgs['Time'] = dfo_usgs.index.floor('h')
    dfo_usgs['00060'] = pd.to_numeric(dfo_usgs['00060'], errors='coerce')
    dfo_usgs_hr = dfo_usgs.groupby('Time')['00060'].mean().reset_index()
    dfo_usgs_hr['values'] = dfo_usgs_hr['00060'] / 35.3147
    dfo_usgs_hr = dfo_usgs_hr[['Time', 'values']]
    if output_path:
        dfo_usgs_hr.to_pickle(output_path)
    return dfo_usgs_hr


# === Wrapper to Set Up NextGen Model Execution ===
class NextGenSetup:
    def __init__(self, gage_id, start_date, end_date, training_start_date, observed_flow_path, troute_output_path, cfe_dir):
        self.gage_id = gage_id
        self.training_start_date = pd.to_datetime(training_start_date)
        self.end_date = pd.to_datetime(end_date)
        self.observed = pd.read_pickle(observed_flow_path)
        self.observed['Time'] = pd.to_datetime(self.observed['Time']).dt.tz_localize(None)
        self.observed = self.observed[(self.observed['Time'] >= self.training_start_date) &
                                      (self.observed['Time'] <= self.end_date)]
        self.observed = self.observed.set_index('Time')
        self.troute_output_path = troute_output_path
        self.cfe_parameters_directory_path = cfe_dir

    def write_config(self, params):
        param_map = {
            'soil_params.depth': params[0], 'refkdt': params[1],
            'max_gw_storage': params[2], 'Cgw': params[3], 'expon': params[4],
            'gw_storage': params[5], 'alpha_fc': params[6],
            'soil_storage': params[7], 'K_nash': params[8], 'K_lf': params[9],
        }
        if param_map['Cgw'] > param_map['gw_storage']:
            return np.full_like(self.observed.values.squeeze(), np.nan)
        update_cfe_parameters(self.cfe_parameters_directory_path, param_map)

    def run_model(self, data_dir):
        #model = PyNGIAB(data_dir, serial_execution_mode=True)
        model = PyNGIAB(data_dir)
        model.run()

    def evaluate(self, feature_id):
        ds = xr.open_dataset(self.troute_output_path)
        simulated = ds['flow'].sel(feature_id=feature_id).values
        simulated = simulated[ds['time'] >= self.training_start_date]
        simulated = simulated[:len(self.observed) - 1]
        return simulated


# === SPOTPY Setup Class for Calibration ===
class SpotpySetup:
    soil_params_depth = Uniform(1.0, 3.0)
    refkdt = Uniform(1.0, 5.0)
    max_gw_storage = Uniform(0.005, 0.9)
    Cgw = Uniform(0.0005, 0.01)
    expon = Uniform(1.0, 7.0)
    gw_storage = Uniform(0.01, 0.3)
    alpha_fc = Uniform(0.1, 0.5)
    soil_storage = Uniform(0.05, 0.4)
    K_nash = Uniform(0.01, 0.1)
    K_lf = Uniform(0.005, 0.05)

    def __init__(self, model_setup, data_dir, feature_id):
        self.model = model_setup
        self.data_dir = data_dir
        self.feature_id = feature_id
        self.run_id = 0
        self.best_like = -np.inf
        self.best_run = -1

        # Ensure spotpy directory exists
        self.output_dir = "/home/jovyan/spotpy"
        os.makedirs(self.output_dir, exist_ok=True)

    def simulation(self, vector):
        self.model.write_config(vector)
        self.model.run_model(self.data_dir)
        return self.model.evaluate(self.feature_id)

    def evaluation(self):
        return self.model.observed.values.squeeze()[1:]

    def objectivefunction(self, simulation, evaluation):
        kge = self.kling_gupta_efficiency(simulation, evaluation)

        # Plot each calibration iteration
        plt.figure(figsize=(10, 4))
        plt.plot(evaluation, label='Observed', color='black')
        plt.plot(simulation, label='Simulated', linestyle='--')
        plt.text(0.5, 0.9, f'KGE: {kge:.2f}', transform=plt.gca().transAxes, fontsize=12)
        plt.legend()
        plt.title(f'CFE-NOM-TR Streamflow for Gage {self.model.gage_id} - Run {self.run_id}')
        plt.xlabel('Time step')
        plt.ylabel('Streamflow [m3/sec]')
        plt.savefig(f'{self.output_dir}/spotpy_run_{self.run_id}.png')
        plt.close()

        if kge > self.best_like:
            self.best_like = kge
            self.best_run = self.run_id

        self.run_id += 1
        return kge

    def kling_gupta_efficiency(self, sim, obs):
        sim = np.nan_to_num(np.array(sim))
        obs = np.nan_to_num(np.array(obs))
        if np.std(obs) == 0 or np.std(sim) == 0:
            return -np.inf
        r = np.corrcoef(sim, obs)[0, 1]
        alpha = np.std(sim) / np.std(obs)
        beta = np.mean(sim) / np.mean(obs)
        return 1 - np.sqrt((r - 1)**2 + (alpha - 1)**2 + (beta - 1)**2)

'''
def run_spotpy_mpi(gage_id, start_date, end_date, training_start_date,
                   observed_flow_path, troute_output_path, cfe_dir,
                   data_dir, feature_id, repetitions=25):
    #from ipyparallel import Cluster
    # Initialize MPI
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    if rank == 0:
        print(f"Running with {comm.Get_size()} MPI processes")
        pass

    # run simulation
    run_spotpy(gage_id, start_date, end_date, training_start_date,
               observed_flow_path, troute_output_path, cfe_dir,
               data_dir, feature_id, repetitions)
    
    if rank == 0:
        print("Optimization complete")
        #best_params = spotpy.analyser.get_best_parameterset(
        #    sampler.getdata(), maximize=False
        #)
        #print("Best parameters:", best_params)
    
        results = spotpy.analyser.load_csv_results(f"spotpy_results_{gage_id}")
        best_params = spotpy.analyser.get_best_parameterset(results, maximize=False)

        # Plot objective function trace
        fig = plt.figure(1, figsize=(9, 5))
        plt.plot(results['like1'])
        plt.ylabel('KGE')
        plt.xlabel('Iteration')
        fig.savefig('/home/jovyan/spotpy/SCEUA_objectivefunctiontrace.png', dpi=300)
    
        # Plot best model run
        bestindex, bestobjf = spotpy.analyser.get_minlikeindex(results)
        best_model_run = results[bestindex]
        fields = [word for word in best_model_run.dtype.names if word.startswith('sim')]
        best_simulation = list(best_model_run[fields])
        time_index = pd.date_range(start=training_start_date, periods=len(best_simulation), freq='D')
    
        fig = plt.figure(figsize=(16, 9))
        ax = plt.subplot(1, 1, 1)
        ax.plot(time_index, best_simulation, color='black', linestyle='solid', label='Best objf.=' + str(bestobjf))
        ax.plot(time_index, setup.evaluation(), 'r.', markersize=3, label='Observation data')
        plt.xlabel('Date')
        plt.ylabel('Streamflow (m3/sec)')
        plt.legend(loc='upper right')
        fig.savefig('/home/jovyan/spotpy/SCEUA_best_modelrun.png', dpi=300)
    
        # print("\nBest parameter set:")
        # for name, value in zip(setup.parameters()[0], best_params[1:-1]):
        #     print(f"{name}: {value}")
    
        print(f"Best objective function value: {setup.best_like}")
        print(f"Best run ID: {setup.best_run}")
    
        return best_params
    
    pass
'''
# === Function to Run SPOTPY Calibration ===
def run_spotpy(gage_id, start_date, end_date, training_start_date,
               observed_flow_path, troute_output_path, cfe_dir,
               data_dir, feature_id, repetitions=25):
    
    model_setup = NextGenSetup(gage_id, start_date, end_date, training_start_date,
                               observed_flow_path, troute_output_path, cfe_dir)
    setup = SpotpySetup(model_setup, data_dir, feature_id)


    sampler = spotpy.algorithms.sceua(setup, dbname=f"spotpy_results_{gage_id}", dbformat="csv")
    # MPI version
    #sampler = spotpy.algorithms.sceua(setup, 
    #                                  dbname=f"spotpy_results_{gage_id}", 
    #                                  dbformat="csv", 
    #                                  parallel='mpi'
    #                                 )
    sampler.sample(repetitions, ngs=20)

    results = spotpy.analyser.load_csv_results(f"spotpy_results_{gage_id}")
    best_params = spotpy.analyser.get_best_parameterset(results, maximize=False)

    print(f"Best objective function value: {setup.best_like}")
    print(f"Best run ID: {setup.best_run}")
    
    return results, best_params

def plot_spotpy_results(results, training_start_date):
    # Plot objective function trace
    fig = plt.figure(1, figsize=(9, 5))
    plt.plot(results['like1'])
    plt.ylabel('KGE')
    plt.xlabel('Iteration')
    fig.savefig('/home/jovyan/spotpy/SCEUA_objectivefunctiontrace.png', dpi=300)

    # Plot best model run
    bestindex, bestobjf = spotpy.analyser.get_minlikeindex(results)
    best_model_run = results[bestindex]
    fields = [word for word in best_model_run.dtype.names if word.startswith('sim')]
    best_simulation = list(best_model_run[fields])
    time_index = pd.date_range(start=training_start_date, periods=len(best_simulation), freq='D')

    fig = plt.figure(figsize=(16, 9))
    ax = plt.subplot(1, 1, 1)
    ax.plot(time_index, best_simulation, color='black', linestyle='solid', label='Best objf.=' + str(bestobjf))
    ax.plot(time_index, setup.evaluation(), 'r.', markersize=3, label='Observation data')
    plt.xlabel('Date')
    plt.ylabel('Streamflow (m3/sec)')
    plt.legend(loc='upper right')
    fig.savefig('/home/jovyan/spotpy/SCEUA_best_modelrun.png', dpi=300)

    # print("\nBest parameter set:")
    # for name, value in zip(setup.parameters()[0], best_params[1:-1]):
    #     print(f"{name}: {value}")