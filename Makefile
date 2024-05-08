# allow Bashisms
SHELL := /bin/bash
# prefer /usr/bin over /usr/local/bin, especially for python3
PATH := /usr/bin:$(PATH)
HOST ?= 127.0.0.1
# wanted to change PORT to 3080, but found out it's hardcoded throughout
# the directory structure. Ain't worth it.
PORT ?= 3000
SSHPORT ?= 3022
BROWSER ?= $(shell which firefox open 2>/dev/null | head -n 1)
MITMDUMP = $(shell which mitmdump 2>/dev/null | head -n 1)
PYTHON ?= $(shell which python3 2>/dev/null | head -n 1)
APPNAME := getting-started
SSHDCONF := /etc/ssh/sshd_config
SSHDORIG := $(SSHDCONF).orig
USERPUB := $(shell cat $(HOME)/.ssh/id_rsa.pub)
PIDFILE := legaproxy.pid
# add UserAgent strings of some legacy devices we want to support
IPHONE6 := Mozilla/5.0 (iPhone; CPU iPhone OS 12_5_7 like Mac OS X)
IPHONE6 += AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2
IPHONE6 += Mobile/15E148
CHROME := $(shell which chromium chromium-browser 2>/dev/null | head -n 1)
WEBSITE ?= digital.redwoodcu.org
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
ifneq ($(SHOWENV),)
 export
else
 export HOST PORT SSHPORT PATH SSHDCONF SSHDORIG USER USERPUB
endif
all: test
test: bind-run view
$(APPNAME): Dockerfile Makefile
	if [ -f "$@" ]; then \
	 echo $@ already exists >&2; \
	 echo 'Maybe you want to `make distclean` first?' >&2; \
	 false; \
	fi
	docker build -t $@ $(<D)
	touch $@
%: %.template Makefile
	envsubst < $< > $@
run: $(APPNAME)
	docker run \
	 --detach \
	 --publish $(HOST):$(PORT):$(PORT) $< > $<
	docker exec $$(<$<) rc-service sshd restart
bind-run: $(APPNAME)
	docker run \
	 --detach \
	 --publish $(HOST):$(PORT):$(PORT) \
	 --publish $(HOST):$(SSHPORT):$(SSHPORT) \
	 --mount type=bind,src="$(PWD)",target=/app_src \
	 $< > $<
	while read line; do \
	 echo $$line; \
	 if [ "$$line" = "Listening on port $(PORT)" ]; then break; fi \
	done \
	 < <(docker logs --follow $$(<$<))
	docker exec $$(<$<) rc-service sshd restart
view:
	$(BROWSER) $(HOST):$(PORT)/
connect attach: $(APPNAME)
	docker exec --interactive --tty $$(<$<) sh
ssh login: $(APPNAME)
	ssh -p $(SSHPORT) \
	 -oStrictHostKeyChecking=no \
	 -oUserKnownHostsFile=/dev/null \
	 root@localhost
stop:
	-if [ -s "$(APPNAME)" ]; then \
	 docker stop $$(<$(APPNAME)); \
	 docker wait $$(<$(APPNAME)); \
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
	 --allow-hosts 'redwoodcu\.org$$' \
	 --scripts filter.py \
	 --flow-detail 3 \
	 --save-stream-file mitmproxy.log &>mitmdump.log & \
	 echo $$! | tee $@
proxy: $(PIDFILE)
	$(BROWSE) https://$(WEBSITE)/$(INDEXPAGE) $(LOGGING)
proxy.stop:
	if [ -f "$(PIDFILE)" ]; then \
	 kill -s KILL $$(<$(PIDFILE)); \
	else \
	 echo Nothing to stop: mitmdump has not been running >&2; \
	fi
	-rm -f $(PIDFILE)
purge:  # stop with no opportunity to restart
	-$(MAKE) stop
	# truncate file containing the stopped container ID
	# same as :>$(APPNAME)
	>$(APPNAME)
clean:
	$(MAKE) stop
	-if [ -s "$(APPNAME)" ]; then docker rm $$(<$(APPNAME)); fi
	-if [ -f "$(APPNAME)" ]; then docker rmi $(APPNAME); fi
	rm -f $(APPNAME)
distclean: clean
	-rm -f Dockerfile
	if [ -d node_modules ]; then sudo rm -rf node_modules; fi
	if [ -d fontconfig ]; then sudo rm -rf fontconfig; fi
	if [ -d storage ]; then rm -rf storage; fi
useragent:
	@echo '$(IPHONE6)'
localserver: es5-6.html
	@echo testing $< on local computer
	# don't fail launching browser if server launched previously
	-python3 -m http.server --bind 127.0.0.1 8888 &
	@echo waiting a few seconds to launch the browser
	sleep 5 && $(BROWSER) http://localhost:8888/$<
env:
	if [ -z "$(SHOWENV)" ]; then \
	 $(MAKE) SHOWENV=1 $@; \
	else \
	 env; \
	fi
