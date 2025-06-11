#!/bin/bash
set -ex
python3 -m venv .venv
source .venv/bin/activate
pip install playwright
pip install requests
pip install ptpython
pip install rich
# pip install spyder
playwright install
set +x
echo
echo "Run this in your shell:"
echo "source .venv/bin/activate"
echo
