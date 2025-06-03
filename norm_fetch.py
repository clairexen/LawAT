#!.venv/bin/python
# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

from playwright.sync_api import sync_playwright, Locator
import time, getopt, sys, json
from ptpython.repl import embed

# Remember to launch
#   mitmproxy --mode regular --listen-port 8080 -s mitmp_cache.py
# (or similar) when using useProxyMode.
useProxyMode = True

verboseMode = False
useHeadlessMode = True
printHttpRequests = False
launchInteractiveRepl = False

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
    print("    -r, --print-http .... print a log line for each HTTP request")
    print("    -s N, --select=N .... select a single paragraph")
    print("    -v, --verbose ....... verbose log outut")
    print()
    print(f"The default <norm-key> is {defaultNorm}.")
    print()
    print("Note: Run 'mitmproxy -s mitmp_cache.py' (or mitmweb) in another")
    print("terminal window for a simple local proxy when -P is not used.")
    print()

try:
    opts, args = getopt.getopt(sys.argv[1:], "hs:PHirv",
                               ["help", "select=", "no-proxy", "no-headless",
                                "interactive", "print-http", "verbose"])
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

with open("norm_index.json", "r") as f:
    normindex = json.load(f)

if (normkey := args[0]) not in normindex:
    assert False, "unrecognized shortname"
normdata = normindex[normkey]


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
page.goto(normdata["docurl"])

# Remove all "sr-only" elements from the DOM tree
page.locator(".sr-only").evaluate_all("els => els.forEach(el => el.remove())")

# Process a single child node of the current div.contentBlock
def processContentElement(el):
    lines = list()
    cls = set(el.get_attribute("class").split())
    txt = el.inner_text().replace("\xa0", " ")
    match el.tag_name():
        case "H4" if "UeberschrG1" in cls:
            lines.append(f"## {txt.replace('\n\n', ' | ').replace('\n', ' | ')}")
        case "H4" if "UeberschrG1-AfterG2" in cls:
            lines.append(f"### {txt}")
        case "H4" if "UeberschrPara" in cls:
            lines.append(f"#### {txt}")
        case "DIV" if "ParagraphMitAbsatzzahl" in cls:
            parBaseName = el.locator(":scope h5.GldSymbol").inner_text().replace("\xa0", " ")
            parName = parBaseName.replace(".", f" {normdata['title']}.")
            if len(outBuffer) and outBuffer[-1].startswith("#### "):
                lines.append(f"#### {parName} {outBuffer[-1][5:]}")
                del outBuffer[-1]
            else:
                lines.append(f"#### {parName}")
            enumCnt = 0
            for item in el.locator(":scope div.content").all():
                if item.locator(".Absatzzahl").count():
                    enumCnt = 0
                    nr = item.locator(".Absatzzahl").inner_text()
                    nrName = parBaseName.replace(".", f" {nr} {normdata['title']}.")
                    lines += ["", f"**{nrName}**"] + item.locator(".Absatzzahl ~ *").inner_text().split("\n")
                elif item.locator(":scope div.AufzaehlungE1").count():
                    enumCnt += 1
                    lines.append(f"{enumCnt}. {item.inner_text()}")
                else:
                    enumCnt = 0
                    lines.append(f"{item.tag_name()}: {item.outer_html()}")
        case "DIV":
            parName = el.locator(":scope h5.GldSymbol").inner_text()
            parName = parName.replace("\xa0", " ").replace(".", f" {normdata['title']}.")
            if len(outBuffer) and outBuffer[-1].startswith("#### "):
                lines.append(f"#### {parName} {outBuffer[-1][5:]}")
                del outBuffer[-1]
            else:
                lines.append(f"#### {parName}")
            lines += el.locator(":scope .GldSymbol ~ *").inner_text().split("\n")
        case _:
            lines.append(f"{el.tag_name()}: {el.outer_html()}")
    return lines

outFile = open(f"files/{normkey}.md", "w")

# Process Content Blocks
blocks = page.locator("div.contentBlock").all()
for blk in blocks:
    if selectParagraph is not None:
        if f">§&nbsp;{selectParagraph}.<" not in blk.inner_html():
            continue
    if not useHeadlessMode:
        blk.scroll_into_view_if_needed()
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
    if not verboseMode:
        for line in outBuffer:
            if line.startswith("#"):
                print(line)
    print("\n".join(outBuffer), file=outFile)
    if selectParagraph is not None:
        break


#%% Shutdown Playwright

if launchInteractiveRepl:
    embed(globals(), locals())
elif not useHeadlessMode:
    time.sleep(3)
outFile.close()
browser.close()
playwright.stop()
