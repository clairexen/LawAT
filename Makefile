# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

help:
	@echo ""
	@echo "Usage:"
	@echo "  make venv ........ create Python .venv/"
	@echo "  make zip ......... (re-)create RisExFiles.zip"
	@echo "  make json ........ (re-)create RisExData.json"
	@echo "  make purge ....... remove these (re-)created output files"
	@echo ""

venv: .venv/bin/activate
.venv/bin/activate:
	python3 -m venv .venv
	.venv/bin/pip install playwright
	.venv/bin/pip install requests
	.venv/bin/pip install ptpython
	.venv/bin/pip install ipython
	.venv/bin/pip install rich
	.venv/bin/playwright install

zip: RisExFiles.zip
RisExFiles.zip: index.json files/*
	rm -vf RisExFiles.zip
	zip -vXj RisExFiles.zip -r files index.json

json: RisExData.json
RisExData.json: venv index.json files/*
	./RisExUtils.py mkjson

update:
	.venv/bin/python3 RisExUtils.py fetch
	.venv/bin/python3 RisExUtils.py render --down
	$(MAKE) zip json

check-markup:
	check-jsonschema --schemafile schema.json files/*.markup.json
	grep -h '^ *\[' files/*.markup.json | sed -e 's/^ *//; s/\]*,.*//; /\["\(Par\|RisDoc\|Item\|Meta\) / s/ .*/ ..."/' | sort | uniq -c

purge:
	rm -rf .venv RisExData.json __pycache__/ __rismarkup__/ __rishtml__/
	rm -rf RisExFiles.zip

.PHONY: help venv zip json update check-markup purge
