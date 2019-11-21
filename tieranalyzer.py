import glob
import sys
import pprint   
from collections import Counter
from collections import defaultdict
from lxml import etree



def traverse_(d, level):  
    global accumulator
    global tierconstraints
    constraint = d['constraint']
    code = 'x'   
    if constraint == 'Symbolic_Subdivision':
        code = 's'
    elif constraint == 'Symbolic_Association':
        code = 'a'
    elif constraint == '':
        code = 'x'
    elif constraint is None:
        code = 'x'
    else:
        print(repr(constraint))
        0/0 
    #accumulator += "%s%s--%s\n"%('  '*level, d['id'], constraint)
    accumulator += "%s%s%s|"%('.'*level, '', code)
    for child in dico.get(d['id'], []): 
        traverse_(child, level+1)  
            
def check_tiers(filename):
    """check how many tiers there are in a given file""" 
    global accumulator
    accumulator = ''
    global dico
    dico = defaultdict(list)
    #print(filename)
    tree = etree.parse(filename)
    linguistic_types = tree.findall(".//LINGUISTIC_TYPE")   
    global tierconstraints
    tierconstraints = {lt.attrib["LINGUISTIC_TYPE_ID"]:lt.attrib.get("CONSTRAINTS") for lt in linguistic_types}
    #pprint.pprint(tierconstraints)
    tiers = tree.findall(".//TIER")   
    #dico = defaultdict(list)
    for tier in tiers: 
        ID = tier.attrib["TIER_ID"]
        PARENT_REF = tier.attrib.get("PARENT_REF",(filename))
        LTYPE = tier.attrib["LINGUISTIC_TYPE_REF"]
        CONSTRAINT = tierconstraints[LTYPE]
        dico[PARENT_REF].append({'id':ID,
                                'constraint': CONSTRAINT,
                                'ltype': LTYPE
                                }
                               )
    #pprint.pprint(dico)
    traverse_({'id':filename,
               'constraint': '',
               'ltype': ''
               },
                0
              )
    #print(accumulator)
    return accumulator
    #count = len(tiers)
    #return count

if __name__ == "__main__":
    # retrieve all ELAN files and check for tiers
    # count tiers for each file
    # print how many tiers are found in how many files
    LIMIT = 1111
    DEFAULTDIRECTORY = 'elareafs'
    directory = DEFAULTDIRECTORY
    try:
        directory = sys.argv[1]
    except IndexError:
        pass
    HASHES =  [check_tiers(f) for f in glob.glob("%s/*eaf"%directory)[:LIMIT]]
    COUNTED_HASHES = Counter(HASHES)    
    ranks = [(COUNTED_HASHES[key], key) for key in COUNTED_HASHES.keys()]
    print("\n".join(
                    ["%s:%s" % x 
                    for x 
                    in sorted(ranks)[::-1]
                    ]
                  )
        )
    #TIERCOUNTS = [check_tiers(f) for f in glob.glob("%s/*"%directory)[:LIMIT]]
    #COUNTED_COUNTS = Counter(TIERCOUNTS)
    #for key in sorted(COUNTED_COUNTS.keys()):
        #print(key, COUNTED_COUNTS[key])
