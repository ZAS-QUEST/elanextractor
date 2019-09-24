import sys
from lxml import etree

def countVernacularWords(filename):
  root = etree.parse(filename)
  print(filename)
  #the LINGUISTIC_TYPE_REF's which contain vernacular sentences
  candidates = ['Text', 'transcription', 'word-txt', 'word', 'UtteranceType']
  for candidate in candidates:   
    #try different LINGUISTIC_TYPE_REF's to identify the relevant tiers
    querystring = "TIER[@LINGUISTIC_TYPE_REF='%s']"%candidate 
    vernaculartiers = root.findall(querystring)
    if vernaculartiers != []: #we found a tier of the linguistic type
      for t in vernaculartiers: 
        #create a list of all words in that tier by splitting and collating all annotation values of that tier
        wordlist = [val #flatten list
                    for sublist in [av.text.split() 
                                    for av in t.findall(".//ANNOTATION_VALUE")
                                    if av.text!=None] 
                    for val in sublist]     
        if wordlist != []:
          #output the amount found with tier type and ID
          print("\t%s@%s: %s"%(t.attrib["TIER_ID"],candidate,len(wordlist)))
    
if __name__ == "__main__":
  filename = sys.argv[1]
  countVernacularWords(filename)
  
