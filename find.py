#!.venv/bin/python
# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

from playwright.sync_api import sync_playwright
import time, getopt, sys, json, os
from ptpython.repl import embed

# Remember to launch
#   mitmproxy --mode regular --listen-port 8080 -s mitmp_cache.py
# (or similar) when using useProxyMode.
useProxyMode = True

useHeadlessMode = True
printHttpRequests = False
launchInteractiveRepl = False

defaultNorm = "BG.StGB"

#%% Usage + Getopt + Load Index

def usage():
    print()
    print(f"Usage: {sys.argv[0]} [options] [<norm-key>]")
    print()
    print("    -P, --no-proxy ...... do not use local proxy on port 8080")
    print("    -H, --no-headless ... no headless mode (i.e. show browser window)")
    print("    -i, --interactive ... launch interactive REPL before shutting down")
    print("    -r, --print-http .... print a log line for each HTTP request")
    print()
    print(f"The default <norm-key> is {defaultNorm}.")
    print()
    print("Note: Run 'mitmproxy -s mitmp_cache.py' (or mitmweb) in another")
    print("terminal window for a simple local proxy when -P is not used.")
    print()

try:
    opts, args = getopt.getopt(sys.argv[1:], "ho:PHir",
                               ["help", "output=", "no-proxy", "no-headless",
                                "interactive", "print-http"])
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
    #elif o in ("-o", "--output"):
    #    output = a
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

if normdata["type"] in ("BG", "BVG"):
    # Fill out search form
    page.goto("https://ris.bka.gv.at/Bundesrecht/")
    page.locator("#MainContent_TitelField_Value").fill(normdata["title"])
    page.locator("#MainContent_VonParagrafField_Value").fill("0")
    page.locator("#MainContent_TypField_Value").fill(normdata["type"])
    page.locator("#MainContent_SearchButton").click()

    # Click through to complete norm
    with context.expect_page() as new_page_info:
        page.locator("a").get_by_text("heute", exact=True).click()
    page = new_page_info.value
    page.wait_for_load_state()

    print(f"Document URL for {normkey}:", page.url)
    normdata["docurl"] = page.url


#%% Save Index + Shutdown Playwright

with open("index.json", "w") as f:
    json.dump(normindex, f, ensure_ascii=False, indent=4)
    print(file=f)
os.system("set -ex; zip -vXj RisExFiles.zip index.json")

if launchInteractiveRepl:
    embed(globals(), locals())
elif not useHeadlessMode:
    time.sleep(3)
browser.close()

playwright.stop()
