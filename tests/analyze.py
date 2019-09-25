import sys
from lxml import etree
import glob
import datetime
import os 

def getTimeslots(root):
  timeorder = root.find(".//TIME_ORDER")
  timeslots = dict([(slot.attrib["TIME_SLOT_ID"],slot.attrib["TIME_VALUE"]) 
                    for slot in timeorder.findall("TIME_SLOT")
                    ])
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
        return t.attrib["TIER_ID"],candidate,len(wordlist),secs #now returns on first nonzero candidate. #FIXME better check all candidates before  returning
    
if __name__ == "__main__":
  try:
    filename = sys.argv[1]
    print(filename)
    root = etree.parse(filename)
    timeslots = getTimeslots(root)
    result = countVernacularWords(root,timeslots)
    print("\t%s@%s: %s words (%s seconds)" % result)
  except IndexError:
    eafs = glob.glob("./*eaf")
    globalwords = 0
    globalsecs = 0
    for eaf in eafs: 
      root = etree.parse(eaf)
      try:
        timeslots = getTimeslots(root)
      except KeyError: 
        print("skipping %s (no time slots)" % eaf)
        continue
      result = countVernacularWords(root,timeslots)
      try:
        globalwords += result[2]
        globalsecs += result[3]
        hours = str(datetime.timedelta(seconds=globalsecs)).split('.')[0]
      except TypeError:
        print("skipping %s" % eaf)
    print("Processed %i files in %s.\n%s transcribed in %i words." % (len(eafs),os.getcwd(),hours, globalwords))
      
    
      
  
