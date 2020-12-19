import os
import csv
import glob
from dateutil import parser
from datetime import datetime, timedelta


def round_time_to_hour(t):
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    return t.replace(second=0, microsecond=0, minute=0, hour=t.hour) + timedelta(
        hours=t.minute // 30
    )


def get_hourly_positions(filename):
    datafile = os.path.join(os.path.dirname(__file__), filename)
    csv_file = open(datafile)
    reader = csv.DictReader(csv_file)
    hourly_positions = {}
    i = 0
    for row in reader:
        timestamp = parser.parse(row["report_date"])
        rounded_time = round_time_to_hour(timestamp)
        time_string = str(rounded_time)
        # check if position data has already been stored for this hour
        if time_string not in hourly_positions:
            # we have not stored position data yet for this rounded hour
            # so we simply copy the data
            hourly_positions[time_string] = row
        elif time_string in hourly_positions:
            # we have aready stored position data for this rounded hour
            # so we need to decide whether or not to replace it
            # with the current row's position data
            previous_time = hourly_positions[time_string]["report_date"]
            previous_time = parser.parse(previous_time)
            # calculate time deltas for the previous and current data rows
            # to determine how close they are to the rounded hour
            previous_difference = abs(previous_time - rounded_time)
            current_difference = abs(timestamp - rounded_time)
            # only replace the existing position data for this hour
            # if the current timestamp is closer to the hour
            if current_difference < previous_difference:
                hourly_positions[time_string] = row
        # print progress for script user
        i += 1
        print("Processed row {} for {}".format(i, filename))
    return hourly_positions


def write_output(filename, hourly_positions):
    outname = filename.split("/")[-1]
    with open("hourly-positions-" + outname, "w") as outfile:
        fieldnames = ["latitude", "longitude", "report_date", "rounded_time"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        # write the header first
        writer.writeheader()
        for rounded_time, data in hourly_positions.items():
            data["rounded_time"] = rounded_time
            # write the data to a new CSV row
            writer.writerow(data)


if __name__ == "__main__":
    filenames = glob.glob("position_data/*.csv")
    for filename in filenames:
        # replace all timestamps with a rounded hourly timestamp
        hourly_positions = get_hourly_positions(filename)
        # write new data to CSV
        write_output(filename, hourly_positions)
