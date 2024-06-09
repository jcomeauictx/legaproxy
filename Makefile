# allow Bashisms
SHELL := /bin/bash
# prefer /usr/bin over /usr/local/bin, especially for python3
PATH := /usr/bin:$(PATH)
HOST ?= 127.0.0.1
SSHPORT ?= 3022
BROWSER ?= $(shell which firefox open 2>/dev/null | head -n 1)
MITMDUMP = $(shell which mitmdump 2>/dev/null | head -n 1)
PYTHON ?= $(shell which python3 2>/dev/null | head -n 1)
APPNAME ?= npx
TESTFILE := sarge/capabilities.html
DOCKERRUN ?= docker run --interactive --rm
SSHDCONF := /etc/ssh/sshd_config
SSHDORIG := $(SSHDCONF).orig
USERPUB := $(shell cat $(HOME)/.ssh/id_rsa.pub)
PIDFILE := legaproxy.pid
# add UserAgent strings of some legacy devices we want to support
IPHONE6 := Mozilla/5.0 (iPhone; CPU iPhone OS 12_5_7 like Mac OS X)
IPHONE6 += AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2
IPHONE6 += Mobile/15E148
CHROME := $(shell which chromium chromium-browser 2>/dev/null | head -n 1)
WEBSITE ?= redwoodcu.org
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
# don't use `localhost`, many Debian installs have both 127.0.0.1 and ::1
PROXYHOST := 127.0.0.1
PROXYPORT := 8080
PROXY := $(PROXYHOST):$(PROXYPORT)
ifeq ($(MITMBROWSER),$(CHROME))
 BROWSE += --temp-profile  # forces new chromium instance
 BROWSE += --proxy-server=$(PROXY)  # add proxy to browser commandline
endif
# proxy envvars lowercase, for testing with wget
https_proxy=http://$(PROXY)
http_proxy=http://$(PROXY)
# copied from python-antlr-example Makefile
GRAMMARS := https://raw.githubusercontent.com/antlr/grammars-v4/master
JAVASCRIPT := JavaScript
PARSER ?= JAVASCRIPT
TARGET ?= Python3
JAVASCRIPTGRAMMAR := $(GRAMMARS)/javascript/javascript
GRAMMAR := $($(PARSER)GRAMMAR)
BASE := $(GRAMMAR)/$(TARGET)
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
 export HOST SSHPORT PATH SSHDCONF SSHDORIG USER USERPUB FIXUP
endif
all: test
test: run
$(APPNAME): | Dockerfile
	if [ -f "$@" ]; then \
	 echo $@ already exists >&2; \
	 echo 'Maybe you want to `make distclean` first?' >&2; \
	 false; \
	fi
	docker build -t $@ .
	touch $@
retouch:
	touch Dockerfile $(APPNAME)
%: %.template Makefile
	envsubst < $< > $@
run: jsfix.py | $(APPNAME) $(PARSERS)
	cat $(TESTFILE) | \
	 sed -n 's/ *[<]td class="test"[>]//p' | \
	 sed -e 's/[<].*[>]//' -e 's/&gt;/>/' | \
	 ./$<
check:  # run on container itself
	$(MAKE) DOCKERRUN= run
rerun:
	$(MAKE) retouch
	$(MAKE) run
bind-run: | $(APPNAME)
	docker run \
	 --detach \
	 --publish $(HOST):$(SSHPORT):$(SSHPORT) \
	 --mount type=bind,src="$(PWD)",target=/app_src \
	 --entrypoint /usr/sbin/sshd $| -D >> $|
bind-rerun:
	$(MAKE) retouch
	$(MAKE) bind-run
reconnect reattach:
	$(MAKE) retouch
	$(MAKE) connect
connect attach: | $(APPNAME)
	if [ -s "$|" ]; then \
	 docker exec --interactive --tty $$(tail -n 1 $|) /bin/sh; \
	else \
	 echo 'No active containers; `make bind-run` first.' >&2; \
	fi
ssh login: $(APPNAME)
	ssh -p $(SSHPORT) \
	 -oStrictHostKeyChecking=no \
	 -oUserKnownHostsFile=/dev/null \
	 root@localhost
stop:
	-if [ -s "$(APPNAME)" ]; then \
	  for container in $$(<$(APPNAME)); do \
	   docker stop $$container; \
	   docker wait $$container; \
	 done; \
	fi
$(dir $(MITMDUMP))mitmdump:
	@echo mitmdump not found, installing it now... >&2
	pip3 install mitmproxy || \
	 pip3 install --break-system-packages mitmproxy
$(PIDFILE): $(dir $(MITMDUMP))mitmdump
	$< --anticache \
	 --anticomp \
	 --listen-host $(PROXYHOST) \
	 --listen-port $(PROXYPORT) \
	 --scripts filter.py \
	 --flow-detail 3 \
	 --save-stream-file mitmproxy.log &>mitmdump.log & \
	 echo $$! | tee $@  # doesn't necessarily store correct PID
proxy: $(PIDFILE)
	$(BROWSE) https://$(WEBSITE)/$(INDEXPAGE) $(LOGGING)
proxy.stop:
	-if [ -f "$(PIDFILE)" ]; then \
	 kill $$(lsof -t -itcp@$(PROXYHOST):$(PROXYPORT) \
	  -s tcp:listen); \
	else \
	 echo Nothing to stop: mitmdump has not been running >&2; \
	fi
	-rm -f $(PIDFILE)
clean:
	$(MAKE) stop
	-for container in $$(<$(APPNAME)); do docker rm $$container; done
	rm -rf dummy $(GENERATED) __pycache__
distclean: clean
	-if [ -f "$(APPNAME)" ]; then docker rmi $(APPNAME); fi
	rm -f $(APPNAME)
	rm -f Dockerfile
	if [ -d node_modules ]; then sudo rm -rf node_modules; fi
	if [ -d fontconfig ]; then sudo rm -rf fontconfig; fi
	if [ -d storage ]; then rm -rf storage; fi
	rm -f dummy $(DOWNLOADED)
useragent:
	@echo '$(IPHONE6)'
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
	antlr4 -Dlanguage=$(TARGET) $+
$(HEADERS): $(G4FILES) | $(BASEFILES)
	antlr4 -Dlanguage=Cpp $+
cpp: $(HEADERS)
	$(MAKE) parse
diff:
	for modified in $$(find storage/modified/ -type f); \
	 do original=storage/files/$${modified##storage/modified/}; \
	 colordiff $$original $$modified; \
	done
