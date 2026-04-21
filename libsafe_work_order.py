import argparse
import localutils
import csv
import os
import re
import sys

def get_resource_info(record):
  resource = localutils.get_json(record['resource']['ref'])
  repo_code = localutils.get_json(record['repository']['ref'])['repo_code']
  return (resource['title'], "_".join([repo_code, resource['ead_id'], record['ref_id']]))

if os.path.exists("libsafe.csv"):
  os.remove("libsafe.csv")

# initialize a LIBSAFE manifest
manifest = []

# take as input a list of IDs that we want to look up in ArchivesSpace
parser = argparse.ArgumentParser()
parser.add_argument('file', help="The file of IDs to look up")
args = parser.parse_args()

# open our file and process the IDs:
if os.path.exists(args.file):
  with open(args.file) as f:
    reader = csv.reader(f)
    for row in reader:
      info = []
      if re.match(r"^pst.+?_[0-9]{5}_[0-9a-f]{32}$", row[0]):
        refid = row[0].split('_')[-1]
      elif re.match(r"^[0-9a-f]{32}$", row[0]):
        refid = row[0]
      else:
        print(f"error: {row[0]} is not a well-formed ID")
        continue

      results = localutils.get_json(f"/search?q={refid}&page=1")
      if results['results']:
        records = [r for r in results['results'] if r['ref_id'] == refid]
        if len(records) == 1:
          record = records[0]
          data = localutils.get_json(record['uri'])
          info.append(data['title'].strip())
          info.extend(get_resource_info(data))
        else:
          info.append(f"no record found with ID {refid}")
      else:
        info.append(f"no results for ID {refid}")
      
      with open("libsafe.csv", 'a') as fw:
        writer = csv.writer(fw)
        writer.writerow(info)
else:
  print("File not found: {}".format(args.file))
  sys.exit()