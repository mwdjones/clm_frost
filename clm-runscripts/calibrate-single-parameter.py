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

######
# Parameters
######

#Dictionary containing params and their test values (multipliers)
params = {'SLOPEBETA': [0, 1, 2, 3, 4], 
			'QDRAIPERCHMAX': [1e-9, 1e-7, 1e-5, 1e-3, 1e-1],
			'BASEFLOW': [10e-8, 10e-7, 10e-6, 10e-4, 10e-2, 1, 2]}

PARAM = 'SLOPEBETA' #One of 'slopebeta', 'qdraiperchmax', 'baseflow', 'control'

######
# Case Setup
######

#Source Root - Where the CESM code lives
SRCROOT_DIR = '/glade/u/home/marielj/cesm2.1.3'
#CIME Root - Where the CIME code lives, i.e. where the create_newcase scripts are
CIMEROOT_DIR = '/glade/u/home/marielj/cesm2.1.3/cime'
#Case Root - Where all the CESM cases are stored
CASEROOT_DIR = '/glade/u/home/marielj/clm_frost/cesm_cases/mbp-tuning'
#User Mods Dir - Where the surface and domain files are
USER_MODS_DIR = '/glade/u/home/marielj/cesm2.1.3/components/clm/tools/PTCLM/mydatafiles/1x1pt_US-MBP'
#Forcing Data Root - Where the atmospheric forcing data is
CLMFORC_DIR = '/glade/u/home/marielj/inputdata/atm/datm7/CLM1PT_data'
COMPSET = '2000_DATM%1PT_CLM50%SP_SICE_SOCN_MOSART_SGLC_SWAV'  #I1PtClm50SpGs

for i in range(0, len(params[PARAM])):
	CASE_NAME = 'mbp_tuning_nospinup_' + PARAM + '_v' + str(i) 
	CASE_DIR = CASEROOT_DIR + '/' + CASE_NAME
	
	#print(CASE_NAME)
	#print(params[PARAM][i])

	#Check if directory exists - if not, create new case
	if(not os.path.exists(CASE_DIR)):
		print('Case does not exist. Creating new case.')
		#Create case
		os.chdir(CIMEROOT_DIR + '/scripts')
		subprocess.check_output(['./create_newcase',
						'--case=%s' % CASE_DIR,
						'--compset=%s' % COMPSET,
						'--user-mods-dir=%s' % USER_MODS_DIR,
						'--res=CLM_USRDAT', 
						'--project=UMIN0008', 
						'--run-unsupported',
						'--handle-preexisting-dirs=r'])
        
	else:
		print('Case already exists.')

	os.chdir(CASE_DIR)

	######
	# Set up case
	######

	pipe = subprocess.Popen(['./case.setup'], stdout=subprocess.PIPE)
	result = pipe.communicate()[0]
	print(result)
	print('Setup complete')

	######
	# Change XML
	######

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
	f.write(" fsurdat = '/glade/u/home/marielj/cesm2.1.3/components/clm/tools/PTCLM/mydatafiles/1x1pt_US-MBP/surfdata_1x1pt_US-MBP_hist_16pfts_Irrig_CMIP6_simyr2000_c230123.nc'\n")
	f.write(" hist_nhtfrq = 0,-24\n")
	f.write(" hist_mfilt  = 1200,365\n")
	f.write(" hist_fincl2 = 'RAIN', 'H2OSNO', 'QSOIL', 'QVEGT', 'QSNOMELT', 'QRUNOFF', 'ZWT', 'ZWT_PERCH', 'SNOW', 'TSA', 'SOILICE', 'QINFL'\n")

	######
	# Make Parameter Change
	######

	if(PARAM == 'BASEFLOW'):
		#Can change this value easily in the namelist files
		f.write(" baseflow_scalar = " + str(params[PARAM][i]*1e-2))
		
	f.close()
	if(PARAM == 'SLOPEBETA'):
		#Copy user mods from directory to case directory -- DO NOT change the CLM_USER_MODS xml
		USR_MODS_DIR='/glade/u/home/marielj/clm_frost/cesm_cases/calibration-mods/' + CASE_NAME
		os.chdir(USR_MODS_DIR)
		
		shutil.copy2('initVerticalMod.F90', CASE_DIR + '/SourceMods/src.clm')
				
		#Check files made it
		if(os.path.exists(CASE_DIR + '/SourceMods/src.clm/initVerticalMod.F90')):
			print('Mods copied successfully.')
		
		os.chdir(CASE_DIR)
	if(PARAM == 'QDRAIPERCHMAX'):
		#Copy user mods from directory to case directory -- DO NOT change the CLM_USER_MODS xml
		USR_MODS_DIR='/glade/u/home/marielj/clm_frost/cesm_cases/calibration-mods/' + CASE_NAME
		os.chdir(USR_MODS_DIR)
		
		shutil.copy2('SoilHydrologyMod.F90', CASE_DIR + '/SourceMods/src.clm')
				
		#Check files made it
		if(os.path.exists(CASE_DIR + '/SourceMods/src.clm/SoilHydrologyMod.F90')):
			print('Mods copied successfully.')
		
		os.chdir(CASE_DIR)

	
	######
	# Run Simulation
	######
	
	#Clear run directory
	pipe = subprocess.Popen(['./case.build', '--clean-all'], stdout=subprocess.PIPE)

	#Build
	pipe = subprocess.Popen(['qcmd', '-- ./case.build'], stdout=subprocess.PIPE)
	result = pipe.communicate()[0]
	print(result)
	print(CASE_NAME + " Build Complete")

	#Run
	pipe = subprocess.Popen(['qcmd', '-- ./case.submit'], stdout=subprocess.PIPE)
	result = pipe.communicate()[0]
	print(result)
	print(CASE_NAME + " Run Complete")

	######
	# Store Output
	######

	#Make Save Folder
	#Check for directory
	if(not os.path.exists('/glade/u/home/marielj/clm_frost/cesm_cases/stored-data/%s' % CASE_NAME)):
		os.mkdir('/glade/u/home/marielj/clm_frost/cesm_cases/stored-data/%s' % CASE_NAME)
	
	SAVEPATH = '/glade/u/home/marielj/clm_frost/cesm_cases/stored-data/' + CASE_NAME
	SCRATCH_DIR = '/glade/scratch/marielj/' + CASE_NAME + '/run'
	FILE_NAME = '*' + '.h1.' + '*'

	#Check if history files have been saved, if not, save them -- not finding files
	os.chdir(SCRATCH_DIR)

	files = glob.glob(FILE_NAME)
	for file in files:
		if(not os.path.isfile(SAVEPATH + '/' + file)):
			shutil.copy2(file, SAVEPATH)
			print(file + " did not exist. Saved.")
		else:
			print(file + " already exists.")
	

