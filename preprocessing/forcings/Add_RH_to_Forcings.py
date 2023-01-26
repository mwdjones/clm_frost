#%%
import pandas as pd 
import numpy as np
import datetime as dt
import xarray as xr
import cftime
import dask
from glob import glob

#%%
'''SUBSET RH DATA'''

data = pd.read_csv("preprocessing/inputdata/AMF_US-MBP_BASE_HH_2-5.csv", 
    skiprows = 2, 
    na_values = -9999)

data['TIMESTAMP_START'] = pd.to_datetime(data.TIMESTAMP_START, format = '%Y%m%d%H%M')
data['TIMESTAMP_END'] = pd.to_datetime(data.TIMESTAMP_END, format = '%Y%m%d%H%M')

data = data.rename(columns = {'TIMESTAMP_START':'TIMESTAMP'})

'''
#TRY EDI Data          
data = pd.read_csv('preprocessing/inputdata/BogLake_Met_data_30min.csv', skiprows = 1, sep = ",", 
    names=["TIMESTAMP", "Air_TempC_Avg", "RH", "Soil_TempC_5cm", "Soil_TempC_10cm", "Soil_TempC_20cm",     
            "Soil_TempC_30cm", "Soil_TempC_40cm", "Soil_TempC_50cm", "Soil_TempC_100cm",  "Soil_TempC_200cm",     
            "WS_Tot",  "WindDir_D",  "WindDir_SD",  "PAR_Den_Avg"],
    parse_dates = ['TIMESTAMP'],
    na_values = {'RH':['NA',]})
'''


# Subset to the right variables 
RH = data[['TIMESTAMP', 'RH']]

# Sort into Year-Month combos
RH['Year'] = RH.TIMESTAMP.dt.year
RH['Month'] = RH.TIMESTAMP.dt.month
RH['Year-Month'] = RH.TIMESTAMP.dt.strftime('%Y') + '-' + RH.TIMESTAMP.dt.strftime('%m')

#Subset to proper years
RH = RH[(RH.Year > 2010) & (RH.Year < 2018)]

#Patch long NA period in August 2017 with data from the NADP site in the EDI data
patch_data = pd.read_csv('preprocessing/inputdata/NADP_Met_data_30min.csv', skiprows = 1, sep = ",", 
    names=["TIMESTAMP", "Air_TempC_Avg", "RH", "Soil_TempC_Avg", "WS_Tot", "WindDir_D", "WindDir_SD", "PAR_Den_Avg", "Soil_VWC_Avg"],
    parse_dates = ['TIMESTAMP'],
    na_values = {'RH':['NA',]})

RH_patch = patch_data[['TIMESTAMP', 'RH']]
RH_patch = RH_patch[(RH_patch.TIMESTAMP.dt.year == 2017) & (RH_patch.TIMESTAMP.dt.month == 8)]



# %%
'''OPEN ALL NCDF DATA'''

vals = set(RH['Year-Month'])

for val in vals:
    #Open sample data set
    test = xr.open_mfdataset(val + '.nc', decode_times = False)

    #Select RH data:
    if val == '2017-08':
        test_RH = RH_patch
    else:
        test_RH = RH[RH['Year-Month'] == val]

    #Subset netdcf spatially 
    test2 = test.drop_sel(lon = 1)

    #If leap Feb and leap year remove Feb29 data
    r = test_RH['RH']
    if (val.endswith('02')) & (len(r) > len(test2.time)):
        #remove feb 9
        r = r[:len(test2.time)]

    #print(val + ": " + str(min(r)))

    #print("NEW" + val + ": " + str(min(r)))

    # Interpolate
    r3 = pd.Series(r).interpolate(method = "linear")

    print("NAN" + val + ": " + str(any(np.isnan(r3))))

    #Reshape
    r4 = np.reshape(list(r3),(-1,1,1))

    #Add RH Data
    test2['RH'] = xr.DataArray(r4, 
        dims = ['time', 'lat', 'lon'], 
        attrs = {'FillValue': np.NaN, 
                'long_name': 'relative humidity at the lowest atm level (RH)',
                'units': '%' })

    #Write sample
    test2.to_netcdf('preprocessin/forcings-modified' + val + '.nc')
    

# %%
'''CHECK'''
#Open file to check
dat = xr.open_mfdataset('preprocessing/forcings-modified/2017-08.nc')
# %%
