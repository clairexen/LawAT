#!/usr/bin/env python3
# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

"""
# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

Use with `from RisEnQuery import *`.
Run `tx(intro())` (or `md(intro())`) for an introduction
"""

_rex_src, _rex_repcnt = None, 0
#/#_rex_src, _rex_repcnt = "RisExFiles.zip", 1 # replace(count=1)
#/#_rex_src, _rex_repcnt = "RisExData.json", 2 # replace(count=2)
#/#_rex_src, _rex_repcnt = "/mnd/data/RisExFiles.zip", 3 # replace(count=3)
#/#_rex_src, _rex_repcnt = "/mnd/data/RisExData.json", 4 # replace(count=4)

def intro():
    """
        Return the introduction message for RisEnQuery.py.
    """
    return """
Utility library for accessing and searching RisExFiles.zip.

Import as follows in Chat-GPT(-like) script environments:
```
exec(open("/mnt/data/RisEnQuery.py").read().replace("#/#", "", count=3))  # Use /mnd/data/RisExFiles.zip
exec(open("/mnt/data/RisEnQuery.py").read().replace("#/#", "", count=4))  # Use /mnd/data/RisExFiles.json
```

Formatbeschreibung (zipped) Markdown+JSON-Datensätze in RisExFiles.zip
======================================================================

- Längere Normen sind in Blöcke zu je ca. 20 kB zerteilt
- Paragraphenbeginn: "### § <nr> StGB. # <titel>" (Markdown H3)
- Paragraph ohne Absätze: "`§ <nr> StGB.`␣␣\n<text>" (Markdown "quoted code", 2x space + newline)
- Bzw. für jeden Absatz: "`§ <nr> (<abs>) StGB.`␣␣\n<text>" (Markdown "quoted code", 2x space + newline)
- Unterpunkte: "`§ <nr> (<abs>) Z <Z> lit. <lit> StGB.`\n<text>" (ohne 2x space)
- TOC (`.index.json`) referenziert exakt die Zeilennummern der Überschriften im Markdown
- Trennung der Paragraphen durch nächste "### §"-Zeile oder "## "-Heading oder Dateiende
- Unicode-Zeichen (ä, ß, etc.) und geschützte Leerzeichen (\xa0) möglich


RisEnQuery – Kurzdokumentation
==============================

```
# Either import it as module from the current working directory
from RisEnQuery import *

# or load and execute the uploaded Python file directly
exec(open("/mnt/data/RisEnQuery.py").read().replace("#/#", "", 1))
```

Example Session:

```
>>> from RisEnQuery import *
>>> tx(toc("Begr", "BG.StGB"))
## Achter Abschnitt # Begriffsbestimmungen | BG.StGB.004:11-12
### § 74 StGB # Andere Begriffsbestimmungen | BG.StGB.004:58-108
### § 255 StGB # Begriff des Staatsgeheimnisses | BG.StGB.010:149-153

>>> hd(fetch("BG.StGB.004:11-109"))
## Achter Abschnitt # Begriffsbestimmungen
### § 68 StGB # Zeitberechnung
### § 69 StGB # Öffentliche Begehung
### § 70 StGB # Gewerbsmäßige Begehung
### § 71 StGB # Schädliche Neigung
### § 72 StGB # Angehörige
### § 73 StGB # Ausländische Verurteilungen
### § 74 StGB # Andere Begriffsbestimmungen
## Besonderer Teil # Erster Abschnitt # Strafbare Handlungen gegen Leib und Leben

>>> sel("BG.StGB", "BG.StPO")
>>> toc("+Eltern")[:3]
[('### § 72 StGB # Angehörige', 'BG.StGB.004:45-52'), ('### § 240 StPO', 'BG.StPO.015:18-22')]

>>> sel("BG.ABGB")
>>> toc("+Eltern")[:3]
[('## Drittes Hauptstück # Rechte zwischen Eltern und Kindern # Erster Abschnitt # Allgemeine Bestimmungen', 'BG.ABGB.002:11-12'), ('### § 137 ABGB # Allgemeine Grundsätze', 'BG.ABGB.002:13-20'), ('### § 138 ABGB # Kindeswohl', 'BG.ABGB.002:21-49')]

>>> sel() # Reset Selection

>>> with sel("BG.StPO", "BG.StGB"): utoc("+Anzeig") # Change selection temporarily
### § 25 StPO # Örtliche Zuständigkeit | BG.StPO.001:278-302
### § 25a StPO # Abtretung | BG.StPO.001:303-310
### § 44 StPO # Anzeige der Ausgeschlossenheit und Antrag auf Ablehnung | BG.StPO.003:33-43
### § 66 StPO # Opferrechte | BG.StPO.004:169-200
## 3. Abschnitt # Anzeigepflicht, Anzeige- und Anhalterecht | BG.StPO.005:131-132
### § 78 StPO # Anzeigepflicht | BG.StPO.005:133-147
### § 79 StPO | BG.StPO.005:148-152
### § 80 StPO # Anzeige- und Anhalterecht | BG.StPO.005:153-160
### § 99 StPO # Ermittlungen | BG.StPO.006:202-222
### § 100 StPO # Berichte | BG.StPO.006:223-255
### § 108 StPO # Antrag auf Einstellung | BG.StPO.007:111-137
### § 147 StPO | BG.StPO.010:85-113
### § 155 StPO # Verbot der Vernehmung als Zeuge | BG.StPO.010:188-203
### § 390 StPO | BG.StPO.021:125-141
### § 393 StPO | BG.StPO.021:162-182
### § 298 StGB # Vortäuschung einer mit Strafe bedrohten Handlung | BG.StGB.012:117-124


>>> with sel("BG.StPO", "BG.StGB", "BG.ABGB"): uls("*.toc.md")
BG.ABGB.toc.md
BG.StGB.toc.md
BG.StPO.toc.md


>>> tx(get("§ 71 StGB"))
### § 71 StGB # Schädliche Neigung | BG.StGB.004:40-44

`§ 71 StGB.`
Auf der gleichen schädlichen Neigung beruhen mit Strafe bedrohte Handlungen, wenn sie gegen dasselbe Rechtsgut gerichtet oder auf gleichartige verwerfliche Beweggründe oder auf den gleichen Charaktermangel zurückzuführen sind.

>>> tx(get(" § 74 StGB ").split("\n")[9:18])
`§ 74 (1) Z 4 StGB.`
Beamter: jeder, der bestellt ist, im Namen des Bundes, eines Landes, eines Gemeindeverbandes, einer Gemeinde oder einer anderen Person des öffentlichen Rechtes, ausgenommen einer Kirche oder Religionsgesellschaft, als deren Organ allein oder gemeinsam mit einem anderen Rechtshandlungen vorzunehmen, oder sonst mit Aufgaben der Bundes-, Landes- oder Gemeindeverwaltung betraut ist; als Beamter gilt auch, wer nach einem anderen Bundesgesetz oder auf Grund einer zwischenstaatlichen Vereinbarung bei einem Einsatz im Inland einem österreichischen Beamten gleichgestellt ist;
`§ 74 (1) Z 4a StGB.`
Amtsträger: jeder, der
(Anm.: lit. a aufgehoben durch BGBl. I Nr. 61/2012)
`§ 74 (1) Z 4a lit. b StGB.`
für den Bund, ein Land, einen Gemeindeverband, eine Gemeinde, für eine andere Person des öffentlichen Rechts, ausgenommen eine Kirche oder Religionsgesellschaft, für einen anderen Staat oder für eine internationale Organisation Aufgaben der Gesetzgebung, Verwaltung oder Justiz als deren Organ oder Dienstnehmer wahrnimmt, Unionsbeamter (Z 4b) ist oder - für die Zwecke der §§ 168g, 304, 305, 307 und 307a - der öffentliche Aufgaben im Zusammenhang mit der Verwaltung der oder Entscheidungen über die finanziellen Interessen der Europäischen Union in Mitgliedstaaten oder Drittstaaten übertragen bekommen hat und diese Aufgaben wahrnimmt,
`§ 74 (1) Z 4a lit. c StGB.`
sonst im Namen der in lit. b genannten Körperschaften befugt ist, in Vollziehung der Gesetze Amtsgeschäfte vorzunehmen, oder

>>> tx(untag(get(" § 74 StGB ").split("\n")[9:18]))
`  4.`
Beamter: jeder, der bestellt ist, im Namen des Bundes, eines Landes, eines Gemeindeverbandes, einer Gemeinde oder einer anderen Person des öffentlichen Rechtes, ausgenommen einer Kirche oder Religionsgesellschaft, als deren Organ allein oder gemeinsam mit einem anderen Rechtshandlungen vorzunehmen, oder sonst mit Aufgaben der Bundes-, Landes- oder Gemeindeverwaltung betraut ist; als Beamter gilt auch, wer nach einem anderen Bundesgesetz oder auf Grund einer zwischenstaatlichen Vereinbarung bei einem Einsatz im Inland einem österreichischen Beamten gleichgestellt ist;
`  4a.`
Amtsträger: jeder, der
(Anm.: lit. a aufgehoben durch BGBl. I Nr. 61/2012)
`    b)`
für den Bund, ein Land, einen Gemeindeverband, eine Gemeinde, für eine andere Person des öffentlichen Rechts, ausgenommen eine Kirche oder Religionsgesellschaft, für einen anderen Staat oder für eine internationale Organisation Aufgaben der Gesetzgebung, Verwaltung oder Justiz als deren Organ oder Dienstnehmer wahrnimmt, Unionsbeamter (Z 4b) ist oder - für die Zwecke der §§ 168g, 304, 305, 307 und 307a - der öffentliche Aufgaben im Zusammenhang mit der Verwaltung der oder Entscheidungen über die finanziellen Interessen der Europäischen Union in Mitgliedstaaten oder Drittstaaten übertragen bekommen hat und diese Aufgaben wahrnimmt,
`    c)`
sonst im Namen der in lit. b genannten Körperschaften befugt ist, in Vollziehung der Gesetze Amtsgeschäfte vorzunehmen, oder

>>> tx(toc(find("+verfälscht", "BG.StGB") & find("+Urkund", "BG.StGB"))) # Liste der StGB Paragraphen mit "verfälscht" und "Urkund" im Text
### § 147 StGB # Schwerer Betrug | BG.StGB.006:496-518
### § 223 StGB # Urkundenfälschung | BG.StGB.009:33-40
### § 224a StGB # Annahme, Weitergabe oder Besitz falscher oder verfälschter besonders geschützter Urkunden | BG.StGB.009:46-50
### § 226 StGB # Tätige Reue | BG.StGB.009:67-74
### § 264 StGB # Verbreitung falscher Nachrichten bei einer Wahl oder Volksabstimmung | BG.StGB.010:218-225

>>> tx(grep("Urkund", get("", "BG.StGB"))) # Volltextsuche nach "Urkund" im StGB

## Achter Abschnitt # Begriffsbestimmungen | BG.StGB.004:11-12

### § 74 StGB # Andere Begriffsbestimmungen | BG.StGB.004:58-108

Urkunde: eine Schrift, die errichtet worden ist, um ein Recht oder ein Rechtsverhältnis zu begründen, abzuändern oder aufzuheben oder eine Tatsache von rechtlicher Bedeutung zu beweisen;

## Sechster Abschnitt # Strafbare Handlungen gegen fremdes Vermögen | BG.StGB.006:209-210

### § 147 StGB # Schwerer Betrug | BG.StGB.006:496-518

eine falsche oder verfälschte Urkunde, ein falsches, verfälschtes oder entfremdetes unbares Zahlungsmittel, ausgespähte Daten eines unbaren Zahlungsmittels, falsche oder verfälschte Daten, ein anderes solches Beweismittel oder ein unrichtiges Meßgerät benützt oder

### § 165 StGB # Geldwäscherei | BG.StGB.006:894-925
...
```

Zweck:
------
RisEnQuery.py ermöglicht den Zugriff auf Gesetzesdateien im ZIP-Archiv "RisExFiles.zip". Es erlaubt strukturierte Suchen in Inhaltsverzeichnissen (.index.json) und den Abruf von Gesetzestexten (.md).

Funktionen:
-----------
- intro():
  → Gibt diesen Einführungstext zurück.

- ls(normPat=None):
  → Gibt eine Liste aller (matchender) Normen im Archiv zurück.

- fetch(filename):
  → Lädt eine Datei (Text oder JSON) aus dem Archiv. Ergebnisse werden im Cache gespeichert.

- pat(pattern):
  → Erstellt ein Regex-Objekt aus einem Shell-Muster, Fix-String (=) oder RegEx (/).

- sel(*p):
  → Selektiert die Liste der Normen die bei toc(), get(), und find() verwendet werden
     wenn normPat den Wert None hat. (Reset mit sel() ohne argumente.)

- toc(searchPat, normPat=None):
  → Durchsucht .index.json-Dateien nach Überschriften, die dem Muster entsprechen.
     Gibt eine liste der gefundenden Überschriften zurück.  WICHTIG: Die Dateinamen
     beginnen mit dem Typ des Gesetzes. Also zB "BG.StGB", nicht nur "StGB".

- get(searchPat, normPat=None):
  → Durchsucht .index.json-Dateien nach Überschriften, die dem Muster entsprechen.
     Zitiert die gefundenden Paragraphen vollständig.

- find(searchPat, normPat=None):
  → Ähnlich toc() und get(), aber gibt ein set von fetch keys zurück.

- grep(grepPat, data):
  → Durchsucht die string(s) im zweiten Argument nach dem pattern.

- untag(data):
  → Gibt die Eingabe mit den Citation-Tags für Aufzählungspunkte (wie
     zB `§ 74 (1) Z 4a StGB.` und `§ 74 (1) Z 4a lit. b StGB.`) mit
     dem entsprechenden Originaltext der Norm (also zB `  4a.` und
     `    b)`) ersetzt zurück. Die Ausgabe von untag(), bzw. das
     Ausgabeformat von untag(), ist, wie die Normen dem Anwender
     zitiert werden sollten.

- tx(data):
  → Ausgabe auf der Konsole in plain ASCII

- hd(data):
  → Ausgabe der Überschriften aus dem Markdown text

- md(data):
  → Ausgabe von vormattiertem Markdown auf der Konsole mit ANSI escape codes (mit rich.markdown)

WICHTIG:
--------
Immer zuerst die Datenbank (RisEnQuery.py und RisExFiles.zip) befragen, bevor internes Wissen verwendet wird.
Normbegriffe können ähnlich, aber unterschiedlich zwischen Ländern oder Paragrafen sein.
Nur durch die Datenbank kann sichergestellt werden, dass nach österreichischem Recht korrekt zitiert wird.

Merksatz: "Immer zuerst toc() oder get() – nie raten!"
"""

import json, os, sys, re, fnmatch

if _rex_src is None:
    import glob
    _rex_dir = {"index.json"} | {fn.removeprefix("files/") for fn in glob.glob("files/*")}
    _rex_rd_text = lambda fn: open(fn if fn == "index.json" else f"files/{fn}").read()
    _rex_rd_json = lambda fn: json.load(open(fn if fn == "index.json" else f"files/{fn}"))

elif _rex_src.endswith(".zip"):
    import zipfile
    _rex_zip = zipfile.ZipFile(_rex_zipPath)
    _rex_dir = set([f.filename for f in _rex_zip.filelist])
    _rex_rd_text = lambda fn: _rex_zip.open(fn).read().decode()
    _rex_rd_json = lambda fn: json.load(_rex_zip.open(fn))

elif _rex_src.endswith(".json"):
    _rex_json = json.load(open(_rex_src))
    _rex_dir = set(_rex_json.keys())
    _rex_rd_text = _rex_json.get
    _rex_rd_json = _rex_json.get

else:
    assert False, f"Unrecognized files extension: {_rex_src}"

_rex_trace = False
_rex_ls_cache = dict()
_rex_fetch_cache = dict()
_rex_selected = None
_rex_index = _rex_rd_json("index.json")
_rex_sorted_norms = tuple(sorted(_rex_index.keys()))
_rex_is_upy = sys.implementation.name == 'micropython'

def reload(count=None):
    """
        Reload RisEnQuery.py (and clear caches)
    """
    if count is None:
        count = _rex_repcnt
    if _rex_repcnt in (0, 1, 2):
        pySrcFile = "RisEnQuery.py"
    elif _rex_repcnt in (3, 4):
        pySrcFile = "/mnt/data/RisEnQuery.py"
    exec(open(pySrcFile).read().replace("#/#", "", count), globals())

def ls(p: str = None):
    """
        Return the list of currently selected norms.
    """

    if p is None:
        if _rex_selected is not None:
            return _rex_selected
        return _rex_sorted_norms

    if (key := (p, _rex_selected)) not in _rex_ls_cache:
        normPat = pat(p) if p is not None else None
        normList = list()
        for n in ls():
            if normPat is None or normPat.fullmatch(n):
                normList.append(n)
        if len(normList) == 0 and "." not in p:
            for n in ls():
                if normPat is None or normPat.fullmatch(n.split(".", 1)[1]):
                    normList.append(n)
        _rex_ls_cache[key] = tuple(normList)
    return _rex_ls_cache[key]

def fetch(key: str):
    """
        Fetch a file (by file name) from RisExFiles.zip.

        If fn ends with .json, the parsed JSON data
        structure is returned.

        If fn ends with :N or :N-M, the line N or the
        lines M-N are returned as a single multi-line string.

        Otherwise all the lines of the entire text
        file are returned as a list.
    """

    if key not in _rex_fetch_cache:
        if ":" in key:
            fn, ln = key.split(":", 1)
            if "-" in ln:
                fromLine, toLine = ln.split("-", 1)
            else:
                fromLine, toLine = ln, ln
            _rex_fetch_cache[key] = "\n".join(fetch(fn)[int(fromLine)-1:int(toLine)])

        else:
            fn = key
            if fn not in _rex_dir:
                for ext in (".json", ".md"):
                    if (fn + ext) in _rex_dir: fn += ext; break
            src = _rex_src if _rex_src is not None else "files/"
            if fn.endswith(".json"):
                if _rex_trace:
                    print(f"Fetching JSON from '{src}': {fn}", file=sys.stderr)
                _rex_fetch_cache[key] = _rex_rd_json(fn)
            else:
                if _rex_trace:
                    print(f"Fetching TEXT from '{src}': {fn}", file=sys.stderr)
                data = _rex_rd_text(fn)
                if type(data) is str:
                    data = data.split("\n")
                _rex_fetch_cache[key] = data

    return _rex_fetch_cache[key]

def pat(s: str) -> re.Pattern:
    """
        Compile the given shell pattern or regex into
        a re.Pattern object and return it.

        If the pattern starts with a forward slash (/) then
        that forward slash is removed from 's' and the
        remaining string is treated as a regex.

        If the pattern starts with an equal-sign (=) then
        the remaining string is a fixed string, not
        a pattern off any kind.

        Otherwise the string in 's' is treated as a
        shell pattern and is converted to a regex via
        fnmatch.translate().

        If the pattern is prefixed with a plus sign (+) then
        the pattern is applied to the entire text of the
        sections being searched, not just the section header.

        In either case the special syntax <FROM-TO>
        (for example <12-345>) matches all integers
        in the specified range.
    """

    if type(s) is re.Pattern:
        return s

    def handleRangePatterns(s: str) -> str:
        def rangeRegex(n: int, m: int) -> str:
            return '(?:0*(?:' + "|".join([str(i) for i in range(n, m+1)]) + '))'
        def replacer(match):
            n, m = int(match.group(1)), int(match.group(2))
            return rangeRegex(min(n, m), max(n, m))
        return re.sub(r"<(\d+)\\?-(\d+)>", replacer, s)

    matchFullTextTag = "(?#MatchFullTextTag)" if s.startswith("+") else ""
    s = s.removeprefix("+")

    if s.startswith("/"):
        return re.compile(matchFullTextTag + handleRangePatterns(s[1:]))
    if s.startswith("="):
        return re.compile(matchFullTextTag + re.escape(s[1:]))
    return re.compile(matchFullTextTag + handleRangePatterns(fnmatch.translate(s).removesuffix("\\Z")))

class _rex_sel_context:
    def __init__(self, oldRexSelected, newRexSelected):
        self.oldRexSelected = oldRexSelected
        self.newRexSelected = newRexSelected

    def __str__(self):
        return " ".join(f"{pf}*" for pf in self.newRexSelected)

    def __iter__(self):
        return [f"{pf}*" for pf in self.newRexSelected].__iter__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        global _rex_selected
        _rex_selected = self.oldRexSelected
        return False

def sel(*p):
    """
        Select a list of norms.

        This list of files is used whenever the normPat argument to toc(),
        get(), or find() is left None.

        Running sel() without arguments resets the list of selected files.

        Returns a context manager that restores the previous selection
        in its __exit__() callback.
    """

    global _rex_selected
    oldRexSelected = _rex_selected
    _rex_selected = None

    if len(p) == 0:
        return _rex_sel_context(oldRexSelected, _rex_selected)

    newRexSelected = set()
    for pat in p:
        if type(pat) is set:
            newRexSelected += pat
        elif type(pat) is tuple:
            newRexSelected += set(pat)
        else:
            for n in ls(pat):
                newRexSelected.add(n)

    _rex_selected = tuple(sorted(newRexSelected))
    return _rex_sel_context(oldRexSelected, _rex_selected)

def toc(searchPat: str, normPat: str = None):
    """
        Search for searchPat in the tables-of-contents .index.json
        files selected by normPat, or all toc files when normPat
        is None.

        If normPat is specified, it may apply to the part of the
        TOC JSON filename without the .index.json suffix or any of
        the files that belong to a norm.

        See pat() for details on the pattern syntax.

        In addition, searchPat may also be a set of fetch keys,
        such as returned by find().
    """

    setMode = type(searchPat) is set

    matches = list()
    if not setMode:
        searchPat = pat(searchPat)
        fullTextMode = searchPat.pattern.startswith("(?#MatchFullTextTag)")

    if normPat is not None:
        if type(normPat) is set or type(normPat) is tuple:
            normList = tuple(sorted(normPat))
        else:
            normList = ls(normPat)
    else:
        normList = ls()

    for norm in normList:
        for par, dat in fetch(f"{norm}.index.json").items():
            if isinstance(dat, str):
                continue
            key = (norm,par) + tuple(dat)
            print(key)
            ref, _, txt = dat
            if setMode:
                if key in searchPat:
                    matches.append(key)
            elif fullTextMode:
                if searchPat.search(fetch(ref)):
                    matches.append(key)
            elif searchPat.search(txt):
                matches.append(key)

    return matches

def find(searchPat: str, normPat: str = None):
    """
        Like toc() but return a set of fetch keys.
    """
    return {key for _, key in toc(searchPat, normPat)}

def get(searchPat: str, normPat: str = None):
    """
        Like toc() but return the full Markdown
        text for all matching paragraphs.
    """
    outLines = list()
    for _, key in toc(searchPat, normPat):
        outLines.append(fetch(key).replace("\n", f" | {key}\n", 1))
    return "\n".join(outLines)

def grep(grepPat: str, s: str):
    """
        Search for a pattern in the string(s) provided in the second argument.

        Return a list of the matching lines, as well as the relevant headers
        for the sections containing matching lines.
    """
    if type(s) is not str:
        s = "\n".join([f"{t[0]} | {t[1]}" if type(t) is tuple else t for t in s])

    matches = list()
    grepPat = pat(grepPat)

    lastLineMatched = False
    lastH2, lastH3 = None, None
    for line in s.split("\n"):
        if line.startswith("## "):
            lastH2, lastH3 = line, None
            lastLineMatched = False
        if line.startswith("### "):
            lastH3 = line
            lastLineMatched = False
        if grepPat.search(line):
            if lastH2 is not None:
                matches.append("")
                matches.append(lastH2)
            if lastH3 is not None:
                matches.append("")
                matches.append(lastH3)
            if line != lastH2 and line != lastH3:
                if not lastLineMatched:
                    matches.append("")
                matches.append(line)
            lastH2, lastH3 = None, None
            lastLineMatched = True
        else:
            lastLineMatched = False

    return matches

def untag(*a):
    """
        Return the string(s) with tags such as
           `§ 74 (1) Z 4a StGB.` and
           `§ 74 (1) Z 4a lit. b StGB.`
        replaced with something such as
           `  4a.` and
           `    b)`

        We should always cite norms to the user in
        the output format of untag(), not with the
        full tags included in the markdown text.
    """

    if len(a) == 0:
        return ""

    if len(a) > 1:
        outList = list()
        for s in a:
            if type(r := untag(s)) is str:
                outList.append(r)
            else:
                for t in r:
                    outList.append(r)
        return outList

    assert len(a) == 1
    s = a[0]

    if type(s) is not str:
        return [untag(t) for t in s]

    outLines = list()
    for line in s.split("\n"):
        if not line.startswith("`") or not "`" in line[1:]:
            outLines.append(line)
            continue

        _, tag, text = line.split("`", 2)
        tagFields = tag.split()
        if not tag.startswith("§") or len(tagFields) <= 4:
            outLines.append(line)
            continue

        item = tagFields[-2]
        item = item.removesuffix(".")
        item = item.removesuffix(")")

        lvl = (len(tagFields)-3) // 2
        if lvl == 1: item += "."
        elif lvl == 2: item += ")"
        else: assert False
        outLines.append(f"`{'  '*lvl}{item}`{text}")

    return "\n".join(outLines)

def tx(*a):
    """
        Print (markdown or any other) text to the console as-is
    """
    for s in a:
        if type(s) is not str:
            s = "\n".join([t if type(t) is str else f"{t[0]} | {t[1]}" for t in s]) + "\n"
        print(s)

def hd(a):
    """
        Print only the headers from the given markdown text
    """
    for s in a:
        if type(s) is str:
            s = s.split("\n")
        for line in s:
            if line.startswith("#"): print(line)

def md(*a):
    """
        Render markdown text to the console using rich.markdown
    """
    from rich.console import Console, ConsoleOptions, RenderResult
    from rich.markdown import Markdown
    from rich.markdown import Heading
    from rich.panel import Panel
    from rich.text import Text
    from rich import box

    def replacement__rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        text = self.text
        text.justify = "left" # <-- only this line has changed
        if self.tag == "h1":
            # Draw a border around h1s
            yield Panel(
                text,
                box=box.HEAVY,
                style="markdown.h1.border",
            )
        else:
            # Styled text for h2 and beyond
            if self.tag == "h2":
                yield Text("")
            yield text

    original__rich_console__ = Heading.__rich_console__
    Heading.__rich_console__ = replacement__rich_console__

    for s in a:
        if type(s) is not str:
            s = "\n".join([f"{t[0]} | {t[1]}" if type(t) is tuple else t for t in s]) + "\n"
        Console().print(Markdown(s))

    Heading.__rich_console__ = original__rich_console__

# Output Helper Functions:
# print ('untagged') plain (markdown) text
def u(*a): tx(untag(*a))
def uls(*a): tx(ls(*a))
def uintro(*a): tx(intro(*a))
def ufetch(*a): u(fetch(*a))
def utoc(*a):   u(toc(*a))
def uget(*a):   u(get(*a))
def ugrep(*a):  u(grep(*a))

# Output Helper Functions:
# print ('untagged') rendered markdown text
def v(*a): md(untag(*a))
def vls(*a): tx(ls(*a))
def vintro(*a): md(intro(*a))
def vfetch(*a): v(fetch(*a))
def vtoc(*a):   v(toc(*a))
def vget(*a):   v(get(*a))
def vgrep(*a):  v(grep(*a))

# Output Helper Functions:
# print plain (markdown) text
def txfetch(*a): tx(fetch(*a))
def txtoc(*a):   tx(toc(*a))
def txget(*a):   tx(get(*a))
def txgrep(*a):  tx(grep(*a))

# Output Helper Functions:
# print headers from markdown text
def hdfetch(*a): hd(fetch(*a))
def hdtoc(*a):   hd(toc(*a))
def hdget(*a):   hd(get(*a))
def hdgrep(*a):  hd(grep(*a))

# Output Helper Functions:
# print rendered markdown text
def mdfetch(*a): md(fetch(*a))
def mdtoc(*a):   md(toc(*a))
def mdget(*a):   md(get(*a))
def mdgrep(*a):  md(grep(*a))

if __name__ == "__main__" and len(sys.argv) > 1 and _rex_repcnt == 0:
    if sys.argv[1] == "intro":
        txintro()
    elif sys.argv[1] == "ls":
        uls(*sys.argv[2:])
    elif sys.argv[1] == "fetch":
        txfetch(*sys.argv[2:])
    elif sys.argv[1] == "pat":
        tx(pat(*sys.argv[2:]).pattern)
    elif sys.argv[1] == "toc":
        txtoc(*sys.argv[2:])
    elif sys.argv[1] == "grep":
        txgrep(sys.argv[2], get(*sys.argv[3:]))
    elif sys.argv[1] == "untag":
        tx(untag(get(*sys.argv[2:])))
    elif sys.argv[1] == "get":
        txget(*sys.argv[2:])
    elif sys.argv[1] == "md":
        md(get(*sys.argv[2:]))
    else:
        assert False
