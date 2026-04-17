import os
import requests
import csv

if os.path.exists("links.csv"):
  with open("links.csv") as f:
    reader = csv.reader(f)
    for row in reader:
      r = requests.get(row[1])
      if r.status_code != 200:
        print("bad link: " + row[0])
