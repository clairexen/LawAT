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
	@echo "  make zip ......... (re-)create RisExFiles.zip"
	@echo "  make json ........ (re-)create RisExData.json"
	@echo "  make purge ....... remove .venv and RisExFiles.zip"
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
.venv/bin/activate: # mkvenv.sh
	bash mkvenv.sh

zip: RisExFiles.zip
RisExFiles.zip: index.json files/*
	rm -vf RisExFiles.zip
	zip -vXj RisExFiles.zip -r files index.json

json: RisExData.json
RisExData.json: venv index.json files/*
	.venv/bin/python3 mkjson.py

define fetch_body
files/$N.toc.md: venv index.json
	./fetch.py $N

endef

NORM_LIST := $(shell jq -r 'keys[]' index.json)
fetch: $(foreach N,$(NORM_LIST),files/$N.toc.md)
$(eval $(foreach N,$(NORM_LIST),$(fetch_body)))

purge:
	rm -rf .venv RisExFiles.zip RisExData.json

.PHONY: query help shell intro venv zip json fetch purge
