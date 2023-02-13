#!/usr/bin/env cesm
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 13 09:50:00 2023
Modifying CLM code to test parameter sensitivity. For now this will run without spinup. When the spin up issues are solved, the 
parameter adjustements will be made in between the prespinup (AD) and the spinup.

@author: M.W. Jones
"""

import os
import glob
import subprocess
import shutil

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr

'''Parameters'''
#Dictionary containing params and their test values
#params = {}

PARAM = 'SLOPEBETA' #One of 'slopebeta', 'mu', 'baseflow'

'''Case Setup'''
#Source Root - Where the CESM code lives
SRCROOT_DIR = '/glade/u/home/marielj/cesm2.1.3'
#CIME Root - Where the CIME code lives, i.e. where the create_newcase scripts are
CIMEROOT_DIR = '/glade/u/home/marielj/cesm2.1.3/cime'
#Case Root - Where all the CESM cases are stored
CASEROOT_DIR = '/glade/u/home/marielj/clm-frost/cesm_cases/mbp-tuning'
#User Mods Dir - Where the surface and domain files are
USER_MODS_DIR = '/glade/u/home/marielj/cesm2.1.3/components/clm/tools/PTCLM/mydatafiles/1x1pt_US-MBP'
#Forcing Data Root - Where the atmospheric forcing data is
CLMFORC_DIR = '/glade/u/home/marielj/inputdata/atm/datm7/CLM1PT_data'

os.chdir(CIMEROOT_DIR + '/scripts')

CASE_NAME = 'mbp_tuning_nospinup_' + PARAM + '_v' + '0' # + str(i) - will eventually loop through values
CASE_DIR = CASEROOT_DIR + '/' + CASE_NAME
COMPSET = '2000_DATM%1PT_CLM50%SP_SICE_SOCN_MOSART_SGLC_SWAV'  #I1PtClm50SpGs

subprocess.check_output(['./create_newcase',
                            '--case=%s' % CASE_DIR,
                            '--compset=%s' % COMPSET,
                            '--user-mods-dir=%s' % USER_MODS_DIR,
                            '--res=CLM_USRDAT', 
                            '--project=UMIN0008', 
                            '--run_unsupported'])

os.chdir(CASE_DIR)

'''Set up case'''
pipe = subprocess.Popen(['./case.setup'], stdout=subprocess.PIPE)
result = pipe.communicate()[0]
print (result)

'''Change XML'''

#General
subprocess.check_output(['./xmlchange', 'DATM_MODE=CLM1PT'])
subprocess.check_output(['./xmlchange', 'CLM_FORCE_COLDSTART=off'])
subprocess.check_output(['./xmlchange', 'CONTINUE_RUN=FALSE'])

#Calendar
subprocess.check_output(['./xmlchange', 'CALENDAR=NO_LEAP'])

#Run start date
subprocess.check_output(['./xmlchange', 'RUN_STARTDATE=2011-01-01'])

#Align with tower data
subprocess.check_output(['./xmlchange', 'DATM_CLMNCEP_YR_ALIGN=2011'])
subprocess.check_output(['./xmlchange', 'DATM_CLMNCEP_YR_START=2011'])
subprocess.check_output(['./xmlchange', 'DATM_CLMNCEP_YR_END=2017'])

#Stop options
subprocess.check_output(['./xmlchange', 'STOP_OPTION=nyears'])
subprocess.check_output(['./xmlchange', 'STOP_N=7'])

#Set Forcing data directory
subprocess.check_output(['./xmlchange', 'DIN_LOC_ROOT_CLMFORC=%s' % CLMFORC_DIR])

#History files
file_name = 'user_nl_clm'
f = open(file_name, 'w')
f.write(" hist_nhtfrq = 0,-24\n hist_mfilt  = 1200,365\n hist_fincl2 = 'RAIN', 'H2OSNO', 'QSOIL', 'QVEGT', 'QSNOMELT', 'QRUNOFF', 'ZWT', 'ZWT_PERCH', 'SNOW', 'TSA', 'SOILICE', 'QINFL'")
f.close()


'''Make Parameter Change'''


'''Run Simulation'''
pipe = subprocess.Popen(['qcmd -- ./case.build'], stdout=subprocess.PIPE)
result = pipe.communicate()[0]
print (result)

'''Check Output'''

