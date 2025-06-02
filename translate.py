
from types import SimpleNamespace
import json
import re

def parseStGB():
    currentPar = None
    db = SimpleNamespace(
        title=None,
        paragraphs=dict(),
        fullText=list()
    )
    with open("raw/StGB.txt") as f:
        for linenr, line in enumerate(f):
            line = line.strip()

            if linenr == 0:
                db.title = line
                next

            if line == "":
                currentPar = None
                next

            if m := re.match(r"^(§ [0-9a-z]+)\. ?(.*)", line):
                if m[2] != "":
                    db.fullText.append([m[1], m[2]])
                else:
                    currentPar = m[1]
                next

            if currentPar is not None:
                if currentPar not in db.paragraphs:
                    db.paragraphs[currentPar] = list()
                db.paragraphs[currentPar].append(line)
                db.fullText.append([currentPar, line])

            else:
                if line.endswith(" Teil"):
                    headerType="h1"
                elif line.endswith(" Abschnitt"):
                    headerType="h2"
                elif len(db.fullText) and db.fullText[-1][0] == "h2":
                    headerType = "h3"
                else:
                    headerType = "h4"
                db.fullText.append([headerType, line])
    return db.__dict__

db = parseStGB()
print(json.dumps(db))

