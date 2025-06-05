#!.venv/bin/python
# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

from playwright.sync_api import sync_playwright, Locator
import time, getopt, sys, json, os
from ptpython.repl import embed

# Remember to launch
#   mitmproxy --mode regular --listen-port 8080 -s mitmp.py
# (or similar) when using useProxyMode.
useProxyMode = True

verboseMode = False
useHeadlessMode = True
printHttpRequests = False
launchInteractiveRepl = False
launchEarlyInteractiveRepl = False

defaultNorm = "BG.StGB"
selectParagraph = None


#%% Monkey Patch Playwright

Locator.outer_html = lambda self: self.evaluate("el => el.outerHTML")
Locator.tag_name = lambda self: self.evaluate("el => el.tagName")


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

os.system(f"mkdir -p files; rm -vf files/{normkey}.*")

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
                   .locator(":scope ~ div .ErlText").nth(-1).inner_text()

# Extract intro sentence
if (p := infoBlocks.locator(":scope p.PromKlEinlSatz")).count() == 1:
    introSentence = p.inner_text().strip()
else:
    introSentence = None

# Remove all "sr-only" elements from the DOM tree
page.locator(".sr-only").evaluate_all("els => els.forEach(el => el.remove())")

# Initial State
fileIndex = 0
blockIndex = 0
indexData = list()
outBuffer = list()

# Process a single child node of the current div.contentBlock
def processContentElement(el):
    lines = list()
    cls = set(el.get_attribute("class").split())
    txt = el.inner_text().replace("\xa0", " ")

    match el.tag_name():
        case "H4" if "UeberschrG1" in cls or "UeberschrG1-AfterG2" in cls:
            txt = txt.replace('\n\n', ' # ').replace('\n', ' # ')
            if len(outBuffer) and outBuffer[-1].startswith("## "):
                lines.append(f"## {outBuffer[-1][3:]} # {txt}")
                del outBuffer[-1]
            else:
                lines.append(f"## {txt}")

        case "H4" if "UeberschrPara" in cls:
            lines.append("")
            lines.append(f"### {txt}")

        case "DIV" if "ParagraphMitAbsatzzahl" in cls:
            parBaseName = el.locator(":scope h5.GldSymbol").inner_text().replace("\xa0", " ").removesuffix(".")
            parName = parBaseName + f" {normdata['title']}"
            if len(outBuffer) and outBuffer[-1].startswith("### "):
                lines.append(f"### {parName} # {outBuffer[-1][4:]}")
                del outBuffer[-1]
            else:
                lines.append("")
                lines.append(f"### {parName}")
            for item in el.locator(":scope div.content, :scope .SchlussteilE0").all():
                if item.locator(".Absatzzahl").count():
                    nr = item.locator(".Absatzzahl").inner_text()
                    parName = parBaseName + f" {nr} {normdata['title']}"
                    lines += ["", f"`{parName}.`  "] + item.locator(".Absatzzahl ~ *").inner_text().split("\n")
                elif item.locator(":scope div.AufzaehlungE1").count():
                    symName = item.locator("xpath=..").locator(":scope div.SymE1").inner_text().removesuffix(".")
                    symName = parName.removesuffix(normdata['title']) + f"Z {symName} {normdata['title']}"
                    if len(lines) and not lines[-1].endswith("  "): lines[-1] += "  "
                    lines.append(f"`{symName}.` {item.inner_text()}")
                elif item.get_attribute("class") == "SchlussteilE0":
                    if len(lines) and not lines[-1].endswith("  "): lines[-1] += "  "
                    lines.append(f"{item.inner_text()}")
                else:
                    lines.append(f"{item.tag_name()}: {item.outer_html()}")

        case "DIV" if el.locator(":scope h5.GldSymbol").count():
            parName = el.locator(":scope h5.GldSymbol").inner_text()
            parName = parName.replace("\xa0", " ").removesuffix(".") + f" {normdata['title']}"
            if len(outBuffer) and outBuffer[-1].startswith("### "):
                lines.append(f"### {parName} # {outBuffer[-1][4:]}")
                del outBuffer[-1]
            else:
                lines.append("")
                lines.append(f"### {parName}")
            lines += ["", f"`{parName}.`  "] + el.locator(":scope .GldSymbol ~ *").inner_text().split("\n")

        case _:
            lines.append(f"**FIXME** {el.tag_name()}: {el.outer_html()}")

    return lines

if launchEarlyInteractiveRepl:
    embed(globals(), locals())

# Remove changelog and metadata contentBlocks
infoBlocks.evaluate("el => el.remove()")

blocks = page.locator("div.contentBlock").all()

while blockIndex is not None and blockIndex < len(blocks):
    fileSize = 0
    fileIndex += 1
    indexData.append([f"{normkey}.{fileIndex:03}", []])
    print(f"-- {normkey}.{fileIndex:03}.md --")
    if selectParagraph is not None:
        outFile = sys.stdout
    else:
        outFile = open(f"files/{normkey}.{fileIndex:03}.md", "w")

    print(f"# {normkey}.{fileIndex:03}", file=outFile)
    match normdata['type']:
        case "BG":
            print(f"**Typ:** Bundesgesetz  ", file=outFile)
        case _:
            assert False, "Unrecognized type"
    print(f"**Kurztitel:** {normdata['title']}  ", file=outFile)
    print(f"**Langtitel:** {langtitel}  ", file=outFile)
    print(f"**Letzte Änderung:** {lastchange}  ", file=outFile)
    print(f"**Quelle:** {normdata['docurl']}  ", file=outFile)
    print("*Mit RisEx für RisEn-GPT zu MarkDown konvertiert. " +
            "(Irrtümer und Fehler vorbehalten.)*", file=outFile)
    print("", file=outFile)
    lineNum = 8

    if introSentence is not None and fileIndex == 1:
        print("", file=outFile)
        print(introSentence, file=outFile)
        lineNum += 2

    # Process Content Blocks
    while blockIndex < len(blocks):
        blk = blocks[blockIndex]
        blockIndex += 1

        if selectParagraph is not None:
            if f">§&nbsp;{selectParagraph}.<" not in blk.inner_html():
                continue

        if not useHeadlessMode:
            blk.scroll_into_view_if_needed()
            blk.evaluate("el => el.style.backgroundColor = 'lightblue'")

        outBuffer = list()

        if verboseMode:
            print("------")

        for el in blk.locator(":scope > *").all():
            if verboseMode:
                print("<", f"{el.tag_name()}: {el.outer_html()}")
            for line in processContentElement(el):
                if verboseMode:
                    print(">", line)
                outBuffer.append(line)
            if verboseMode:
                print()

        if not useHeadlessMode:
            blk.evaluate("el => el.style.backgroundColor = ''")

        tx = "\n".join(outBuffer)
        fileSize += len(tx)

        if "split" in normdata and tx.startswith("## ") and \
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
        print("\n`END-OF-DATA-FILE`", file=outFile)

    if selectParagraph is None:
        outFile.close()
        os.system(f"set -ex; zip -vXj RisExFiles.zip files/{normkey}.{fileIndex:03}.md")

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
    os.system(f"set -ex; zip -vXj RisExFiles.zip files/{normkey}.toc.json")


#%% Shutdown Playwright

if launchInteractiveRepl:
    embed(globals(), locals())
elif not useHeadlessMode:
    time.sleep(3)

browser.close()
playwright.stop()
