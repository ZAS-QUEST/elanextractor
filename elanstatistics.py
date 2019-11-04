import os 
import sys
import glob
import datetime
from lxml import etree 
import logging
logging.basicConfig(filename='elanstatistics.log',level=logging.WARNING)

def getTimeslots(root):
  """
  Create a dictionary with time slot ID as keys and offset in ms as values
  """
  
  timeorder = root.find(".//TIME_ORDER")
  timeslots = dict([(slot.attrib["TIME_SLOT_ID"],slot.attrib["TIME_VALUE"]) 
                    for slot in timeorder.findall("TIME_SLOT")
                    ])
  return timeslots

def getAlignableAnnotations(root):
  """
  Create a dictionary with alignable annotations ID as keys and the elements themselves as values
  """
  
  aas = root.findall(".//ALIGNABLE_ANNOTATION") 
  d = dict([(aa.attrib["ANNOTATION_ID"],aa) 
                    for aa in aas 
                    ]) 
  return d

def getDuration(annotation):
  """
  compute a list of durations of each annotation by substracting start times from end times
  """
  
  try:
    return int(timeslots[annotation.attrib["TIME_SLOT_REF2"]])-int(timeslots[annotation.attrib["TIME_SLOT_REF1"]])
  except AttributeError:
    return 0
  

def countVernacularWords(root,timeslots,alignableannotations):
  """
  Retrieve tiers with transcription in an ELAN file. 
  Return the ID of the first tier found, the linguistic type matched, aggregate number of words, aggregate time. 
  """
  
  #the LINGUISTIC_TYPE_REF's which contain vernacular sentences
  candidates = [
        'interlinear-text-item', 
        'Nese Utterances',
        'po (practical orthography)'
        't', 
        #'tx', #check usages of this        
        'text',
        'Text',
        'transcription', 
        'Transcription',
        'ut', 
        'utterance transcription',
        'UtteranceType', 
        'word-txt', 
      ]
  results = []
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
        #get a list of duration from the time slots directly mentioned in annotations
        timelist = [getDuration(aa) 
                    for aa in t.findall(".//ALIGNABLE_ANNOTATION")
                    if aa.find(".//ANNOTATION_VALUE").text!=None
                    ]      
        #get a list of durations from time slots mentioned in parent elements
        timelistannno = [getDuration(alignableannotations.get(ra.attrib["ANNOTATION_REF"])) 
                    for ra in t.findall(".//REF_ANNOTATION")
                    if ra.find(".//ANNOTATION_VALUE").text!=None
                    ]     
        secs = sum(timelist+timelistannno)/1000          
        #output the amount found with tier type and ID
        results.append((t.attrib["TIER_ID"],candidate,len(wordlist),secs)) 
  return results  
    
if __name__ == "__main__":  
    """
    usage: > python3 analyze.py myfile.eaf
    The script checks for tiers which contain transcribed text in an given ELAN file
    The words in this tier are counter and if possible matched to time codes
    
    usage: > python3 analyze.py 
    As above, but for all files in directory. Aggregate sums for words and time are given. 
    
    """
    try:
            filename = sys.argv[1]
    except IndexError: #no positional argument provided. Default is working directory
            filename = '.'
    print(filename)
    if os.path.isfile(filename):
        root = etree.parse(filename)
        timeslots = getTimeslots(root)
        alignableannotations = getAlignableAnnotations(root)
        results = countVernacularWords(root,timeslots,alignableannotations) 
        for result in results:
            print("\t%s@%s: %s words (%s seconds)" % result)    
    elif os.path.isdir(filename):
        eafs = glob.glob("%s/*eaf"%filename) 
        globalwords = 0
        globalsecs = 0
        hours = "00:00:00"
        for eaf in eafs: 
            try:
                root = etree.parse(eaf)
            except etree.XMLSyntaxError:
                logging.warning("empty document %s"% eaf)
                continue
            try:
                timeslots = getTimeslots(root)
            except KeyError: 
                
                logging.warning("skipping %s (no time slots)" % eaf)
                continue
            alignableannotations = getAlignableAnnotations(root)
            results = countVernacularWords(root,timeslots,alignableannotations)
            for result in results:
                try:
                    globalwords += result[2] #aggregate words 
                    globalsecs += result[3] #aggregate time
                    hours = str(datetime.timedelta(seconds=globalsecs)).split('.')[0] #convert to human readable format
                except TypeError:
                    print("skipping %s" % eaf)
        print("Processed %i files in %s.\n%s transcribed in %i words." % (len(eafs),filename,hours, globalwords))
    else:
        print("path %s could not be found" %filename)
