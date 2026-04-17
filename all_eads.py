# dump every EAD record to a local XML file (for version control purposes)

import localutils
from asnake.aspace import ASpace

AS = ASpace()

all_ids = localutils.get_json('/repositories/3/resources?all_ids=true')
for id in all_ids:
  resource = AS.repositories(3).resources(id)
  print("working on {} {}".format(resource.id_0, resource.title))
  eadfn = "pstsc_{}_ead.xml".format(resource.id_0)
  r = AS.client.get('/repositories/3/resource_descriptions/{}.xml?include_unpublished=true&include_daos=true&numbered_cs=true'.format(id))
  if r.status_code == 200:
    ead = r.text
    with open("ead/{}".format(eadfn), 'w') as f:
      f.write(r.text)
  else: 
    print(r.json()['error'])
    continue