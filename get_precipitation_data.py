import argparse
import json
import glob
from datetime import datetime, timedelta
import dateutil.parser
import pandas as pd
import numpy as np
import xarray as xr
import plotly.graph_objects as go
# local
from countries import countries

GEOMETRY = None
CC = countries.CountryChecker('500cities/cities.shp')
PLACES = [
    { 'city': 'New Orleans', 'state': 'LA' },
    { 'city': 'Houston', 'state': 'TX' },
    { 'city': 'Baltimore', 'state': 'MD' },
    { 'city': 'Norfolk', 'state': 'VA' },
    { 'city': 'Seattle', 'state': 'WA' },
    { 'city': 'Portland', 'state': 'OR' }
]

def within_area(latlon):
    global GEOMETRY
    lat = float(latlon[0])
    lon = float(latlon[1])
    # longitude values in the data are from 0 to 360
    # but longitude values in the shapefile are -180 to 180
    if lon > 180:
        lon = lon - 360
    # find the shapefile region that this point is inside of
    # area = CC.getCountry(countries.Point(lat, lon))
    point = CC.getPoint(lat, lon)
    contained = GEOMETRY.Contains(point)
    if contained:
        return True
    else:
        return False

def filter_data(dataset):
    global GEOMETRY

    df = dataset.to_dataframe()
    df = df.loc[:,['time','tp']]

    df_us = df.sort_index(level=0)

    latvals = df_us.index.get_level_values('latitude')
    lonvals = df_us.index.get_level_values('longitude')

    # initialize values
    minlat = 90
    maxlat = -90
    minlon = 180
    maxlon = -180
    buf = json.loads(GEOMETRY.ExportToJson())
    for coord in buf['coordinates'][0]:
        lon = coord[0]
        lat = coord[1]
        if lat < minlat:
            minlat = lat
        if lat > maxlat:
            maxlat = lat
        if lon < minlon:
            minlon = lon
        if lon > maxlon:
            maxlon = lon

    # print(minlat, maxlat, minlon, maxlon)

    # convert longitude to 0-360 range
    if minlon < 0:
        minlon += 360
    if maxlon < 0:
        maxlon += 360

    # print(minlat, maxlat, minlon, maxlon)

    # latitude filter
    latfilter = ((latvals >= minlat) & (latvals <= maxlat))
    # longitude filter
    lonfilter = ((lonvals >= minlon) & (lonvals <= maxlon))
    # apply filters to the dataframe
    df_us = df_us.loc[latfilter & lonfilter]

    # add another boolean column to our data
    # which we can then filter on to delete unwanted rows
    df_us['inArea'] = df_us.index.map(within_area)

    # national filter
    df_us = df_us[df_us['inArea'] != False]

    # reset lat and lon vals based on filtered dataframe
    latvals = df_us.index.get_level_values('latitude')
    lonvals = df_us.index.get_level_values('longitude')

    # step = 0.75
    # to_bin = lambda x: np.floor(x/step)*step
    to_bin = lambda x: x
    df_us["latbin"] = latvals.map(to_bin)
    df_us["lonbin"] = lonvals.map(to_bin)
    # df_us['time'] = '2020-04-07'

    df_flat = df_us.drop_duplicates(subset=['latbin','lonbin'])

    df_no_nan = df_flat[np.isfinite(df_flat['tp'])]
    df_viz = df_no_nan.loc[:, ['latbin','lonbin','tp']]

    return df_viz

def visualize(df_viz, mapbox_token):

    df_viz['tp'] = df_viz['tp'] * 0.0393701 # conversion from mm to in
    # max_precip = 6 # limiting the highest daily precipitation for coloring plot
    # df_viz['tp'][df_viz['tp'] >= max_precip] = max_precip 
    # df_viz.tail(20)

    # colorscale = [[0.0, '#171c42'], [0.07692307692307693, '#263583'], [0.15384615384615385, '#1a58af'], [0.23076923076923078, '#1a7ebd'], [0.3076923076923077, '#619fbc'], [0.38461538461538464, '#9ebdc8'], [0.46153846153846156, '#d2d8dc'], [0.5384615384615384, '#e6d2cf'], [0.6153846153846154, '#daa998'], [0.6923076923076923, '#cc7b60'], [0.7692307692307693, '#b94d36'], [0.8461538461538461, '#9d2127'], [0.9230769230769231, '#6e0e24'], [1.0, '#3c0911']]

    # https://github.com/plotly/plotly.js/blob/5bc25b490702e5ed61265207833dbd58e8ab27f1/src/components/colorscale/scales.js
    colorscale = [
        [0, 'rgb(5,10,172)'],
        [0.35, 'rgb(40,60,190)'],
        [0.5, 'rgb(70,100,245)'],
        [0.6, 'rgb(90,120,245)'],
        [0.7, 'rgb(106,137,247)'], # fades out into:
        [1, 'rgba(255,255,255,0.05)'] # white nearly invisible
    ]

    val_min = df_viz['tp'].min()
    val_max = df_viz['tp'].max()
    # print(val_max, val_min)

    data = []

    # https://images.plot.ly/plotly-documentation/images/python_cheat_sheet.pdf?_ga=2.113218049.441476779.1587291103-1421256715.1585761166
    data.append(
        go.Scattermapbox(
            lon=df_viz['lonbin'].values,
            lat=df_viz['latbin'].values,
            mode='markers',
            text=df_viz['tp'].values,
            marker=go.Marker(
                cmax=val_max,
                cmin=val_min,
                color=df_viz['tp'].values,
                colorscale=colorscale,
                reversescale=True,
                showscale = True,
                opacity = 0.65
        
            ),
        )
    )

    layout = go.Layout(
        margin=dict(t=0,b=0,r=0,l=0),
        autosize=True,
        hovermode='closest',
        showlegend=True,
        mapbox=dict(
            accesstoken=mapbox_token,
            bearing=0,
            center=dict(
                lat=45,
                lon=-122
            ),
            pitch=0,
            zoom=4,
            style='dark'
        ),
    )

    fig = go.Figure(data=data, layout=layout)
    fig.show()

    # print out how long this script run took
    ending = datetime.now()
    print('Ending:', ending)
    print()
    print('Elapsed:', ending - starting)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mapbox_token', help='the CSV file to inspect')
    args = parser.parse_args()

    starting = datetime.now()
    print('Starting:', starting)

    all_means = {}
    all_data = pd.DataFrame()

    filenames = glob.glob('forecast/*.grib2')
    filenames = sorted(filenames)

    previous_time_data = {}

    for filename in filenames:
        DATASET = xr.open_dataset(
            filename,
            engine='cfgrib'
        )

        dataframes = []
        means = {}

        for p in PLACES:
            city = p['city']
            # get the city feature from the shapefile
            feature = CC.getFeature(city, p['state'])
            # get the centroid point of the city feature
            centroid = feature.geometry().Centroid()
            # create a 1-degree buffer around the centroid
            GEOMETRY = centroid.Buffer(1)
            # filter the weather data to the buffer region
            accum_df = filter_data(DATASET)
            # make a new copy of the dataframe
            df = accum_df.copy(deep=True )
            # convert from accumulated value
            if city in previous_time_data:
                df['tp'] = df['tp'] - previous_time_data[city]['tp']
            else:
                previous_time_data[city] = {}
            # store the accumulated values to substract from the next time's data
            previous_time_data[city]['tp'] = accum_df['tp']
            # ditch the latbin and lonbin columns
            df.drop(columns=['latbin', 'lonbin'])
            # store the result
            dataframes.append(df)
            # print some statistics
            val_min = df['tp'].min()
            val_max = df['tp'].max()
            val_mean = df['tp'].mean()
            val_stdev = df['tp'].std()
            # print()
            # print(city)
            # print("max: " + str(val_max))
            # print("min: " + str(val_min))
            # print("mean: " + str(val_mean))
            # print("stdev: " + str(val_stdev))
            means[city] = str(val_mean)
            # save the city area to GeoJSON
            city = city.replace(' ', '_')
            with open('areas_geojson/' + city + '.geojson', 'w') as outfile:
                outfile.write(feature.ExportToJson())

        # convert filename to datetime object
        hours = int(filename[-9:-6])
        date = filename[15:23]
        dt = dateutil.parser.parse(date) + timedelta(hours=hours)
        # convert datetime object to string
        forecast_time = str(dt)
        # store the city averages for this time
        all_means[forecast_time] = means
        # combine all city data into one dataframe
        dataframe = pd.concat(dataframes)
        dataframe['time'] = forecast_time
        dataframe = dataframe.loc[:, ['tp','time']]
        all_data = pd.concat([all_data, dataframe])
        # export the combined cities dataframe to CSV, named by time
        dataframe.to_csv('precip_data/' + forecast_time + '.csv')

    with open('means/means.js', 'w') as outfile:
        outfile.write('var AVERAGES = ' + json.dumps(all_means, indent=4) + ';')

    # ALL DATA
    all_data['precip'] = all_data['tp']
    all_data = all_data.loc[:, ['precip','time']]
    all_data.to_csv('precip_data/COMBINED.csv')

    # visualize(dataframe, args.mapbox_token)
