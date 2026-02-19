PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
PREFIX ?= /usr/local

.PHONY: install uninstall

install:
	$(PIP) install . --prefix $(PREFIX) --no-build-isolation

uninstall:
	$(PIP) uninstall -y userdic-py
