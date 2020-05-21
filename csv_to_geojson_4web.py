import csv
import json

data = []

output = {
	'type': 'FeatureCollection',
	'features': []
}

max_tp = 0

with open('precip.csv', 'r') as csvfile:
	reader = csv.DictReader(csvfile)
	for r in reader:
		del r['latbin']
		del r['lonbin']
		precip = float(r['tp'])
		if precip > max_tp:
			max_tp = precip
		point = {
			'type': 'Feature',
			'properties': {
				'tp': precip
			},
			'geometry': {
				'type': 'Point',
				'coordinates': [
					r['longitude'],
					r['latitude']
				]
			}
		}
		output['features'].append(point)

print('Max Precip:', max_tp)

with open('js/data.js', 'w') as outfile:
	outfile.write('var DATA = %s%s' % (json.dumps(output, indent=4), ';'))