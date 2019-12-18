import sys
import pprint
import json
import requests


def nerd_text(text):
    """sent text to online resolver and retrieve wikidataId's"""

    url = "http://cloud.science-miner.com/nerd/service/disambiguate"
    if len(text.split()) < 5: #cannot do NER on less than 5 words
        return []
    #send text 
    rtext = requests.post(url, json={"text": text}).text
    #parse json
    retrieved_entities = json.loads(rtext).get("entities", [])
    #extract names and wikidataId's
    return [(x["rawName"], x["wikidataId"])
            for x in retrieved_entities
            if x.get("wikidataId") and x["wikidataId"] not in blacklist
           ]

blacklist = [
    "Q7946755", #'wasn', radio station
    "Q3089073", #'happy, happy', norwegian comedy film
    "Q19893364",#'Inside The Tree', music album
    ]

if __name__ == "__main__":
    FILENAME = sys.argv[1]
    with open(FILENAME) as infile:
        JSONFILE = json.loads(infile.read())

    FOUND_ENTITIES = {}

    LIMIT = 9999999
    OFFSET = 0
    # OFFSET = 3
    # LIMIT = 4
    for i, key in enumerate(list(JSONFILE.keys())[OFFSET:LIMIT]):
        print(i, key)
        #setup dictionary to store filenames as keys and entities as values
        FOUND_ENTITIES[key] = {}
        for type_ in JSONFILE[key]:
            print(" ", type_)
            for tier in JSONFILE[key][type_]:
                print("  ", tier)
                #the json file holds a list of sentences
                #we collate them to one large paragraph
                collated_text = ". ".join(JSONFILE[key][type_][tier])
                entities = nerd_text(collated_text)
                for entity in entities:
                    FOUND_ENTITIES[key][entity[1]] = entity[0]

    #pprint.pprint(FOUND_ENTITIES)

    OUTFILE = "%s_nerd.json" % FILENAME.split(".")[0]
    with open(OUTFILE, "w") as out:
        out.write(json.dumps(FOUND_ENTITIES, sort_keys=True, indent=4))
    print("output is in ", OUTFILE)