#!/usr/bin/env python3
# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

import glob, json

data = dict()

for fn in ["index.json"] + glob.glob("files/*.json") + glob.glob("files/*.md"):
    if fn.endswith(".json"):
        data[fn.removeprefix("files/")] = json.load(open(fn))
    else:
        data[fn.removeprefix("files/")] = open(fn).read().split("\n")

with open("RisExData.json", "w") as f:
    json.dump(data, f)
