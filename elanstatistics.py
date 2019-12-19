import os
import sys
import glob
import datetime
import json
import pprint
import logging
from lxml import etree
from langdetect import detect_langs,  lang_detect_exception
# for language identification in transcriptions
from tiernames import (
    acceptable_translation_tier_types,
    acceptable_transcription_tier_types,
    acceptable_word_tier_types,
    acceptable_gloss_tier_types,
    acceptable_pos_tier_types,
)

logging.basicConfig(filename="elanstatistics.log", level=logging.WARNING)
LANGDETECTTHRESHOLD = 0.95  # 85% seems to have no false positives in a first run


def get_timeslots(root):
    """
    Create a dictionary with time slot ID as keys and offset in ms as values
    """

    timeorder = root.find(".//TIME_ORDER")
    timeslots = {slot.attrib["TIME_SLOT_ID"]:slot.attrib["TIME_VALUE"]
                 for slot
                 in timeorder.findall("TIME_SLOT")
                }
    return timeslots


def get_alignable_annotations(root):
    """
  Create a dictionary with alignable annotations ID as keys and the elements themselves as values
  """

    aas = root.findall(".//ALIGNABLE_ANNOTATION")
    #d = dict([(aa.attrib["ANNOTATION_ID"], aa) for aa in aas])
    #d =
    return {aa.attrib["ANNOTATION_ID"]:aa for aa in aas}


def get_duration(annotation):
    """
  compute a list of durations of each annotation by substracting start times from end times
  """

    try:
        return int(timeslots[annotation.attrib["TIME_SLOT_REF2"]]) - int(
            timeslots[annotation.attrib["TIME_SLOT_REF1"]]
        )
    except AttributeError:
        return 0


def get_vernacular_words(root, timeslots, alignableannotations, filename):
    """
    Retrieve tiers with transcription in an ELAN file.
    Return the ID of the first tier found, the linguistic type matched,
    aggregate number of words, aggregate time.
    """

    # the LINGUISTIC_TYPE_REF's which contain vernacular sentences
    transcriptioncandidates = acceptable_transcription_tier_types
    transcriptions = {}
    time_in_seconds = []
    tierfound = False
    for candidate in transcriptioncandidates:
        # try different LINGUISTIC_TYPE_REF's to identify the relevant tiers
        querystring = "TIER[@LINGUISTIC_TYPE_REF='%s']" % candidate
        vernaculartiers = root.findall(querystring)
        if vernaculartiers != []:  # we found a tier of the linguistic type
            tierfound = True
            for tier in vernaculartiers:
                tierID = tier.attrib["TIER_ID"]
                # create a list of all words in that tier by splitting
                # and collating all annotation values of that tier
                wordlist = [
                    av.text.strip()
                    for av in tier.findall(".//ANNOTATION_VALUE")
                    if av.text is not None
                ]
                # get a list of duration from the time slots directly mentioned in annotations
                if wordlist == []:
                    continue
                timelist = [
                    get_duration(aa)
                    for aa in tier.findall(".//ALIGNABLE_ANNOTATION")
                    if aa.find(".//ANNOTATION_VALUE").text is not None
                ]
                # get a list of durations from time slots mentioned in parent elements
                timelistannno = [
                    get_duration(alignableannotations.get(ra.attrib["ANNOTATION_REF"]))
                    for ra in tier.findall(".//REF_ANNOTATION")
                    if ra.find(".//ANNOTATION_VALUE").text is not None
                ]
                secs = sum(timelist + timelistannno) / 1000
                time_in_seconds.append(secs)
                try:  # detect candidate languages and retrieve most likely one
                    toplanguage = detect_langs(" ".join(wordlist))[0]
                except lang_detect_exception.LangDetectException:
                    #we are happy that this is an unknown language
                    toplanguage = None
                #print(toplanguage)
                if (toplanguage
                        and toplanguage.lang == "en"
                        and toplanguage.prob > LANGDETECTTHRESHOLD):
                    # language is English
                    logging.warning(
                        'ignored vernacular tier with English language content at %.2f%% probability ("%s ...")'
                        % (toplanguage.prob * 100, " ".join(wordlist)[:100])
                    )
                    continue
                try:
                    transcriptions[candidate][tierID] = wordlist
                except KeyError:
                    transcriptions[candidate] = {}
                    transcriptions[candidate][tierID] = wordlist


                # output the amount found with tier type and ID
                # results.append((t.attrib["TIER_ID"],candidate,wordlist,secs))
    if not tierfound:  # there is no tier of the relevant type
        print(filename,
              {[x.attrib["LINGUISTIC_TYPE_REF"]
                for x
                in root.findall(".//TIER")]},
             )
    return transcriptions, time_in_seconds


def get_transcription(root, timeslots, alignableannotations, filename):
    """ compute total amounts of words and seconds transcribed """

    results = get_vernacular_words(root, timeslots, alignableannotations, filename)
    localwords = []
    localsecs = 0
    for result in results:
        tierID = result[0]
        tiertype = result[1]
        localwords.append(result[2]) #aggregate words
        localsecs += result[3] #aggregate time )
    return localwords, localsecs, tierID, tiertype


def get_translations(filename, root):
    """
    Check for tiers which contain translations.
    If tiers are not empty, check whether language is English
    Return a list of all tiers with lists of all words they contain in linear order
    """

    translationcandidates = acceptable_translation_tier_types
    translations = {}
    for candidate in translationcandidates:
        querystring = "TIER[@LINGUISTIC_TYPE_REF='%s']" % candidate
        translationtiers = root.findall(querystring)
        if translationtiers != []:  # we found a tier of the linguistic type
            for tier in translationtiers:
                tierID = tier.attrib["TIER_ID"]
                # create a list of all words in that tier
                wordlist = [
                    av.text.strip()
                    for av in tier.findall(".//ANNOTATION_VALUE")
                    if av.text is not None
                ]
                if wordlist == []:
                    continue
                # sometimes, annotators put non-English contents in translation tiers
                # for our purposes, we want to discard such content
                try:  # detect candidate languages and retrieve most likely one
                    toplanguage = detect_langs(" ".join(wordlist))[0]
                except lang_detect_exception.LangDetectException:
                    logging.warning(
                        "could not detect language for %s in %s" % (wordlist, filename)
                    )
                    continue
                if toplanguage.lang != "en":
                    continue
                if toplanguage.prob < LANGDETECTTHRESHOLD:
                    # language is English, but likelihood is too small
                    logging.warning(
                        'ignored %.2f%% probability English for "%s ..."'
                        % (toplanguage.prob * 100, " ".join(wordlist)[:100])
                    )
                    continue
                #how many words should the average annotation have for this
                #tier to be counted as translation?
                translation_minimum = 1.5
                avg_annotation_length = sum(
                    [len(x.strip().split()) for x in wordlist]
                ) / len(wordlist)
                if avg_annotation_length < translation_minimum:
                    logging.warning(
                        "%s has too short annotations (%s) for the tier to be a translation (%s ,...)"
                        % (tierID,
                           avg_annotation_length,
                           ", ".join(wordlist[:3])
                          )
                    )
                    continue
                try:
                    translations[candidate][tierID] = wordlist
                except KeyError:
                    translations[candidate] = {}
                    translations[candidate][tierID] = wordlist

    # if translations == []:
    # print(filename, [x.attrib["LINGUISTIC_TYPE_ID"] for x in root.findall(".//LINGUISTIC_TYPE")])
    return translations


def get_word_gloss_pairs(filename, root, parentdic):
    """retrieve all glosses from an eaf file and map to text from parent annotation"""

    def get_word_for_gloss(annotation_value):
        """retrieve the parent annotation's text"""

        # get the XML parent, called <REF_ANNOTATION>
        ref_annotation = annotation_value.getparent()
        # find the attributed called ANNOTATION_REF, which gives the ID of the referred annotation
        annotation_ref = ref_annotation.attrib["ANNOTATION_REF"]
        # retrieve the referenced annotation
        querystring = (
            ".//REF_ANNOTATION[@ANNOTATION_ID='%s']/ANNOTATION_VALUE" % annotation_ref
        )
        parent = root.find(querystring)
        return parent.text

    glosscandidates = acceptable_gloss_tier_types
    retrieved_glosstiers = {}

    for candidate in glosscandidates:
        querystring = "TIER[@LINGUISTIC_TYPE_REF='%s']" % candidate
        glosstiers = root.findall(querystring)
        if glosstiers != []:  # we found a tier of the linguistic type
            retrieved_glosstiers[candidate] = {}
            for tier in glosstiers:
                tierID = tier.attrib["TIER_ID"]
                parent = parentdic[tierID]
                parentID = parent.attrib["TIER_ID"]
                parent_type = parent.attrib["LINGUISTIC_TYPE_REF"]
                if not parent_type in acceptable_word_tier_types:
                    logging.warning(
                        "%s: Type %s is not accepted for potential parent %s of gloss candidate %s" %
                        (filename, parent_type, parentID, tierID)
                    )
                    continue
                # create a list of all annotations in that tier
                annotations = tier.findall(".//ANNOTATION_VALUE")
                # retrieve the text values associated with the parent annotations
                #(i.e., the vernacular words)
                words = [get_word_for_gloss(annotation) for annotation in annotations]
                # retrieve the glosses
                glosses = [
                    "" if av.text is None else av.text.strip() for av in annotations
                ]
                #print(len(words), len(glosses))
                retrieved_glosstiers[candidate][tierID] = (words, glosses)
    return retrieved_glosstiers


def create_parent_dic(root, filename):
    """
    match all tier IDs with the referenced parent IDs

    The parents are not the XML parents but are different tiers,
    which are the logical parents of a tier
    """
    dico = {}
    tiers = root.findall(".//TIER")
    for tier in tiers:
        TIER_ID = tier.attrib["TIER_ID"]
        # map all tiers to their parent tiers
        PARENT_ID = tier.attrib.get("PARENT_REF")
        parent = None
        if PARENT_ID:
            parent = root.find(".//TIER[@TIER_ID='%s']" % PARENT_ID)
        dico[TIER_ID] = parent
    return dico


if __name__ == "__main__":
    """
    usage: > python3 elanstatistics.py myfile.eaf
    The script checks for tiers which contain transcribed text in an given ELAN file
    The words in this tier are counted and if possible matched to time codes
    Tiers which look like translation tiers are checked whether
    they contain English translations.
    Words in translation tiers are counted and the tally is printed.

    usage: > python3 elanstatistics.py somedirectory
    As above, but for all files in directory.

    usage: > python3 elanstatistics.py
    As above, but for working directory .
    """

    try:
        filename = sys.argv[1]
    except IndexError:  # no positional argument provided. Default is working directory
        filename = "."
    print("processing", filename)
    if os.path.isfile(filename):  # argument is a single file FIXME currently broken
        pass
        #root = etree.parse(filename)
        #timeslots = get_timeslots(root)
        #alignableannotations = get_alignable_annotations(root)
        #seconds, words = get_transcription(
            #root, timeslots, alignableannotations, filename
        #)
        #print("%s words (%s seconds)" % (len(words), seconds))
        #translations = get_translations(filename, root)
        #translationsummary = [len(x) for x in translations]
        #print("translation length: %s words" % (sum([len(x) for x in translations])))
    elif os.path.isdir(filename):  # argument is a directory
        LIMIT = 999999999
        # LIMIT = 113 #for development purposes, only process a subset of a directory
        eafs = sorted(glob.glob("%s/*eaf" % filename))[:LIMIT]
        # default values for output
        globalwordcount = 0
        globalsecondcount = 0
        hours = "00:00:00"

        eaftranslations = {}  # match filenames with the translations they contain
        eaftranscriptions = {}  # match filenames with the transcriptions they contain
        eafwordglosses = {}  # match filenames with the glosses they contain
        for eaf in eafs:
            try:
                xmlroot = etree.parse(eaf)
            except etree.XMLSyntaxError:
                logging.warning("empty document %s", eaf)
                continue
            try:
                timeslots = get_timeslots(xmlroot)
            except KeyError:
                logging.warning("skipping %s (no time slots)", eaf)
                continue
            except AttributeError:
                logging.warning("skipping %s (no time slots)", eaf)
                continue
            parentdic = create_parent_dic(xmlroot, eaf)
            # get transcription info
            alignableannotations = get_alignable_annotations(xmlroot)
            transcriptionresults = get_vernacular_words(xmlroot,
                                                        timeslots,
                                                        alignableannotations,
                                                        eaf)
            transcriptiontiers = transcriptionresults[0]
            # transcriptions = [t for t in transcriptionresults[0]]
            globalwordcount += sum([len(tier) for tier in transcriptiontiers])
            #print(globalwordcount)
            #globalsecondcount += transcriptionresults[1]
            times = transcriptionresults[1]
            # tiertype = transcriptionresults[3]
            eaftranscriptions[eaf] = transcriptionresults[0]
            #get translation info
            TRANSLATIONS = get_translations(eaf, xmlroot)
            eaftranslations[eaf] = TRANSLATIONS
            #TRANSLATIONSUMMARY = [len(x) for x in TRANSLATIONS]
            glosses = get_word_gloss_pairs(eaf, xmlroot, parentdic)
            eafwordglosses[eaf] = glosses

        # compute statistics
        englishwordcount = sum([len(tier)
                                for key
                                in eaftranslations
                                for tier
                                in eaftranslations[key]]
                              )
        #convert to human readable format
        HOURS = str(datetime.timedelta(seconds=globalsecondcount)).split('.')[0]
        #save translations
        with open("translations-%s.json" % filename, "w") as jsonfile:
            jsonfile.write(
                json.dumps(
                    eaftranslations, sort_keys=True, ensure_ascii=False, indent=4
                )
            )
        with open("transcriptions-%s.json" % filename, "w") as jsonfile:
            jsonfile.write(
                json.dumps(
                    eaftranscriptions, sort_keys=True, ensure_ascii=False, indent=4
                )
            )
        with open("glosses-%s.json" % filename, "w") as jsonfile:
            jsonfile.write(
                json.dumps(eafwordglosses, sort_keys=True, ensure_ascii=False, indent=4)
            )
        #print results
        print("Processed %i files in %s.\n%s transcribed in %i words." % (len(eafs),
                                                                          filename,
                                                                          hours,
                                                                          globalwordcount))
        print(
            "Total translations into English: %i words in %i files of directory %s/ (of total %i files)"
            % (
                englishwordcount,
                len([x for x in eaftranslations if eaftranslations[x] != []]),
                os.path.abspath(filename).split("/")[-1],
                len(eaftranslations),
            )
        )
    else:  # invalid argument
        print("path %s could not be found" % filename)
