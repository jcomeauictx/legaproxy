# allow Bashisms
SHELL := /bin/bash
# prefer pip-installed mitmdump over Debian package
# as of Trixie, it still attempts to import blinker._saferef, which hasn't
# existed for years.
PATH := $(HOME)/.local/bin:$(PATH)
HOST ?= 127.0.0.1
DATADIR := $(HOME)/.legaproxy/chrome
CACHE := $(DATADIR)/Cache "$(DATADIR)/Code Cache"
BRANCH := $(shell git branch --show-current)
REMOTES := $(filter-out original, $(shell git remote))
SSHPORT ?= 3022
BROWSER ?= $(word 1, $(shell which firefox w3m open false))
MITMDUMP = $(word 1, $(shell which mitmdump false))
PYTHON ?= $(word 1, $(shell which python3 false))
PYLINT ?= $(word 1, $(shell which pylint3 pylint true))
APPNAME ?= npx
TESTFILE := sarge/capabilities.html
DOCKERRUN ?= docker run --interactive --rm
SSHDCONF := /etc/ssh/sshd_config
SSHDORIG := $(SSHDCONF).orig
USERPUB := $(shell cat $(HOME)/.ssh/id_rsa.pub)
# add UserAgent strings of some legacy devices we want to support
IPHONE6 := Mozilla/5.0 (iPhone; CPU iPhone OS 12_5_7 like Mac OS X)
IPHONE6 += AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2
IPHONE6 += Mobile/15E148
CHROME := $(shell which chromium chromium-browser 2>/dev/null | head -n 1)
WEBSITE ?= redwoodcu.org
PYTHON_SCRIPTS := $(wildcard *.py)
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
#BROWSE += --temp-profile  # forces new chromium instance, disables cache
# however, --temp-profile also presumably forgets the MITM cert between runs
# --disable-cache, suggested by claude.ai, has no discernable effect
# (added `rm -rf $(CACHE)` to relevant recipes instead)
#BROWSE += --disable-cache
 BROWSE += --user-data-dir=$(DATADIR)
 BROWSE += --proxy-server=$(PROXY)  # add proxy to browser commandline
endif
# proxy envvars lowercase, for testing with wget
https_proxy=http://$(PROXY)
http_proxy=http://$(PROXY)
# copied from python-antlr-example Makefile
GRAMMARS := https://raw.githubusercontent.com/antlr/grammars-v4/master
JAVASCRIPT := JavaScript
CPP := Cpp
PYTHON3 := Python3
PARSER ?= JAVASCRIPT
TARGET ?= PYTHON3
PYTHONPATH += $(PWD)/$($(PARSER))/$($(TARGET))
FIXUP ?= arrow,var
CARGO := $(word 1, $(shell which cargo false))
SWC := $(word 1, $(shell which swc false))
ifneq ($(SHOWENV),)
 export
else  # export what's needed for envsubst and for python scripts
 export HOST SSHPORT PATH SSHDCONF SSHDORIG USER USERPUB FIXUP PYTHONPATH \
        https_proxy http_proxy
endif
all: proxy
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
$(HOME)/%:
	mkdir --parents $@
run:
	$(MAKE) -C $(PYTHONPATH)
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
	pip3 install --user -U mitmproxy || \
	 pip3 install --user -U --break-system-packages mitmproxy
async: async.log
async.stop:
	wget --verbose --output-document=- http://example.com/mitm/shutdown
%.log: %.py mitm/%.html mitm/pixel.png .FORCE | $(dir $(MITMDUMP))mitmdump
	$| --anticache \
	 --anticomp \
	 --listen-host $(PROXYHOST) \
	 --listen-port $(PROXYPORT) \
	 --scripts $< \
	 --flow-detail 3 2>&1 | tee $@ &
	sleep 3  # allow mitmproxy to start up
	rm -rf $(CACHE)  # delete browser cache
	$(BROWSE) http://example.com/
	# on closing browser window, the following should run
	$(MAKE) $*.stop
mitmdump.log: | $(dir $(MITMDUMP))mitmdump
	pid=$$(lsof -t -itcp@$(PROXYHOST):$(PROXYPORT) -s tcp:listen); \
	if [ "$$pid" ]; then \
	 echo mitmdump is already running >&2; \
	else \
	 : "creating an empty logfile" > $@; \
	 $| --anticache \
	  --anticomp \
	  --listen-host $(PROXYHOST) \
	  --listen-port $(PROXYPORT) \
	  --scripts filter.py \
	  --flow-detail 3 \
	  --save-stream-file mitmproxy.log &>$@ & \
	fi
proxy: mitmdump.log $(DATADIR)
	rm -rf $(CACHE)  # delete browser cache
	$(BROWSE) https://$(WEBSITE)/$(INDEXPAGE) $(LOGGING)
proxy.stop:
	pid=$$(lsof -t -itcp@$(PROXYHOST):$(PROXYPORT) -s tcp:listen); \
	if [ "$$pid" ]; then \
	 kill $$pid; \
	else \
	 echo Nothing to stop: mitmdump has not been running >&2; \
	fi
	mv mitmdump.log /var/tmp/mitmdump.$$(date +%Y%m%d%H%M%S).log
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
env:
ifneq ($(SHOWENV),)
	env
else
	$(MAKE) SHOWENV=1 $@
endif
diff:
	for modified in $$(find storage/modified/ -type f); \
	 do original=storage/files/$${modified##storage/modified/}; \
	 colordiff $$original $$modified; \
	done
swc.is_installed:
	if [ "$(notdir $(SWC))" = "false" ]; then \
	 echo 'Must install swc: `cargo install swc_cli`' >&2; \
	 echo 'Then add $(HOME)/.cargo/bin to your PATH' >&2; \
	fi
cargo.is_installed:
	if [ "(notdir $(CARGO))" = "false" ]; then \
	 echo 'Must install cargo: e.g. `sudo apt install rustup`' >&2; \
	 echo 'Then `rustup toolchain install stable` >&2; \
	fi
shell:
	$(PYTHON)
%.es5.js %.es3.js: %.js swc.is_installed
	$(SWC) compile \
	 --config-file $(patsubst .%,%,$(suffix $(basename $@))).swcrc \
	 --out-file $@ \
	 $<
mitm/pixel.png:
	convert -size 1x1 xc:none $@
push:
	-$(foreach remote, $(REMOTES), git push $(remote) $(BRANCH);)
%.pylint: %.py
	$(PYLINT) $<
pylint: $(PYTHON_SCRIPTS:.py=.pylint)
.FORCE:
.PRECIOUS: %.log
