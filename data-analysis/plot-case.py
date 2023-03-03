import glob
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
import subprocess
import shutil
import cftime
import os

'''SET UP'''
source_dir = '/glade/u/home/marielj/clm_frost/'

#Cases to cycle through
dirs = glob.glob(source_dir + 'cesm_cases/stored-data/*', recursive = True)

#Strip the string to get case name
case_names = [string[55:] for string in dirs]

for case in case_names:
    print('Plotting case: ' + case)
    #Save directory for figures
    if(not os.path.exists(source_dir + 'data-analysis/figures/cases/%s' % case)):
        os.mkdir(source_dir + 'data-analysis/figures/cases/%s' % case)
    save_dir = source_dir + 'data-analysis/figures/cases/' + case + '/'

    #import full transient spinup data
    case_data = xr.open_mfdataset(source_dir + 'cesm_cases/stored-data/' + case + '/' + case + '.clm2.h1.*-01-01-00000.nc', 
                                 parallel = True)


    '''PLOT FUNCTIONS'''
    def plot_var(dataset, var, rolling = False):
        fig, ax = plt.subplots(figsize = (6,4))

        #Plot accelerated spinup data
        dataset[var].plot(linewidth = 1, alpha = 0.4, ax = ax, color = 'red')

        #Plot rolling average
        if(rolling):
            roll = dataset[var].rolling(time = 30).mean()
            plt.plot(dataset.time, roll, color = 'red', linewidth = 0.5)

        ax.set_title(dataset[var].long_name)
        ax.set_xlim(cftime.DatetimeNoLeap(2011, 1, 1, 0, 0, 0, 0, has_year_zero=True),
                       cftime.DatetimeNoLeap(2017, 12, 31, 0, 0, 0, 0, has_year_zero=True))

        plt.savefig(save_dir + str(var) + '.pdf', bbox_inches = 'tight')
        plt.show()

    '''PLOTS'''
    vars_to_plot = ['H2OSNO', 'QINFL', 'QRUNOFF', 'QSNOMELT', 'QSOIL', 'QVEGT', 'RAIN', 'SNOW', 'TSA', 'ZWT']

    for v in vars_to_plot:
        plot_var(case_data, v)
        
    print('Case plotted')