#!.venv/bin/python
# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

import re, glob, fnmatch
import time, sys, json, os, tempfile
from collections import namedtuple
from urllib.parse import urljoin
from ptpython.repl import embed
from pathlib import Path
import unicodedata


# Global flags and command line options
#######################################

FlagDefaults = {
    "headless": True,
    "interactive": False,
    "proxy": "http://127.0.0.1:8080",
    "loghttp": False
}

FlagsType = namedtuple("FlagsType", FlagDefaults.keys(),
        defaults=FlagDefaults.values())
flags = FlagsType()

def updateFlags(*opts):
    global flags

    for o in opts:
        key, val = o.removeprefix("--"), None
        if "=" in key: key, val = key.split("=", 1)

        defBoolVal = True
        if key.startswith("no-"):
            defBoolVal = not defBoolVal
            key = key.removeprefix("no-")
            assert val is None

        if val is None:
            flags = flags._replace(**{key: defBoolVal})
        elif type(FlagDefaults["proxy"]) == str:
            flags = flags._replace(**{key: val})
        else:
            flags = flags._replace(**{key: eval(val)})

    return flags


# Various Other Utility Functions
#################################

# Python version of prettyJSON() from RisExtractor.js
def prettyJSON(data, indent="", autofold=False, addFinalNewline=True):
    def fold_soft_preserve(s, width=80):
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

    if autofold and isinstance(data, str) and len(data) > 80:
        return ',\n'.join(indent + json.dumps(line, separators=",:", ensure_ascii=False)
                for line in fold_soft_preserve(data))

    if not isinstance(data, list) or not data or \
            (autofold and len(json.dumps(data, separators=",:", ensure_ascii=False)) < 80):
        return indent + json.dumps(data, separators=",:", ensure_ascii=False)

    if isinstance(data[0], str) and (data[0] == "Text" or data[0].startswith("Text ")):
        autofold = True

    s = [indent + "[" + json.dumps(data[0], separators=",:", ensure_ascii=False)]
    for item in data[1:]:
        s.append(",\n" + prettyJSON(item, indent + "    ", autofold, False))
    s.append("]\n" if addFinalNewline else "]")
    return ''.join(s)

def fixPrettyJSON(text):
    dbgMode = False
    result = []
    stack = [0]

    for line in text.split("\n"):
        line = line.rstrip(",\t ")
        brOnly = re.sub(r'"([^"\\]|\\.)+"|[^\[\]]+', "_", line)
        while line.endswith("]") and brOnly.endswith("]"):
            if brOnly.count("[") >= brOnly.count("]"):
                break
            line = line.removesuffix("]")
            brOnly = brOnly.removesuffix("]")

        stripped = line.lstrip()
        if not len(stripped): continue
        indent = len(line) - len(stripped)

        while indent < stack[-1]:
            stack.pop()
            if dbgMode or not result:
                result.append(' ' * stack[-1] + ']')
            else:
                result[-1] += "]"

        result.append(line)

        if indent > (stack[-1] if stack else 0):
            stack.append(indent)

    while stack[-1]:
        stack.pop()
        if dbgMode or not result:
            result.append(' ' * stack[-1] + ']')
        else:
            result[-1] += "]"

    if dbgMode:
        return "\n".join(result)
    return ",\n".join(result) + "\n"

def markdownHeaderToAnchor(header: str) -> str:
    anchor = unicodedata.normalize("NFC", header)  # normalize unicode (e.g., ä → ä)
    anchor = anchor.lower()  # convert to lowercase
    anchor = re.sub(r"\s+", "-", anchor)  # replace spaces with hyphens
    anchor = re.sub(r"[^\w\s\-]", "", anchor)  # remove punctuation except hyphens and spaces
    anchor = anchor.removeprefix("-") # remove one (and only one) leading hyphen
    return anchor

def markdownEscape(text):
    # Escape all Markdown special characters, including @ and >
    return re.sub(r'([\\`*_{}[\]()#+\-.!|>~@>])', r'\\\1', text)

def docTypeToLongName(typ):
    match typ:
        case "BG": return "Bundesgesetz"
    assert False, "Unrecognized doc type: {typ}"


# Playwright Helper Functions
#############################

from playwright.sync_api import sync_playwright, Locator

playwright_instance = None
playwright_page = None

def startPlaywright():
    playwright = sync_playwright().start()

    if flags.proxy:
        browser = playwright.chromium.launch(
            headless=flags.headless,
            proxy={"server": flags.proxy},
            args=["--ignore-certificate-errors"],
        )
        context = browser.new_context(
            ignore_https_errors=True,  # this is also required
        )
    else:
        browser = playwright.chromium.launch(
            headless=flags.headless,
        )
        context = browser.new_context(
        )

    page = context.new_page()

    if flags.loghttp:
        page.on("request", lambda request: print(f"> {request.method} {request.url}"))

    global playwright_instance, playwright_page
    playwright_instance = playwright
    playwright_page = page

    return page

def stopPlaywright():
    global playwright_instance, playwright_page
    playwright_instance.stop()
    playwright_instance = None
    playwright_page = None

# Monkey-Patch Playwright Classes

Locator.outer_html = lambda self: self.evaluate("el => el.outerHTML")
Locator.tag_name = lambda self: self.evaluate("el => el.tagName")

Locator.stripped_text = lambda self: "\n".join([line.strip() for line in self.inner_text().split("\n")])

Locator.get_attrset = lambda self, name: set() if self.get_attribute(name) is None \
                                               else set(self.get_attribute(name).split())

# Other Playwright-Based Utility Functions

def playwrightRequest(img_src):
    filename = f"{normkey}.obj.{img_src.replace('/', '.')}"
    filename = filename.replace(".~.Dokumente.Bundesnormen.", ".BN.")
    filename = filename.replace(".hauptdokument.", ".H.")
    assert ".~." not in filename

    if not (p := Path(f"files/{filename}")).is_file():
        img_url = urljoin(page.url, img_src)
        response = playwright_page.request.get(img_url)
        assert response.ok, f"Failed to fetch image: {response.status}"
        p.write_bytes(response.body())
    return filename


# RisDoc -> Markdown Engine
###########################

class RisDocMarkdownEngine:
    def __init__(self, risDoc, idxDat):
        self.risDoc = risDoc
        self.idxDat = idxDat

        self.meta = {
            item[0].removeprefix("Meta "): item for item in self.risDoc
                    if type(item) is list and len(item) and item[0].startswith("Meta ")
        }
        self.pars = {
            item[0].removeprefix("Par "): item for item in self.risDoc
                    if type(item) is list and len(item) and item[0].startswith("Par ")
        }

        self.lines = []
        self.lineNumStack = []

    def pushLineNum(self):
        self.lineNumStack.append(len(self.lines))

    def popLineNum(self):
        numLines = len(self.lines) - self.lineNumStack.pop()
        return "\n".join(self.lines[len(self.lines)-numLines:])


# CLI Interface
###############

def cli_fetch(*args):
    page = startPlaywright()

    normindex = json.load(open("index.json"))
    if not len(args): args = normindex.keys()

    for normkey in args:
        normdata = normindex[normkey]

        print(f"Loading {normkey} from {normdata['docurl']}")
        page.goto(normdata["docurl"])
        page.add_script_tag(path="RisExtractor.js")

        if 'promulgationsklausel' in normdata:
            t = normdata['promulgationsklausel'].\
                    replace('\\', '\\\\').replace('"', '\\"')
            page.evaluate(f'risUserPromKl = "{t}"')

        if flags.interactive:
            embed(globals(), locals())

        print(f"Extracting files/{normkey}.ris.json")
        stopParJs = f"'{normdata['stop']}'" if 'stop' in normdata else "null"
        risDocJsonText = page.evaluate(f"prettyJSON(risExtractor(null, {stopParJs}, '{normkey}'))")
        open(f"files/{normkey}.ris.json", "w").write(risDocJsonText)

    print("DONE.")
    stopPlaywright()

def cli_render(*args):
    normindex = json.load(open("index.json"))
    if not len(args): args = normindex.keys()

    for normkey in args:
        print(f"Loading {normkey} RisDoc from files/{normkey}.ris.json")
        engine = RisDocMarkdownEngine(
                json.load(open(f"files/{normkey}.ris.json")),
                normindex[normkey])

        if flags.interactive:
            embed(globals(), locals())

    print("DONE.")

def cli_risdoc(*args):
    optFix = False
    optFmt = False
    optUpd = False
    optDiff = False
    doAll = True

    def handleArg(arg):
        if arg != "-" and not os.access(arg, os.F_OK) and \
                os.access(fn := f"files/{arg}.ris.json", os.F_OK): arg = fn

        txt = (open(arg) if arg != "-" else sys.stdin).read()

        if optFix:
            txt = fixPrettyJSON(txt)

        if optFmt:
            txt = prettyJSON(json.loads(txt))

        if optDiff:
            with tempfile.NamedTemporaryFile(delete_on_close=False) as fp:
                fp.write(txt.encode())
                fp.close()
                os.system(f"diff -u '{arg}' {fp.name}")

        if optUpd or not optDiff:
            (open(arg, "w") if optUpd and arg != "-" else sys.stdout).write(txt)

    for arg in args:
        if optNo := arg.startswith("--no-"): del arg[2:3]
        if arg == "--fix": optFix = not optNo; continue
        if arg == "--fmt": optFmt = not optNo; continue
        if arg == "--upd": optUpd = not optNo; continue
        if arg == "--diff": optDiff = not optNo; continue
        handleArg(arg)
        doAll = False

    if doAll:
        for arg in json.load(open("index.json")).keys():
            print(f"Processing {arg} RisDoc from files/{arg}.ris.json")
            handleArg(arg)

def cli_mkjson():
    data = dict()

    for fn in ["index.json"] + glob.glob("files/*.json") + glob.glob("files/*.md"):
        if fn.endswith(".json"):
            data[fn.removeprefix("files/")] = json.load(open(fn))
        else:
            data[fn.removeprefix("files/")] = open(fn).read().split("\n")

    with open("RisExData.json", "w") as f:
        json.dump(data, f)

def main(*args):
    while len(args) and args[0].startswith("--"):
        updateFlags(args[0])
        args = args[1:]
    assert len(args) and f"cli_{args[0]}" in globals()
    return globals()[f"cli_{args[0]}"](*args[1:])

if __name__ == "__main__":
    main(*sys.argv[1:])
