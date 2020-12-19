import csv
import json

VARIABLE_NAMES = {
    # basic bundle
    "PRMSL_P0_L101_GLL0": "air_pressure_at_sea_level",
    "TMP_P0_L103_GLL0": "air_temperature",
    "DPT_P0_L103_GLL0": "dew_point_temperature",
    "APCP_P8_L1_GLL0_acc": "precipitation_amount",
    "TCDC_P0_L200_GLL0": "total_cloud_cover",
    "RH_P0_L103_GLL0": "relative_humidity",
    "GUST_P0_L1_GLL0": "wind_gust",
    # "x": "wind_speed",
    # "x": "wind_direction",
    "VGRD_P0_L103_GLL0": "northward_wind",
    "UGRD_P0_L103_GLL0": "eastward_wind",
    # maritime bundle
    "WTMP_P0_L1_GLL0": "sea_surface_temperature",
    "WWSDIR_P0_L101_GLL0": "sea_surface_wave_mean_direction",
    "MWSPER_P0_L101_GLL0": "sea_surface_wave_mean_period",
    "HTSGW_P0_L101_GLL0": "sea_surface_wave_significant_height",
    # "x": "sea_water_speed",
    # "x": "sea_water_direction",
    "VOGRD_P0_L1_GLL0": "northward_sea_water_velocity",
    "UOGRD_P0_L1_GLL0": "eastward_sea_water_velocity",
}


def write_output_to_json_file(filename, data):
    values = []
    for key, val in data.items():
        values.append(val)
    output = {"meta": {"unit_system": "si"}, "data": values}
    fileprefix = filename.split(".")[0]
    with open(fileprefix + ".json", "w") as jsonFile:
        jsonFile.write(json.dumps(output, indent=4))
        # jsonFile.write(json.dumps(output))


def convert_csv_to_json():
    # Specify input position data files
    csvfiles = ["nwp-hourly-positions-nienburg.csv", "nwp-hourly-positions-niteroi.csv"]
    # iterate through the input CSV files
    for filename in csvfiles:
        # initialize the output data object
        output_data = {}
        # open the CSV input file
        with open(filename, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                issuance = row["Forecast Issuance"]
                time = row["Valid Time"]
                lat = row["Latitude"]
                lon = row["Longitude"]
                # build the unique lookup key for our data dictionary
                lookup_key = ",".join([issuance, time, lat, lon])
                # translate GRIB2 variable name to JSON
                variable = row["Variable"]
                value_key = VARIABLE_NAMES[variable]
                # retrieve the actual data value
                value = row["Value"]
                # name = row["Name"]
                # units = row['Units']
                # bundle = row['Bundle']
                if lookup_key not in output_data:
                    output_data[lookup_key] = {
                        "location": {"coordinates": {"lat": lat, "lon": lon}},
                        "times": {
                            "issuance_time": (issuance + "+00:00").replace(" ", "T"),
                            "valid_time": (time + "+00:00").replace(" ", "T"),
                        },
                        "values": {value_key: value},
                    }
                else:
                    # this point forecast already exists in our data dictionary
                    # so we simply need to add the new data value
                    output_data[lookup_key]["values"][value_key] = value
            # output the data to JSON
            write_output_to_json_file(filename, output_data)


if __name__ == "__main__":
    convert_csv_to_json()
