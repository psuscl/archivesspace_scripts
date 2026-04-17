import argparse
import localutils
import csv
import os
import json
import datetime

def process_record(data):
  # resolve ancestor references
  for ancestor in data['ancestors']:
    j = localutils.get_json(ancestor['ref'])
    data[ancestor['level']] = j['title']
  del(data['ancestors'])

  # resolve instance information
  for instance in data['instances']:
    if 'sub_container' in instance:
      tc = localutils.get_json(instance['sub_container']['top_container']['ref'])
      data['top_container'] = tc['display_string']
      if 'ils_holding_id' in tc:
          data['location'] = tc['ils_holding_id']
    elif 'digital_object' in instance:
      dao = localutils.get_json(instance['digital_object']['ref'])
      if 'user_defined' in dao:
        if dao['user_defined']['enum_1'] == "preservation":
          data['digital_object'] = dao['uri']
  del(data['instances'])

  # clean up dates
  if 'dates' in data:
    for date in data['dates']:
      if 'expression' in date:
        data['date'] = date['expression']
  del(data['dates'])

  # create specific columns for note types
  if 'notes' in data:
    for note in data['notes']:
      if note['jsonmodel_type'] == "note_singlepart":
        data[note['type']] = "; ".join(note['content'])
      else:
        note_content = []
        for subnote in note['subnotes']:
          note_content.append(subnote['content'])
        data[note['type']] = "; ".join(note_content)
  del(data['notes'])

  return data

parser = argparse.ArgumentParser()
parser.add_argument('file', help="file with data in it")
args = parser.parse_args()

manifest = []

if os.path.exists(args.file):
  with open(args.file) as f:
    reader = csv.reader(f)
    for row in reader:
      elements = row[0].split('_')
      refid = elements[2]
      results = localutils.get_json('/search?q={}&page=1'.format(refid))
      if results['results']:
        for result in results['results']:
          if 'ref_id' in result:
            if result['ref_id'] == refid:
              print("getting metadata for {}".format(refid))
              data = localutils.get_json(result['uri'])
              
              print("cleaning up record")
              data = process_record(data)

              # we have to round-trip the record through the JSON module so it exports as unicode
              data = json.dumps(data).encode(encoding='UTF-8')
              manifest.append(json.loads(data))
      else:
          print("no results: {}".format(refid))

outfile = "refids_{}.json".format(datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
if os.path.exists(outfile):
  os.remove(outfile)

with open(outfile, 'a') as fw:
  print("writing output to {}".format(outfile))
  fw.write(json.dumps(manifest))
