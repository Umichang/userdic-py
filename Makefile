ifeq ($(OS),Windows_NT)
PREFIX ?= $(LOCALAPPDATA)/userdic-py
PYTHON ?= py -3
WINDOWS_PYTHON ?= py -3
else
PREFIX ?= /usr/local
PYTHON ?= python3
WINDOWS_PYTHON ?= python
endif

BINDIR ?= $(PREFIX)/bin
LIBDIR ?= $(PREFIX)/lib/userdic-py

.PHONY: install uninstall

install:
	$(PYTHON) scripts/make_install.py --bindir "$(BINDIR)" --libdir "$(LIBDIR)" --windows-python-launcher "$(WINDOWS_PYTHON)"

uninstall:
	$(PYTHON) scripts/make_uninstall.py --bindir "$(BINDIR)" --libdir "$(LIBDIR)"
