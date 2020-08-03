import os
import sys
import glob
from osgeo.ogr import GetDriverByName
from datetime import datetime, timedelta
import dateutil.parser
import pandas as pd
import numpy as np
import xarray as xr
dir_path = os.path.dirname(os.path.realpath(__file__))
parent = os.path.join(dir_path, os.pardir)
sys.path.append(os.path.join(parent,'..'))
from utils_grib import coarse_geo_filter, precise_geo_filter
# Load the shapefile area
filename = os.path.join(dir_path, 'ukraine/ukraine.shp')
driver = GetDriverByName('ESRI Shapefile')
shpfile = driver.Open(filename)
AREA = shpfile.GetLayer()

# TMP_P0_L1_GLL0
# LHTFL_P0_L1_GLL0 
# SHTFL_P0_L1_GLL0 
# SPFH_P0_L103_GLL0
# TSOIL_P0_2L106_GLL0
# SOILW_P0_2L106_GLL0
# DSWRF_P8_L1_GLL0_acc
# USWRF_P8_L1_GLL0_acc
# DLWRF_P8_L1_GLL0_acc
# ULWRF_P8_L1_GLL0_acc
# ULWRF_P8_L8_GLL0_acc
# lv_DBLL0_l1
# lv_DBLL0_l0

def parse_data(ds):
    # Print information on data variables
    # print(ds.keys())
    # Rename the wind variables for clarity
    ds = ds.rename({'SOILW_P0_2L106_GLL0': 'soil_moisture'})
    # Get only the wind values to reduce the volume of data,
    # otherwise converting to a dataframe will take a long time
    ds = ds.get(['soil_moisture'])
    # Convert the xarray dataset to a dataframe
    df = ds.to_dataframe()
    # Get longitude values from index
    lons = df.index.get_level_values('lon_0')
    # Map longitude range from (0 to 360) into (-180 to 180)
    maplon = lambda lon: (lon - 360) if (lon > 180) else lon
    # Create new longitude and latitude columns in the dataframe
    df['longitude'] = lons.map(maplon)
    df['latitude'] = df.index.get_level_values('lat_0')
    df['depth'] = df.index.get_level_values('lv_DBLL0')
    # Perform an initial coarse filter on the global dataframe
    # by limiting the data to the area's bounding box,
    # thereby reducing the total processing time of the `precise_geo_filter`
    df = coarse_geo_filter(df, AREA)
    # Perform the precise filter to remove data outside of the shapefile area
    df = precise_geo_filter(df, AREA)
    # depth filter
    # # depth of 0 = '0-10cm'
    # # depth of 1 = '10-40cm'
    # # depth of 2 = '40-100cm'
    # # depth of 3 = '100-200cm'
    depthfilter = (df['depth'] == 0)
    # water filter (oceans and lakes have soil moisture 100% so we exclude those)
    waterfilter = (df['soil_moisture'] < 1)
    # Apply filters to the dataframe
    df = df.loc[depthfilter & waterfilter]
    return df

if __name__ == '__main__':

    all_data = pd.DataFrame()

    filenames = glob.glob('agricast/*.grib2')
    filenames = sorted(filenames)

    for filename in filenames:
        print('Processing ', filename)
        DATASET = xr.open_dataset(filename, engine='pynio')
        # filter the weather data to the buffer region
        dataframe = parse_data(DATASET)
        # # print some statistics
        # val_min = df['soil_moisture'].min()
        # val_max = df['soil_moisture'].max()
        # val_mean = df['soil_moisture'].mean()
        # val_stdev = df['soil_moisture'].std()
        # # print()
        # # print("max: " + str(val_max))
        # # print("min: " + str(val_min))
        # # print("mean: " + str(val_mean))
        # # print("stdev: " + str(val_stdev))

        # convert filename to datetime object
        hours = int(filename[-9:-6])
        date = filename[15:23]
        dt = dateutil.parser.parse(date) + timedelta(hours=hours)
        # convert datetime object to string
        forecast_time = str(dt)

        dataframe['time'] = forecast_time
        dataframe = dataframe.loc[:, ['latitude','longitude','soil_moisture','time']]
        all_data = pd.concat([all_data, dataframe])
        # export the combined dataframe to CSV, named by time
        dataframe.to_csv('ukraine_data/' + forecast_time + '.csv', index=False)

    # ALL DATA
    all_data = all_data.loc[:, ['latitude','longitude','soil_moisture','time']]
    all_data.to_csv('ukraine_data/COMBINED.csv', index=False)
