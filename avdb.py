import argparse
import csv
import re
import pandas as pd
import localutils
from asnake.aspace import ASpace

# REQUIREMENTS
#
# The CSV file we take as input should have the following columns:
# uri : the URI of the record we're keeping
# avdb_uri : the URI of the AVdb record from which we're overlaying (suppress when we're done)
# title_match : if "avdb" is set in this column, we overlay the AVdb title (otherwise we keep the original)

# TO DO:
#
# Handle cases where we are adding top containers to AVdb records but not doing the overlay (happens with 00002-av sometimes)

# read location URIs and codes into a pandas dataframe
# TO DO: handle this through the API using ArchivesSnake
df_loc = pd.read_csv('gcs_locations.csv')
df_tc = pd.read_csv('gcs_top_containers.csv')

# set our command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--dry-run', help="say what we will do without doing it", action="store_true")
parser.add_argument('file', help="The file with data to process")
args = parser.parse_args()

def search_top_container(box):
  repo = ASpace().repositories(3)
  results = [x for x in repo.search.with_params(q=f"{box}, primary_type:top_container", page="1") if x.indicator == box]
  if len(results) > 1:
    return results[0].uri
  else:
    return None

# handle the creation and/or linking of top containers
def handle_top_container(row, args):
  if row['top_container']:
    if row['top_container'] in df_tc['code'].values:
      tc_ref = df_tc.loc[df_tc['code'] == row['top_container']]['uri'].iloc[0]
      if args.dry_run:
        print(f"top container ref {tc_ref}")
        return
      else:
        return tc_ref
    else:
      print("top container provided but not found in the CSV file, will have to create it")
  
  top_container = {
    "jsonmodel_type": "top_container",
    "type": row['container_type'],
    "indicator": row['physloc'].replace('GCS/', ''),
    "ils_holding_id": row['physloc'],
    "container_locations": [{
      "jsonmodel_type": "container_location",
      "status": "current",
      "start_date": "2026-02-20",
      "ref": df_loc.loc[df_loc['code'] == row['location']]['uri'].iloc[0]
    }]
  }

  if args.dry_run:
    print("would create a new top container here")
    return
  else:
    tc_ref = localutils.post_json('/repositories/3/top_containers', top_container, returnURI = True)
    return tc_ref

try:
  with open(args.file) as f:
    reader = csv.DictReader(f)
    for row in reader:
      # download both the record we're keeping and the AVDB record we're overlaying
      data = localutils.get_json(row['uri'])
      avdb_data = localutils.get_json(row['avdb_uri'])

      # if the avdb-overlay record is suppressed it means I already fixed it -- move on
      if avdb_data['suppressed']:
        print("found this entry suppressed in 00087-av, moving on")
        continue

      # check the title flag to see if we want the avdb-overlay title
      #if 'title_match' in row:
      #  if row['title_match'] == "avdb":
      #    data['title'] = avdb_data['title']
      
      # strip general note whitespace
      for note in data['notes']:
        if note['type'] == "odd":
          for subnote in note['subnotes']:
            subnote['content'] = subnote['content'].strip()

      # keep the format notes but copy over the subject headings from avdb-overlay
      data['subjects'] = avdb_data['subjects']

      # convert avdb-overlay physdesc notes to extents in the record we're keeping
      physdesc_notes = [n for n in avdb_data['notes'] if n['type'] == "physdesc"]
      if len(physdesc_notes) > 0:
        extent = physdesc_notes[0]['content'][0]
        extent = re.sub(r"<\/*extent>", "", extent)
        data['extents'].append({
          "jsonmodel_type": "extent",
          "portion": "whole",
          "number": extent,
          "extent_type": "items"
        })

      # copy any scopecontent or general notes we find in avdb-overlay
      for note in avdb_data['notes']:
        if note['type'] == "scopecontent":
          data['notes'].append(note)
        elif note['type'] == "odd":
          data['notes'].append(note)
      
      # if a top container already exists, grab its URI from the CSV file; otherwise create one from scratch
      # (uses our pandas dataframe for GCS locations to get the URI -- should maybe have an API solution for this but w/e)
      tc_ref = handle_top_container(row, args)

      # link the existing top container to the avdb record
      if data['instances']:
        for instance in data['instances']:
          if "sub_container" in instance:
            instance['sub_container'] = {
              'jsonmodel_type': "sub_container",
              'top_container': {'ref': tc_ref}
            }

            if row['subtype']:
              instance['sub_container']['type_2'] = row['subtype']
              if row['subtype'] == "cassette":
                instance['sub_container']['indicator_2'] = row['physloc'].split('/')[-1].split('.')[-1]
              elif row['subtype'] == "reel":
                instance['sub_container']['indicator_2'] = row['physloc'].split(' ')[-1]

      # suppress the avdb-overlay record when we're done
      if args.dry_run:
        print(f"this is where we would suppress {row['avdb_uri']}")
      else:
        localutils.post_uri("{}/suppressed?suppressed=true".format(row['avdb_uri']))

      # post our AVDB object with updated metadata
      if args.dry_run:
        print(f"this is where we would post updates to {row['uri']}")
      else:
        localutils.post_json(row['uri'], data)
except OSError:
  print(f"file not found: {args.file}")