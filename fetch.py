#!.venv/bin/python
# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

from playwright.sync_api import sync_playwright, Locator
import time, getopt, sys, json, os, re, fnmatch
from urllib.parse import urljoin
from ptpython.repl import embed
from pathlib import Path
import unicodedata
from RisExUtils import *

# Remember to launch
#   mitmproxy --mode regular --listen-port 8080 -s mitmp.py
# (or similar) when using useProxyMode.
useProxyMode = True

verboseMode = False
useHeadlessMode = True
printHttpRequests = False
launchInteractiveRepl = False
launchEarlyInteractiveRepl = False
deleteOldObjects = False

defaultNorm = "BG.StGB"
selectParagraph = None


#%% Monkey Patch Playwright

Locator.outer_html = lambda self: self.evaluate("el => el.outerHTML")
Locator.tag_name = lambda self: self.evaluate("el => el.tagName")

Locator.stripped_text = lambda self: "\n".join([line.strip() for line in self.inner_text().split("\n")])

Locator.get_attrset = lambda self, name: set() if self.get_attribute(name) is None \
                                               else set(self.get_attribute(name).split())


#%% Various Utility Functions

def markdownHeaderToAnchor(header: str) -> str:
    anchor = unicodedata.normalize("NFC", header)  # normalize unicode (e.g., ä → ä)
    anchor = anchor.lower()  # convert to lowercase
    anchor = re.sub(r"\s+", "-", anchor)  # replace spaces with hyphens
    anchor = re.sub(r"[^\w\s\-]", "", anchor)  # remove punctuation except hyphens and spaces
    anchor = anchor.removeprefix("-") # remove one (and only one) leading hyphen
    return anchor

def fetchObject(img_src):
    filename = f"{normkey}.obj.{img_src.replace('/', '.')}"
    filename = filename.replace(".~.Dokumente.Bundesnormen.", ".BN.")
    filename = filename.replace(".hauptdokument.", ".H.")
    assert ".~." not in filename

    if not (p := Path(f"files/{filename}")).is_file():
        img_url = urljoin(page.url, img_src)
        response = page.request.get(img_url)
        assert response.ok, f"Failed to fetch image: {response.status}"
        p.write_bytes(response.body())
        os.system(f"set -ex; zip -vXj RisExFiles.zip files/{filename}")
    return filename


#%% Usage + Getopt + Load Index

def usage():
    print()
    print(f"Usage: {sys.argv[0]} [options] [<norm-key>]")
    print()
    print("    -P, --no-proxy ...... do not use local proxy on port 8080")
    print("    -H, --no-headless ... no headless mode (i.e. show browser window)")
    print("    -i, --interactive ... launch interactive REPL before shutting down")
    print("    -e, --early ......... launch interactive REPL at an arlier time")
    print("    -r, --print-http .... print a log line for each HTTP request")
    print("    -s N, --select=N .... select a single paragraph")
    print("    -v, --verbose ....... verbose log outut")
    print()
    print(f"The default <norm-key> is {defaultNorm}.")
    print()
    print("Note: Run 'mitmproxy -s mitmp.py' (or mitmweb) in another")
    print("terminal window for a simple local proxy when -P is not used.")
    print()

try:
    opts, args = getopt.getopt(sys.argv[1:], "hs:PHierv",
                               ["help", "select=", "no-proxy", "no-headless",
                                "interactive", "early", "print-http", "verbose"])
except getopt.GetoptError as err:
    # print help information and exit:
    print(err)  # will print something like "option -a not recognized"
    usage()
    sys.exit(2)

for o, a in opts:
    if o in ("-h", "--help"):
        usage()
        sys.exit()
    elif o in ("-P", "--no-proxy"):
        useProxyMode = False
    elif o in ("-H", "--no-headless"):
        useHeadlessMode = False
    elif o in ("-r", "--print-http"):
        printHttpRequests = True
    elif o in ("-i", "--interactive"):
        launchInteractiveRepl = True
    elif o in ("-e", "--early"):
        launchEarlyInteractiveRepl = True
    elif o in ("-v", "--verbose"):
        verboseMode = True
    elif o in ("-s", "--select"):
        selectParagraph = a
    else:
        assert False, "unhandled option"

if len(args) == 0:
    args = [defaultNorm]
elif len(args) != 1:
    usage()
    sys.exit(2)

with open("index.json", "r") as f:
    normindex = json.load(f)

if (normkey := args[0]) not in normindex:
    assert False, "unrecognized shortname"
normdata = normindex[normkey]

force_erl_item = None
if 'force_erl_item' in normdata:
    force_erl_item = re.compile("|".join([
        f"(?:{p[1:]})" if p.startswith("/") else
        fnmatch.translate(p).removesuffix("\\Z")
        for p in normdata['force_erl_item']
    ]))

force_erl_ueberschr = None
if 'force_erl_ueberschr' in normdata:
    force_erl_ueberschr = re.compile("|".join([
        f"(?:{p[1:]})\\Z" if p.startswith("/") else
        fnmatch.translate(p)
        for p in normdata['force_erl_ueberschr']
    ]))

filePatterns = [
    f"{normkey}.[0-9][0-9][0-9].md",
    f"{normkey}.toc.json",
    f"{normkey}.toc.md",
]
if deleteOldObjects:
    filePatterns.append(f"{normkey}.obj.*")
if selectParagraph is None:
    os.system(f"""
        mkdir -p files
        rm -vf files/{' files/'.join(filePatterns)}
    """)
if not deleteOldObjects:
    filePatterns.append(f"{normkey}.obj.*")


#%% Initialize Browser Context

playwright = sync_playwright().start()

if useProxyMode:
    browser = playwright.chromium.launch(
        headless=useHeadlessMode,
        proxy={"server": "http://127.0.0.1:8080"},
        args=["--ignore-certificate-errors"],
    )
    context = browser.new_context(
        ignore_https_errors=True,  # this is also required
    )
else:
    browser = playwright.chromium.launch(
        headless=useHeadlessMode,
    )
    context = browser.new_context(
    )

page = context.new_page()

if printHttpRequests:
    page.on("request", lambda request: print(f"> {request.method} {request.url}"))


#%% Actual Playwright Script

# Load Document
print(f"Loading {normkey} from {normdata['docurl']}")
page.goto(normdata["docurl"])
page.add_script_tag(path="RisExtractor.js")

if 'promulgationsklausel' in normdata:
    t = normdata['promulgationsklausel'].\
            replace('\\', '\\\\').replace('"', '\\"')
    page.evaluate(f'risUserPromKl = "{t}"')

print(f"Extracting files/{normkey}.ris.json")
stopParJs = f"'{normdata['stop']}'" if 'stop' in normdata else "null"
risDocJsonText = page.evaluate(f"prettyJSON(risExtractor(null, {stopParJs}, '{normkey}'))")
open(f"files/{normkey}.ris.json", "w").write(risDocJsonText)

if False:
    print("DONE.")
    browser.close()
    playwright.stop()
    sys.exit(0)

langtitel = page.locator("h3") \
 .get_by_text("Langtitel", exact=True) \
 .evaluate("""el => {
  let node = el.nextSibling;
  while (node && node.nodeType !== Node.TEXT_NODE) {
    node = node.nextSibling;
  }
  return node ? node.textContent.trim() : null;
}""")
print(f"Langtitel: {langtitel}")

# Extract last changelog
infoBlocks = page.locator(".documentContent").nth(0)
lastchange = infoBlocks.locator(":scope h3").get_by_text("Änderung") \
                   .locator(":scope ~ div .ErlText").nth(-1).stripped_text()

# Extract intro sentence
if (p := infoBlocks.locator(":scope p.PromKlEinlSatz")).count() == 1:
    introSentence = p.stripped_text().strip()
elif "promulgationsklausel" in normdata:
    introSentence = normdata['promulgationsklausel']
else:
    introSentence = None

# Extract Date
dateStr = page.locator("#Title").inner_text().split()[-3:]
assert dateStr[0] == "Fassung"
assert dateStr[1] == "vom"
dateStr = dateStr[2]

# Remove all "sr-only" elements from the DOM tree
page.locator(".sr-only").evaluate_all("els => els.forEach(el => el.remove())")

# Initial State
fileIndex = 0
blockIndex = 0
indexData = list()
outBuffer = list()

# Process a single child node of the current div.contentBlock
def processContentElement(el, outbuf, parName = None):
    cls = el.get_attrset("class")
    txt = el.stripped_text().replace("\xa0", " ")

    def handleHeader():
        tx = txt.replace('\n\n', ' # ').replace('\n', ' # ')
        if len(outbuf) and outbuf[-1].startswith("## "):
            outbuf.append(f"## {outbuf[-1][3:]} # {tx}")
            del outbuf[-2]
        else:
            outbuf.append("")
            outbuf.append(f"## {tx}")

    def handleParHeader():
        nonlocal parName, txt
        if txt.startswith("§"):
            parName = txt.split()[:2]
            for p in parName:
                txt = txt.removeprefix(p).lstrip()
            parName = " ".join(parName).replace(".", "") + f" {normdata['title']}"
            txt = f"{parName} # {txt}" if txt != "" else parName
        outbuf.append("")
        outbuf.append(f"### {txt}")

    def handleGldSymbolDiv():
        nonlocal parName, outbuf
        parName = el.locator(":scope h5.GldSymbol").stripped_text()
        parName = parName.replace("\xa0", " ").removesuffix(".") + f" {normdata['title']}"

        if len(outbuf) and outbuf[-1].startswith("### "):
            if not outbuf[-1].startswith(f"### {parName}"):
                outbuf.append(f"### {parName} # {outbuf[-1][4:]}")
                del outbuf[-2]
        else:
            outbuf.append("")
            outbuf.append(f"### {parName}")

        if "ParagraphMitAbsatzzahl" in cls:
            for item in el.locator(":scope > *").all():
                if not "GldSymbolFloatLeft" in item.get_attrset("class"):
                    processContentElement(item, outbuf, parName)
        else:
            outbuf += ["", f"`{parName}.`  "]
            if (items := el.locator(":scope .GldSymbol ~ *")).count():
                outbuf.append(items.stripped_text())

    def handleList():
        nonlocal outbuf
        for item in el.locator(":scope > li").all():
            if force_erl_item is not None and \
                    force_erl_item.match(tx := item.stripped_text().replace("\xa0", " ")):
                pf = item.locator(":scope > .SymE0, :scope > .SymE1, :scope > .SymE2").stripped_text()
                tx = tx.removeprefix(pf).replace("\n", " ").strip()
                handleText("p", False, False, txtOverwrite=f"**{pf}** {tx}")
                continue

            if force_erl_ueberschr is not None and \
                    force_erl_ueberschr.match(tx := item.stripped_text().replace("\xa0", " ")):
                handleText("p", False, True, txtOverwrite=tx.replace("\n", " "))
                continue

            znr = item.locator(":scope > .SymE0, :scope > .SymE1, :scope > .SymE2")
            if znr.count() == 0: znr = item.locator(".Absatzzahl")
            znr = znr.stripped_text().removesuffix(".")

            if znr.startswith("("):
                subName = parName.removesuffix(normdata['title']) + f"{znr} {normdata['title']}"
                outbuf += ["", f"`{subName}.`  "]
            else:
                if znr[0].isnumeric():
                    subName = parName.removesuffix(normdata['title']) + f"Z {znr} {normdata['title']}"
                else:
                    subName = parName.removesuffix(normdata['title']) + f"lit. {znr} {normdata['title']}"
                if len(outbuf) and not outbuf[-1].endswith("  "): outbuf[-1] += "  "
                outbuf.append(f"`{subName}.`")

            for e in item.locator(":scope > div.content > *").all():
                if "GldSymbolFloatLeft" in item.get_attrset("class"): continue
                processContentElement(e, outbuf, subName)

    def handleText(br = False, absHack = False, bold = False, txtOverwrite = None):
        nonlocal outbuf
        if br == "p":
            if len(outbuf) and not outbuf[-1] == "":
                outbuf.append("")
        elif br:
            if len(outbuf) and not outbuf[-1].endswith("  "):
                outbuf[-1] += "  "
        tx = el.stripped_text() if txtOverwrite is None else txtOverwrite
        if absHack and (n := el.locator(":scope > .Absatzzahl")).count():
            tx = tx.removeprefix(n.stripped_text())
        if bold:
            tx = f"**{tx}**  "
        for k in el.locator(":scope .Kursiv").all():
            kt = k.stripped_text()
            tx = tx.replace(kt, f"*{kt}*")
        outbuf.append(tx)

    def handleObjects():
        nonlocal outbuf
        if len(outbuf) and not outbuf[-1].endswith("  "):
            outbuf[-1] += "  "
        md = list()
        for i in range(el.evaluate("el => el.childNodes.length")):
            match el.evaluate(f"el => el.childNodes[{i}].nodeType"):
                case 1:
                    assert el.evaluate(f"el => el.childNodes[{i}].tagName") == "IMG"
                    src = el.evaluate(f"el => el.childNodes[{i}].getAttribute('src')")
                    filename = fetchObject(src)
                    md.append(f"![{filename}]({filename} \"{src}\")")
                case 3:
                    tx = el.evaluate(f"el => el.childNodes[{i}].nodeValue").replace("\xa0", " ").strip()
                    if len(tx): md.append(f"**{tx}**")
                case _:
                    assert False
        outbuf.append(f"{' '.join(md)}  ");

    def any_in(s, *a):
        return any([item in s for item in a])

    match el.tag_name():
        case "P" if any_in(cls, "UeberschrG2"):
            handleHeader()

        case "H4" if any_in(cls, "UeberschrG1", "UeberschrG1-", "UeberschrG1-AfterG2", "UeberschrArt"):
            handleHeader()

        case "H4" if any_in(cls, "UeberschrPara"):
            if parName is None:
                handleParHeader()
            else:
                handleText("p", False, True)

        case "H4" if any_in(cls, "ErlUeberschrL"):
            handleText("p", False, True)

        case "P" if any_in(cls, "Abs", "Abs_small_indent", "SatznachNovao", "Abstand"):
            handleText()

        case "P" if any_in(cls, "ErlText"):
            if force_erl_ueberschr is not None and \
                    force_erl_ueberschr.match(txt):
                handleText("p", False, True, txtOverwrite=txt.replace("\n", " "))
            else:
                handleText(True)

        case "P" if any_in(cls, "AbbildungoderObjekt"):
            handleObjects()

        case "DIV" if any_in(cls, "Abs", "Abs_small_indent"):
            handleText(False, True)

        case "DIV" if any_in(cls, "AufzaehlungE0", "AufzaehlungE1", "AufzaehlungE2"):
            handleText()

        case "DIV" if any_in(cls, "SchlussteilE0", "SchlussteilE1", "SchlussteilE2", "SchlussteilE0_5"):
            handleText(True)

        case "DIV" if el.locator(":scope h5.GldSymbol").count():
            handleGldSymbolDiv()

        case "OL":
            handleList()

        case _:
            outbuf.append(f"**FIXME** {el.tag_name()}: {el.outer_html()}")

    return parName

if launchEarlyInteractiveRepl:
    embed(globals(), locals())

# Remove changelog and metadata contentBlocks
infoBlocks.evaluate("el => el.remove()")

blocks = page.locator("div.contentBlock").all()

metaDataLines = list()
match normdata['type']:
    case "BG":
        metaDataLines.append(f"**Typ:** Bundesgesetz  ")
    case _:
        assert False, "Unrecognized type"
titles = [normdata['title']]
if "extratitles" in normdata:
    titles += normdata['extratitles']
metaDataLines.append(f"**Kurztitel:** {', '.join(titles)}  ")
metaDataLines.append(f"**Langtitel:** {langtitel}  ")
metaDataLines.append(f"**Gesamte Rechtsvorschrift in der Fassung vom:** {dateStr}  ")
metaDataLines.append(f"**Letzte Änderung:** {lastchange}  ")
metaDataLines.append(f"**Quelle:** {normdata['docurl']}  ")
metaDataLines.append(f"**RisEx-Link:** https://github.com/clairexen/RisEx/blob/main/files/@RisExFile@  ")
metaDataLines.append("*Mit RisEx für RisEn-GPT von HTML zu MarkDown konvertiert. " +
                     "(Irrtümer und Fehler vorbehalten.)*")

while blockIndex is not None and blockIndex < len(blocks):
    fileSize = 0
    fileIndex += 1
    indexData.append([f"{normkey}.{fileIndex:03}", []])
    if selectParagraph is not None:
        outFile = sys.stdout
    else:
        print(f"-- {normkey}.{fileIndex:03}.md --")
        outFile = open(f"files/{normkey}.{fileIndex:03}.md", "w")

    print(f"# {normkey}.{fileIndex:03} — {normdata['caption']}", file=outFile)
    lineNum = 1

    for line in metaDataLines:
        print(line.replace("@RisExFile@", f"{normkey}.{fileIndex:03}.md"), file=outFile)
        lineNum += 1

    if fileIndex == 1:
        print("", file=outFile)
        print(f"*(Inhaltsverzeichnis: [{normkey}.toc]({normkey}.toc.md))*", file=outFile)
        lineNum += 2
        if introSentence is not None:
            print("", file=outFile)
            print(introSentence, file=outFile)
            lineNum += 2
    else:
        print("", file=outFile)
        print(f"*(Fortsetzg. v. [{normkey}.{fileIndex-1:03}]({normkey}.{fileIndex-1:03}.md))*", file=outFile)
        lineNum += 2

    # Process Content Blocks
    while blockIndex < len(blocks):
        blk = blocks[blockIndex]
        blockIndex += 1

        if selectParagraph is not None:
            if f">§&nbsp;{selectParagraph}." not in blk.inner_html():
                continue

        if not useHeadlessMode:
            blk.scroll_into_view_if_needed()
            blk.evaluate("el => el.style.backgroundColor = 'lightblue'")

        outBuffer = list()
        parName = None

        if verboseMode:
            print("------")

        for el in blk.locator(":scope > *").all():
            if verboseMode:
                print("<", f"{el.tag_name()}: {el.outer_html()}")
            parName = processContentElement(el, outBuffer, parName)
            if verboseMode:
                for line in outBuffer:
                    print("->", line)
                print()

        if not useHeadlessMode:
            blk.evaluate("el => el.style.backgroundColor = ''")

        if True:
            unnormalizedOutBufLines = len(outBuffer)
            outBuffer = sum([t.split("\n") for t in outBuffer], [])
            # assert unnormalizedOutBufLines == len(outBuffer)

        tx = "\n".join(outBuffer)
        fileSize += len(tx)

        if "split" in normdata and tx.startswith("\n## ") and \
                                   fileSize > normdata['split'] and fileSize > len(tx):
            blockIndex -= 1
            break

        for line in outBuffer:
            lineNum += 1
            if not verboseMode and (line.startswith("#") or line.startswith("**FIXME** ")):
                print(line)
            if line.startswith("#"):
                indexData[-1][-1].append([lineNum, line])

        print(tx, file=outFile)

        if "stop" in normdata:
            stopList = normdata['stop']
            if type(stopList) is str:
                stopList = [stopList]
            for line in outBuffer:
                for par in stopList:
                    if line.startswith(f"### {par} {normdata['title']}"):
                        if par == stopList[-1]:
                            blockIndex = None
                        blk = None
            if blk is None:
                break

        if selectParagraph is not None:
            blockIndex = None
            break

    if blockIndex is None or blockIndex >= len(blocks):
        indexData[-1][-1].append([lineNum+2, "END-OF-DATA-SET"])
        print("\n`END-OF-DATA-SET`", file=outFile)
    else:
        indexData[-1][-1].append([lineNum+2, "END-OF-DATA-FILE"])
        print(f"\n`END-OF-DATA-FILE` *(fortges. in [{normkey}.{fileIndex+1:03}]({normkey}.{fileIndex+1:03}.md))*", file=outFile)

    if selectParagraph is None:
        outFile.close()

if selectParagraph is None:
    outFile = open(f"files/{normkey}.toc.json", "w")
    if False:
        json.dump(dict(indexData), outFile, ensure_ascii=False, indent=0)
    else:
        sep = "{"
        for fn, items in indexData:
            print(f"{sep}\n  \"{fn}\": [\n    ", end="", file=outFile)
            print(",\n    ".join([json.dumps(item, ensure_ascii=False) for item in items]), file=outFile)
            print("  ]", end="", file=outFile)
            sep = ","
        print("\n}", file=outFile)
    outFile.close()

    outFile = open(f"files/{normkey}.toc.md", "w")
    print(f"# {normkey}.TOC — {normdata['caption']}", file=outFile)
    for line in metaDataLines:
        print(line.replace("@RisExFile@", f"{normkey}.toc.md"), file=outFile)

    print("", file=outFile)
    print("## Inhaltsverzeichnis", file=outFile)
    for fn, items in indexData:
        for _, txt in items:
            if txt.startswith("## "):
                for line in txt.removeprefix('## ').split(" # "):
                    print("", file=outFile)
                    print(f"**{line}**  ", file=outFile)
            elif txt.startswith("### "):
                print(f"* [{txt.removeprefix('### ')}]({fn}.md#{markdownHeaderToAnchor(txt)})", file=outFile)

    print(f"\n`END-OF-TOC` *(fortges. in [{normkey}.001]({normkey}.001.md))*", file=outFile)
    outFile.close()

if selectParagraph is None:
    os.system(f"""
        [ -f RisExFiles.zip ] && zip -d RisExFiles.zip "{'" "'.join(filePatterns)}"
        set -ex; zip -vXj RisExFiles.zip files/{' files/'.join(filePatterns)}
    """)


#%% Shutdown Playwright

if launchInteractiveRepl:
    embed(globals(), locals())
elif not useHeadlessMode:
    time.sleep(3)

browser.close()
playwright.stop()
