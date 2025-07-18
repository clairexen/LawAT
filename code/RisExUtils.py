#!.venv/bin/python
# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

import ptpython, inspect, traceback
import re, pcre2, glob, fnmatch, requests
import time, sys, json, os, tempfile, shutil
import unicodedata, urllib3, types, pprint
from types import SimpleNamespace
from collections import namedtuple, defaultdict
from urllib.parse import urljoin
from pathlib import Path
from lxml import html


# Global flags and command line options
#######################################

normindex = {k: v for k, v in json.load(open("normlist.json")).items() if len(k) > 1}

GlobalFlagDefaults = {
    "esc": False,
    "show": False,
    "strict": True,
    "down": False,
    "embed": False,
    "exit": True,
    "logjs": True,
    "loghttp": False,
    "logdown": True,
    "verbose": False,
    "forai": True,
    "play": False,
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
        elif type(FlagDefaults[key]) == str:
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

    if flags.exit:
        sys.exit()

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

def fetchUrl(url):
    def _sanitize(url: str) -> str:
        """Return a filesystem‑safe filename derived from *url*."""
        safe = re.sub(r"[^a-zA-Z0-9\.-]", "_", url)
        if len(safe) > 200:
            digest = hashlib.sha256(url.encode()).hexdigest()[:16]
            safe = f"{safe[:200]}_{digest}"
        return safe
    cached_file = os.path.join("__webcache__", f"{_sanitize(url)}.content")
    if not os.access(cached_file, os.F_OK):
        urllib3.disable_warnings()
        proxies = { "http": flags.proxy, "https": flags.proxy } if flags.proxy else {}
        response = requests.get(url, proxies=proxies, verify=False)
        response.raise_for_status()
        if not os.access(cached_file, os.F_OK):
            open(cached_file, "wb").write(response.content)
    return cached_file

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
def prettyJSON(data, indent=None, autofold=False, addFinalNewline=True, incindent="    "):
    if indent is None:
        if isinstance(data, dict): data = data["document"]
        s = '{ "$schema": "https://raw.githubusercontent.com/clairexen/LawAT/refs/heads/main/docs/lawdoc.json",\n'
        return s + '  "document": ' + prettyJSON(data, "", autofold, False, "") + '}\n'

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
        s.append(",\n" + prettyJSON(item, indent + incindent, autofold, False))
    s.append("]\n" if addFinalNewline else "]")
    return ''.join(s)

def fixPrettyJSON(text):
    dbgMode = False
    result = []
    stack = [0]

    lines = text.split("\n")
    if lines[0].startswith("{"):
        lines = lines[1:]
        lines[0] = lines[0].removeprefix('  "document": ')
        if not lines[-1]: del lines[-1]
        lines[-1] = lines[-1].removesuffix("}")

    for line in lines:
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
        case "BVG": return "Bundesverfassungsgesetz"
        case "BV": return "Verordnung eines Bundesministeriums"
        case "WLG": return "Wiener Landesgesetz"
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

def renderText(item, inRem=False, plain=False):
    if type(item) is str:
        if plain: return item
        return markdownEscape(item)

    head, *tail = item
    tag, s = head.split(), []

    if tag[0] == "Rem" and not plain:
        assert inRem is False
        inRem = True
        s.append("*")

    for t in tail:
        s.append(renderText(t, inRem, plain))

    if tag[0] == "Rem" and not plain:
        s.append("*")

    return "".join(s)

engineIndexOutput = dict()

class LawDocMarkdownEngine:
    def __init__(self, risDoc):
        globals()["_dbg_engine"] = self

        if isinstance(risDoc, dict):
            risDoc = risDoc["document"]
        self.risDoc = risDoc
        self.normkey = risDoc[0].removeprefix("LawDoc ")
        self.normdata = normindex[self.normkey]

        self.strict_mode = flags.strict
        if "disable-strict-mode" in self.normdata:
            self.strict_mode = False

        self.meta = {
            item[0].removeprefix("Meta "): item for item in self.risDoc
                    if type(item) is list and len(item) and item[0].startswith("Meta ")
        }
        self.pars = {
            item[0].removeprefix("Part "): item for item in self.risDoc
                    if type(item) is list and len(item) and item[0].startswith("Part ")
        }

        self.srcAnchors = dict(line.split(" #", 1) for line in self.meta["PartAnchors"][1:])

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
                if self.strict_mode:
                    assert False, f"Unsupported Tag in genText(): {tag}"
                else:
                    print(f"Unsupported Tag in genText(): {tag}")

        return self.popLineNum()

    def genItem(self, item, typ, br=True):
        self.pushLineNum()
        head, *tail = item
        tag = head.split()

        if br or not flags.forai:
            self.largeBreak()

        if tag[0] != "Rem":
            assert tag[0] == "Item"
            cite = head.removeprefix("Item ")
            match typ:
                case "Num" if re.fullmatch(r"[0-9]+[a-z]*\.", cite):
                    cite = f"Z {cite[:-1]}"
                case "Lit" if re.fullmatch(r"[a-z]+[0-9]*\)", cite):
                    cite = f"lit. {cite[:-1]}"
            self.citepath.append(cite)

        firstIndentLine = None
        if not flags.forai:
            firstIndentLine = len(self.lines)
        elif tag[0] != "Rem":
            if typ == "Abs" or (br and typ == "List" and len(self.citepath) == 2):
                self.largeBreak()
                self.push(f"`{' '.join(self.citepath)} {self.normdata['title']}.`  ")
            else:
                self.smallBreak()
                self.push(f"`{' '.join(self.citepath)} {self.normdata['title']}.`")

        if tag[0] != "Rem":
            for t in tail:
                self.genText(t)
        else:
            self.push(renderText(item))

        if firstIndentLine is not None:
            self.indentSinceLine(firstIndentLine, head.removeprefix('Item ') if tag[0] != "Rem" else None)

        if tag[0] != "Rem":
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

    def genTable(self, item):
        self.pushLineNum()
        head, *tail = item
        tag = head.split()

        self.largeBreak()
        self.push(f'<table><tbody>')
        for tline in tail:
            assert tline[0] == "TabLine"
            self.push(f'<tr>')
            for tcell in tline[1:]:
                self.genTabCell(tcell)
            self.append(f'</tr>')
        self.push(f'</tbody></table>')
        self.largeBreak()

        return self.popLineNum()

    def genTabCell(self, item):
        self.pushLineNum()
        head, *tail = item
        tag, fmt = head.split()
        assert tag == "TabCell"

        hLeft = fmt.startswith(":")
        hRight = fmt.endswith(":")
        hCenter = hLeft and hRight
        hLeft = hLeft and not hCenter
        hRight = hRight and not hCenter
        fmt = fmt.replace(":", "")

        vTop = "A" in fmt or "^" in fmt
        vBottom = "V" in fmt or "v" in fmt
        vCenter = "X" in fmt or "x" in fmt

        # I want this syntax in python: ("A", "V", "X", or "O") in fmt
        isTH = "A" in fmt or "V" in fmt or "X" in fmt or "O" in fmt

        rowSpan, colSpan = fmt.replace("A", ":").replace("V", ":").replace("X", ":").replace("O", ":") \
                              .replace("^", ":").replace("v", ":").replace("x", ":").replace("o", ":").split(":")
        rowSpan = int(rowSpan) if rowSpan else 0
        colSpan = int(colSpan) if colSpan else 0

        style = []
        if vTop: style.append(f'vertical-align:top')
        if vBottom: style.append(f'vertical-align:bottom')
        if vCenter: style.append(f'vertical-align:center')
        if hLeft: style.append(f'text-align:left')
        if hRight: style.append(f'text-align:right')
        if hCenter: style.append(f'text-align:center')

        self.append('<th' if isTH else '<td')
        if rowSpan > 1: self.append(f' rowspan={rowSpan}')
        if colSpan > 1: self.append(f' colspan={colSpan}')
        if style: self.append(f' style="{";".join(style)}"')
        self.append('>' + renderText(item, plain=True))
        self.append('</th>' if isTH else '</td>')

        return self.popLineNum()

    def genPart(self, parDoc):
        self.pushLineNum()
        firstLine = len(self.lines)
        startNewSection = False

        assert not self.citepath
        self.citepath.append(parDoc[0].removeprefix("Part "))
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
                if self.strict_mode:
                    assert False, f"Unknown Tag in genPart(): {item[0]}"
                print(f"Unknown Tag in genPart(): {item[0]}")
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

                    elif tag[0] == "Table":
                        self.genTable(item)

                    else:
                        if self.strict_mode:
                            assert False, f"Unsupported Tag in genPart(): {tag}"
                        else:
                            print(f"Unsupported Tag in genPart(): {tag}")

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
                if tag[0] != "Part":
                    continue
                self.genPart(item)
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
        self.push(f"*Mit RisEx für RisEn, RisEn-GPT, und LawAT von HTML zu MarkDown konvertiert. (Irrtümer und Fehler vorbehalten.)*")

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

            firstPart = True
            for p in pars:
                if isinstance(p, str):
                    p = self.parmap[p]

                if not flags.forai:
                    self.largeBreak()
                    self.push("----")

                if partIdx is None and firstPart:
                    self.pushHdr(self.meta['Promulgation'][-1])

                self.largeBreak()
                #self.push("----")
                firstPartLine = len(self.lines)
                self.lines += self.lines[p.firstLine:p.lastLine+1]
                lastPartLine = len(self.lines)-1
                #self.push("----")

                ref = f"{k}:{firstPartLine-firstLine+1}-{lastPartLine-firstLine+1}"
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

                firstPart = False


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

def cli_update(*args):
    addFlag("new", False)
    args = updateFlags(*args)

    if flags.new and not args:
        for arg in normindex.keys():
            if not os.access(f"files/{arg}.index.json", os.F_OK):
                args.append(arg)
        if not args:
            print("Nothing new.")
            return

    cli_fetch(*args)
    cli_render("--index", "--down", *args)

def cli_fetch(*args):
    addFlag("patch", True)
    args = updateFlags(*args)

    if not len(args):
        args = normindex.keys()

    if flags.play:
        page = startPlaywright()

    for normkey in args:
        normdata = normindex[normkey]
        dates = (normdata['idFv'] if 'idFv' in normdata else []) + [""]

        for date in dates:
            datestr = date if date else "markup"
            url = normdata["docurl"]

            if date:
                url += f"&FassungVom={date}"
            elif 'pin' in normdata:
                url += f"&FassungVom={dates[normdata['pin']]}"

            print(f"Loading {normkey} from {url}")
            if flags.play:
                page.goto(url)
                page.add_script_tag(path="code/RisExtractor.js")

                if 'promulgationsklausel' in normdata:
                    t = normdata['promulgationsklausel'].\
                            replace('\\', '\\\\').replace('"', '\\"')
                    page.evaluate(f'risUserPromKl = "{t}"')

                embed()

            stopPartJs = f"'{normdata['stop']}'" if 'stop' in normdata else "null"
            if flags.play:
                print(f"  `- writing markup object tree to {flags.filesdir}/{normkey}.{datestr}.json")
                risDocJsonText = page.evaluate(f"prettyJSON(risExtractor(null, {stopPartJs}, '{normkey}'))")
                risDocJsonText = json.loads(risDocJsonText)
            else:
                cached_file = fetchUrl(url)
                print(f"  `- writing markup object tree to {flags.filesdir}/{normkey}.{datestr}.json")
                risDocJsonText = os.popen(f"node code/RisExtractor.js '{cached_file}' {stopPartJs}").read()
                risDocJsonText = json.loads(risDocJsonText)
                if risDocJsonText[0] == "LawDoc":
                    risDocJsonText[0] = f"LawDoc {normkey}"
                for item in risDocJsonText:
                    if isinstance(item, list):
                        if item[0] == "Meta RisSrcLink":
                            item[1] = url
                        if item[0] == "Meta Promulgation" and 'promulgationsklausel' in normdata:
                            t = normdata['promulgationsklausel'].\
                                    replace('\\', '\\\\').replace('"', '\\"')
                            item[1] = t

            if "remove-headers" in normdata:
                changecnt = 0
                def text(el):
                    if not isinstance(el, list):
                        return el.replace("\u00a0", " ")
                    return " ".join([text(c) for c in el[1:]])
                def walker(el, pat):
                    nonlocal changecnt
                    if not isinstance(el, list):
                        return el
                    if el[0].startswith("Head") or el[0].startswith("Title") or \
                            el[0].startswith("SubHdr"):
                        t = el[0] + " " + text(el)
                        if pat.match(t):
                            changecnt += 1
                            return None
                    return [c for c in [el[0]] + [walker(c, pat) for c in el[1:]] if c is not None]
                risDocJsonText = walker(risDocJsonText, re.compile(normdata["remove-headers"]))
                print(f"  `- removed {changecnt} headers matching /{normdata['remove-headers']}/.")

            risDocJsonText = prettyJSON(risDocJsonText)

            if not os.access("__rismarkup__", os.F_OK):
                os.mkdir("__rismarkup__")
            open(f"__rismarkup__/{normkey}.{datestr}.json", "w").write(risDocJsonText)

            if not os.access(flags.filesdir, os.F_OK):
                os.mkdir(flags.filesdir)
            open(f"{flags.filesdir}/{normkey}.{datestr}.json", "w").write(risDocJsonText)

            if flags.patch:
                patches = set(glob.glob(f"patches/{normkey}.c[0-9][0-9][0-9]-*.diff"))
                patches |= set(glob.glob(f"patches/{normkey}.c[0-9][0-9][0-9]_{datestr}-*.diff"))
                for patch in sorted(patches):
                    cli_patch(normkey, patch)

    if flags.play:
        stopPlaywright()
    print("DONE.")

def cli_render(*args):
    addFlag("prdemo", False)
    addFlag("index", False)
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
        data = [v if isinstance(v, str) else [k,v.ref4human,v.ref4ai,v.title]
                for k,v in engineIndexOutput[normkey].items()]
        with open(f"{flags.filesdir}/{normkey}.index.json", "w") as f:
            f.write("{\n")
            f.write("  \"toc\": [")
            sep = "\n    "
            for item in data:
                f.write(f"{sep}{json.dumps(item, ensure_ascii=False)}")
                sep = ",\n    "
            f.write("\n")
            f.write("  ],\n")
            f.write("  \"index\": {")
            sep = "\n    "
            for idx, item in enumerate(data):
                if isinstance(item, str): continue
                f.write(f"{sep}\"{item[0]}\": {idx}")
                sep = ",\n    "
            f.write("\n")
            f.write("  }\n")
            f.write("}\n")

    if flags.index:
        print("Generating Top-Level Index Files.")
        cli_index()

    print("DONE.")
    embed()

def cli_index():
    with open(f"{flags.filesdir}/index.md", "w") as f_md:
        with open(f"{flags.filesdir}/index.json", "w") as f_json:
            f_md.write(f"# LawAT Rechtsdatensatz — Index der Normen\n")
            f_json.write(f"[")
            json_sep = "\n  "
            for pf, header in (
                        ("BVG.", "Bundesverfassungsgesetze"),
                        ("BG.", "Bundesgesetze"),
                        ("BV.", "Verordnungen der Bundesminister(ien)"),
                        ("WLG.", "Wiener Landesgesetze"),
                    ):
                f_md.write(f"\n## {header}\n")
                f_md.write("\n".join(sorted([f'* [{normindex[normkey]["caption"]}]({normkey}.md)'
                        for normkey in normindex.keys() if normkey.startswith(pf)]))+"\n")
                f_json.write(f"{json_sep}{json.dumps(header, separators=",:", ensure_ascii=False)}")
                json_sep = ",\n  "
                f_json.write((json_sep + "  ").join([""] + sorted([f'[{json.dumps(normindex[normkey]["caption"], separators=",:", ensure_ascii=False)},{json.dumps(normkey, separators=",:", ensure_ascii=False)}{"".join(","+json.dumps(d, separators=",:", ensure_ascii=False) for d in (normindex[normkey]["idFv"] if "idFv" in normindex[normkey] else []))}]'
                        for normkey in normindex.keys() if normkey.startswith(pf)])))
            f_json.write(f"\n]\n")

def cli_patch(*args):
    norm, *patches = args

    norm = norm.removeprefix("files/").removesuffix(".markup.json")

    for patch in patches:
        patch = patch.removeprefix("patches/").removesuffix(".diff")

        rc = os.system(f"set -ex; patch --no-backup-if-mismatch -r - -fs 'files/{norm}.markup.json' 'patches/{patch}.diff'")
        assert rc == 0

        txt = open(f"files/{norm}.markup.json").read()
        try:
            markup = json.loads(txt)["document"]
        except json.decoder.JSONDecodeError:
            print(" `- applying fixPrettyJSON algorithm")
            txt = fixPrettyJSON(txt) + "]"
            markup = json.loads(txt)

        for i in range(1,len(markup)):
            if markup[i][0] == "Meta LocalChanges":
                markup[i].append(patch)
                break
        else:
            assert 0, '"Meta LocalChanges"-element not found'

        txt = prettyJSON(markup)
        open(f"files/{norm}.markup.json", "w").write(txt)

def cli_diff(norm):
    os.system(f"bash -c \"diff --label {norm}.markup.json --label {norm}.markup.json -uF '^\\[' " + \
              f"<(git cat-file blob :files/{norm}.markup.json;) files/{norm}.markup.json\"")

def cli_markup(*args):
    addFlag("fix", False)
    addFlag("fmt", False)
    addFlag("upd", False)
    addFlag("diff", False)
    addFlag("check", False)
    args = updateFlags(*args)

    def handleArg(arg):
        if (a := arg) != "-" and not os.access(arg, os.F_OK) and \
                os.access(fn := f"{flags.filesdir}/{arg}.markup.json", os.F_OK): arg = fn

        print(f"Processing {a} LawDoc from {arg}", file=sys.stderr)

        if flags.check:
            rc = os.system(f"set -ex; .venv/bin/check-jsonschema -v --schemafile docs/lawdoc.json '{arg}'")
            assert rc == 0

        txt = (open(arg) if arg != "-" else sys.stdin).read()

        if flags.check:
            regex = pcre2.compile(open("docs/lawdoc.pcre").read())
            if not (m := regex.match(txt)):
                print(f"Matching docs/lawdoc.pcre against '{arg}' failed.")
                print(f"Markup FAILED pcre regex verification!")
                sys.exit(1)
            else:
                mlines = [t.removesuffix("\n").count("\n") + bool(t)
                          for t in [m.group(1), m.group(2), m.group(3)]]
                if mlines[1] == 0 and m.group(3).strip() == "]}":
                    print(f"Markup passed pcre regex verification. Woohoo!")
                else:
                    print(f"Matching (valid) initial number of lines: {mlines[0]}")
                    if mlines[1]:
                        print(f"First non-matching (invalid) document part:\n{m.group(2)}")
                    else:
                        print(f"First lines of non-matching document part:\n{'\n'.join(m.group(3).split('\n')[:10])}")
                    print(f"Markup FAILED pcre regex verification!")
                    sys.exit(1)
            return

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

    if not args:
        args = (*normindex.keys(),)

    while args:
        handleArg(args[0])
        args = updateFlags(*args[1:])

def cli_rs(*args):
    addFlag("scan", True)
    addFlag("fetch", True)
    args = updateFlags(*args)

    #rsdata = { "items": {}, "index": {} }
    rsdata = json.load(open("files/rsdata.json"))

    if flags.scan:
        pos = 1
        lastPos = 1
        query = [
            "Abfrage=Justiz", "Gericht=OGH",
            # "AenderungenSeit=EinemJahr",
            # "AenderungenSeit=EinemMonat",
            "AenderungenSeit=ZweiWochen",
            # "AenderungenSeit=EinerWoche",
            "SucheNachRechtssatz=True",
            # "Norm=ABGB"
        ]
        while pos <= lastPos:
            print(f"Scanning positions {pos} - {pos+99}{f' / {lastPos}' if lastPos>1 else ''}.")
            htmldata = open(fetchUrl(f"https://ris.bka.gv.at/Ergebnis.wxe?{'&'.join(query)}&ResultPageSize=100&Position={pos}")).read()
            tree = html.fromstring(htmldata)
            lastPos = int(tree.cssselect(".NumberOfDocuments")[0].text_content().strip().removesuffix(".").split(" ")[-1])

            for row in tree.cssselect(".bocListDataRow"):
                a = row.cssselect(":scope a")[0]
                rsid = a.text_content()
                if ";" in rsid: rsid = rsid.split(";", 1)[0]
                if rsid in rsdata["items"]: continue
                url = f"https://ris.bka.gv.at/Dokument.wxe?Abfrage=Justiz&{a.attrib['href'].split('&')[-1]}"
                print(f"Tagging {rsid}: {url}")
                rsdata["items"][rsid] = url

            pos += 100

        print("Finished scan. Updating files/rsdata.json.")
        with open("files/rsdata.json", "w") as f:
            json.dump(rsdata, f, ensure_ascii=False, indent=2)

    if flags.fetch:
        cnt = 0
        queue = sum(isinstance(url, str) for url in rsdata["items"].values())
        for rsid, url in rsdata["items"].items():
            if not isinstance(url, str): continue
            print(f"Fetching {rsid} [{cnt}/{queue}]: {url}")
            tree = html.fromstring(open(fetchUrl(url)).read())
            rsdata["items"][rsid] = {
                "RS": rsid,
                "URL": url,
                "Gericht": tree.xpath("//h3[contains(., 'Gericht')]/..")[0].text_content(). \
                                replace(" ", "").strip().split("\n")[1],
                "ET_Count": len(tree.xpath("//h3[contains(., 'Entscheidungstexte')]/../ul/li")),
                "Normen": sorted(set([it.text_content() for it in tree.xpath("//h3[contains(., 'Norm')]/..")[0]. \
                                        getchildren() if it.tag != "div" and it.text_content()][1:])),
                "Rechtssatz": tree.xpath("//h3[contains(., 'Rechtssatz')]/..")[1].text_content().strip(). \
                                        removeprefix("Rechtssatz\n").strip(),
                "Datum_Seit": tree.xpath("//h3[contains(., 'Im RIS seit')]/..")[0].text_content().strip(). \
                                        removeprefix("Im RIS seit\n").strip(),
                "Datum_Update": tree.xpath("//h3[contains(., 'Zuletzt aktualisiert am')]/..")[0].text_content().strip(). \
                                        removeprefix("Zuletzt aktualisiert am\n").strip(),
            }
            if res := tree.xpath("//h3[contains(., 'Rechtsgebiet')]/.."):
                rsdata["items"][rsid]["Rechtsgebiet"] = res[0].text_content(). \
                                replace(" ", "").strip().split("\n")[1]
            if res := tree.xpath("//h3[contains(., 'Schlagworte')]/.."):
                rsdata["items"][rsid]["Schlagworte"] = sorted(w.strip() for w in \
                                res[0].text_content().strip().removeprefix("Schlagworte").split(",") if w.strip())
            cnt += 1
            if cnt % 100 == 0:
                print("Finished batch. Updating files/rsdata.json.")
                with open("files/rsdata.json", "w") as f:
                    json.dump(rsdata, f, ensure_ascii=False, indent=2)

        print(f"Finished fetch. Updating files/rsdata.json (len={len(rsdata['items'])}).")
        rsdata["items"] = dict(sorted(rsdata["items"].items()))
        with open("files/rsdata.json", "w") as f:
            json.dump(rsdata, f, ensure_ascii=False, indent=2)

    rsdata["index"] = {}
    for rsitem in rsdata["items"].values():
        for norm in rsitem["Normen"]:
            n = norm.split(" ")
            if len(n) != 2: continue
            if not n[1].startswith("§"): continue
            if n[0] not in rsdata["index"]:
                rsdata["index"][n[0]] = {}
            partName = f"§ {n[1].removeprefix('§')} {n[0]}"
            if partName not in rsdata["index"][n[0]]:
                rsdata["index"][n[0]][partName] = []
            rsdata["index"][n[0]][partName] = sorted(set(rsdata["index"][n[0]][partName] + [rsitem["RS"]]))

    print(f"Finished indexing. Updating files/rsdata.json.")
    rsdata["index"] = dict(sorted((k, dict(sorted(v.items()))) for k,v in rsdata["index"].items()))
    with open("files/rsdata.json", "w") as f:
        json.dump(rsdata, f, ensure_ascii=False, indent=2)

def cli_mkjson():
    data = dict()

    for fn in ["normlist.json"] + glob.glob(f"{flags.filesdir}/*.json") + glob.glob(f"{flags.filesdir}/*.md"):
        if fn.endswith(".json"):
            data[fn.removeprefix(f"{flags.filesdir}/")] = json.load(open(fn))
        else:
            data[fn.removeprefix(f"{flags.filesdir}/")] = open(fn).read().split("\n")

    with open("LawAT_DataSet.json", "w") as f:
        json.dump(data, f)

def cli_mkwebapp():
    data = dict()
    for fn in sorted([f"{flags.filesdir}/index.json", f"{flags.filesdir}/rsdata.json"] +
                     glob.glob(f"{flags.filesdir}/*.index.json") + glob.glob(f"{flags.filesdir}/*.markup.json") +
                     glob.glob(f"{flags.filesdir}/*.[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].json")):
        data[fn.removeprefix(f"{flags.filesdir}/")] = json.load(open(fn))
    with open("webapp.json", "w") as f:
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
