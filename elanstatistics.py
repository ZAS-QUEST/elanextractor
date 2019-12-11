import os 
import sys
import glob
import datetime
import json
from lxml import etree 
from langdetect import detect_langs, lang_detect_exception  #for language identification in transcriptions
langdetectthreshold = .95 #85% seems to have no false positives in a first run
import logging
logging.basicConfig(filename='elanstatistics.log',level=logging.WARNING)
import pprint


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
  

def getVernacularWords(root,timeslots,alignableannotations,filename):
  """
  Retrieve tiers with transcription in an ELAN file. 
  Return the ID of the first tier found, the linguistic type matched, aggregate number of words, aggregate time. 
  """
  
  #the LINGUISTIC_TYPE_REF's which contain vernacular sentences
  transcriptioncandidates = [
        'arta',
        'Arta',
        'conversación',
        'default-lt',#needs qualification
        'default-lt',
        'en', #very experimental, could be used for English but is used in 0214 files
        'Fonética',
        'Frases', 
        'Hablado',
        'Hija',
        'hija',
        'ilokano',
        'interlinear-text-item',
        'Ikaan sentences',
        'Khanty Speech',  
        'main-tier',
        'Madre',
        'madre',
        'Matanvat text',
        'Nese Utterances',
        'po (practical orthography)'
        'o', 
        'or',   
        'orth',
        'orthT',
        'orthografia',
        'orthografía',
        'orthography',
        'po (practical orthography)',
        'Phrases',
        'Practical Orthography',
        'sentences',
        'Sumi',
        't',#check this
        'Tamang',
        'text',
        'Text',
        'texto',
        'Texto',
        'texto ',
        'time aligned',#check this
        'timed chunk',
        'tl',#check this
        'transcript', 
        'transcription', 
        'transcription', 
        'transcription_orthography',
        'trs',
        'Transcription',
        'Transcripción',
        'Transcrição',
        'TRANSCRIÇÃO',
        'tx', #check usages of this 
        'tx2', #check usages of this 
        'txt',
        'type_utterance',
        'unit', #some Dutch texts from TLA
        'ut', 
        'Utterance',
        'utterance',
        'utterances',
        'utterance transcription',
        'UtteranceType', 
        'vernacular', 
        'Vernacular', 
        'vilela',
        'Vilela',
        'word-txt', 
        #'Word', #probably more often used for glossing 
        #'word', #probably more often used for glossing 
        'word_orthography',
        #'words', #probably more often used for glossing 
        #'Words', #more often used for glossing 
        'default transcript',
        '句子',
        '句子 ',
        '句子 '
      ]
  transcriptions = {}
  time_in_seconds = []
  tierfound = False
  for candidate in transcriptioncandidates:   
        #try different LINGUISTIC_TYPE_REF's to identify the relevant tiers
        querystring = "TIER[@LINGUISTIC_TYPE_REF='%s']"%candidate 
        vernaculartiers = root.findall(querystring)
        if vernaculartiers != []: #we found a tier of the linguistic type
            tierfound = True
            for t in vernaculartiers: 
                tierID =  t.attrib["TIER_ID"]
                #create a list of all words in that tier by splitting and collating all annotation values of that tier
                wordlist = [av.text.strip() 
                                            for av in t.findall(".//ANNOTATION_VALUE")
                                            if av.text!=None 
                            ]  
                #get a list of duration from the time slots directly mentioned in annotations 
                if wordlist == []:
                    continue 
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
                time_in_seconds.append(secs)
                try:
                    transcriptions[candidate][tierID] = wordlist
                except KeyError:
                    transcriptions[candidate] = {}
                    transcriptions[candidate][tierID] = wordlist
                
                
                #output the amount found with tier type and ID
                #results.append((t.attrib["TIER_ID"],candidate,wordlist,secs)) 
  if not tierfound: #there is no tier of the relevant type 
      print(filename, list(set([x.attrib["LINGUISTIC_TYPE_REF"] for x in root.findall(".//TIER")]))) 
  return transcriptions, time_in_seconds 


#def getTranscription(root,timeslots,alignableannotations,filename):       
    #""" compute total amounts of words and seconds transcribed """
    
    #results = getVernacularWords(root,timeslots,alignableannotations, filename) 
    #localwords = []
    #localsecs = 0
    #for result in results:
        #tierID = result[0]
        #tiertype = result[1]
        #localwords.append(result[2]) #aggregate words 
        #localsecs += result[3] #aggregate time )      
    #return localwords, localsecs, tierID, tiertype
        
    
def getTranslations(filename,root): 
    """
    Check for tiers which contain translations. 
    If tiers are not empty, check whether language is English 
    Return a list of all tiers with lists of all words they contain in linear order 
    """
        
    translationcandidates = [
        'eng', 
        'english translation',
        'English translation',
        'fe',
        'fg',
        'fn',
        'fr',
        'free translation',
        'Free Translation',
        'Free Translation (English)',
        'ft',
        'fte', 
        'tf (free translation)',
        'tf (free translation)',
        'tf_eng (free english translation)',
        'tl',
        'tn',
        'tn (translation in lingua franca)',
        'trad',
        'traduccion', 
        'traducción',
        'traducción ', 
        'Traducción',
        'Traduction',
        'translation', 
        'translations', 
        'Translation', 
        '翻译'
      ]
    translations = {}
    for candidate in translationcandidates:  
        querystring = "TIER[@LINGUISTIC_TYPE_REF='%s']"%candidate 
        translationtiers = root.findall(querystring) 
        if translationtiers != []: #we found a tier of the linguistic type
            for t in translationtiers:
                tierID =  t.attrib["TIER_ID"]
                #create a list of all words in that tier
                wordlist = [av.text for av   
                                    in t.findall(".//ANNOTATION_VALUE")
                                    if av.text!=None
                            ]  
                if wordlist == []:
                    continue  
                #sometimes, annotators put non-English contents in translation tiers
                #for our purposes, we want to discard such content
                try: #detect candidate languages and retrieve most likely one
                    toplanguage = detect_langs(' '.join(wordlist) )[0] 
                except lang_detect_exception.LangDetectException:
                    logging.warning("could not detect language for %s in %s"%(wordlist, filename))
                    continue
                if toplanguage.lang != 'en':
                    continue
                if toplanguage.prob < langdetectthreshold: #language is English, but likelihood is too small
                    logging.warning('ignored %.2f%% probability English for "%s ..."' %(toplanguage.prob*100,' '.join(wordlist)[:100]))
                    continue  
                try:
                    translations[candidate][tierID] = wordlist
                except KeyError:
                    translations[candidate] = {}
                    translations[candidate][tierID] = wordlist
                
    #if translations == []:
      #print(filename, [x.attrib["LINGUISTIC_TYPE_ID"] for x in root.findall(".//LINGUISTIC_TYPE")]) 
    return translations
                                
    
if __name__ == "__main__":  
    """
    usage: > python3 elanstatistics.py myfile.eaf
    The script checks for tiers which contain transcribed text in an given ELAN file
    The words in this tier are counted and if possible matched to time codes
    Tiers which look like translation tiers are checked whether they contain English translations. 
    Words in translation tiers are counted and the tally is printed.
    
    usage: > python3 elanstatistics.py somedirectory
    As above, but for all files in directory.  
    
    usage: > python3 elanstatistics.py 
    As above, but for working directory .       
    """
    
    try:
            filename = sys.argv[1]
    except IndexError: #no positional argument provided. Default is working directory
            filename = '.'
    print("processing", filename)
    if os.path.isfile(filename): #argument is a single file FIXME currently broken
        root = etree.parse(filename)
        timeslots = getTimeslots(root)
        alignableannotations = getAlignableAnnotations(root) 
        seconds, words = getTranscription(root,timeslots,alignableannotations,filename) 
        print("%s words (%s seconds)" % (len(words), seconds))   
        translations = getTranslations(filename, root)
        translationsummary = [len(x) for x in translations]
        print("translation length: %s words" %(sum([len(x) for x in translations])))       
    elif os.path.isdir(filename): #argument is a directory
        limit = 999999999
        limit = 113 #for development purposes, only process a subset of a directory
        eafs = glob.glob("%s/*eaf"%filename)[:limit]
        #default values for output
        globalwordcount = 0
        globalsecondcount = 0
        hours = "00:00:00"
        
        eaftranslations = {} #match filenames with the translations they contain
        eaftranscriptions = {} #match filenames with the transcriptions they contain
        for eaf in eafs:  
            print(eaf)
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
            except AttributeError:                 
                logging.warning("skipping %s (no time slots)" % eaf)
                continue
            #get transcription info
            alignableannotations = getAlignableAnnotations(root)                   
            transcriptionresults = getVernacularWords(root,timeslots,alignableannotations,eaf)
            print(transcriptionresults)
            transcriptiontiers = transcriptionresults[0]  
            #transcriptions = [t for t in transcriptionresults[0]] 
            globalwordcount += sum([len(tier) for tier in transcriptiontiers])
            #print(globalwordcount)
            ##globalsecondcount += transcriptionresults[1] 
            times = transcriptionresults[1] 
            #tiertype = transcriptionresults[3]  
            eaftranscriptions[eaf] = transcriptionresults[0]
            ##get translation info
            #translations = getTranslations(eaf, root)
            #eaftranslations[eaf] = translations
            #translationsummary = [len(x) for x in translations]
        
        #compute statistics
        pprint.pprint(eaftranslations)
        englishwordcount = sum([len(tier) for key in eaftranslations for tier in eaftranslations[key]])
        #hours = str(datetime.timedelta(seconds=globalsecondcount)).split('.')[0] #convert to human readable format 
        #save translations
        with open('translations.json', 'w') as jsonfile: 
            jsonfile.write(json.dumps(eaftranslations, sort_keys=True,  ensure_ascii=False, indent=4))
        with open('transcriptions.json', 'w') as jsonfile: 
            jsonfile.write(json.dumps(eaftranscriptions, sort_keys=True, ensure_ascii=False, indent=4))
        #print results
        #print("Processed %i files in %s.\n%s transcribed in %i words." % (len(eafs), filename, hours, globalwordcount))
        print("Total translations into English have %i words in %i files of directory %s/ (of total %i files)" % (englishwordcount, len([x for x in eaftranslations if eaftranslations[x] != []]), os.path.abspath(filename).split('/')[-1], len(eaftranslations)))
    else: #invalid argument
        print("path %s could not be found" %filename)
