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
LOGFILE = "updates_{}.txt".format(datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
DRY_RUN = args.dry_run
REQUIRED_FIELDS = ['title', 'identifier']

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

def process_records(file):
    with open(file, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        check_required_fields(fields)
        for row in reader:
            data = download_object(row, fields)
            if not data:
                log_message("Object not found with the identifier provided, skipping\n")
                continue
            ### This is the part where we make changes
            


if __name__ == "__main__":
    if os.path.exists(args.file):
        if DRY_RUN:
            print("ALERT: We're just dry-running. No data will be added to ArchivesSpace at this stage.")
        process_records(args.file)
    else:
        print("File not found: {}".format(args.file))