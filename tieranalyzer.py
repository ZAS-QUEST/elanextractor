import glob
import sys
import pprint
from collections import Counter
from collections import defaultdict
from lxml import etree
from random import shuffle
import matplotlib.pyplot as plt 
from matplotlib import cm
import squarify     




def analyze_tier(d, level, lump=False):
    """analyze a tier and its children"""

    global accumulator
    global tierconstraints
    constraint = d['constraint']
    code = 'x'
    if constraint == 'Symbolic_Subdivision' or constraint == 'Symbolic Subdivision':
        code = 's'
    elif constraint == 'Symbolic_Association' or constraint == 'Symbolic Association' :
        code = 'a'
    elif constraint == 'Time_Subdivision' or constraint == 'Time Subdivision':
        if lump:
            code = 's'
        else:
            code = 't'
    elif constraint == 'Included_In':
        if lump:
            code = 's'
        else:
            code = 'i'
    elif constraint == 'root':
        code = 'R'
    elif constraint == '':
        code = 'x'
    elif constraint is None:
        code = 'x'
    else:
        print(repr(constraint))
        0/0
    #accumulator += "%s%s--%s\n"%('  '*level, d['id'], constraint)
    #accumulator += "%s%s%s|"%('.'*level, '', code)
    accumulator += code
    children = dico[d['id']] 
    if children == []:
        return
    accumulator += '['
    for child in children:
        analyze_tier(child, level+1, lump=lump)        
    accumulator += ']'
        

def check_tiers(filename, lump=False):
    """
    check the tiers there are in a given file and
    return a fingerprint describing the structure
    Dots indicate the level
    The type of a tier is indicated by
    - s: subdivision
    - a: association
    - x: anything else
    """

    #due to memory constraints we use global variables
    global accumulator
    global dico
    global tierconstraints

    accumulator = '['
    dico = defaultdict(list)
    try:
        tree = etree.parse(filename)
    except etree.XMLSyntaxError:
        return ''
    linguistic_types = tree.findall(".//LINGUISTIC_TYPE")
    #map tier IDs to their constraints
    tierconstraints = {lt.attrib["LINGUISTIC_TYPE_ID"]:lt.attrib.get("CONSTRAINTS") for lt in linguistic_types}
    tiers = tree.findall(".//TIER")
    for tier in tiers:
        ID = tier.attrib["TIER_ID"]
        #map all tiers to their parent tiers, defaulting to the file itself
        PARENT_REF = tier.attrib.get("PARENT_REF", (filename))
        ltype = tier.attrib["LINGUISTIC_TYPE_REF"]
        try:
            constraint = tierconstraints[ltype]
        except KeyError:
            print("reference to unknown LINGUISTIC_TYPE_ID  %s when establishing constraints in %s" %(ltype,filename))
            continue
        dico[PARENT_REF].append({'id': ID,
                                 'constraint': constraint,
                                 'ltype': ltype
                                }
                               )
    #start with dummy tier
    analyze_tier({'id':filename,
                  'constraint': 'root',
                  'ltype': ''
                 },
                 0,
                 lump=lump
                )    
    accumulator += ']'
    return accumulator

if __name__ == "__main__":
    # retrieve all ELAN files and check for tiers
    # analyze tiers for each file
    # fingerprint each file
    # tally fingerprints and write the results

    LIMIT = 999999 
    #LIMIT = 111 
    DEFAULTDIRECTORY = 'elareafs'
    directory = DEFAULTDIRECTORY
    try:
        directory = sys.argv[1]
    except IndexError:
        pass
    lump = True
    fingerprints = [check_tiers(f, lump=lump) for f in glob.glob("*eafs/*eaf")[:LIMIT]]
    #count occurences
    counted_fingerprints = Counter(fingerprints)
    #sort by number of occurences and print
    ranks = sorted([(counted_fingerprints[key], key) for key in counted_fingerprints.keys()])[::-1]
    values = [x[0] for x in ranks] 
    squarify.plot(sizes=values, label=values[:38], color=[cm.pink(x*.1) for x in [2,8,4,7,1,6,3,9,5]]) 
    plt.axis('off') 
    plt.savefig('tiertypetreemap.png')
    with open("tierranks.txt", 'w') as out:
        out.write("\n".join(["%s:%s" % x
                     for x
                     in ranks
                    ]
                   )
         )
