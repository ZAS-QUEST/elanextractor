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

# terms which are occasionally recognized, but which are always false positives in the context of ELD
blacklist = [
    "Q7946755", #'wasn', radio station
    "Q3089073", #'happy, happy', norwegian comedy film
    "Q19893364",#'Inside The Tree', music album
    "Q49084,"# ss/ short story
    "Q17646620",# "don't" Ed Sheeran song
    "Q2261572",# "he/she" Gender Bender
    "Q35852",# : "ha" hectare
    "Q119018",#: "Mhm" Mill Hill Missionaries
    "Q932347",# "gave",# generic name referring to torrential rivers, in the west side of the Pyrenees
    "Q16836659", #"held" feudal land tenure in England
    "Q914307",# "ll" Digraph
    "Q3505473",# "stayed" Stay of proceedings
    "Q303",# "him/her" Elvis Presley
    "Q2827398",#: "Aha!" 2007 film by Enamul Karim Nirjhar
    "Q1477068",# "night and day" Cole Porter song
    "Q1124888",# "CEDA" Spanish Confederation of the Autonomous Righ
    
	


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
