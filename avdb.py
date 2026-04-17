import csv
import re
import pandas as pd
import localutils

# I decided to only run this script one location at a time, so that I can keep a closer
# eye on what we're doing and make sure nothing squirrelly happens

# read location URIs and codes into a pandas dataframe
df_loc = pd.read_csv('gcs_locations.csv')
df_tc = pd.read_csv('gcs_top_containers.csv')

with open('section_x.csv') as f:
  reader = csv.DictReader(f)
  for row in reader:
    # download both the record we're keeping and the AVDB record we're overlaying
    data = localutils.get_json(row['uri'])
    avdb_data = localutils.get_json(row['avdb_uri'])

    # if the avdb-overlay record is suppressed it means I already fixed it -- move on
    if avdb_data['suppressed']:
      print("found this entry suppressed in 00087-av, moving on")
      continue

    # if the titles match, keep the original; otherwise check the flag and see which one to keep
    if row['title_match'] == "avdb":
      data['title'] = avdb_data['title']
    
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
    
    # if we need to create the top container from scratch, do that here
    # (use our pandas dataframe for GCS locations to get the URI)
    top_container = {
      "jsonmodel_type": "top_container",
      "type": "cassette",
      "indicator": row['physloc'].replace('GCS/',''),
      "ils_holding_id": row['physloc'],
      "container_locations": [{
        "jsonmodel_type": "container_location",
        "status": "current",
        "start_date": "2026-02-20",
        "ref": df_loc.loc[df_loc['code'] == row['location']]['uri'].iloc[0]
      }]
    }
    tc_ref = localutils.post_json('/repositories/3/top_containers', top_container, returnURI = True)
    
    # link the existing top container to the avdb record
    for instance in data['instances']:
      if "sub_container" in instance:
        instance['sub_container'] = {
          'jsonmodel_type': "sub_container",
          'top_container': {'ref': tc_ref}
        }

    # suppress the avdb-overlay record when we're done
    localutils.post_uri("{}/suppressed?suppressed=true".format(row['avdb_uri']))

    # post our AVDB object with updated metadata
    localutils.post_json(row['uri'], data)