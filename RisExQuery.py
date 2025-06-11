#!/usr/bin/env python3
# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

"""
Utility library for accessing and searching RisExFiles.zip.

Import as follows in Chat-GPT(-like) script environments:
exec(open("/mnt/data/RisExQuery.py").read().replace("#/#", 1))


Formatbeschreibung (zipped) Markdown+JSON-Datensätze in RisExFiles.zip
======================================================================

_ Längere Normen sind in Blöcke zu je ca. 20 kB zerteilt
- Paragraphenbeginn: "### § <nr> StGB. # <titel>" (Markdown H3)
- Paragraphen: "`§ <nr> StGB.`␣␣\n<text>" (Markdown "quoted code", 2x space + newline)
- Absätze: "`§ <nr> (<abs>) StGB.`␣␣\n<text>" (Markdown "quoted code", 2x space + newline)
- Unterpunkte: "`§ <nr> (<abs>) Z <Z> lit. <lit> StGB.`␣␣\n<text>"
- TOC (`.toc.json`) referenziert exakt die Zeilennummern der "###"-Überschriften im Markdown
- Trennung der Paragraphen durch nächste "### §"-Zeile oder Dateiende
- Unicode-Zeichen (ä, ß, etc.) und geschützte Leerzeichen (\xa0) möglich


RisExQuery – Kurzdokumentation
==============================

```
# Either import it as module from the current working directory
from RisExQuery import *

# or load and execute the uploaded Python file directly
exec(open("/mnt/data/RisExQuery.py").read().replace("#/#", 1))
```

Example Session:

```
>>> from RisExQuery import *
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

>>> tx(get("§ 71 StGB"))
### § 71 StGB # Schädliche Neigung| BG.StGB.004:40-44

`§ 71 StGB.`
Auf der gleichen schädlichen Neigung beruhen mit Strafe bedrohte Handlungen, wenn sie gegen dasselbe Rechtsgut gerichtet oder auf gleichartige verwerfliche Beweggründe oder auf den gleichen Charaktermangel zurückzuführen sind.
```

Zweck:
------
RisExQuery.py ermöglicht den Zugriff auf Gesetzesdateien im ZIP-Archiv "RisExFiles.zip". Es erlaubt strukturierte Suchen in Inhaltsverzeichnissen (.toc.json) und den Abruf von Gesetzestexten (.md).

Funktionen:
-----------
- ls(filePat=None):
  → Gibt eine Liste aller (matchender) Dateinamen im Archiv zurück.

- fetch(filename):
  → Lädt eine Datei (Text oder JSON) aus dem Archiv. Ergebnisse werden im Cache gespeichert.

- pat(pattern):
  → Erstellt ein Regex-Objekt aus einem Shell-Muster, Fix-String (=) oder RegEx (/).

- toc(searchPat, filePat=None):
  → Durchsucht .toc.json-Dateien nach Überschriften, die dem Muster entsprechen.
     Gibt eine liste der gefundenden Überschriften zurück.

- get(searchPat, filePat=None):
  → Durchsucht .toc.json-Dateien nach Überschriften, die dem Muster entsprechen.
     Zitiert die gefundenden Paragraphen vollständig.

- tx(data):
  → Ausgabe auf der Konsole in plain ASCII

- hd(data):
  → Ausgabe auf der header aus dem Markdown text

- md(data):
  → Ausgabe von vormattiertem Markdown auf der Konsole mit ANSI escape codes (mit rich.markdown)

WICHTIG:
--------
Immer zuerst die Datenbank (RisExFiles.zip) befragen, bevor internes Wissen verwendet wird.
Normbegriffe können ähnlich, aber unterschiedlich zwischen Ländern oder Paragrafen sein.
Nur durch die Datenbank kann sichergestellt werden, dass nach österreichischem Recht korrekt zitiert wird.

Merksatz: "Immer zuerst toc() oder get() – nie raten."
"""

import zipfile, json, os, sys, re, fnmatch

_rex_zipPath = "RisExFiles.zip"
#/#_rex_zipPath = "/mnt/data/RisExFiles.zip"

_rex_zip = zipfile.ZipFile(_rex_zipPath)
_rex_dir = set([f.filename for f in _rex_zip.filelist])
_rex_ls_cache = { None: (_rex_dir_sorted := sorted(_rex_dir)) }
_rex_fetch_cache = dict()

def ls(p: str = None):
    """
        Return the list of file names from RisExFiles.zip.
    """
    if p not in _rex_ls_cache:
        filePat = pat(p)
        fileList = list()
        for fn in _rex_dir_sorted:
            for suffix in ["", ".md", ".json", ".toc.json"]:
                if filePat.fullmatch(fn.removesuffix(suffix)):
                    fileList.append(fn)
                    break
        _rex_ls_cache[p] = fileList
    return _rex_ls_cache[p]

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
            with _rex_zip.open(fn) as f:
                if fn.endswith(".json"):
                    _rex_fetch_cache[key] = json.load(f)
                else:
                    _rex_fetch_cache[key] = [line.decode().removesuffix("\n") for line in f]

    return _rex_fetch_cache[key]

def pat(s: str) -> re.Pattern:
    """
        Compile the given shell pattern or regex into
        a re.Pattern object and return it.

        If 's' starts with a forward slash (/) then that
        forward slash is removed from 's' and the remaining
        string is treated as a regex.

        Otherwise the string in 's' is treated as a
        shell pattern and is converted to a regex via
        fnmatch.translate().

        In either case the special syntax <FROM-TO>
        (for example <12-345>) matches all integers
        in the specified range.

        If 's' starts with an equal-sign (=) then
        the remaining string is a fixed string, not
        a pattern off any kind.
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

    if s.startswith("/"):
        return re.compile(handleRangePatterns(s[1:]))
    if s.startswith("="):
        return re.compile(re.escape(s[1:]))
    return re.compile(handleRangePatterns(fnmatch.translate(s).removesuffix("\\Z")))

def toc(searchPat: str, filePat: str = None):
    """
        Search for searchPat in the tables-of-contents .toc.json
        files selected by filePat, or all toc files when filePat
        is None.

        If filePat is specified, it may apply to the part of the
        TOC JSON filename without the .toc.json suffix or any of
        the files that belong to a norm.

        See pat() for details on the pattern syntax.
    """

    matches = list()
    searchPat = pat(searchPat)

    tocFiles = ls(r"/[A-Z]+\.[A-Za-z]+\.*\.toc\.json")
    if filePat is not None:
        tocFiles = set()
        for fn in ls(filePat):
            tocFiles.add(".".join(fn.split(".")[:2]) + ".toc.json")
        tocFiles = sorted(tocFiles)

    for fn in tocFiles:
        for tf, items in fetch(fn).items():
            for i in range(len(items)-1):
                if searchPat.search(items[i][1]):
                    n, m = items[i][0], items[i+1][0]-1
                    matches.append((items[i][1], f"{tf}:{n}-{m}"))

    return matches

def get(searchPat: str, filePat: str = None):
    """
        Like toc() but return the full Markdown
        text for all matching paragraphs.
    """
    outLines = list()
    for _, key in toc(searchPat, filePat):
        outLines.append(fetch(key).replace("\n", f"| {key}\n", 1))
    return "\n".join(outLines)

def tx(s: str):
    """
        Print (markdown or any other) text to the console as-is
    """
    if type(s) is not str:
        s = "\n".join([f"{t[0]} | {t[1]}" if type(t) is tuple else t for t in s]) + "\n"
    print(s)

def hd(s: str):
    """
        Print only the headers from the given markdown text
    """
    if type(s) is str:
        s = s.split("\n")
    for line in s:
        if line.startswith("#"): print(line)

def md(s: str):
    """
        Render markdown text to the console using rich
    """
    from rich.console import Console, ConsoleOptions, RenderResult
    from rich.markdown import Markdown
    from rich.markdown import Heading
    from rich.text import Text

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

    if type(s) is not str:
        s = "\n".join([f"{t[0]} | {t[1]}" if type(t) is tuple else t for t in s]) + "\n"

    original__rich_console__ = Heading.__rich_console__
    Heading.__rich_console__ = replacement__rich_console__
    Console().print(Markdown(s))
    Heading.__rich_console__ = original__rich_console__

if __name__ == "__main__" and len(sys.argv) > 1:
    match sys.argv[1]:
        case "ls":
            for line in ls(*sys.argv[2:]):
                print(line)
        case "fetch":
            print(fetch(*sys.argv[2:]))
        case "pat":
            print(pat(*sys.argv[2:]).pattern)
        case "toc":
            tx(toc(*sys.argv[2:]))
        case "get":
            tx(get(*sys.argv[2:]))
        case "md":
            md(get(*sys.argv[2:]))
