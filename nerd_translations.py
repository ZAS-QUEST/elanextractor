import json
import requests
import pprint
import sys

def nerd_text(text):
    url = 'http://cloud.science-miner.com/nerd/service/disambiguate'
    if len(text.split(' ')) < 5:
        return []
    rtext = requests.post(url, json={'text': text}).text
    #pprint.pprint(rtext)
    retrieved_entities = json.loads(rtext).get('entities', [])
    return list(set([(x['rawName'], x['wikidataId']) 
            for x in retrieved_entities if x.get('wikidataId')
           ]))

filename = sys.argv[1]    
with open(filename) as infile: 
    jsonfile = json.loads(infile.read())

found_entities = {}

LIMIT = 9999999
OFFSET = 1035
#OFFSET = 3
#LIMIT = 4
for i, key in enumerate(list(jsonfile.keys())[OFFSET:LIMIT]):
    print(i, key)
    found_entities[key] = {}
    for type_ in jsonfile[key]:
        print(" ", type_)
        for tier in jsonfile[key][type_]:
            print("  ", tier)
            collated_text = ". ".join(jsonfile[key][type_][tier])
            entities = nerd_text(collated_text)
            for entity in entities:
                found_entities[key][entity[1]] = entity[0]

pprint.pprint(found_entities)

with open('%s_nerd.json'%filename.split('.')[0], 'w') as out:
    out.write(json.dumps(found_entities, sort_keys=True, indent=4))
