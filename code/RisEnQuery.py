#!/usr/bin/env python3
# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

def welcome():
    print(
"""
---------------------
Welcome to RisEnQuery
---------------------

Use with `from RisEnQuery import *`.
Run `welcome()` to print this message.
Run `intro()` for an introduction
""")

_rex_src, _rex_repcnt = None, 0
#/#_rex_src, _rex_repcnt = "LawAT_DataSet.zip", 1 # replace(count=1)
#/#_rex_src, _rex_repcnt = "LawAT_DataSet.json", 2 # replace(count=2)
#/#_rex_src, _rex_repcnt = "/mnd/data/LawAT_DataSet.zip", 3 # replace(count=3)
#/#_rex_src, _rex_repcnt = "/mnd/data/LawAT_DataSet.json", 4 # replace(count=4)

def intro():
    """
        Print the introduction message for RisEnQuery.py.
    """
    V(_rex_intro_message)

_rex_intro_message = r"""
Utility library for accessing and searching LawAT_DataSet.zip.

Import as follows in Chat-GPT(-like) script environments:
```
exec(open("/mnt/data/RisEnQuery.py").read().replace("#/#", "", count=3))  # Use /mnd/data/LawAT_DataSet.zip
exec(open("/mnt/data/RisEnQuery.py").read().replace("#/#", "", count=4))  # Use /mnd/data/LawAT_DataSet.json
```

Formatbeschreibung (zipped) Markdown+JSON-Datensätze in LawAT_DataSet.zip
======================================================================

- Längere Normen sind in Blöcke zu je ca. 20 kB zerteilt
- Paragraphenbeginn: ``` ### § <nr> StGB. # <titel> ``` (Markdown H3)
- Paragraph ohne Absätze: ``` `§ <nr> StGB.`␣␣\n<text> ``` (Markdown "quoted code", 2x space + newline)
- Bzw. für jeden Absatz: ``` `§ <nr> (<abs>) StGB.`␣␣\n<text> ``` (Markdown "quoted code", 2x space + newline)
- Unterpunkte: ``` `§ <nr> (<abs>) Z <Z> lit. <lit> StGB.`\n<text> ``` (ohne 2x space)
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

````
>>> from RisEnQuery import *
>>> p(q("Begr", "BG.StGB"))
## Achter Abschnitt # Begriffsbestimmungen | BG.StGB.004:11-12
### § 74 StGB # Andere Begriffsbestimmungen | BG.StGB.004:58-108
### § 255 StGB # Begriff des Staatsgeheimnisses | BG.StGB.010:149-153

>>> h(fetch("BG.StGB.004:11-109"))
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
>>> Q("+Eltern")[:3]
[('### § 72 StGB # Angehörige', 'BG.StGB.004:45-52'), ('### § 240 StPO', 'BG.StPO.015:18-22')]

>>> sel("BG.ABGB")
>>> Q("+Eltern")[:3]
[('## Drittes Hauptstück # Rechte zwischen Eltern und Kindern # Erster Abschnitt # Allgemeine Bestimmungen', 'BG.ABGB.002:11-12'), ('### § 137 ABGB # Allgemeine Grundsätze', 'BG.ABGB.002:13-20'), ('### § 138 ABGB # Kindeswohl', 'BG.ABGB.002:21-49')]

>>> sel() # Reset Selection

>>> with sel("BG.StPO", "BG.StGB"): p(q("+Anzeig")) # Change selection temporarily
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


>>> with sel("BG.StPO", "BG.StGB", "BG.ABGB"): p(ls("*.toc.md"))
BG.ABGB.toc.md
BG.StGB.toc.md
BG.StPO.toc.md


>>> p(g("§ 71 StGB"))
### § 71 StGB # Schädliche Neigung | BG.StGB.004:40-44

`§ 71 StGB.`
Auf der gleichen schädlichen Neigung beruhen mit Strafe bedrohte Handlungen, wenn sie gegen dasselbe Rechtsgut gerichtet oder auf gleichartige verwerfliche Beweggründe oder auf den gleichen Charaktermangel zurückzuführen sind.

>>> p(g(" § 74 StGB ").split("\n")[9:18])
`§ 74 (1) Z 4 StGB.`
Beamter: jeder, der bestellt ist, im Namen des Bundes, eines Landes, eines Gemeindeverbandes, einer Gemeinde oder einer anderen Person des öffentlichen Rechtes, ausgenommen einer Kirche oder Religionsgesellschaft, als deren Organ allein oder gemeinsam mit einem anderen Rechtshandlungen vorzunehmen, oder sonst mit Aufgaben der Bundes-, Landes- oder Gemeindeverwaltung betraut ist; als Beamter gilt auch, wer nach einem anderen Bundesgesetz oder auf Grund einer zwischenstaatlichen Vereinbarung bei einem Einsatz im Inland einem österreichischen Beamten gleichgestellt ist;
`§ 74 (1) Z 4a StGB.`
Amtsträger: jeder, der
(Anm.: lit. a aufgehoben durch BGBl. I Nr. 61/2012)
`§ 74 (1) Z 4a lit. b StGB.`
für den Bund, ein Land, einen Gemeindeverband, eine Gemeinde, für eine andere Person des öffentlichen Rechts, ausgenommen eine Kirche oder Religionsgesellschaft, für einen anderen Staat oder für eine internationale Organisation Aufgaben der Gesetzgebung, Verwaltung oder Justiz als deren Organ oder Dienstnehmer wahrnimmt, Unionsbeamter (Z 4b) ist oder - für die Zwecke der §§ 168g, 304, 305, 307 und 307a - der öffentliche Aufgaben im Zusammenhang mit der Verwaltung der oder Entscheidungen über die finanziellen Interessen der Europäischen Union in Mitgliedstaaten oder Drittstaaten übertragen bekommen hat und diese Aufgaben wahrnimmt,
`§ 74 (1) Z 4a lit. c StGB.`
sonst im Namen der in lit. b genannten Körperschaften befugt ist, in Vollziehung der Gesetze Amtsgeschäfte vorzunehmen, oder

>>> p(untag(g(" § 74 StGB ").split("\n")[9:18]))
`  4.`
Beamter: jeder, der bestellt ist, im Namen des Bundes, eines Landes, eines Gemeindeverbandes, einer Gemeinde oder einer anderen Person des öffentlichen Rechtes, ausgenommen einer Kirche oder Religionsgesellschaft, als deren Organ allein oder gemeinsam mit einem anderen Rechtshandlungen vorzunehmen, oder sonst mit Aufgaben der Bundes-, Landes- oder Gemeindeverwaltung betraut ist; als Beamter gilt auch, wer nach einem anderen Bundesgesetz oder auf Grund einer zwischenstaatlichen Vereinbarung bei einem Einsatz im Inland einem österreichischen Beamten gleichgestellt ist;
`  4a.`
Amtsträger: jeder, der
(Anm.: lit. a aufgehoben durch BGBl. I Nr. 61/2012)
`    b)`
für den Bund, ein Land, einen Gemeindeverband, eine Gemeinde, für eine andere Person des öffentlichen Rechts, ausgenommen eine Kirche oder Religionsgesellschaft, für einen anderen Staat oder für eine internationale Organisation Aufgaben der Gesetzgebung, Verwaltung oder Justiz als deren Organ oder Dienstnehmer wahrnimmt, Unionsbeamter (Z 4b) ist oder - für die Zwecke der §§ 168g, 304, 305, 307 und 307a - der öffentliche Aufgaben im Zusammenhang mit der Verwaltung der oder Entscheidungen über die finanziellen Interessen der Europäischen Union in Mitgliedstaaten oder Drittstaaten übertragen bekommen hat und diese Aufgaben wahrnimmt,
`    c)`
sonst im Namen der in lit. b genannten Körperschaften befugt ist, in Vollziehung der Gesetze Amtsgeschäfte vorzunehmen, oder

>>> p(q(s("+verfälscht", "BG.StGB") & S("+Urkund", "BG.StGB"))) # Liste der StGB Paragraphen mit "verfälscht" und "Urkund" im Text
### § 147 StGB # Schwerer Betrug | BG.StGB.006:496-518
### § 223 StGB # Urkundenfälschung | BG.StGB.009:33-40
### § 224a StGB # Annahme, Weitergabe oder Besitz falscher oder verfälschter besonders geschützter Urkunden | BG.StGB.009:46-50
### § 226 StGB # Tätige Reue | BG.StGB.009:67-74
### § 264 StGB # Verbreitung falscher Nachrichten bei einer Wahl oder Volksabstimmung | BG.StGB.010:218-225

>>> p(grep("Urkund", G("", "BG.StGB"))) # Volltextsuche nach "Urkund" im StGB

## Achter Abschnitt # Begriffsbestimmungen | BG.StGB.004:11-12

### § 74 StGB # Andere Begriffsbestimmungen | BG.StGB.004:58-108

Urkunde: eine Schrift, die errichtet worden ist, um ein Recht oder ein Rechtsverhältnis zu begründen, abzuändern oder aufzuheben oder eine Tatsache von rechtlicher Bedeutung zu beweisen;

## Sechster Abschnitt # Strafbare Handlungen gegen fremdes Vermögen | BG.StGB.006:209-210

### § 147 StGB # Schwerer Betrug | BG.StGB.006:496-518

eine falsche oder verfälschte Urkunde, ein falsches, verfälschtes oder entfremdetes unbares Zahlungsmittel, ausgespähte Daten eines unbaren Zahlungsmittels, falsche oder verfälschte Daten, ein anderes solches Beweismittel oder ein unrichtiges Meßgerät benützt oder

### § 165 StGB # Geldwäscherei | BG.StGB.006:894-925
...
````

Zweck:
------
RisEnQuery.py ermöglicht den Zugriff auf Gesetzesdateien im ZIP-Archiv "LawAT_DataSet.zip". Es erlaubt strukturierte Suchen in Inhaltsverzeichnissen (.index.json) und den Abruf von Gesetzestexten (.md).

Die Wichtigsten Funktionen:
---------------------------

- intro():
  → Gibt diesen Einführungstext aus.

- sel(*p):
  → Selektiert die Liste der Normen die bei ls(), Q(), G(), und S() verwendet werden
     wenn normPat den Wert None hat. (Reset mit sel() ohne argumente.)

- ls(normPat=None):
  → Gibt eine Liste aller (matchender) Normen im Archiv zurück.

- Q(searchPat, normPat=None):
  → Durchsucht .index.json-Dateien nach Überschriften, die dem Muster entsprechen.
     Gibt eine liste der gefundenden Überschriften zurück.  WICHTIG: Die Dateinamen
     beginnen mit dem Typ des Gesetzes. Also zB "BG.StGB", nicht nur "StGB".
     ("q" is for query)

- S(searchPat, normPat=None):
  → Ähnlich Q(), aber gibt ein set() (anstelle einer list()) von fetch keys zurück.
    ("s" is for set-search)

- G(searchPat, normPat=None):
  → Durchsucht .index.json-Dateien nach Überschriften, die dem Muster entsprechen.
     Zitiert die gefundenden Paragraphen vollständig.
     ("g" is for get)

- H(searchPat, normPat=None):
  → Das gleiche wie G(), aber zitiert die "for humans" variante vom markdown text.

- grep(grepPat, data):
  → Durchsucht die string(s) im zweiten Argument nach dem pattern.

- untag(data):
  → Gibt die Eingabe mit den Citation-Tags für Aufzählungspunkte (wie
     zB `§ 74 (1) Z 4a StGB.` und `§ 74 (1) Z 4a lit. b StGB.`) mit
     dem entsprechenden Originaltext der Norm (also zB `  4a.` und
     `    b)`) ersetzt zurück. Die Ausgabe von untag(), bzw. das
     Ausgabeformat von untag(), ist, wie die Normen dem Anwender
     zitiert werden sollten.

- P(data):
  → Ausgabe auf der Konsole in plain ASCII

- V(data):
  → Ausgabe von vormattiertem Markdown auf der Konsole mit ANSI escape codes (mit rich.markdown)

WICHTIG:
--------
Speziell an AI-Agents: Immer zuerst die Datenbank (RisEnQuery.py und
LawAT_DataSet.zip) befragen, bevor internes Wissen verwendet wird!  Normbegriffe
können ähnlich, aber unterschiedlich zwischen Ländern oder Paragrafen sein.
Nur durch die Datenbank kann sichergestellt werden, dass nach österreichischem
Recht korrekt zitiert wird.

Merksatz: "Immer zuerst Q() oder gleich Q() oder P() – nie raten!"
""".split("\n")

import json, os, sys, re, fnmatch
from collections import namedtuple

Cite = namedtuple("Cite", "norm par vref pref title")
if hasattr(Cite, "__str__"):
    Cite.__str__ = lambda self: f"<{self.title.strip('# ').replace(' # ', ' — ')}>"

# various hacks for micropython compatibility
_rex_re_Pattern = re.pattern if hasattr(re, 'Pattern') else type(re.compile("."))

def str_removeprefix(s, pf):
    if s.startswith(pf):
        return s[len(pf):]
    return s

def str_removesuffix(s, pf):
    if s.endswith(pf):
        return s[:-len(pf)]
    return s

if _rex_src is None:
    import glob
    _rex_dir = {"normlist.json"} | {str_removeprefix(fn, "files/") for fn in glob.glob("files/*")}
    _rex_rd_text = lambda fn: open(fn if fn == "normlist.json" else f"files/{fn}").read()
    _rex_rd_json = lambda fn: json.load(open(fn if fn == "normlist.json" else f"files/{fn}"))

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
_rex_index = _rex_rd_json("normlist.json")
_rex_sorted_norms = tuple(sorted(_rex_index.keys()))
_rex_is_upy = sys.implementation.name == 'micropython'
_rex_edit_history = list()
_rex_print_f = print
_rex_trace_f = lambda*args,**kwargs: print(*args, **kwargs, file=sys.stderr) if _rex_trace else None

def _rex_capture(fun):
    global _rex_print_f
    old_rex_print_f = _rex_print_f
    capture_buffer = []

    def capture_print_f(*args, sep=' ', end='\n', file=None, flush=False):
        capture_buffer.append(sep.join(str(a) for a in args) + end)
        return old_rex_print_f(*args, sep=sep, end=end, file=file, flush=flush)

    _rex_print_f = capture_print_f
    fun()
    _rex_print_f = old_rex_print_f
    return "".join(capture_buffer).split("\n")

def _rex_rerun_intro_examples(cmds = None):
    if cmds is None:
        cmds = [str_removeprefix(line, ">>> ") for line in re.sub(r"^.*?\n````\n|\n````.*?$", "",
                "\n".join(_rex_intro_message), 0, re.S).split("\n") if line.startswith(">>> ")]
    output_buffer = []
    local_vars = dict()

    for cmd in cmds:
        P(f"\n>>> {cmd}")
        output_buffer.append("")
        output_buffer.append(f">>> {cmd}")
        if cmd.startswith("from RisEnQuery "): continue
        output = _rex_capture(lambda: exec(cmd, globals(), local_vars))
        if len(output) > 20: output = output[:20] + ["..."]
        output_buffer += output

    return output_buffer

def _rex_update_intro_examples():
    new_code = re.sub(r"\n````\n.*?\n````\n",
            "\n````\n" + "\n".join(_rex_rerun_intro_examples()) + "\n````\n",
            open("RisEnQuery.py").read(), 1, re.S)
    open("RisEnQuery.py.new", "w").write(new_code)


# ----------------------------------------------------------------------------------------------------
# Main RisEn Feature Functions

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
        Fetch a file (by file name) from LawAT_DataSet.zip.

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
                _rex_trace_f(f"Fetching JSON from '{src}': {fn}")
                _rex_fetch_cache[key] = _rex_rd_json(fn)
            else:
                _rex_trace_f(f"Fetching TEXT from '{src}': {fn}")
                data = _rex_rd_text(fn)
                if type(data) is str:
                    data = data.split("\n")
                _rex_fetch_cache[key] = data

    return _rex_fetch_cache[key]

def pat(s: str) -> _rex_re_Pattern:
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

    if type(s) is _rex_re_Pattern:
        return s

    def handleRangePatterns(s: str) -> str:
        def rangeRegex(n: int, m: int) -> str:
            return '(?:0*(?:' + "|".join([str(i) for i in range(n, m+1)]) + '))'
        def replacer(match):
            n, m = int(match.group(1)), int(match.group(2))
            return rangeRegex(min(n, m), max(n, m))
        return re.sub(r"<(\d+)\\?-(\d+)>", replacer, s)

    matchFullTextTag = "(?#MatchFullTextTag)" if s.startswith("+") else ""
    s = str_removeprefix(s, "+")

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

        This list of files is used whenever the normPat argument to Q(),
        G(), or S() is left None.

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

def Q(searchPat: str, normPat: str = None):
    """
        QUERY

        Search for searchPat in the tables-of-contents .index.json
        files selected by normPat, or all toc files when normPat
        is None.

        If normPat is specified, it may apply to the part of the
        TOC JSON filename without the .index.json suffix or any of
        the files that belong to a norm.

        See pat() for details on the pattern syntax.

        In addition, searchPat may also be a set of fetch keys,
        such as returned by S().
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
        for item in fetch(f"{norm}.index.json")["toc"]:
            if isinstance(item, str):
                continue
            key = Cite(norm, *item)
            _, ref, _, txt = item
            if setMode:
                if key in searchPat:
                    matches.append(key)
            elif fullTextMode:
                if searchPat.search(fetch(ref)):
                    matches.append(key)
            elif searchPat.search(txt):
                matches.append(key)

    return matches

def S(searchPat: str, normPat: str = None):
    """
        SEARCH/SET

        Like Q() but return a set instead of a list.
    """
    return set(Q(searchPat, normPat))

def G(searchPat: str, normPat: str = None, ggMode=False):
    """
        GET

        Like Q() but return the full Markdown
        text for all matching paragraphs.
    """
    out = list()
    first = True
    for key in Q(searchPat, normPat):
        if not first:
            out.append(f"\n----\n# {key}\n")
        out.append(fetch(key[2] if ggMode else key[3]))
        first = False
    return "\n".join(out)

def H(*args, **kwargs):
    """
        HUMANS

        Like G() but return the "Human Friendly" markdown
        text instead of the "AI Friendly" version.
    """
    return G(*args, **kwargs, ggMode=True)

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


# ----------------------------------------------------------------------------------------------------
# I/O Helpers 

def P(*a):
    """
        Print (markdown or any other) text to the console as-is
    """
    for s in a:
        if isinstance(s, (tuple, int)) or s is None:
            s = str(s)
        elif not isinstance(s, str):
            items = [str(t) for t in s]
            if isinstance(s, set):
                items = sorted(items)
            s = "\n".join(items) + "\n"
        _rex_print_f(s)

def V(*a):
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
            s = "\n".join([str(t) for t in s]) + "\n"
        Console().print(Markdown(s))

    Heading.__rich_console__ = original__rich_console__

def ed(text=""):
    import tempfile
    if not isinstance(text, str):
        return edit("\n".join(text)).split("\n")
    with tempfile.NamedTemporaryFile(delete_on_close=False) as fp:
        fp.write(text.encode())
        fp.close()
        os.system(f"editor '{fp.name}' 2> x");
        new_text = open(fp.name).read()
    _rex_edit_history.append((text, new_text))
    return new_text

def pp(*args, **kwargs):
    """
        A thin wrapper for pprint.pp()
    """
    import pprint, shutil
    term_width = shutil.get_terminal_size().columns
    pprint.pp(*args, width=term_width, **kwargs)

def foldSoftPreserve(s, width=80):
    out, start, last_space = [], 0, -1
    for i, c in enumerate(s):
        if c == ' ': last_space = i
        if i - start >= width:
            if last_space > start:
                out.append(s[start:last_space + 1])
                start = last_space + 1
            else:
                out.append(s[start:i])
                start = i
            last_space = -1
    if start < len(s):
        out.append(s[start:])
    return out

def pr(*args, indent_head="", indent_body="", indent_tail="", depth=1):
    """
        A not-so-thin wrapper for pprint.pp()
    """
    import pprint, shutil, types
    term_width = shutil.get_terminal_size().columns
    next_indent_head = indent_head + " `- "
    next_indent_body = indent_body + " |  "
    next_indent_tail = indent_body + "    "
    def handle_unroll(items, withLabels=False):
        countdn = len(items)
        for item in items:
            countdn -= 1
            label = ""
            if withLabels:
                label, item = item
                label = label + ": "
            this_head = next_indent_head + label
            this_tail = next_indent_tail + " "*len(label)
            this_body = next_indent_body + " "*len(label) if countdn else this_tail
            pr(item, indent_head=this_head, indent_body=this_body, indent_tail=this_tail, depth=depth-1)
    while args and args[-1] is ...:
        args = args[:-1]; depth += 1
    for arg in args:
        if depth > 0 and isinstance(arg, (list, dict, set, types.GeneratorType)):
            print(indent_head + f"{type(arg)}:")
            next_indent_head = indent_body + " `- "
            if hasattr(arg, 'items'):
                handle_unroll(list(arg.items()), True)
            else:
                handle_unroll(list(arg))
            next_indent_head = indent_head + " `- "
        elif isinstance(arg, str):
            this_indent = indent_head + "# "
            for line in arg.split("\n"):
                print(indent_head + "# " + ("\n" + indent_body + "  ").
                        join(foldSoftPreserve(line, term_width-len(indent_head)+2-5)))
        else:
            s = pprint.pformat(arg, indent=2, width=(term_width-len(indent_head)-5), compact=True, sort_dicts=False)
            s = indent_head + s.replace("\n", "\n"+indent_body)
            print(s)


# ----------------------------------------------------------------------------------------------------
# The Shell

def MAGIC(pattern):
    """
        An alias for V(H(pattern)).

        In the shell, a line starting with §, /, +,  or = is automatically converted to a call to P().
        This way you only just to type the cite name of a paragraph on the shell, and instead
        of the usual Python syntax error, you'll be presented with the text of the paragraph.

        And if the first charter is duplicated, then it's an alias for P(Q(pattern)).

        Thus, "§ 69 JN" will show you the one paragraph, and "§ * StGB *Urkund"
    """
    if len(pattern) > 2 and pattern[0] == pattern[1]:
        P(Q(pattern[1:]))
    else:
        V(H(pattern))


def shell():
    from ptpython.repl import embed
    from prompt_toolkit.validation import Validator, ValidationError
    from prompt_toolkit.document import Document

    welcome()

    def configure_repl(repl):
        original_accept_handler = repl.default_buffer.accept_handler
        original_show_results = repl._show_result

        def custom_accept_handler(buf):
            text = buf.text.strip()
            if text.startswith("§") or \
                 text.startswith("=") or \
                 text.startswith("/") or \
                 text.startswith("+"):
                buf.document = Document(f"MAGIC({repr(text)})")
            return original_accept_handler(buf)

        # Disable validation for custom input lines
        class CustomValidator(Validator):
            def validate(self, document):
                if document.text.strip().startswith("§") or \
                    document.text.strip().startswith("=") or \
                    document.text.strip().startswith("/") or \
                    document.text.strip().startswith("+"):
                    # Don't validate (i.e., don't error)
                    return
                else:
                    # Let ptpython validate normal input
                    if repl._validator:
                        repl._validator.validate(document)

        def custom_show_result(output):
            return original_show_results(output)

        repl.default_buffer.accept_handler = custom_accept_handler
        repl.default_buffer.validator = CustomValidator()
        repl._show_result = custom_show_result

    embed(globals=globals(), locals=locals(), configure=configure_repl)

if __name__ == "__main__" and len(sys.argv) == 2 and _rex_repcnt == 0 and sys.argv[1] == "shell":
    shell()
