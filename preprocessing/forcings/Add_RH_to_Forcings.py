import pandas as pd 
import numpy as np
import datetime as dt

#Need to take in the compiled forcings from Spruce CLM and add the RH data from the Fluxnet site to the ncdf files

#Load Rh data from FLuxnet sites
RH = pd.read_csv("/MEF_Fluxnet/AMF_US-MBP_BASE_HH_2-5.csv", 
    skiprows = 2,
    parse_dates = ['TIMESTAMP_START', 'TIMESTAMP_END'], 
    format = '%Y%m%d%H%M'
    )