import csv
import localutils

with open('uris.csv') as f:
  reader = csv.reader(f)
  for row in reader:
    data = localutils.get_json(row[0])

    # do stuff
    for location in data['container_locations']:
      if location['status'] == "current":
        location['ref'] = "/locations/18700"
    
    localutils.post_json(row[0], data)
        