PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin
LIBDIR ?= $(PREFIX)/lib/userdic-py

.PHONY: install uninstall

install:
	install -d $(BINDIR)
	install -d $(LIBDIR)/userdic_py
	for f in userdic_py/*.py; do install -m 644 $$f $(LIBDIR)/userdic_py/; done
	printf '%s\n' '#!/usr/bin/env python3' 'from pathlib import Path' 'import sys' '' 'sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib" / "userdic-py"))' '' 'from userdic_py.converter import run' '' 'if __name__ == "__main__":' '    raise SystemExit(run())' > $(BINDIR)/userdic-py
	chmod 755 $(BINDIR)/userdic-py

uninstall:
	rm -f $(BINDIR)/userdic-py
	rm -rf $(LIBDIR)
