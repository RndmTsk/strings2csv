#!/usr/bin/env python

import glob, os, sys, getopt, csv

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    if argv is None:
        argv = sys.argv

    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hf:", ["help"])
        except getopt.error, msg:
            raise Usage(msg)

    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2

    filename = "localizations.csv"
    for opt, arg in opts:
        if opt == "-f":
            filename = arg

    # Actual program start
    l10nsFile = filename
    stringsFiles = getStringsFiles(".")
    mergedStringsFiles = mergeStringsFiles(stringsFiles)
    languages = languageListFromFiles(mergedStringsFiles)

    with open(l10nsFile, 'wb') as csvfile:
        fieldnames = ["path", "file", "object-id", "comment"] + languages
        csvWriter = csv.writer(csvfile, delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)
        csvWriter.writerow(fieldnames)
        for mergedFileInfo in mergedStringsFiles:
            mergedFileContent = getMergedStringsFileContents(mergedFileInfo)
            for entry in mergedFileContent:
                values = []
                for lang in languages:
                    if lang in entry["value"]:
                        values.append(entry["value"][lang])
                    else:
                        values.append("") 

                row = [mergedFileInfo["path"], mergedFileInfo["name"], entry["object-id"], entry["comment"]] + values
                csvWriter.writerow(row)

# Functions
def completeFilename(file):
    return os.path.join(file["path"], file["lang"] + ".lproj", file["name"])

def mergedFilenameForLang(mergedFile, lang):
    return os.path.join(mergedFile["path"], lang + ".lproj", mergedFile["name"])

def languageListFromFiles(mergedFiles):
    result = []
    for mergedFile in mergedFiles:
        for lang in mergedFile["langs"]:
            if lang not in result:
                result.append(lang)

    return result 

# Strings File:
#   path => file path excluding <lang>.lproj
#   lang => en, fr, etc.
#   name => <filename>.strings
def getStringsFiles(start):
    stringsFiles = []
    for root, dirs, files in os.walk(start):
        stringsFiles += [{"path" : os.path.relpath(root).rstrip(os.path.basename(root)), "lang" : os.path.basename(root).rstrip("lproj")[:-1], "name" : file} for file in files if file.endswith(".strings")]

    return stringsFiles

# Merged Strings File:
#   path => file path excluding lang.lproj
#   langs => [en, fr [, ...]]
#   name => <filename>.strings
def mergeStringsFiles(files):
    result = {}
    for file in files:
        resultKey = file["path"] + file["name"]

        if resultKey in result:
            result[resultKey] = { "path" : file["path"], "langs" : result[file["path"] + file["name"]]["langs"] + [file["lang"]], "name" : file["name"] }
        else:
            result[resultKey] = { "path" : file["path"], "langs" : [file["lang"]], "name" : file["name"] }

    return result.values()

# Strings File Contents:
#   comment => /* ... */
#   object-id => LiR-e1-W2x
#   value => ['en' : my english string, 'fr' : my french string [, ...]]
def getMergedStringsFileContents(mergedFile):
    baseFilename = mergedFilenameForLang(mergedFile, mergedFile["langs"][0])
    mergedFileContents = getStringsFileContents(baseFilename, mergedFile["langs"][0])

    languages = mergedFile["langs"][1:]
    for lang in languages:
        filename = mergedFilenameForLang(mergedFile, lang)
        currentFileContents = getStringsFileContents(filename, lang)
        for (objectId, entry) in currentFileContents.iteritems():
            if mergedFileContents.get(objectId) == None:
                mergedFileContents[objectId] = entry
            else:
                mergedFileContents[objectId]["value"][lang] = entry["value"][lang]

    return mergedFileContents.values()

def getStringsFileContents(filename, lang):
    hasComment = False
    fileContents = {}
    with open(filename, 'r') as input:
        for line in input:
            line = line.strip()
            if not line: # Skip blank lines
                continue

            if line.startswith("/*") or line.startswith("//"):
                hasComment = True
                comment = line
                continue

            # TODO: (TL) Multi-line comments
            if line.endswith(";"):
                # Found a line that is a translation
                splitLine = line.split("=", 1)
                if splitLine[0].endswith(".text\" "):
                    objectId = splitLine[0].lstrip("\"").rstrip(".text\" ")
                else:
                    objectId = splitLine[0].lstrip("\"").rstrip("\" ")

                if hasComment and comment != None:
                    entry = { "comment" : comment }
                else:
                    entry = { "comment" : "" }
                entry["object-id"] = objectId
                entry["value"] = { lang : splitLine[1].lstrip(" \"").rstrip("\";") }
                fileContents[objectId] = entry
                hasComment = False
                comment = None

    return fileContents

# MAIN #
if __name__ == "__main__":
    sys.exit(main())
