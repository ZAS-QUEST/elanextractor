import glob
import sys
from collections import Counter
from collections import defaultdict
from lxml import etree

def traverse_(dico, key, level, accumulator): 
    #accumulator += "  "*level+key[-30:]+"\n"
    accumulator += "  "*level+".\n"
    for child in dico.get(key, []):
        accumulator += traverse_(dico, child, level+1, accumulator)
    return accumulator
            
def check_tiers(filename):
    """check how many tiers there are in a given file""" 
    print(filename)
    tree = etree.parse(filename)
    tiers = tree.findall(".//TIER")   
    dico = defaultdict(list)
    for tier in tiers: 
        ID = tier.attrib["TIER_ID"]
        PARENT_REF = tier.attrib.get("PARENT_REF",filename)
        dico[PARENT_REF].append(ID)
    accumulator = traverse_(dico, filename, 0, '')
    return accumulator
    #count = len(tiers)
    #return count

if __name__ == "__main__":
    # retrieve all ELAN files and check for tiers
    # count tiers for each file
    # print how many tiers are found in how many files
    LIMIT = 11
    DEFAULTDIRECTORY = 'elareafs'
    directory = DEFAULTDIRECTORY
    try:
        directory = sys.argv[1]
    except IndexError:
        pass
    HASHES =  [check_tiers(f) for f in glob.glob("%s/*"%directory)[:LIMIT]]
    COUNTED_HASHES = Counter(HASHES)    
    for key in sorted(COUNTED_HASHES.keys()):
        print(hash(key), COUNTED_HASHES[key])
    #TIERCOUNTS = [check_tiers(f) for f in glob.glob("%s/*"%directory)[:LIMIT]]
    #COUNTED_COUNTS = Counter(TIERCOUNTS)
    #for key in sorted(COUNTED_COUNTS.keys()):
        #print(key, COUNTED_COUNTS[key])
