# script containing common functions for working with data with ArchivesSnake,
# so that you don't need to write the same code in multiple Python scripts

import os
import json
from asnake.aspace import ASpace

aspace = ASpace()

# get a JSON object from the ArchivesSpace API using ArchivesSnake
def get_json(uri):
    r = aspace.client.get(uri)
    if r.status_code == 200:
        return r.json()
    else:
        r.raise_for_status()

# post a JSON object to the ArchivesSpace API using ArchivesSnake
def post_json(uri, data, returnURI=False):
    r = aspace.client.post(uri, json=data)
    message = r.json()
    if r.status_code == 200:
        if 'uri' in message:
            print("{}: {}".format(message['status'], message['uri']))
            if returnURI:
                return message['uri']
        else:
            print("{}: {}".format(message['status'], uri))
            if returnURI:
                return uri
    else:
        print("Error: {}".format(message['error']))
        if returnURI:
            return None

# here's if you want to post without a JSON object (i.e. to suppress a record)
def post_uri(uri):
    r = aspace.client.post(uri)
    message = r.json()
    if r.status_code == 200:
        if 'uri' in message:
            print("{}: {}".format(message['status'], message['uri']))
        else:
            print("{}: {}".format(message['status'], uri))
    else:
        print("Error: {}".format(message['error']))

# delete an object through the ArchivesSpace API using ArchivesSnake
def delete_json(uri):
    r = aspace.client.delete(uri)
    message = r.json()
    if r.status_code == 200:
        if 'uri' in message:
            print("{}: {}".format(message['status'], message['uri']))
        else:
            print("{}: {}".format(message['status'], uri))
    else:
        print("Error: {}".format(message['error']))

# write JSON to a file (e.g. if you want to work on it in OpenRefine)
def write_json(filename, data):
    if os.path.exists(filename):
        os.remove(filename)
    with open(filename, 'w') as f:
        f.write(json.dumps(data))
