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
	rm -vf RisExMarkup.zip RisExBigDocs.zip RisExFiles.zip
	zip -vXj RisExBigDocs.zip -r files index.json -i index.json "*.big.md"
	zip -vXj RisExMarkup.zip  -r files index.json -i index.json "*.ris.json"
	zip -vXj RisExFiles.zip   -r files index.json -x "*.ris.json" "*.big.md"

json: RisExData.json
RisExData.json: venv index.json files/*
	./RisExUtils.py mkjson

define fetch_body
files/$N.md: venv RisExUtils.py index.json
	./RisExUtils.py fetch $N
	./RisExUtils.py render --down $N

endef

NORM_LIST := $(shell jq -r 'keys[]' index.json)
update: $(foreach N,$(NORM_LIST),files/$N.md)
$(eval $(foreach N,$(NORM_LIST),$(fetch_body)))

purge:
	rm -rf .venv RisExData.json __pycache__/ __rishtml__/
	rm -rf RisExMarkup.zip RisExBigDocs.zip RisExFiles.zip

.PHONY: query help shell intro venv zip json update purge
