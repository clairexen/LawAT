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
	.venv/bin/pip install requests
	.venv/bin/pip install ptpython
	.venv/bin/pip install ipython
	.venv/bin/pip install rich
	.venv/bin/pip install check-jsonschema
	.venv/bin/pip install playwright
	.venv/bin/playwright install

zip: RisExFiles.zip
RisExFiles.zip: normlist.json files/*
	rm -vf RisExFiles.zip
	zip -vXj RisExFiles.zip -r files normlist.json

json: RisExData.json
RisExData.json: venv normlist.json files/*
	.venv/bin/python3 RisExUtils.py mkjson
	.venv/bin/python3 RisExUtils.py mkwebapp

update:
	rm -rf files __rismarkup__ __webcache__
	.venv/bin/python3 RisExUtils.py fetch
	.venv/bin/python3 RisExUtils.py render --down --index
	$(MAKE) zip json

check-markup: JSON_SCHEMA ?= docs/lawdoc.json
check-markup:
	.venv/bin/check-jsonschema -v --check-metaschema $(JSON_SCHEMA)
	set -e; for f in files/*.markup.json; do .venv/bin/check-jsonschema -v --schemafile $(JSON_SCHEMA) $$f; done
	grep -h '^ *\[' files/*.markup.json | sed -re 's/^ *//; s/\]*[\}?,].*//; /\["(Part|Item|Meta|Table|TabCell) / s/ .*/ ..."/' | sort | uniq -c

mitmp:
	mitmdump -s mitmp.py

webapp:
	.venv/bin/python3 RisExUtils.py mkwebapp
	( sleep 1; xdg-open http://0.0.0.0:8000/; ) &
	cd webapp && ../.venv/bin/python3 -m http.server

deploy:
	.venv/bin/python3 RisExUtils.py mkwebapp
	[ -d __ghpages__ ] || git clone -b gh-pages git@github.com:clairexen/LawAT.git __ghpages__
	-cd __ghpages__ && git rm -rf .
	cp -vt __ghpages__/ RisExData.json RisExFiles.zip webapp/lawdoc.json
	cp -vt __ghpages__/ webapp/index.html webapp/style.css
	cp -vt __ghpages__/ webapp/lawdoc.js webapp/lawdoc.css
	cp -vt __ghpages__/ webapp/tocui.js webapp/tocui.css
	cd __ghpages__ && git add . && git commit -m deploy && git push

purge:
	rm -rf .venv __pycache__/ __ghpages__/ __rismarkup__/ __webcache__/
	rm -rf RisExData.json RisExFiles.zip webapp/lawdoc.json

.PHONY: help venv zip json update check-markup mitmp webapp deploy purge
