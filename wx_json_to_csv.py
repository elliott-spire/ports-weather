import csv
import json
import argparse


def main(filepath):

    with open(filepath) as jsonfile:
        response = json.load(jsonfile)

    output = filepath.split("/")[1][:-5] + ".csv"
    print(output)

    with open(output, "w", newline="") as csvfile:
        f = csv.writer(csvfile)
        # Write CSV Header
        f.writerow(
            [
                "Forecast Issuance",
                "Valid Time",
                "Latitude",
                "Longitude",
                "Variable",
                "Value",
            ]
        )

        for x in response["data"]:
            for key, val in x["values"].items():
                f.writerow(
                    [
                        x["times"]["issuance_time"],
                        x["times"]["valid_time"],
                        x["location"]["coordinates"]["lat"],
                        x["location"]["coordinates"]["lon"],
                        key,
                        val,
                    ]
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Read a JSON file containing a Spire Weather Point API response, and output as CSV"
    )
    parser.add_argument("filepath", type=str, help="The path to the JSON input")
    args = parser.parse_args()
    main(args.filepath)
