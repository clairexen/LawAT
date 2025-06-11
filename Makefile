# RIS Extractor -- Copyright (C) 2025  Claire Xenia Wolf <claire@clairexen.net>
# Shared freely under ISC license (https://en.wikipedia.org/wiki/ISC_license)

help:
	@echo ""
	@echo "Usage:"
	@echo ""
	@echo "  make venv ........ create Python .venv/"
	@echo "  make zip ......... (re-)create RisExFiles.zip"
	@echo "  make purge ....... remove .venv and RisExFiles.zip"
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

.PHONY: help venv zip purge
