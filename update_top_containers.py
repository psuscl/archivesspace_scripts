import csv
import localutils

# takes CSV import: column 1 URI, column 2 location code

with open('update_top_containers.csv') as f:
  reader = csv.reader(f)
  for row in reader:
    uri = row[0]
    data = localutils.get_json(uri)
    data['ils_holding_id'] = row[1]
    localutils.post_json(row[0], data)
