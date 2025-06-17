# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

ifneq ($Q,)
query: venv zip
	.venv/bin/python3 RisEnQuery.py $Q
endif

help:
	@echo ""
	@echo "Usage:"
	@echo "  make venv ........ create Python .venv/"
	@echo "  make zip ......... (re-)create RisEx*.zip"
	@echo "  make json ........ (re-)create RisExData.json"
	@echo "  make purge ....... remove these (re-)created output files"
	@echo ""
	@echo "Interactive ptpython shell (with RisEnQuery.py pre-loaded):"
	@echo "  make shell ....... interactive shell"
	@echo "  make intro ....... shell, with intro() message"
	@echo ""
	@echo "Running a query:"
	@echo "  make Q=\"<RisEnQuery.py Args>\""
	@echo ""
	@echo "For example:"
	@echo "  make Q=\"toc Urkunden\""
	@echo ""

shell: venv zip
	.venv/bin/ptpython -i RisEnQuery.py

intro: venv zip
	.venv/bin/ptpython -i RisEnQuery.py intro

venv: .venv/bin/activate
.venv/bin/activate:
	python3 -m venv .venv
	.venv/bin/pip install playwright
	.venv/bin/pip install requests
	.venv/bin/pip install ptpython
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
	./RisExUtils.py fetch
	./RisExUtils.py render --down

lstags:
	grep -h '^ *\[' *.markup.json | sed -e 's/^ *//; s/,.*//; /\["\(Par\|RisDoc\|Item\|Meta\) / d;' | sort | uniq -c

purge:
	rm -rf .venv RisExData.json __pycache__/ __rismarkup__/ __rishtml__/
	rm -rf RisExFiles.zip

.PHONY: query help shell intro venv zip json update lstags purge
