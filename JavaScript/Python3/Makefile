# allow Bashisms
SHELL := /bin/bash
# prefer /usr/bin over /usr/local/bin, especially for python3
PATH := /usr/bin:$(PATH)
TESTFILE := ../../sarge/capabilities.html
# leave HOSTSUFFIX blank to capture everything
HOSTSUFFIX=
INDEXPAGE ?=
# make sure browser isn't blank in case of no chromium
ifeq ($(CHROME)$(MITMBROWSER),)
 MITMBROWSER := w3m
else
 MITMBROWSER ?= $(CHROME)
endif
LOGGING := &>$(HOME)/$(notdir $(word 1, $(MITMBROWSER))).log &
BROWSE := $(MITMBROWSER)
# copied from python-antlr-example Makefile
GRAMMARS := https://raw.githubusercontent.com/antlr/grammars-v4/master
JAVASCRIPT := JavaScript
CPP := Cpp
PYTHON3 := Python3
PYLINT ?= $(shell which pylint pylint3 2>/dev/null | head -n 1)
PYTHONPATH ?= $(PWD)
PARSER ?= JAVASCRIPT
TARGET ?= PYTHON3
JAVASCRIPTGRAMMAR := $(GRAMMARS)/javascript/javascript
GRAMMAR := $($(PARSER)GRAMMAR)
BASE := $(GRAMMAR)/$($(TARGET))
EXAMPLES = $(GRAMMAR)/examples
JAVASCRIPTG4FILES := $(JAVASCRIPT)Parser.g4 $(JAVASCRIPT)Lexer.g4
G4FILES := $($(PARSER)G4FILES)
G4FILE := $(word 1, $(G4FILES))
PARSERS := $($(PARSER))Parser.py $($(PARSER))Lexer.py
HEADERS := $($(PARSER))Parser.h $($(PARSER))Lexer.h
CXXFLAGS += -I/usr/include/antlr4-runtime
PARSE := $(word 1, $(PARSERS))
LISTENER := $(G4FILE:.g4=Listener.py)
JAVASCRIPTEXAMPLES := ArrowFunctions.js Constants.js LetAndAsync.js
JAVASCRIPTEXAMPLE ?= $(word 1, $(JAVASCRIPTEXAMPLES))
EXAMPLE := $($(PARSER)EXAMPLE)
JAVASCRIPTBASEFILES := $(G4FILES:.g4=Base.py)
BASEFILES := $($(PARSER)BASEFILES)
DOWNLOADED = $(BASEFILES) $(JAVASCRIPTEXAMPLE)
DOWNLOADED += *Parser.g4 *Lexer.g4
GENERATED = *Parser.py *Lexer.py
GENERATED += *Listener.py *.interp *.tokens __pycache__
FIXUP ?= arrow,var
ifneq ($(SHOWENV),)
 export
else
 export FIXUP
endif
all: test
test: run
run: jsfix.py | $(APPNAME) $(PARSERS)
	cat $(TESTFILE) | \
	 sed -n 's/ *[<]td class="test"[>]//p' | \
	 sed -e 's/[<].*[>]//' -e 's/&gt;/>/' | \
	 ./$<
rerun:
	$(MAKE) retouch
	$(MAKE) run
clean:
	rm -rf dummy $(GENERATED)
distclean: clean
	rm -f dummy $(DOWNLOADED)
localserver: | $(TESTFILE)
	@echo testing $< on local computer
	# don't fail launching browser if server launched previously
	-python3 -m http.server --bind 127.0.0.1 8888 &
	@echo waiting a few seconds to launch the browser
	sleep 5 && $(BROWSER) http://localhost:8888/$|
# copied from python-antlr-example project Makefile
$(G4FILES):
	wget -O- $(GRAMMAR)/$@ | sed -e 's/\<this[.]/self./g' \
	 -e s'/!self[.]/not self./g' > $@
$(EXAMPLE):
	if [ "$(PARSER)" = "JAVASCRIPT" ]; then \
	 wget $(EXAMPLES)/$@; \
	fi
$(BASEFILES):
	if [ "$(PARSER)" = "JAVASCRIPT" ]; then \
	 wget $(BASE)/$@; \
	fi
env:
ifneq ($(SHOWENV),)
	env
else
	$(MAKE) SHOWENV=1 $@
endif
$(PARSERS): $(G4FILES) | $(BASEFILES)
	antlr4 -Dlanguage=$($(TARGET)) $+
$(HEADERS): $(G4FILES) | $(BASEFILES)
	antlr4 -Dlanguage=Cpp $+
cpp: $(HEADERS)
	$(MAKE) parse
	./parse pathological.js
%.pylint: %.py
	$(PYLINT) $<
