# this script reads through an EAD XML file and pulls out the ArchivesSpace URIs from
# every component record whose level is not 'series'

import argparse
import xml.etree.ElementTree as ET

ns = {'ead': 'urn:isbn:1-931666-22-9'}

parser = argparse.ArgumentParser()
parser.add_argument('file', help="the name of the data file to process")
args = parser.parse_args()

try:
  tree = ET.parse(args.file)
  root = tree.getroot()
  archdesc = root.find(".//ead:dsc", ns)
  for component in archdesc.findall(".//ead:c", ns):
    if 'level' in component.attrib:
      if component.attrib['level'] != "series":
        print(component.find("ead:did/ead:unitid", ns).text)
except OSError:
  print("file not found: {}".format(args.file))