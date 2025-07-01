#!.venv/bin/python
# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

import re, glob, fnmatch, requests
import ptpython, inspect, traceback
import time, sys, json, os, tempfile, shutil
import unicodedata, urllib3, types, pprint
from types import SimpleNamespace
from collections import namedtuple, defaultdict
from urllib.parse import urljoin
from pathlib import Path


# Global flags and command line options
#######################################


normindex = json.load(open("normlist.json"))

GlobalFlagDefaults = {
    "esc": False,
    "show": False,
    "strict": True,
    "down": False,
    "embed": False,
    "logjs": True,
    "loghttp": False,
    "logdown": True,
    "verbose": False,
    "forai": True,
    "limit": 30000,
    "filesdir": "files",
    "proxy": "http://127.0.0.1:8080",
    "permauri": "https://github.com/clairexen/LawAT/blob/main/files"
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

from pprint import pp
term_width = shutil.get_terminal_size().columns

# Run `./RisExUtils.py render --prdemo BG.VerG` for a demo
def pr(*args, indent_head="", indent_body="", indent_tail="", depth=1):
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

def downloadFile(file, url, par):
    if not flags.down: return
    if os.access(f"{flags.filesdir}/{file}", os.F_OK): return
    if flags.logdown: print(f"[{par}] {file} <- {url}")
    urllib3.disable_warnings()
    proxies = { "http": flags.proxy, "https": flags.proxy } if flags.proxy else {}
    response = requests.get(url, proxies=proxies, verify=False)
    response.raise_for_status()
    open(f"{flags.filesdir}/{file}", "wb").write(response.content)

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

# Python version of prettyJSON() from RisExtractor.js
def prettyJSON(data, indent="", autofold=False, addFinalNewline=True):
    if autofold and isinstance(data, str) and len(data) > 80:
        return ',\n'.join(indent + json.dumps(line, separators=",:", ensure_ascii=False)
                for line in foldSoftPreserve(data))

    if not isinstance(data, list) or not data or \
            (autofold and len(json.dumps(data, separators=",:", ensure_ascii=False)) < 80):
        return indent + json.dumps(data, separators=",:", ensure_ascii=False)

    if isinstance(data[0], str) and data[0].split()[0] == "Text":
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

    if flags.logjs:
        page.on("console", lambda msg: print(f"[{msg.type}] {msg.text}"))

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


# LawDoc -> Markdown Engine
###########################

def renderText(item, inAnm=False, plain=False):
    if type(item) is str:
        if plain: return item
        return markdownEscape(item)

    head, *tail = item
    tag, s = head.split(), []

    if tag[0] == "Anm" and not plain:
        assert inAnm is False
        inAnm = True
        s.append("*")

    for t in tail:
        s.append(renderText(t, inAnm, plain))

    if tag[0] == "Anm" and not plain:
        s.append("*")

    return "".join(s)

engineIndexOutput = dict()

class LawDocMarkdownEngine:
    def __init__(self, risDoc):
        globals()["_dbg_engine"] = self

        self.risDoc = risDoc
        self.normkey = risDoc[0].removeprefix("LawDoc ")
        self.normdata = normindex[self.normkey]

        self.meta = {
            item[0].removeprefix("Meta "): item for item in self.risDoc
                    if type(item) is list and len(item) and item[0].startswith("Meta ")
        }
        self.pars = {
            item[0].removeprefix("Par "): item for item in self.risDoc
                    if type(item) is list and len(item) and item[0].startswith("Par ")
        }

        self.srcAnchors = dict(line.split(" #", 1) for line in self.meta["ParAnchors"][1:])

        self.addIndexHdrs = False
        if self.normkey not in engineIndexOutput:
            self.addIndexHdrs = True
            engineIndexOutput[self.normkey] = dict()
        self.idxout = engineIndexOutput[self.normkey]

        self.lines = []
        self.lineNumStack = []
        self.citepath = []
        self.pars = []
        self.parmap = {}
        self.sections = []
        self.media = {}

        self.body = None
        self.files = {}

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
        if self.lines[-1] == "":
            self.lines[-1] = line.lstrip()
        else:
            self.lines[-1] += line

    def smallBreak(self):
        if not self.lines: return
        if self.lines[-1] == "": return
        if self.lines[-1].endswith("  "): return
        self.append("  ")

    def largeBreak(self):
        if not self.lines: return
        if self.lines[-1] == "": return
        if self.lines[-1].endswith("  "):
            self.lines[-1] = self.lines[-1].removesuffix("  ")
        self.push("")

    def indentSinceLine(self, firstLine, itemLabel=None):
        if firstLine == len(self.lines):
            return
        if self.lines[firstLine] == "":
            firstLine += 1
        if firstLine == len(self.lines):
            return
        if itemLabel is not None:
            self.lines[firstLine] = f"`{itemLabel}` {self.lines[firstLine]}"
        if self.lines[-1] == "":
            del self.lines[-1]
        self.lines[-1] = self.lines[-1].removesuffix("  ")
        for i in range(firstLine, len(self.lines)):
            if not self.lines[i].startswith(">") and self.lines[i]:
                self.lines[i] = f" {self.lines[i]}"
            self.lines[i] = f">{self.lines[i]}"
        self.largeBreak()

    def genText(self, item, *, nobr=False):
        self.pushLineNum()
        head, *tail = item
        tag = head.split()

        match tag[0]:
            case "Text":
                if not nobr:
                    if len(tag) > 1 and tag[1] == "End":
                        self.smallBreak()
                tx = renderText(item)
                if not flags.forai:
                    if "End" in tag:
                        tx = f"&nbsp; {tx}"
                    if "Erl" in tag:
                        self.largeBreak()
                self.push(tx)

            case "Break":
                self.largeBreak()

            case "List":
                self.genList(item)

            case _:
                if flags.strict:
                    assert False, f"Unsupported Tag in genText(): {tag}"
                else:
                    print(f"Unsupported Tag in genText(): {tag}")

        return self.popLineNum()

    def genItem(self, item, typ, br=True):
        self.pushLineNum()
        head, *tail = item
        tag = head.split()

        assert tag[0] == "Item"
        cite = head.removeprefix("Item ")
        match typ:
            case "Num" if re.fullmatch(r"[0-9]+[a-z]*\.", cite):
                cite = f"Z {cite[:-1]}"
            case "Lit" if re.fullmatch(r"[a-z]+[0-9]*\)", cite):
                cite = f"lit. {cite[:-1]}"
        self.citepath.append(cite)

        if br or not flags.forai:
            self.largeBreak()

        firstIndentLine = None
        if not flags.forai:
            firstIndentLine = len(self.lines)
        else:
            if typ == "Abs" or (br and typ == "List" and len(self.citepath) == 2):
                self.largeBreak()
                self.push(f"`{' '.join(self.citepath)} {self.normdata['title']}.`  ")
            else:
                self.smallBreak()
                self.push(f"`{' '.join(self.citepath)} {self.normdata['title']}.`")

        for t in tail:
            self.genText(t)

        if firstIndentLine is not None:
            self.indentSinceLine(firstIndentLine, head.removeprefix('Item '))

        self.citepath.pop()
        return self.popLineNum()

    def genList(self, item, *, br=False):
        self.pushLineNum()
        head, *tail = item
        tag = head.split()

        for t in tail:
            self.genItem(t, tag[-1], br)

        return self.popLineNum()

    def genImage(self, item):
        self.pushLineNum()
        self.push(f"> IMG: {item[1]}")

        return self.popLineNum()

    def genMedia(self, item):
        self.pushLineNum()
        head, *tail = item

        self.push("")
        for t in tail:
            if t[0] == "Text":
                self.append(f" **{markdownEscape(t[1])}**")
            elif t[0] == "Img":
                fn = f"{self.normkey}.obj.{t[1].replace('/', '.')}"
                fn = fn.replace(".~.Dokumente.Bundesnormen.", ".BN.")
                fn = fn.replace(".hauptdokument.", ".H.")
                self.append(f" ![{fn}]({fn} \"{t[1]}\")")
                self.media[fn] = t[1]
                downloadFile(fn,
                        urljoin(self.normdata['docurl'], t[1]),
                        f"{self.citepath[0]} {self.normdata['title']}")
        self.smallBreak()

        return self.popLineNum()

    def genPar(self, parDoc):
        self.pushLineNum()
        firstLine = len(self.lines)
        startNewSection = False

        assert not self.citepath
        self.citepath.append(parDoc[0].removeprefix("Par "))
        parTitle = parCiteStr = f"{' '.join(self.citepath)} {self.normdata['title']}"
        parRegEx = f"^\\s*{' '.join(self.citepath).replace(' ', r'[\.\s\u00a0]*')}\\b\\.?\\s*"

        hasAbsList = False
        firstIndentLine = None
        def startIndent():
            nonlocal firstIndentLine
            if not flags.forai and firstIndentLine is None:
                firstIndentLine = len(self.lines)
        def performIndent():
            nonlocal firstIndentLine
            if firstIndentLine is not None:
                self.indentSinceLine(firstIndentLine)
                firstIndentLine = None

        anchor = None
        lastTyp = None
        for item in parDoc[1:]:
            if type(item[0]) is dict:
                if flags.strict:
                    assert False, f"Unknown Tag in genPar(): {tag}"
                print(f"Unknown Tag in genPar(): {tag}")
                continue

            head, *tail = item
            tag = head.split()

            match tag[0]:
                case "Head":
                    startNewSection = True
                    if flags.forai and lastTyp == "Head":
                        self.append(f" # {renderText(item, plain=True)}")
                    else:
                        self.largeBreak()
                        self.push(f"## {renderText(item, plain=True)}")
                    if self.addIndexHdrs:
                        self.idxout[f"{len(self.idxout):03}"] = renderText(item, plain=True)
                case "Title":
                    assert parTitle is not None
                    t = renderText(item, plain=True)
                    t = re.sub(parRegEx, '', t).rstrip('. ')
                    parTitle = f"{parTitle} {'#' if flags.forai else '—'} {t}"
                case "SubHdr":
                    performIndent()
                    self.pushHdr(f"#### {renderText(item)}")
                case _:
                    if parTitle is not None:
                        if parCiteStr not in self.idxout:
                            self.idxout[parCiteStr] = SimpleNamespace(
                                ref4human=None, ref4ai=None, title=parTitle)
                        anchor = markdownHeaderToAnchor(parTitle)
                        self.pushHdr(f"### {parTitle}")
                        if tag[0] != "Text":
                            parTitle = None

                    if tag[0] == "Text":
                        if parTitle is not None:
                            self.largeBreak()
                            if flags.forai:
                                self.push(f"`{' '.join(self.citepath)} {self.normdata['title']}.`  ")
                            parTitle = None
                            startIndent()
                            self.genText(item, nobr=True)
                        else:
                            if tag[0] == "Text" and not \
                                    (len(tag) > 1 and tag[1] == "End"):
                                self.largeBreak()
                            else:
                                self.smallBreak()
                            startIndent()
                            self.genText(item)

                    elif tag[0] == "Break":
                        self.largeBreak()

                    elif tag[0] == "Media":
                        startIndent()
                        self.genMedia(item)

                    elif tag[0] == "List":
                        if tag[-1] == "Abs" or hasAbsList:
                            hasAbsList = True
                            performIndent()
                        self.genList(item, br=(tag[-1] in ("Abs", "List")))

                    else:
                        if flags.strict:
                            assert False, f"Unsupported Tag in genPar(): {tag}"
                        else:
                            print(f"Unsupported Tag in genPar(): {tag}")

            lastTyp = tag[0]

        performIndent()
        self.largeBreak()

        lastLine = len(self.lines)-2 # not including the empty line we just pushed
        byteCount = sum(len(self.lines[i]) for i in range(firstLine, lastLine+1))

        if not self.sections or \
                (startNewSection and self.sections[-1].pars):
            self.sections.append(SimpleNamespace(
                idx=len(self.sections), pars=[], byteCount=0
            ))

        parinfo = SimpleNamespace(
            name=self.citepath[0],
            anchor=anchor,
            citename=parCiteStr,
            section=len(self.sections)-1,
            indexInDoc=len(self.pars),
            indexInSection=len(self.sections[-1].pars),
            firstLine=firstLine,
            lastLine=lastLine,
            byteCount=byteCount
        )
        self.pars.append(parinfo)
        self.parmap[parinfo.name] = parinfo
        self.sections[-1].pars.append(parinfo.name)
        self.sections[-1].byteCount += parinfo.byteCount

        self.citepath.pop()
        return self.popLineNum()

    def genBody(self):
        if self.body is None:
            self.pushLineNum()
            for item in self.risDoc[1:]:
                tag = item[0].split()
                if tag[0] != "Par":
                    continue
                self.genPar(item)
            self.body = self.popLineNum()

            self.parts = []
            for s in self.sections:
                if not self.parts or self.parts[-1].byteCount + s.byteCount > flags.limit:
                    self.parts.append(SimpleNamespace(sections=[], pars=[], byteCount=0))
                self.parts[-1].byteCount += s.byteCount
                self.parts[-1].sections.append(s.idx)
                self.parts[-1].pars += s.pars
        return self.body

    def genToc(self, lines, partIdx=None, linkfn=""):
        break_func = self.largeBreak
        for line in lines:
            if line.strip() == "":
                continue
            if line.startswith("## "):
                line = line.removeprefix("## ")
                break_func()
                self.push(f"**{line}**  ")
                break_func = self.smallBreak
            else:
                break_func = self.largeBreak
            if line.startswith("### "):
                line = line.removeprefix("### ")
                self.push(f"* [{line}]({linkfn}#{markdownHeaderToAnchor(line)})  ")

    def genFileHeader(self, partIdx, partSuff):
        self.pushLineNum()

        kurztitel = [self.normdata['title']]
        if "extratitles" in self.normdata:
            kurztitel += self.normdata['extratitles']
        kurztitel = ", ".join(kurztitel)

        self.push(f"# {self.normkey}{partSuff.upper()} — {self.normdata['caption']}")
        self.push(f"**Typ:** {docTypeToLongName(self.normdata['type'])}  ")
        self.push(f"**Kurztitel:** {kurztitel}  ")
        self.push(f"**Langtitel:** {self.meta['Langtitel'][-1]}  ")
        self.push(f"**Gesamte Rechtsvorschrift in der Fassung vom:** {self.meta['FassungVom'][-1]}  ")
        self.push(f"**Quelle:** {self.normdata['docurl']}  ")
        self.push(f"**Letzte Änderung im RIS:** {self.meta['LastChange'][-1]}  ")
        self.push(f"**LawAT Permalink:** {flags.permauri}/{self.normkey}{partSuff}.md  ")
        if len(self.meta["LocalChanges"]) > 1:
            changes = [f"[{change}](../patches/{change}.diff)" for change in self.meta["LocalChanges"][1:]]
            self.push(f"**LawAT Änderungen im Markup:** {', '.join(changes)}  ")
        self.push(f"*Mit RisEx für RisEn und LawAT von HTML zu MarkDown konvertiert. (Irrtümer und Fehler vorbehalten.)*")

        if partIdx is not None:
            self.largeBreak()
            self.push(f"*Das ist die \"AI-Friendly\" multi-part Variante dieser Rechtsvorschrift mit kompakter " +
                      f"Formatierung. Siehe [{self.normkey}.md]({self.normkey}.md) für die \"Human-Friendly\" " +
                      f"single-page Variante dieser Norm mit hübscherer Formatierung.*")

        if partIdx:
            self.pushHdr(f"*(Fortsetzg. v. [{self.normkey}.{partIdx-1:03}]({self.normkey}.{partIdx-1:03}.md))*")

        if not partIdx:
            self.pushHdr("## Inhaltsverzeichnis")
            if partIdx is None:
                self.genToc(self.body, partIdx)
            elif partIdx == 0:
                for i in range(len(self.parts)):
                    firstLine = self.parmap[self.parts[i].pars[0]].firstLine
                    lastLine = self.parmap[self.parts[i].pars[-1]].lastLine
                    self.genToc(self.lines[firstLine:lastLine+1], partIdx, f"{self.normkey}.{i+1:03}.md")

        if partIdx == 1:
            self.pushHdr(self.meta['Promulgation'][-1])
        return self.popLineNum()

    def genFile(self, partIdx=None):
        body = self.genBody()

        if partIdx is None:
            partSuff = ""
        else:
            partSuff = f".{partIdx:03}"

        k = f"{self.normkey}{partSuff}"

        if k not in self.files:
            self.pushLineNum()
            firstLine = len(self.lines)

            self.genFileHeader(partIdx, partSuff)

            pars = self.parts[partIdx-1].pars if partIdx else \
                    self.pars if partIdx is None else []

            firstPar = True
            for p in pars:
                if isinstance(p, str):
                    p = self.parmap[p]

                if not flags.forai:
                    self.largeBreak()
                    self.push("----")

                if partIdx is None and firstPar:
                    self.pushHdr(self.meta['Promulgation'][-1])

                self.largeBreak()
                #self.push("----")
                firstParLine = len(self.lines)
                self.lines += self.lines[p.firstLine:p.lastLine+1]
                lastParLine = len(self.lines)-1
                #self.push("----")

                ref = f"{k}:{firstParLine-firstLine+1}-{lastParLine-firstLine+1}"
                if flags.forai:
                    self.idxout[p.citename].ref4ai = ref
                else:
                    self.idxout[p.citename].ref4human = ref

                if not flags.forai:
                    gnr = None
                    if self.normdata['docurl'].startswith(pf := "https://ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer="):
                        gnr = self.normdata['docurl'].removeprefix(pf)
                    aipartidx = int(self.idxout[p.citename].ref4ai.split(":", 1)[0].split(".")[-1])
                    navItems = [
                        f"[🔗 Permalink]({flags.permauri}/{self.normkey}.md#{p.anchor})",
                        f"[📜 RIS-Paragraphenansicht](http://www.ris.bka.gv.at/NormDokument.wxe?" +
                                f"Abfrage=Bundesnormen&Gesetzesnummer={gnr}&Paragraf={p.name.split()[-1]})",
                        f"[📖 RIS-Gesamtansicht]({self.normdata['docurl']}#{self.srcAnchors[p.name]})",
                        f"[🤖 KI-freundliche Fassung]({flags.permauri}/{self.normkey}.{aipartidx:03}.md#{p.anchor})",
                    ]
                    self.largeBreak()
                    self.push(f"\\[ {' | '.join(navItems)} \\]")

                firstPar = False


            if partIdx is not None:
                self.largeBreak()
                if partIdx < len(self.parts):
                    self.push(f"`END-OF-DATA-FILE` *(fortges. in [{self.normkey}.{partIdx+1:03}]({self.normkey}.{partIdx+1:03}.md))*")
                else:
                    self.push(f"`END-OF-DATA-SET`")

            elif self.srcAnchors["END"] != "footer":
                self.largeBreak()
                self.push("----")
                self.largeBreak()
                self.push("*(Weitere relevante Bestimmungen finden Sie am Ende der [📖 RIS-Gesamtansicht]" +
                        f"({self.normdata['docurl']}#{self.srcAnchors['END']}) zu dieser Rechtsvorschrift.)*")

            lastLine = len(self.lines)-1
            byteCount = sum(len(self.lines[i]) for i in range(firstLine, lastLine+1))

            t = self.popLineNum()
            self.files[k] = SimpleNamespace(name=k, byteCount=byteCount,
                    firstLine=firstLine, lastLine=lastLine, text=t)

        return self.files[k].text

# CLI Interface
###############

def cli_find(normkey):
    page = startPlaywright()

    normdata = {
        "type": normkey.split(".", 1)[0],
        "title": normkey.split(".", 1)[1]
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
    lines = open("normlist.json").read().split("\n")
    assert lines[-1] == ""
    assert lines[-2] == "}"
    assert lines[-3] == "\t}"
    del lines[-3:]
    lines += ["\t},", f"\t\"{normkey}\": {{"]
    lines += [f"\t\t\"{key}\": \"{value}\"," for key, value in normdata.items()]
    lines[-1] = lines[-1].removesuffix(",")
    lines += ["\t}", "}", ""]
    open("normlist.json", "w").write("\n".join(lines))

    print("DONE.")
    stopPlaywright()

def cli_fetch(*args):
    args = updateFlags(*args)

    if not len(args):
        args = normindex.keys()

    page = startPlaywright()

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

        print(f"  `- writing markup object tree to {flags.filesdir}/{normkey}.markup.json")
        stopParJs = f"'{normdata['stop']}'" if 'stop' in normdata else "null"
        risDocJsonText = page.evaluate(f"prettyJSON(risExtractor(null, {stopParJs}, '{normkey}'))")

        if not os.access("__rismarkup__", os.F_OK):
            os.mkdir("__rismarkup__")
        open(f"__rismarkup__/{normkey}.markup.json", "w").write(risDocJsonText)

        if not os.access(flags.filesdir, os.F_OK):
            os.mkdir(flags.filesdir)
        open(f"{flags.filesdir}/{normkey}.markup.json", "w").write(risDocJsonText)

        for patch in sorted(glob.glob(f"patches/{normkey}.p[0-9][0-9][0-9]*.diff")):
            cli_patch(normkey, patch)

    print("DONE.")
    stopPlaywright()

def cli_render(*args):
    addFlag("prdemo", False)
    args = updateFlags(*args)

    if not len(args):
        args = normindex.keys()

    engine = None
    def runEngine(normkey, skipBig=False, skipOthers=False):
        nonlocal engine # for easier debug using embed() from within cli_render()
        engine = LawDocMarkdownEngine(json.load(open(f"{flags.filesdir}/{normkey}.markup.json")))

        if not flags.verbose:
            print(f"[{normkey}] Generating files:")

        if not skipBig:
            if not flags.verbose:
                print(f"{' '*15} BIG", end="")
            else:
                print(f"Writing {flags.filesdir}/{normkey}.md.")

            with open(f"{flags.filesdir}/{normkey}.md", "w") as f:
                for line in engine.genFile(): print(line, file=f)
        elif not flags.verbose:
            print(f"{' '*15} ---", end="")
            engine.genFile()

        for i in range(0, len(engine.parts)+1):
            if not flags.verbose:
                if i % 10 == 9:
                    print(f"\n{' '*15}", end="")
                print(" ---" if skipOthers else f" {i:03}" if i > 0 else " TOC", end="")
            if skipOthers: continue
            if flags.verbose:
                print(f"Writing {flags.filesdir}/{normkey}.{i:03}.md.")
            with open(f"{flags.filesdir}/{normkey}.{i:03}.md", "w") as f:
                for line in engine.genFile(i): print(line, file=f)

        if not flags.verbose:
            print()

        if flags.prdemo:
            pr({"hello_world": engine.parts, "foo": {"bar": engine.sections,
                    "a_list_of_strings": engine.lines[100:109]}}, ..., ...)
            sys.exit(0)

    print()
    print("Generating \"AI-Friendly\" Markdown Files..")

    for normkey in args:
        runEngine(normkey, True, False)

    print()
    print("Generating \"Human-Friendly\" Markdown File(s).")
    updateFlags("--no-forai")
    updateFlags("--esc")

    for normkey in args:
        runEngine(normkey, False, True)

    print()
    print("Generating JSON Index File(s).")

    for normkey in args:
        data = {k: v if isinstance(v, str) else [v.ref4human,v.ref4ai,v.title]
                for k,v in engineIndexOutput[normkey].items()}
        with open(f"{flags.filesdir}/{normkey}.index.json", "w") as f:
            f.write("{")
            sep = "\n  "
            for k, v in data.items():
                k = json.dumps(k, ensure_ascii=False)
                v = json.dumps(v, ensure_ascii=False)
                f.write(f"{sep}{k}: {v}")
                sep = ",\n  "
            f.write("\n}\n")

    print("DONE.")
    embed()

def cli_patch(*args):
    norm, *patches = args

    norm = norm.removeprefix("files/").removesuffix(".markup.json")

    for patch in patches:
        patch = patch.removeprefix("patches/").removesuffix(".diff")

        rc = os.system(f"set -ex; patch -fs 'files/{norm}.markup.json' 'patches/{patch}.diff'")
        assert rc == 0

        txt = open(f"files/{norm}.markup.json").read()
        try:
            markup = json.loads(txt)
        except json.decoder.JSONDecodeError:
            print(" `- applying fixPrettyJSON algorithm")
            txt = fixPrettyJSON(txt)
            markup = json.loads(txt)

        for i in range(1,len(markup)):
            if markup[i][0] == "Meta LocalChanges":
                markup[i].append(patch)
                break
        else:
            assert 0, '"Meta LocalChanges"-element not found'

        txt = prettyJSON(markup)
        open(f"files/{norm}.markup.json", "w").write(txt)

def cli_markup(*args):
    addFlag("fix", False)
    addFlag("fmt", False)
    addFlag("upd", False)
    addFlag("diff", False)

    def handleArg(arg):
        if (a := arg) != "-" and not os.access(arg, os.F_OK) and \
                os.access(fn := f"{flags.filesdir}/{arg}.markup.json", os.F_OK): arg = fn

        print(f"Processing {a} LawDoc from {arg}", file=sys.stderr)

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

    for fn in ["normlist.json"] + glob.glob("{flags.filesdir}/*.json") + glob.glob("{flags.filesdir}/*.md"):
        if fn.endswith(".json"):
            data[fn.removeprefix("{flags.filesdir}/")] = json.load(open(fn))
        else:
            data[fn.removeprefix("{flags.filesdir}/")] = open(fn).read().split("\n")

    with open("RisExData.json", "w") as f:
        json.dump(data, f)

def cli_shell():
    updateFlags("--embed")
    embed()

def main(*args):
    args = updateFlags(*args)
    if len(args) and f"cli_{args[0]}" in globals():
        return globals()[f"cli_{args[0]}"](*args[1:])
    print("RisExUtils Command Overview:")
    print("\n".join(f"  rex [global_options] {name.removeprefix('cli_')} [...]" for name in globals().keys() if name.startswith("cli_")))

if __name__ == "__main__":
    main(*sys.argv[1:])
