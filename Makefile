# allow Bashisms
SHELL := /bin/bash
# keep track of dependencies
INSTALLED := .installed
# make sure we can find executables installed in $HOME/*/bin
# and prefer anything under $(INSTALLED) to those anywhere else
PATH := $(PWD)/$(INSTALLED):$(PATH):$(HOME)/.local/bin:$(HOME)/.cargo/bin:.
WHICH := type -p
INSTALLER := $(notdir $(word 1, $(shell $(WHICH) apk apt apt-get yum dnf \
 2>/dev/null)))
ifeq ($(INSTALLER),apk)
INSTALL := sudo $(INSTALLER) add
else
INSTALL := sudo $(INSTALLER) install -y
endif
PYTHON ?= $(word 1, $(shell $(WHICH) python3 python 2>/dev/null))
ifeq ($(PYTHON),)
	$(INSTALL) python3
PYTHON ?= $(word 1, $(shell $(WHICH) python3 python 2>/dev/null))
endif
PYLINT ?= $(word 1, $(shell $(WHICH) pylint3 pylint true 2>/dev/null))
ifeq ($(PYLINT),true)
	$(warning ***NOTE*** no pylint installed, scripts unlinted)
endif
PIP = $(word 1, $(shell $(WHICH) pip3 pip 2>/dev/null))
PIP_GET := $(INSTALL) python3-pip
ifeq ($(INSTALLER),apk)
PIP_GET := $(INSTALL) py3-pip
# assume apk means iSH, alpine 3.14.3, with Python3.9.16
MITM_PKG := git+https://github.com/jcomeauictx/mitmproxy@alpine-ish
else
MITM_PKG := mitmproxy
endif
PIP_INSTALL = $(PIP) install --verbose --user --upgrade --exists-action i
# on non-iSH (non-alpine) systems, use --break-system-packages
ifneq ($(INSTALLER),apk)
PIP_INSTALL += --break-system-packages
endif
PATH := $(HOME)/.local/bin:$(PATH)
HOST ?= 127.0.0.1
DATADIR := $(HOME)/.legaproxy/chrome
CACHE := $(DATADIR)/Cache "$(DATADIR)/Code Cache"
BRANCH := $(shell git branch --show-current)
REMOTES := $(filter-out original, $(shell git remote))
SSHPORT ?= 3022
BROWSER ?= $(word 1, $(shell which wheezy32firefox w3m))
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
# WARNING: setting these at install time breaks pip! set them when needed!
#https_proxy=http://$(PROXY)
#http_proxy=http://$(PROXY)
# copied from python-antlr-example Makefile
PROXY_SETTINGS := https_proxy=http://$(PROXY) http_proxy=http://$(PROXY)
WGET ?= $(PROXY_SETTINGS) wget
GRAMMARS := https://raw.githubusercontent.com/antlr/grammars-v4/master
JAVASCRIPT := JavaScript
CPP := Cpp
PYTHON3 := Python3
PARSER ?= JAVASCRIPT
TARGET ?= PYTHON3
PYTHONPATH += $(PWD)/$($(PARSER))/$($(TARGET))
NSSDB ?= $(HOME)/.pki/nssdb
SQLDB := sql:$(NSSDB)
CERTNICK := mitmproxy
CERTFILE := $(HOME)/.mitmproxy/mitmproxy-ca-cert.pem
FIXUP ?= arrow,var
# archive for running wheezy32firefox (for testing)
ARCHIVE := https://archive.debian.org/debian
# for fetching sibling repos
GITPREFIX := $(dir $(shell git remote get-url origin))
ifneq ($(SHOWENV),)
 export
else  # export what's needed for envsubst and for python scripts
 export HOST SSHPORT PATH SSHDCONF SSHDORIG USER USERPUB FIXUP PYTHONPATH
endif
default: make.log
make.log: Makefile
	$(MAKE) timestamp proxy.stop testproxy 2>&1 | tee -a $@
timestamp:
	@echo starting run at $$(date -u) >&2
test: run
# prefer pip-installed mitmdump over Debian package
# as of Trixie, it still attempts to import blinker._saferef, which hasn't
# existed for years.
$(INSTALLED)/mitmdump: $(INSTALLED)/setuptools $(INSTALLED)/swc .FORCE
	if [ -z "$$($(WHICH) $(@F))" ]; then \
	 $(PIP_INSTALL) $(MITM_PKG); \
	fi
	touch $@
$(INSTALLED)/setuptools: $(INSTALLED)/pip .FORCE
	if ! $(PYTHON) -c 'import distutils'; then \
	 $(PIP_INSTALL) $(@F); \
	fi
	touch $@
$(INSTALLED)/pip: $(INSTALLED) .FORCE
	if [ -z "$$($(WHICH) $(@F))" ]; then \
	 $(PIP_GET); \
	fi
	touch $@
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
stop: smokesignal.stop proxy.stop
	-if [ -s "$(APPNAME)" ]; then \
	  for container in $$(<$(APPNAME)); do \
	   docker stop $$container; \
	   docker wait $$container; \
	 done; \
	fi
async: async.log
async.stop:
	$(WGET) --verbose --output-document=- http://example.com/mitm/shutdown
# have to fetch certs to create them? seems that way.
# (later) nope, not true, but maybe needs a delay. so this should still help
certs:
	$(WGET) -O- http://mitm.it/ | grep mitmproxy-ca-cert
%.log: %.py mitm/%.html mitm/pixel.png .FORCE
	mitmdump --anticache \
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
%.log: | $(INSTALLED)/%
	pid=$$(cat $*.pid 2>/dev/null); \
	if [ "$$pid" ]; then \
	 echo $* is already running >&2; \
	else \
	 : "creating an empty logfile" > $@; \
	 $* --anticache \
	  --anticomp \
	  --listen-host $(PROXYHOST) \
	  --listen-port $(PROXYPORT) \
	  --scripts filter.py \
	  --flow-detail 3 \
	  --save-stream-file mitmproxy.log &>$@ & \
	  echo $$! >$*.pid; \
	 sleep 3; \
	fi
testproxy: mitmdump.log certs $(INSTALLED)/cert \
 $(INSTALLED)/mitmdump | \
 $(DATADIR)
	rm -rf $(CACHE)  # delete browser cache
	$(BROWSE) https://$(WEBSITE)/$(INDEXPAGE) $(LOGGING)
proxy.stop:
	-pid=$$(cat mitmdump.pid 2>/dev/null); \
	if [ "$$pid" ]; then \
	 kill $$pid; \
	else \
	 echo Nothing to stop: mitmdump has not been running >&2; \
	fi
	rm -f mitmdump.pid
	mv mitmdump.log /var/tmp/mitmdump.$$(date +%Y%m%d%H%M%S).log || true
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
smokesignal: ../smokesignal $(INSTALLED)/swc proxy.stop mitmdump.log
	-$(MAKE) PORT=8888 -C $< wsgi &
	-$(PROXY_SETTINGS) $(BROWSER) http://localhost:8888/
smokesignal.stop:
	pid=$$(cat smokesignal.pid 2>/dev/null); \
	-if [ "$$pid" ]; then kill $$pid; fi
	rm -f smokesignal.pid
localserver: | $(TESTFILE)
	@echo testing $< on local computer
	# don't fail launching browser if server launched previously
	-python3 -m http.server --bind 127.0.0.1 8888 &
	echo $$! >$*.pid
	@echo waiting a few seconds to launch the browser
	sleep 3
	-$(BROWSER) http://localhost:8888/$| \
	 >/var/tmp/legaproxy.log 2>&1
	-kill $*.pid
	rm -f *.pid
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
shell:
	$(PYTHON)
%.es5.js %.es3.js: %.js $(INSTALLED)/swc
	swc compile \
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
$(INSTALLED)/cert: $(CERTFILE) $(NSSDB)/cert9.db \
 | $(HOME)/.pki/nssdb/cert9.db $(INSTALLED)/certutil
	if certutil -d $(SQLDB) -L -n "$(CERTNICK)"; then \
	 echo $(CERTNICK) already installed >&2; \
	else \
	 echo installing $<... >&2; \
	 certutil -d $(SQLDB) -A -t "C,," -n "$(CERTNICK)" -a -i $<; \
	 if [ "$$?" = "0" ]; then \
	  touch $@; \
	 else \
	  echo "certutil failed adding $<, status $$?" >&2; \
	 fi; \
	fi
$(NSSDB)/cert9.db:
	mkdir -p $(@D)
	certutil -d $(SQLDB) -N --empty-password
# force reinstall of executables that may have been removed
$(INSTALLED)/certutil: $(INSTALLED) .FORCE
	if [ -z "$$($(WHICH) $(@F))" ]; then \
	 $(INSTALL) libnss3-tools; \
	 touch $@; \
	fi
# the cargo installed swc doesn't inline helpers, we need to build our own
$(INSTALLED)/swc.fetched: $(INSTALLED)/cargo .FORCE
	if [ -z "$$($(WHICH) $(@F:.fetched=))" ]; then \
	 cargo install swc_cli; \
	 touch $@; \
	fi
# my clone of swc
$(INSTALLED)/swc: ../swc | $(INSTALLED)/cargo
	if [ -z "$$($(WHICH) $(@F))" ]; then \
	 (cd $< && cargo build); \
	 ln -sf $$(readlink -f $</target/debug/$(@F)) $@; \
	fi
# default install is to use apt, apk, dnf, etc.
$(INSTALLED)/%: $(INSTALLED) .FORCE
	if [ -z "$$($(WHICH) $(@F))" ]; then \
	 $(INSTALL) $*; \
	 touch $@; \
	fi
$(INSTALLED)/cargo: $(INSTALLED)/rustup .FORCE
	# don't bother installing Debian stable cargo, always too old.
	if [ -z "$$($(WHICH) $(@F))" ] || ! $(@F) --version; then \
	 rustup toolchain install stable; \
	 touch $@; \
	fi
# libraries and headers required for pip install
$(INSTALLED)/libffi-dev: $(INSTALLED)
$(INSTALLED)/python3-dev: $(INSTALLED)
$(INSTALLED):
	mkdir -p $@
$(INSTALLED)/debian-release-7.gpg:
	# https://serverfault.com/a/984605/58945
	wget https://ftp-master.debian.org/keys/release-7.asc -qO- | \
	 gpg --import --no-default-keyring --keyring $@
/opt/wheezy32/usr/bin/iceweasel: \
 | $(INSTALLED)/debian-release-7.gpg $(INSTALLED)/debootstrap
	sudo mkdir -p $@.tmp
	sudo debootstrap \
	 --arch=i386 \
	 --include=iceweasel,chromium \
	 --keyring=$< \
	 wheezy $@.tmp $(ARCHIVE)
	sudo mv $@.tmp $@
../smokesignal ../swc:
	cd .. && git clone --quiet $(GITPREFIX)$(@F)
swcversion: $(INSTALLED)/swc
	swc --version
.FORCE:
.PRECIOUS: %.log
