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
            lines += txt.split("\n")
        case _:
            lines.append(f"{el.tag_name()}: {el.outer_html()}")
    return lines

# Process Content Blocks
blocks = page.locator("div.contentBlock").all()
for blk in blocks:
    if selectParagraph is not None and \
       f"§\xa0{selectParagraph}." not in blk.inner_text():
        continue
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
    print("\n".join(outBuffer))


#%% Shutdown Playwright

if launchInteractiveRepl:
    embed(globals(), locals())
elif not useHeadlessMode:
    time.sleep(3)
browser.close()

playwright.stop()
