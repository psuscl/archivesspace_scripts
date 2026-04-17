# this script follows a lot of conventions I don't really follow anymore:
# could do with an update

import argparse
import csv
import json
import os
import sys
import datetime
import localutils
from asnake.aspace import ASpace

# user arguments:
# file name is required
# provide option to dry run the script to see what it will do before you do it
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', help="file with data to add", required=True)
parser.add_argument('-d', '--dry-run', help="Show what the script will do but don't do it", action="store_true")
args = parser.parse_args()

# global variables
AS = ASpace()
LOGFILE = "addDigitalObjects_{}.txt".format(datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
DRY_RUN = args.dry_run
REQUIRED_FIELDS = ['title', 'identifier']

# Function to collect digital object types from the user
# (1 = access, 2 = preservation)
def get_object_type():
  while True:
    try:
      type = int(input("Choose the object type:\n1) Access\n2) Preservation\n$ "))
    except ValueError:
      print("Invalid entry.\n")
    else:
      if 1 <= type < 3:
        break
      else:
        print("Invalid entry.\n")
  if type == 1:
    return "access"
  else:
    return "preservation"

# Function to collect digital preservation level from the user (scale of 0-3)
# These levels are defined in the PSUL Digital Preservation Policy
def get_preservation_level():
  while True:
    try:
      level = int(input("Choose a preservation level (0-3): "))
    except ValueError:
      print("Please enter a number.\n")
    else:
      if 0 <= level <= 3:
        break
      else:
        print("Invalid entry.\n")
  
  return str(level)

def log_message(text):
  print(text)
  if not DRY_RUN:
    with open(LOGFILE, 'a') as f:
      f.write("{}\n".format(text))

def check_required_fields(fields):
  log_message("Checking for required fields...")
  if all(x in fields for x in REQUIRED_FIELDS):
    log_message("All required fields present!")
    return
  else:
    log_message("ERROR: One or more required fields is absent. Required fields: {}".format(", ".join(REQUIRED_FIELDS)))
    sys.exit()

def download_object(row, fields):
  # we need to pass the field names to this function to check if the URI was provided.
  #
  # if the URI is provided, use that to download the archival object
  # otherwise we derive it from the identifier: if it is well-formed, the refID will be
  #  the last part of the identifier in the spreadsheet, so we will search for that
  #
  # probably a good idea to one day validate the data provided
  log_message("\n----\nProcessing {}".format(row['identifier']))
  if 'uri' in fields:
    return localutils.get_json(row['uri'])
  else:
    log_message("URI not provided, will try to get it from the identifier.")
    refid = row['identifier'].split('_')[-1]
    results = localutils.get_json('/search?q={}&page=1'.format(refid))
    if 'results' in results:
      for result in results['results']:
        if 'ref_id' in result:
          log_message("File found, getting its URI")
          row['uri'] = result['uri']
          return localutils.get_json(row['uri'])
    else:
        return False

def build_digital_object(row, fields, type, level):
  # Here we build the digital object record. Variable fields:
  #
  # Title: comes from the title column in CSV
  # Digital Object ID: comes from the identifier column in CSV
  # User-defined fields: 
  # * 'enum_1' is the object type
  # * 'enum_2' is the preservation level
  dao = {
    'jsonmodel_type': "digital_object",
    'title': row['title'],
    'digital_object_id': row['identifier'],
    'publish': True,
    'user_defined': {'enum_1': type, 'enum_2': level}
  }

  # If the import includes a file URI, add a file version and publish it
  # This is usually a CONTENTdm IIIF manifest or a Kaltura URL
  if 'file_uri' in fields:
    file = {
      'jsonmodel_type': "file_version",
      'file_uri': row['file_uri'],
      'publish': True,
      'is_representative': True,
      'xlink_actuate_attribute': "onLoad",
      'xlink_show_attribute': "embed",
      'caption': row['title']
    }

    dao['file_versions'] = [file]
  else:
    log_message("Warning: {} will post without a file version.".format(row['identifier']))
  return dao

def post_objects(row, data, dao, dao_uri):
  # Try to post the digital object.
  #
  # If it succeeds, get its URI and link it to the archival object provided or found from ref_id
  # If it fails, say why and move on
  r = AS.client.post(dao_uri, json=dao)
  message = json.loads(r.text)
  if r.status_code == 200:
    log_message("Digital object successfully posted: {}".format(message['uri']))
    log_message("Adding digital object link to file...")
    data['instances'].append({
      'instance_type': "digital_object",
      'jsonmodel_type': "instance",
      'is_representative': True,
      'digital_object': {'ref': message['uri']}
    })

    log_message("Link added: {}".format(localutils.post_json(row['uri'], data, returnURI=True)))
  else:
    log_message("Error: {}".format(message['error']))

def process_records(file):
  with open(file, encoding="utf-8-sig") as f:
    object_type = get_object_type()
    level = get_preservation_level()
    log_message("Processing digital objects:")
    log_message("File: {}".format(file))
    log_message("Object type: {}".format(object_type))
    log_message("Preservation level: {}\n".format(level))

    reader = csv.DictReader(f)
    fields = reader.fieldnames
    check_required_fields(fields)
    for row in reader:
      data = download_object(row, fields)
      if not data:
        log_message("Object not found with the identifier provided, skipping\n")
        continue
      dao = build_digital_object(row, fields, object_type, level)
      dao_uri = "/repositories/{}/digital_objects".format(row['uri'].split('/')[2])
      if DRY_RUN:
        log_message("Here we would try to post a digital object:")
        for k, v in row.items():
          log_message("* {}: {}".format(k, v))
      else:
        post_objects(row, data, dao, dao_uri)

if __name__ == "__main__":
  if os.path.exists(args.file):
    if DRY_RUN:
      print("ALERT: We're just dry-running. No data will be added to ArchivesSpace at this stage.")
    process_records(args.file)
  else:
    print("File not found: {}".format(args.file))
