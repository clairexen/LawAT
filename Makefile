# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

help:
	@echo ""
	@echo "Usage:"
	@echo "  make venv ........ create Python .venv/"
	@echo "  make zip ......... (re-)create LawAT_DataSet.zip"
	@echo "  make json ........ (re-)create LawAT_DataSet.json"
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
	.venv/bin/pip install pcre2
	.venv/bin/pip install lxml
	.venv/bin/pip install cssselect
	.venv/bin/playwright install

zip: LawAT_DataSet.zip
LawAT_DataSet.zip: normlist.json files/*
	rm -vf LawAT_DataSet.zip
	zip -vXj LawAT_DataSet.zip -r files normlist.json

json: LawAT_DataSet.json
LawAT_DataSet.json: venv normlist.json files/*
	.venv/bin/python3 code/RisExUtils.py mkjson
	.venv/bin/python3 code/RisExUtils.py mkwebapp

update:
	rm -rf files __rismarkup__ __webcache__
	.venv/bin/python3 code/RisExUtils.py fetch
	.venv/bin/python3 code/RisExUtils.py render --down --index
	$(MAKE) zip json

check-markup: JSON_SCHEMA ?= docs/lawdoc.json
check-markup:
	.venv/bin/check-jsonschema -v --check-metaschema $(JSON_SCHEMA)
	set -e; for f in files/*.markup.json; do .venv/bin/check-jsonschema -v --schemafile $(JSON_SCHEMA) $$f; done
	grep -h '^ *\[' files/*.markup.json | sed -re 's/^ *//; s/\]*[\}?,].*//; /\["(Part|Item|Meta|Table|TabCell) / s/ .*/ ..."/' | sort | uniq -c

mitmp:
	mitmdump -s code/mitmp.py

webapp:
	.venv/bin/python3 code/RisExUtils.py mkwebapp
	( sleep 1; xdg-open http://0.0.0.0:8000/; ) &
	.venv/bin/python3 code/httpsrv.py

deploy:
	.venv/bin/python3 code/RisExUtils.py mkwebapp
	[ -d __ghpages__ ] || git clone -b gh-pages git@github.com:clairexen/LawAT.git __ghpages__
	-cd __ghpages__ && git rm -rf .
	cp -vt __ghpages__/ LawAT_DataSet.json LawAT_DataSet.zip lawdoc.json
	cp -vt __ghpages__/ code/RisEnQuery.py code/risen.js
	cp -vt __ghpages__/ code/index.html code/style.css
	cp -vt __ghpages__/ code/lawdoc.js code/lawdoc.css
	cp -vt __ghpages__/ code/tocui.js code/tocui.css
	cp -vt __ghpages__/ code/logo.png code/favicon.ico
	cd __ghpages__ && git add . && git commit -m deploy && git push

purge:
	rm -rf .venv __pycache__/ __ghpages__/ __rismarkup__/ __webcache__/
	rm -rf code/__pycache__/ LawAT_DataSet.json LawAT_DataSet.zip lawdoc.json

.PHONY: help venv zip json update check-markup mitmp webapp deploy purge
