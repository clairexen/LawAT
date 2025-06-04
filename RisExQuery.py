#!/usr/bin/env python3

"""
Utility library for accessing and searching RisExFiles.zip.
"""

import zipfile, json, os, re, fnmatch

__all__ = [
    "ls",
    "get",
    "pat",
    "toc"
]

fileList = None
fileCache = dict()

zipPath = None

for fn in ["RisExFiles.zip", "/mnt/data/RisExFiles.zip"]:
    if os.access(fn, os.F_OK):
        zipPath = fn
        break

def ls():
    """
        Return the list of file names from RisExFiles.zip.
    """
    global fileList
    if fileList is None:
        with zipfile.ZipFile(zipPath) as z:
            fileList = sorted([f.filename for f in z.filelist])
    return fileList

def get(fn: str):
    """
        Fetch a file (by file name) from RisExFiles.zip.

        If fn ends with .json, the parsed JSON data
        structure is returned.

        Otherwise a list of the lines of the text
        file is returned.
    """
    if fn not in fileCache:
        with zipfile.ZipFile(zipPath) as z:
            with z.open(fn) as f:
                if fn.endswith(".json"):
                    fileCache[fn] = json.load(f)
                else:
                    fileCache[fn] = [line.decode().removesuffix("\n") for line in f]
    return fileCache[fn]

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

def toc(searchPat: str, filePat: str = None):
    """
        Search for searchPat in the tables-of-contents .toc.json
        files selected by filePat, or all toc files when filePat
        is None.

        If filePat is specified, it applies to the part of the
        filename without the .toc.json suffix.

        See pat() for details on the pattern syntax.

        This functions returns a list of 4-tuples, one for each
        found match:
        [ (DataFileName, FirstLine, LastLine, Header, Data), ... ]
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

        for tf, items in get(fn).items():
            for i in range(len(items)-1):
                if searchPat.search(items[i][1]):
                    n, m = items[i][0], items[i+1][0]-1
                    tx = "\n".join(get(f"{tf}.md")[n-1:m])
                    matches.append((f"{tf}.md", n, m, items[i][1], tx))

    return matches
