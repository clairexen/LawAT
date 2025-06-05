#!/usr/bin/env python3

"""
Utility library for accessing and searching RisExFiles.zip.

Import as follows in Chat-GPT(-like) script environments:
exec(open("/mnt/data/RisExQuery.py").read().replace("#/#", 1))
"""

import zipfile, json, os, sys, re, fnmatch

_rex_zipPath = "RisExFiles.zip"
#/#_rex_zipPath = "/mnt/data/RisExFiles.zip"

_rex_zip = zipfile.ZipFile(_rex_zipPath)
_rex_dir = set(sorted([f.filename for f in _rex_zip.filelist]))
_rex_cache = dict()

def ls(p: str = None):
    """
        Return the list of file names from RisExFiles.zip.
    """
    if p is not None:
        return [fn for fn in _rex_dir if fnmatch.fnmatch(fn, p)]
    return _rex_dir

def fetch(key: str):
    """
        Fetch a file (by file name) from RisExFiles.zip.

        If fn ends with .json, the parsed JSON data
        structure is returned.

        Otherwise a list of the lines of the text
        file is returned.
    """

    if key not in _rex_cache:
        if ":" in key:
            fn, ln = key.split(":", 1)
            if "-" in ln:
                fromLine, toLine = ln.split("-", 1)
            else:
                fromLine, toLine = ln, ln
            _rex_cache[key] = "\n".join(fetch(fn)[int(fromLine)-1:int(toLine)])

        else:
            fn = key
            if fn not in _rex_dir:
                for ext in (".md", ".json"):
                    if (fn + ext) in _rex_dir: fn += ext; break
            with _rex_zip.open(fn) as f:
                if fn.endswith(".json"):
                    _rex_cache[key] = json.load(f)
                else:
                    _rex_cache[key] = [line.decode().removesuffix("\n") for line in f]

    return _rex_cache[key]

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

def get(searchPat: str, filePat: str = None):
    """
        Search for searchPat in the tables-of-contents .toc.json
        files selected by filePat, or all toc files when filePat
        is None.

        If filePat is specified, it applies to the part of the
        filename without the .toc.json suffix.

        See pat() for details on the pattern syntax.
    """

    matches = list()
    searchPat = pat(searchPat)
    if filePat is not None:
        filePat = pat(filePat)

    for fn in ls():
        if not fn.endswith(".toc.json"):
            continue

        if filePat is not None:
            if not filePat.fullmatch(fn.removesuffix(".toc.json")):
                continue

        for tf, items in fetch(fn).items():
            for i in range(len(items)-1):
                if searchPat.search(items[i][1]):
                    n, m = items[i][0], items[i+1][0]-1
                    tx = fetch(key := f"{tf}:{n}-{m}")
                    tx = tx.replace("\n", f" | {key}\n", 1)
                    matches.append(tx)

    return "\n".join(matches)

if __name__ == "__main__":
    match sys.argv[1]:
        case "zip":
            os.system(f"rm -vf RisExFiles.zip; set -ex; zip -vXj RisExFiles.zip -r files index.json")
        case "get":
            print(get(*sys.argv[2:]))
