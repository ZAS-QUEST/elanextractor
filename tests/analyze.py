import sys
from lxml import etree

def getTimeslots(root):
  timeorder = root.find(".//TIME_ORDER")
  timeslots = dict([(slot.attrib["TIME_SLOT_ID"],slot.attrib["TIME_VALUE"]) for slot in timeorder.findall("TIME_SLOT")])
  return timeslots

def countVernacularWords(root,timeslots):
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
        timelist = [(int(timeslots[aa.attrib["TIME_SLOT_REF2"]])-int(timeslots[aa.attrib["TIME_SLOT_REF1"]])) 
                    for aa in t.findall(".//ALIGNABLE_ANNOTATION")
                    if aa.find(".//ANNOTATION_VALUE").text!=None
                    ]     
        #if wordlist != []:
        #print(timelist)
        #print(dict(timeslots))
        secs = sum(timelist)/1000
        #output the amount found with tier type and ID
        print("\t%s@%s: %s (%s s)"%(t.attrib["TIER_ID"],candidate,len(wordlist),secs))
    
if __name__ == "__main__":
  filename = sys.argv[1]
  print(filename)
  root = etree.parse(filename)
  timeslots = getTimeslots(root)
  countVernacularWords(root,timeslots)
  
