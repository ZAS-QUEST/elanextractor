import glob
from collections import Counter

def check_tier(filename):
    """check how many tiers there are in a given file"""
    with open(filename) as file_:
        content = file_.read()
        count = content.count("<TIER ")
        return count

if __name__ == "__main__":
    # retrieve all ELAN files and check for tiers
    # count tiers for each file
    # print how many tiers are found in how many files
    LIMIT = 112
    TIERCOUNTS = [check_tier(f) for f in glob.glob("eafs/*")[:LIMIT]]
    COUNTED_COUNTS = Counter(TIERCOUNTS)
    for key in sorted(COUNTED_COUNTS.keys()):
        print(key, COUNTED_COUNTS[key])
