'''Imports'''

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
import pandas as pd
import xarray as xr
from bayes_opt import BayesianOptimization
from bayes_opt import UtilityFunction
import time
import seaborn as sns
from itertools import product
from scipy.interpolate import interp2d
import scipy.stats

#ML
from sklearn.gaussian_process import GaussianProcessRegressor 

'''LOAD CALIBRATION DATA'''
dt2 =pd.read_csv('Streamflow_daily.csv', 
                 parse_dates=['Date'])

# Coerce the data into the types specified in the metadata  
dt2.Watershed = dt2.Watershed.astype('category') 

# Pull out 2017 year
stream = dt2[(dt2.Date.dt.year == 2015)]
stream = stream[stream.Watershed == 'S2'].reset_index(drop = True)


#Convert cm/day to mm/sec
m = 10/(60*60*24)
stream['Flow_mms'] = m*stream['Flow (cm/day)']

'''CLM CASE SETUP'''
from clmmodtools import *

#setup case
CASE_NAME = 'testing_bayesopt_nobuild_derecho_single'
setup_mef_case('/glade/u/home/marielj/clm_frost/cesm_cases/bayesopt', CASE_NAME, MODS = True, nyears = 7)
CASE_DIR = '/glade/u/home/marielj/clm_frost/cesm_cases/bayesopt/testing_bayesopt_nobuild_derecho_single'


'''FUNCTION SETUP'''
def rsquared(x, y):
    slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x, y)
    return r_value**2

def blackbox_clm(fff):
    #change parameter in netcdf file
    target_param_file = '/glade/work/marielj/inputdata/lnd/clm2/paramdata/clm5_params_augmented_base.c171117.nc'
    pft = 12 #arctic grass  
    
    #PFT Params
    #change_pft_param('slatop', pft, slatop, target_param_file)
    #change_pft_param('leaf_long', pft, leaflong, target_param_file)
    #change_pft_param('froot_leaf', pft, frootleaf, target_param_file)
    
    #NON PFT Params
    #change_param('slopebeta', slopebeta, target_param_file)
    change_param('fff', fff, target_param_file)    
    
    os.chdir(CASE_DIR)
    
    #Namelist Params
    #change_nl_param('soil_fmax', fmax)
    #change_nl_param('baseflow_scalar', baseflow)
    
    #run case
    pipe = subprocess.Popen(['./case.submit'], stdout=subprocess.PIPE)
    #result = pipe.communicate()[0]
    #print(result)
    #print(CASE_NAME + " Run Complete")
    
    #time delay -- check if archived data exists, if not wait 5 more seconds
    SCRATCH_DIR = '/glade/derecho/scratch/marielj/archive/' + CASE_NAME + '/lnd/hist/'
    while(not os.path.exists(SCRATCH_DIR + CASE_NAME + '.clm2.h1.2015-01-01-00000.nc')):
        time.sleep(5)
    
    #find WTE data in scracth directory
    os.chdir(SCRATCH_DIR)
    
    #Open data h1 data file
    dat = xr.load_dataset(CASE_NAME + '.clm2.h1.2015-01-01-00000.nc')
    #mean_wtd = -np.mean(dat.ZWT.values) For WTE comparison
    stream_mod = dat.QRUNOFF.values.reshape(365)

    #Calculate correlation
    R = rsquared(stream.Flow_mms.values, stream_mod)
    
    #remove data
    os.remove(CASE_NAME + '.clm2.h1.2015-01-01-00000.nc')
    
    #return average annual WTE
    #return mean_wtd

    #return R2
    return R

'''SAVE PROGRESS'''
from bayes_opt.logger import JSONLogger
from bayes_opt.event import Events

clm_optimizer = BayesianOptimization(
    f = blackbox_clm,
    pbounds = {'fff': (0.1, 5)},
    random_state = 7,
)

#logger object records optimization search
logger = JSONLogger(path="/glade/u/home/marielj/clm_frost/clm-runscripts/logs/clm_logs_single_fff.json", reset = False)
clm_optimizer.subscribe(Events.OPTIMIZATION_STEP, logger)


#Aquisition function
acquisition_function = UtilityFunction(kind = "ucb", kappa = 10e2)

'''RUN OPTIMIZATION'''
clm_optimizer.maximize(init_points = 10, n_iter = 20,
                       aquisition_function = acquisition_function,
                       allow_duplicate_points = True)


'''PLOT PROGRESS'''
#for p in ['slatop', 'leaflong', 'frootleaf', 'slopebeta', 'fff', 'baseflow', 'fmax']:
#    x = [res["params"][p] for res in clm_optimizer.res]
    
#    fig, ax = plt.subplots(1, 1, figsize = (8,1))
#    plt.eventplot(x, orientation='horizontal', colors='b', alpha = 0.4)
#    plt.axis('off')
#    plt.suptitle(p)
#    plt.savefig('/glade/u/home/marielj/clm_frost/cesm_cases/bayesopt/figures/param_' + p + 'redBase.pdf')