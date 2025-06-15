#!.venv/bin/python
# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

import re, glob, fnmatch
import ptpython, inspect, traceback
import time, sys, json, os, tempfile
from collections import namedtuple
from urllib.parse import urljoin
from pathlib import Path
import unicodedata


# Global flags and command line options
#######################################

normindex = json.load(open("index.json"))

GlobalFlagDefaults = {
    "esc": True,
    "show": False,
    "embed": False,
    "loghttp": False,
    "proxy": "http://127.0.0.1:8080",
}

FlagsType = namedtuple("FlagsType", GlobalFlagDefaults.keys(),
        defaults=GlobalFlagDefaults.values())
flags = FlagsType()

def addFlag(name, defVal):
    global FlagsType, flags
    FlagsType = namedtuple("FlagsType", (*FlagsType._fields, name),
            defaults=(*FlagsType._field_defaults.values(), defVal))
    flags = FlagsType(**flags._asdict())

def updateFlags(*opts):
    global flags

    while opts and opts[0].startswith("--"):
        o, *opts = opts

        if o == "--trap":
            sys.excepthook = excepthook
            continue

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

    return opts


# ptpython and other debug helpers
##################################

def pr(*args):
    for arg in args:
        if type(arg) is str:
            print(arg)
        else:
            pr(*arg)

def ptpy_configure(repl):
    if False:
        for n in dir(repl):
            if n.startswith("_"): continue
            print(n, getattr(repl, n))
    repl.swap_light_and_dark = True

def embed():
    if not flags.embed:
        return

    caller = inspect.currentframe().f_back
    print(f"\nCalled embed() from {caller.f_code.co_filename}:{caller.f_lineno} — dropping to ptpython:")
    ptpython.repl.embed(caller.f_globals, caller.f_locals, configure=ptpy_configure)

def excepthook(typ, value, tb):
    traceback.print_exception(typ, value, tb)
    print("\nUncaught exception — dropping to ptpython:")
    ptpython.repl.embed(globals(), locals(), configure=ptpy_configure)


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
    if not flags.esc: return text
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
            headless=not flags.show,
            proxy={"server": flags.proxy},
            args=["--ignore-certificate-errors"],
        )
        context = browser.new_context(
            ignore_https_errors=True,  # this is also required
        )
    else:
        browser = playwright.chromium.launch(
            headless=not flags.show,
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

def renderText(item, inAnm=False):
    if type(item) is str:
        return markdownEscape(item)

    head, *tail = item
    tag, s = head.split(), []

    if tag[0] == "Anm":
        assert inAnm is False
        inAnm = True
        s.append("*")

    for t in tail:
        s.append(renderText(t, inAnm))

    if tag[0] == "Anm":
        s.append("*")

    return "".join(s)

class RisDocMarkdownEngine:
    def __init__(self, risDoc):
        self.risDoc = risDoc
        self.normkey = risDoc[0].removeprefix("RisDoc ")
        self.normdata = normindex[self.normkey]

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
        self.citepath = []

    def pushLineNum(self):
        self.lineNumStack.append(len(self.lines))

    def popLineNum(self):
        numLines = len(self.lines) - self.lineNumStack.pop()
        return self.lines[len(self.lines)-numLines:]

    def push(self, line):
        self.lines.append(line)

    def pushHdr(self, line):
        self.largeBreak();
        self.lines.append(line)
        self.largeBreak();

    def pop(self):
        return self.lines.pop()

    def append(self, line):
        self.lines[-1] += line

    def smallBreak(self):
        if self.lines[-1] == "": return
        if self.lines[-1].endswith("  "): return
        self.append("  ")

    def largeBreak(self):
        if self.lines[-1] == "": return
        if self.lines[-1].endswith("  "):
            self.lines[-1] = self.lines[-1].removesuffix("  ")
        self.push("")

    def genFileHeader(self, partIdx=None):
        # # BG.VerG.TOC — Vereinsgesetz (VerG)
        # **Typ:** Bundesgesetz
        # **Kurztitel:** VerG, VerG_2002
        # **Langtitel:** Bundesgesetz über Vereine (Vereinsgesetz 2002 – VerG)
        # **Gesamte Rechtsvorschrift in der Fassung vom:** 12.06.2025
        # **Letzte Änderung:** BGBl. I Nr. 133/2024 (NR: GP XXVII IA 4123/A AB 2622 S. 274. BR: AB 11571 S. 970.)
        # **Quelle:** https://ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=20001917
        # **RisEx-Link:** https://github.com/clairexen/RisEx/blob/main/files/BG.VerG.toc.md
        # *Mit RisEx für RisEn-GPT von HTML zu MarkDown konvertiert. (Irrtümer und Fehler vorbehalten.)*

        if partIdx is None:
            partSuff = "big"
        elif partIdx:
            partSuff = f"{partIdx:03}"
        else:
            partSuff = "toc"

        self.pushLineNum()

        self.push(f"# {self.normkey}.{partSuff.upper()} — {self.normdata['caption']}")
        self.push(f"**Typ:** {docTypeToLongName(self.normdata['type'])}  ")
        self.push(f"**Quelle:** {self.normdata['docurl']}  ")
        self.push(f"**RisEx-Link:** https://github.com/clairexen/RisEx/blob/main/files/{self.normkey}.{partSuff}.md  ")
        self.push(f"*Mit RisEx für RisEn-GPT von HTML zu MarkDown konvertiert. (Irrtümer und Fehler vorbehalten.)*")

        return self.popLineNum()

    def genText(self, item, *, nobr=False):
        self.pushLineNum()
        head, *tail = item
        tag = head.split()

        match tag[0]:
            case "Text":
                if not nobr and len(tag) > 1 and tag[1] in ("End", "Erl"):
                    self.smallBreak()
                self.push(renderText(item))

            case "Break":
                self.largeBreak()

            case _:
                if tag[0] in ("NumLst", "LitLst", "Lst"):
                    self.genLst(item)
                else:
                    assert False, f"Unsupported Tag in genText(): {tag}"

        # for t in tail: self.genItem(t)

        return self.popLineNum()

    def genItem(self, item, typ, br=True):
        self.pushLineNum()
        head, *tail = item
        tag = head.split()

        assert tag[0] == "Item"
        cite = head.removeprefix("Item ")
        match typ:
            case "NumLst" if re.fullmatch(r"[0-9]+[a-z]*\.", cite):
                cite = f"Z {cite[:-1]}"
            case "LitLst" if re.fullmatch(r"[a-z]+[0-9]*\)", cite):
                cite = f"lit. {cite[:-1]}"
        self.citepath.append(cite)

        if br:
            self.largeBreak()

        if typ == "AbsLst" or (br and typ == "Lst" and len(self.citepath) == 2):
            self.largeBreak()
            self.push(f"`{' '.join(self.citepath)} {self.normdata['title']}.`  ")
        else:
            self.smallBreak()
            self.push(f"`{' '.join(self.citepath)} {self.normdata['title']}.`")

        for t in tail:
            self.genText(t)

        self.citepath.pop()
        return self.popLineNum()

    def genLst(self, item, *, br=False):
        self.pushLineNum()
        head, *tail = item
        tag = head.split()

        for t in tail:
            self.genItem(t, tag[0], br)

        return self.popLineNum()

    def genPar(self, parDoc):
        self.pushLineNum()

        assert not self.citepath
        self.citepath.append(parDoc[0].removeprefix("Par "))
        parTitle = f"{' '.join(self.citepath)} {self.normdata['title']}"

        lastTyp = None
        for item in parDoc[1:]:
            if type(item[0]) is dict:
                #  assert False, f"Unsupported Tag in genText(): {tag}"
                #print(f"Unsuppoerted {item=}")
                continue

            head, *tail = item
            tag = head.split()

            match tag[0]:
                case "Head":
                    if lastTyp == "Head":
                        self.append(f" # {renderText(item)}")
                    elif len(tag) > 1 and tag[1] == "Erl":
                        self.pushHdr(f"#### {renderText(item)}")
                    else:
                        self.pushHdr(f"## {renderText(item)}")
                case "Title":
                    if len(tag) > 1 and tag[1] == "Erl":
                        self.pushHdr(f"#### {renderText(item)}")
                    else:
                        assert parTitle is not None
                        parTitle = f"{parTitle} # {renderText(item)}"
                case _:
                    if parTitle is not None:
                        self.pushHdr(f"### {parTitle}")
                        if tag[0] != "Text":
                            parTitle = None

                    if tag[0] == "Text":
                        if parTitle is not None:
                            self.largeBreak()
                            self.push(f"`{' '.join(self.citepath)} {self.normdata['title']}.`  ")
                            parTitle = None
                            self.genText(item, nobr=True)
                        else:
                            self.largeBreak()
                            self.genText(item)

                    elif tag[0] == "Break":
                        self.largeBreak()

                    elif tag[0] in ("AbsLst", "NumLst", "LitLst", "Lst"):
                        self.genLst(item, br=True)

                    else:
                        assert False, f"Unsupported Tag in genText(): {tag}"

            lastTyp = tag[0]

        self.largeBreak()
        self.citepath.pop()
        return self.popLineNum()

    def genFile(self, partIdx=None):
        self.pushLineNum()
        self.genFileHeader(partIdx)
        for item in self.risDoc[1:]:
            tag = item[0].split()
            if tag[0] != "Par":
                continue
            self.genPar(item)
        self.largeBreak()
        self.push("`END-OF-DATA-SET`")
        return self.popLineNum()

# CLI Interface
###############

def cli_find(normkey):
    page = startPlaywright()

    normdata = {
        "type": normkey.split(".", 1)[0],
        "title": normkey.split(".", 1)[1],
        "split": 20000
    }

    if normdata["type"] in ("BG", "BVG"):
        # Fill out search form
        page.goto("https://ris.bka.gv.at/Bundesrecht/")
        page.locator("#MainContent_TitelField_Value").fill(normdata["title"])
        page.locator("#MainContent_VonParagrafField_Value").fill("0")
        page.locator("#MainContent_TypField_Value").fill(normdata["type"])
        page.locator("#MainContent_SearchButton").click()

        # Click through to complete norm
        with page.context.expect_page() as new_page_info:
            page.locator("a").get_by_text("heute", exact=True).click()
        page = new_page_info.value
        page.wait_for_load_state()

        print(f"Document URL for {normkey}:", page.url)
        docurl = page.url

    print("Opening {docurl}")
    os.system(f"xdg-open '{docurl}'")
    time.sleep(0.5)

    normdata["stop"] = input("Letzter paragraph (zB '§ 123a')? ")
    normdata["caption"] = input("Caption? ")
    normdata["docurl"] = docurl

    # Update Index JSON
    lines = open("index.json").read().split("\n")
    assert lines[-1] == ""
    assert lines[-2] == "}"
    assert lines[-3] == "\t}"
    del lines[-3:]
    lines += ["\t},", f"\t\"{normkey}\": {{"]
    lines += [f"\t\t\"{key}\": \"{value}\"," for key, value in normdata.items()]
    lines[-1] = lines[-1].removesuffix(",")
    lines += ["\t}", "}", ""]
    open("index.json", "w").write("\n".join(lines))

    print("DONE.")
    stopPlaywright()

def cli_fetch(*args):
    page = startPlaywright()

    if not len(args):
        args = normindex.keys()

    for normkey in args:
        normdata = normindex[normkey]

        print(f"Loading {normkey} from {normdata['docurl']}")
        page.goto(normdata["docurl"])
        page.add_script_tag(path="RisExtractor.js")

        if 'promulgationsklausel' in normdata:
            t = normdata['promulgationsklausel'].\
                    replace('\\', '\\\\').replace('"', '\\"')
            page.evaluate(f'risUserPromKl = "{t}"')

        embed()

        print(f"Extracting files/{normkey}.ris.json")
        stopParJs = f"'{normdata['stop']}'" if 'stop' in normdata else "null"
        risDocJsonText = page.evaluate(f"prettyJSON(risExtractor(null, {stopParJs}, '{normkey}'))")
        open(f"files/{normkey}.ris.json", "w").write(risDocJsonText)

    print("DONE.")
    stopPlaywright()

def cli_render(*args):
    if not len(args):
        args = normindex.keys()

    for normkey in args:
        print(f"Loading {normkey} RisDoc from files/{normkey}.ris.json")
        engine = RisDocMarkdownEngine(json.load(open(f"files/{normkey}.ris.json")))

        embed()

        with open(f"files/{normkey}.big.md", "w") as f:
            for line in engine.genFile(): print(line, file=f)

    print("DONE.")

def cli_risdoc(*args):
    addFlag("fix", False)
    addFlag("fmt", False)
    addFlag("upd", False)
    addFlag("diff", False)

    def handleArg(arg):
        print(f"Processing {arg} RisDoc from files/{arg}.ris.json", file=sys.stderr)

        if arg != "-" and not os.access(arg, os.F_OK) and \
                os.access(fn := f"files/{arg}.ris.json", os.F_OK): arg = fn

        txt = (open(arg) if arg != "-" else sys.stdin).read()

        if flags.fix:
            txt = fixPrettyJSON(txt)

        if flags.fmt:
            txt = prettyJSON(json.loads(txt))

        if flags.diff:
            with tempfile.NamedTemporaryFile(delete_on_close=False) as fp:
                fp.write(txt.encode())
                fp.close()
                os.system(f"diff -u '{arg}' {fp.name}")

        if flags.upd or not flags.diff:
            (open(arg, "w") if flags.upd and arg != "-" else sys.stdout).write(txt)

    args = updateFlags(*args)

    if not args:
        args = (*normindex.keys(),)

    while args:
        handleArg(args[0])
        args = updateFlags(*args[1:])

def cli_mkjson():
    data = dict()

    for fn in ["index.json"] + glob.glob("files/*.json") + glob.glob("files/*.md"):
        if fn.endswith(".json"):
            data[fn.removeprefix("files/")] = json.load(open(fn))
        else:
            data[fn.removeprefix("files/")] = open(fn).read().split("\n")

    with open("RisExData.json", "w") as f:
        json.dump(data, f)

def cli_shell():
    updateFlags("--embed")
    embed()

def main(*args):
    args = updateFlags(*args)
    assert len(args) and f"cli_{args[0]}" in globals()
    return globals()[f"cli_{args[0]}"](*args[1:])

if __name__ == "__main__":
    main(*sys.argv[1:])
