# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

ifneq ($Q,)
query: venv zip
	.venv/bin/python3 RisExQuery.py $Q
endif

help:
	@echo ""
	@echo "Usage:"
	@echo "  make venv ........ create Python .venv/"
	@echo "  make zip ......... (re-)create RisExFiles.zip"
	@echo "  make purge ....... remove .venv and RisExFiles.zip"
	@echo ""
	@echo "Running a query:"
	@echo "  make Q=\"<RisExQuery.py Args>\""
	@echo ""
	@echo "For example:"
	@echo "  make Q=\"toc Urkunden\""
	@echo ""

venv: .venv/bin/activate
.venv/bin/activate: # mkvenv.sh
	bash mkvenv.sh

zip: RisExFiles.zip
RisExFiles.zip: index.json files/*
	rm -vf RisExFiles.zip
	zip -vXj RisExFiles.zip -r files index.json

purge:
	rm -rf .venv RisExFiles.zip

.PHONY: query help venv zip purge
