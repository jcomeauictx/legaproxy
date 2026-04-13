# allow Bashisms
SHELL := /bin/bash
# keep track of dependencies
INSTALLED := $(CURDIR)/.installed
# make sure we can find executables installed in $HOME/*/bin
PATH := $(PATH):$(HOME)/.local/bin:$(HOME)/.cargo/bin:.
WHICH := command -v
# no need for `apt` in this list, any that have `apt` also have `apt-get`,
# and the latter covers far more systems.
INSTALLER := $(notdir $(word 1, $(shell $(WHICH) apk apt-get yum dnf)))
ifeq ($(INSTALLER),apk)
INSTALL := sudo $(INSTALLER) add
else
INSTALL := sudo $(INSTALLER) install -y
endif
# python3 preferred, but you can attempt to run it under python2:
# `make PYTHON=python2`
# NOTE: now that we're using $(PYTHON) as part of a path ($(INSTALLED...)
# we're only using the name, not the full path. so if you're using a custom
# python under /usr/local/bin or wherever, you also have to set PATH.
PYTHON ?= $(notdir $(word 1, $(shell $(WHICH) python3 python python2)))
ifeq ($(PYTHON),)
$(shell $(INSTALL) python3)
PYTHON := python3
endif
PY_VER := $(shell $(PYTHON) -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
PYLINT ?= $(word 1, $(shell $(WHICH) pylint3 pylint true 2>/dev/null))
ifeq ($(PYLINT),true)
$(warning ***NOTE*** no pylint installed, scripts unlinted)
endif
PY := $(notdir $(PYTHON:.exe=))
PIP = $(PYTHON) -m pip
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
HOST ?= 127.0.0.1
DATADIR := $(HOME)/.legaproxy/chrome
# limit `make log` to this many entries
LOGLIMIT ?= 10000
CACHE := $(DATADIR)/Cache "$(DATADIR)/Code Cache"
BRANCH := $(shell git branch --show-current)
REMOTES := $(filter-out original, $(shell git remote))
SSHPORT ?= 3022
# testing on tk-ish-dev docker image, firefox and w3m are available
# testing on Debian trixie, chromium, firefox, wheezy32firefox, and w3m are.
# on iPhone, only safari and other iOS browsers are likely suitable, even
# with Mocha-X11 installed.
# just set BROWSER if you have a preference, but it either has to
# honor http_proxy and https_proxy, or have options setting up the proxy
# added to this Makefile
CHROME := $(word 1, $(shell $(WHICH) chromium chromium-browser))
$(warning CHROME=$(CHROME))
WHEEZY32FF := $(shell $(WHICH) /opt/wheezy32/usr/lib/iceweasel/iceweasel)
# wheezy32firefox only usable when iceweasel exists
W32FIREFOX := $(word 2, $(WHEEZY32FF) wheezy32firefox)
FIREFOX := $(word 1, $(shell $(WHICH) firefox) $(W32FIREFOX))
BROWSER ?= $(word 1, $(CHROME) $(FIREFOX) $(shell $(WHICH) w3m))
$(warning BROWSER=$(BROWSER))
TESTFILE := sarge/capabilities.html
SSHDCONF := /etc/ssh/sshd_config
SSHDORIG := $(SSHDCONF).orig
USERPUB := $(shell cat $(HOME)/.ssh/id_rsa.pub)
# add UserAgent strings of some legacy devices we want to support
IPHONE6 := Mozilla/5.0 (iPhone; CPU iPhone OS 12_5_7 like Mac OS X)
IPHONE6 += AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2
IPHONE6 += Mobile/15E148
WEBSITE ?= redwoodcu.org
TESTSITE ?= example.com
PYTHON_SCRIPTS := $(wildcard *.py)
# leave HOSTSUFFIX blank to capture everything
HOSTSUFFIX=
INDEXPAGE ?=
LOGGING := &>$(HOME)/$(notdir $(BROWSER)).log &
BROWSE := $(BROWSER)
# don't use `localhost`, many Debian installs have both 127.0.0.1 and ::1
PROXYHOST := 127.0.0.1
PROXYPORT := 8080
PROXY := $(PROXYHOST):$(PROXYPORT)
ifeq ($(BROWSER),$(CHROME))
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
WGET ?= $(PROXY_SETTINGS) wget -q
NSSDB ?= $(HOME)/.pki/nssdb
SQLDB := sql:$(NSSDB)
CERTNICK := mitmproxy
CERTFILE := $(HOME)/.mitmproxy/mitmproxy-ca-cert.pem
# archive for running wheezy32firefox (for testing)
ARCHIVE := https://archive.debian.org/debian
# for fetching sibling repos
GITPREFIX := $(dir $(shell git remote get-url origin))
MITM_OPTIONS := --anticache
ifeq ($(INSTALLER),apk)
MITM_OPTIONS += -a -z -b $(PROXYHOST) -p $(PROXYPORT) -s
MITM_SAVE := -w
# slow startup if running under iSH
SLEEP ?= 10
# old mitmproxy 0.9.x: web app served at http://mitm/ (APP_DOMAIN default)
CERT_APP_URL := http://mitm/
else
MITM_OPTIONS += --anticomp --flow-detail 3 \
 --listen-host $(PROXYHOST) --listen-port $(PROXYPORT) --scripts
MITM_SAVE := --save-stream-file
SLEEP ?= 3
# modern mitmproxy: mitm.it is the magic cert-download domain
CERT_APP_URL := http://mitm.it/
endif
ifneq ($(SHOWENV),)
 export
else  # export what's needed for envsubst and for python scripts
 export HOST SSHPORT PATH SSHDCONF SSHDORIG USER USERPUB
endif
default: debug
retest: clean reinstall test tests.results
make.log: .FORCE
	$(MAKE) timestamp proxy.stop testproxy 2>&1 | tee -a $@
timestamp:
	@echo starting run at $$(date -u) >&2
test: tests.log
$(INSTALLED)/mitmdump: $(INSTALLED)/$(INSTALLER)/mitmdump
	touch $@
$(INSTALLED)/apk/mitmdump: .FORCE | $(INSTALLED)/apk
	$(MAKE) reinstall
	touch $@
$(INSTALLED)/apt-get/mitmdump: | $(INSTALLED)/apt-get
	# on desktop, prefer pip-installed mitmdump over Debian package;
	# as of Trixie, it still attempts to import blinker._saferef,
	# which hasn't existed for years.
	$(PIP_INSTALL) $(MITM_PKG)
	touch $@
# not sure whether setuptools needs to be installed separately any more.
# seems to me if it's needed it will be pullled in by whatever needs it.
# FIXME: if this is made a dependency on anything, flesh out the recipe
# to use distro installer where available
$(INSTALLED)/setuptools: | $(INSTALLED)/pip
	if ! $(PYTHON) -c 'import distutils'; then \
	 $(PIP_INSTALL) $(@F); \
	fi
	touch $@
$(INSTALLED)/pip: $(INSTALLED)/$(PYTHON)/pip
	touch $@
$(INSTALLED)/python2/pip: | get-pip.py $(INSTALLED)/python2
	python2 $|
	touch $@
$(INSTALLED)/python3/pip: | $(INSTALLED)/python3
	$(PIP_GET)
	touch $@
%: %.template Makefile
	envsubst < $< > $@
$(HOME)/%:
	# for making $(INSTALLED) and subdirs
	mkdir --parents $@
stop: smokesignal.stop proxy.stop
async: async.log | $(INSTALLED)/w3m
async.stop:
	$(WGET) -O- http://example.com/mitm/shutdown
# have to fetch certs to create them? seems that way.
# (later) nope, not true, but maybe needs a delay. so this should still help
certs:
	-$(WGET) -O- $(CERT_APP_URL) | \
	 grep --color=always -E 'mitmproxy-ca-cert|$$'
%.grep: | . ../mitmproxy ../netlib ../pathod
	grep -r '$*' $|
%.grepl: | . ../mitmproxy ../netlib ../pathod
	grep -rl '$*' $|
# these two rules only match full words
# e.g. imp.grep will match imp but not import
%.grepw: | . ../mitmproxy ../netlib ../pathod
	grep -r '\<$*\>' $|
%.grepwl: | . ../mitmproxy ../netlib ../pathod
	grep -rl '\<$*\>' $|
# the following is the recipe for async.log and possibly others
%.log: %.py mitm/%.html mitm/pixel.png %.log.rotate .FORCE
	@echo using %.log recipe for async.py and similar scripts >&2
	mitmdump $(MITM_OPTIONS) $< 2>&1 | tee $@ &
	sleep $(SLEEP)  # allow mitmproxy to start up
	rm -rf $(CACHE)  # delete browser cache
	-$(BROWSE) http://example.com/
	read -p "<enter> to terminate..."
	$(MAKE) $*.stop
# the following is the recipe for mitmdump.log, and possibly others
%.log: .FORCE | $(INSTALLED)/%
	@echo using %.log recipe for mitmdump >&2
	pid=$$(cat $*.pid 2>/dev/null); \
	if [ "$$pid" ]; then \
	 echo $* is already running >&2; \
	else \
	 : "creating an empty logfile" > $@; \
	 echo starting up $*; \
	 $* $(MITM_OPTIONS) $(CURDIR)/filter.py \
	  $(MITM_SAVE) mitmproxy.log &>$@ & \
	  echo $$! >$*.pid; \
	 sleep $(SLEEP); \
	fi
testproxy: $(INSTALLED)/mitmdump mitmdump.log certs | $(DATADIR)
	@echo starting testproxy >&2
	rm -rf $(CACHE)  # delete browser cache
	$(BROWSE) https://$(WEBSITE)/$(INDEXPAGE) $(LOGGING)
	read -p "<enter> to terminate..."
	$(MAKE) proxy.stop
proxy.stop:
	-pid=$$(cat mitmdump.pid 2>/dev/null); \
	if [ "$$pid" ]; then \
	 kill $$pid; \
	else \
	 echo Nothing to stop: mitmdump has not been running >&2; \
	fi
	rm -f mitmdump.pid
	@echo rotating mitmdump.log after stopping
	$(MAKE) mitmdump.log.rotate
clean:
	$(MAKE) stop
	rm -rf dummy $(GENERATED) __pycache__
	rm -f make.log
distclean: clean
	if [ -d fontconfig ]; then sudo rm -rf fontconfig; fi
	if [ -d storage ]; then rm -rf storage; fi
	rm -f dummy $(DOWNLOADED)
useragent:
	@echo '$(IPHONE6)'
smokesignal: ../smokesignal $(INSTALLED)/swc proxy.stop mitmdump.log
	-$(MAKE) PORT=8888 -C $< wsgi &
	@echo BROWSER=$(BROWSER)
	@echo attempting $(PROXY_SETTINGS) $(BROWSER) http://localhost:8888/ >&2
	-$(PROXY_SETTINGS) $(BROWSER) http://localhost:8888/
smokesignal.stop:
	-pid=$$(cat smokesignal.pid 2>/dev/null); \
	if [ "$$pid" ]; then kill $$pid; fi
	rm -f smokesignal.pid
localserver: | $(TESTFILE)
	@echo testing $< on local computer
	# don't fail launching browser if server launched previously
	-python3 -m http.server --bind 127.0.0.1 8888 & \
	echo $$! >$*.pid
	@echo waiting a few seconds to launch the browser
	sleep $(SLEEP)
	-$(BROWSER) http://localhost:8888/$| \
	 >/var/tmp/legaproxy.log 2>&1
	-kill $$(cat $*.pid)
	rm -f *.pid
browse:
	$(BROWSE) https://$(TESTSITE)/
env:
ifneq ($(SHOWENV),)
	env
else
	$(MAKE) SHOWENV=1 $@
endif
storagediff:
	for modified in $$(find storage/modified/ -type f); \
	 do original=storage/files/$${modified##storage/modified/}; \
	 colordiff $$original $$modified; \
	done
shell:
	$(PYTHON)
mitm/pixel.png:
	convert -size 1x1 xc:none $@
%.branch: | ../netlib ../mitmproxy ../pathod
	for dir in $|; do \
	 (cd $$dir && git checkout $*); \
	done
	git checkout $*
push: ../netlib ../mitmproxy ../pathod
	-$(foreach remote, $(REMOTES), git push $(remote) $(BRANCH);)
	@for dir in $+; do $(MAKE) -C $$dir $@; done
%.pylint: %.py
	$(PYLINT) $<
pylint: $(PYTHON_SCRIPTS:.py=.pylint)
# the cert needs to be installed before launching chromium (at least)
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
# consider forcing reinstall of executables that may have been removed
$(INSTALLED)/certutil: $(INSTALLED)
	if [ -z "$$($(WHICH) $(@F))" ]; then \
	 $(INSTALL) libnss3-tools; \
	 touch $@; \
	fi
# the cargo installed swc doesn't inline helpers, and alpine/iSH
# can't compile it, so we need to use a remote executable for now.
$(INSTALLED)/swc: $(INSTALLED)/swcserver
	ln -sf $(CURDIR)/remoteswc $(HOME)/.local/bin/$(@F)
	touch $@
# default install is to use apt-get, apk, dnf, etc.
# NOTE: must make explicit $(INSTALLED)/something rules, not a pattern rule,
# or $(HOME)/% directory creation may not work properly.
# THE RULE: shortest stem wins, earliest breaks the tie
#$(INSTALLED)/%: $(INSTALLED)
$(INSTALLED)/cargo: $(INSTALLED)/rustup .FORCE
	# don't bother installing Debian stable cargo, always too old.
	if [ -z "$$($(WHICH) $(@F))" ] || ! $(@F) --version; then \
	 rustup toolchain install stable && \
	 touch $@ ||rm -f $@; \
	fi
# libraries and headers required for pip install
$(INSTALLED)/libffi-dev: $(INSTALLED)
$(INSTALLED)/python3-dev: $(INSTALLED)
$(INSTALLED)/w3m: $(INSTALLED)
	$(INSTALLER) $(INSTALL) $(@F)
	touch $@
$(INSTALLED):
	mkdir -p $@
$(INSTALLED)/debian-release-7.gpg: $(INSTALLED)
	# https://serverfault.com/a/984605/58945
	wget https://ftp-master.debian.org/keys/release-7.asc -qO- | \
	 gpg --import --no-default-keyring --keyring $@
$(INSTALLED)/swcserver: $(INSTALLED)
	if [ -z "$$(getent hosts $(@F))" ]; then \
	 echo alpine/iSH cannot run a suitable version of swc >&2; \
	 echo you must put an entry for $(@F) in /etc/hosts >&2; \
	 false; \
	fi
	touch $@
/opt/wheezy32/usr/bin/iceweasel: \
 | $(INSTALLED)/debian-release-7.gpg $(INSTALLED)/debootstrap
	sudo mkdir -p /opt/wheezy32.tmp
	sudo debootstrap \
	 --arch=i386 \
	 --include=iceweasel,chromium \
	 --keyring=$< \
	 wheezy /opt/wheezy32.tmp $(ARCHIVE)
	sudo mv /opt/wheezy32.tmp /opt/wheezy32
../smokesignal ../swc ../netlib ../mitmproxy ../pathod:
	cd .. && git clone --quiet $(GITPREFIX)$(@F)
	cd $@ && git checkout $(BRANCH) || true  # not all have alpine-ish
swcversion: $(INSTALLED)/swc
	swc --version
tests.log: tests.log.rotate tests.$(PY).log.rotate .FORCE | \
 ../netlib ../mitmproxy
	-for dir in $|; do \
	 $(MAKE) PYTHON=$(PYTHON) -C $$dir tests; done 2>&1 | tee $(CURDIR)/$@
	cp $@ tests.$(PY).log
%.rotate:
	for i in $$(seq 1 9 | tac); do \
	 if [ -e $*.$$i ]; then \
	  mv -f $*.$$i $*.$$((i + 1)); \
	 fi; \
	done
	rm -f $*.??  # get rid of all files 10+
	[ -e "$*" ] && cp -f $* $*.1 || true
log: | ../netlib ../mitmproxy ../pathod
	-for dir in $|; do $(MAKE) LOGLIMIT=$(LOGLIMIT) -C $$dir $@; done
	git $@ | head -n $(LOGLIMIT)
pull status diff commit: | ../netlib ../mitmproxy ../pathod
	-for dir in $|; do $(MAKE) -C $$dir $@; done
	if [ "$@" != "commit" ]; then \
	 git $@; \
	else \
	 git $@ -a; \
	fi
%.diff: | ../netlib ../mitmproxy ../pathod
	for dir in $|; do $(MAKE) -C $$dir $@; done
tests.%.diff: | tests.log.%
	diff -y <(grep -v '^DEBUG:' tests.log) <(grep -v '^DEBUG:' $|) | less
rebuild reinstall: | $(wildcard ../netlib ../mitmproxy ../pathod)
	@for dir in $|; do $(MAKE) -C $$dir $(patsubst re%,%,$@); done
debug: clean reinstall make.log
	#-tail -n 30 mitmdump.log
%.results:
	egrep '^(Ran|FAILED) ' $*.log
results: tests.results
%.pem: %
	openssl x509 -in $< -inform der -out $@ -outform pem
%.text: %
	openssl x509 -in $< -inform der -noout -text || \
	 openssl x509 -in $< -inform pem --noout -text
%.der: %.pem
	openssl x509 -in $< -inform pem -out $@ -outform der
.FORCE:
.PRECIOUS: %.log tests.log
