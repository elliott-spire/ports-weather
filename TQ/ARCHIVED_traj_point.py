"""
Read list of coordinate pairs and timestamps from CSV file input,
extract point values from GRIB files corresponding to the same time,
and export result into a new CSV.

Bilinear interpolation is performed on the data to obtain the point values if
the chosen location is not one of the grid points from the forecast fields.
"""
from __future__ import print_function
from datetime import datetime, timedelta
from pathlib import Path
import csv
import Nio

# Here we list the data fields for each bundle to know which data to extract
DEF_VARIABLES = {
    "basic": [
        "TMP_P0_L103_GLL0",  # Temperature, K
        "DPT_P0_L103_GLL0",  # Dew point temperature, K
        "RH_P0_L103_GLL0",  # Relative humidity, %
        "UGRD_P0_L103_GLL0",  # U-component of wind, m s-1
        "VGRD_P0_L103_GLL0",  # V-component of wind, m s-1
        "GUST_P0_L1_GLL0",  # Wind speed (gust), m s-1
        "PRMSL_P0_L101_GLL0",  # Pressure reduced to MSL, Pa
        "TCDC_P0_L200_GLL0",  # Total cloud cover, %
        "APCP_P8_L1_GLL0_acc",  # Total precipitation, kg m-2
    ],
    "maritime": [
        "HTSGW_P0_L101_GLL0",  # Significant height of combined wind waves and swell, m
        "WWSDIR_P0_L101_GLL0",  # Direction of combined wind waves and swell, degree true
        "MWSPER_P0_L101_GLL0",  # Mean period of combined wind waves and swell, s
        "UOGRD_P0_L1_GLL0",  # U-component of current, m s-1
        "VOGRD_P0_L1_GLL0",  # V-component of current, m s-1
        "WTMP_P0_L1_GLL0",  # Water temperature, K
    ],
}

# Build a dictionary row object for the output CSV
def create_row(issuance, time, lat, lon, name, long_name, value, units, bundle):
    return {
        "Forecast Issuance": issuance,
        "Valid Time": time,
        "Latitude": lat,
        "Longitude": lon,
        "Variable": name,
        "Name": long_name,
        "Value": value,
        "Units": units,
        "Bundle": bundle,
    }


# Write the data to an output CSV file
def write_output(filename, data):
    # Set the fieldnames for the output CSV
    headers = [
        "Forecast Issuance",
        "Valid Time",
        "Latitude",
        "Longitude",
        "Variable",
        "Name",
        "Value",
        "Units",
        "Bundle",
    ]
    # Write the extracted data to the output CSV
    with open("nwp-" + filename, "w") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=headers)
        writer.writeheader()
        for rows in data:
            writer.writerows(rows)


# Parse the datetime out of a grib2 filename,
# assuming it is in the following format:
# sof-d.20200317.t06z.0p125.basic.global.f000.grib2
def parse_datetime(filename):
    parts = filename.split(".")
    date = parts[1]
    year = int(date[0:4])
    month = int(date[4:6])
    day = int(date[6:8])
    # Strip `t` and `z` and parse the issuance time integer
    issuance_time = parts[2]
    issuance_time = int(issuance_time[1:3])
    # Strip `f` and parse the lead time integer
    lead_time = parts[-2]
    lead_time = int(lead_time[1:])
    # Combine issuance and lead times to get valid hours
    hours = issuance_time + lead_time
    valid_dt = datetime(year, month, day) + timedelta(hours=hours)
    issuance_dt = datetime(year, month, day) + timedelta(hours=issuance_time)
    return issuance_dt, valid_dt


# Extract data from a grib2 file at multiple point locations
# and return an array of dictionary row objects
def process_file(filename, bundle, variables, issuance, time, lat, lon):
    print("Processing", filename)
    nc = Nio.open_file(filename, mode="r", format="grib")
    # initialize output data
    rows = []
    # Use PyNio's extended selection to do the interpolation for us.
    # https://www.pyngl.ucar.edu/NioExtendedSelection.shtml
    # Here all variables are 2-D. If 3-D (or higher dimension) fields will be extracted
    # the pattern will need to be adjusted.
    select = "lat_0|{lat}i lon_0|{lon}i".format(lat=lat, lon=lon)
    # Iterate through variables to collect the data
    for name in variables:
        if name in nc.variables:
            var = nc.variables[name]
            value = var[select]
            units = var.attributes["units"]
            lname = var.attributes["long_name"]
            # Append a single row of data for this variable
            rows.append(
                create_row(issuance, time, lat, lon, name, lname, value, units, bundle)
            )
        # else:
        #     # Variable name was not found
        #     # so indicate in the output that data is missing
        #     value = units = lname = "Missing"
        # # Append a single row of data for this variable
        # rows.append(create_row(issuance, time, lat, lon, name, lname, value, units))
    nc.close()
    return rows


def get_grib2_filenames():
    # Initial filenames object
    filenames = {}
    # Get the complete list of GRIB2 filenames
    for path in Path("DATA_DIR").rglob("*.grib2"):
        fpath = str(path)
        filename = path.name
        bundle = filename.split(".")[-4]
        issuance, timestamp = parse_datetime(filename)
        lookup_key = bundle + str(timestamp)
        filenames[lookup_key] = {
            "filename": filename,
            "issuance": issuance,
            "filepath": fpath,
        }
    return filenames


if __name__ == "__main__":
    # Specify the weather bundles of interest
    bundles = ["basic", "maritime"]
    # Specify input position data files
    csvfiles = ["hourly-positions-nienburg.csv", "hourly-positions-niteroi.csv"]
    # Create the filenames object
    filenames = get_grib2_filenames()
    # iterate through the input CSV files
    for filename in csvfiles:
        # initialize the output data object
        output_data = []
        # open the CSV input file
        with open(filename, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            # iterate through each of the bundles
            for bundle in bundles:
                # get the variable names for this bundle
                variables = DEF_VARIABLES[bundle]
                # iterate through each row of this input CSV
                for row in reader:
                    # unpack the input data
                    lat = row["latitude"]
                    lon = row["longitude"]
                    original_time = row["report_date"]
                    # cut the timezone out of the timestamp
                    rounded_time = row["rounded_time"].split("+")[0]
                    # create the lookup key to find the correct GRIB2 file
                    lookup_key = bundle + rounded_time
                    # check if we have a GRIB2 file that corresponds
                    # to the hourly timestamp of this position update
                    if lookup_key in filenames:
                        details = filenames[lookup_key]
                        # extract weather data for this point
                        rows = process_file(
                            details["filepath"],
                            bundle,
                            variables,
                            details["issuance"],
                            rounded_time,
                            lat,
                            lon,
                        )
                        # store the weather data for this location
                        # in our final output data object
                        output_data.append(rows)
            # write the output data to a CSV
            write_output(filename, output_data)
