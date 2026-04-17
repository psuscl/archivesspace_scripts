import argparse
import csv
import json
import os
import re
import localutils
from asnake.aspace import ASpace

aspace = ASpace()

parser = argparse.ArgumentParser()
parser.add_argument('file', help="file with data in it")
args = parser.parse_args()

if os.path.exists(args.file):
  digital_objects = []
  with open(args.file) as f:
    reader = csv.reader(f)
    for row in reader:
      if re.match(r'.+?_.+?_[0-9a-f]{32}', row[0]):
        refid = row[0].split('_')[-1]
      elif re.match(r'[0-9a-f]{32}', row[0]):
        refid = row[0]
      else:
        print("not a valid ArchivesSpace refID: {}".format(row[0]))
      
      results = [x for x in aspace.search.with_params(q=refid, page="1") if x.ref_id == refid]
      
      # find a better way to test if only one result was found!
      if len(results) == 1:
        data = results[0]
        print(data.title)
      else:
        print("bad news, there are either 0 or (somehow) multiple results")
else:
  print("file not found: {}".format(args.file))

