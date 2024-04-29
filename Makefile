# allow Bashisms
SHELL := /bin/bash
HOST ?= 127.0.0.1
# wanted to change PORT to 3080, but found out it's hardcoded throughout
# the directory structure. Ain't worth it.
PORT ?= 3000
SSHPORT ?= 3022
BROWSER ?= $(shell which firefox open 2>/dev/null | head -n 1)
APPNAME := getting-started
SSHDCONF := /etc/ssh/sshd_config
SSHDORIG := $(SSHDCONF).orig
USERPUB := $(shell cat $(HOME)/.ssh/id_rsa.pub)
PIDFILE := /var/run/legaproxy.pid
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
 BROWSE += --proxy-server=$(PROXY)  # add proxy to browser commandline
endif
# proxy envvars lowercase, for testing with wget
https_proxy=http://$(PROXY)
http_proxy=http://$(PROXY)
ifneq ($(SHOWENV),)
 export
else
 export HOST PORT SSHPORT
endif
all: proxy
test: bind-run view
$(APPNAME): Dockerfile Makefile
	docker build -t $@ $(<D)
	touch $@
%: %.template
	envsubst < $< > $@
run: $(APPNAME)
	docker run \
	 --detach \
	 --publish $(HOST):$(PORT):$(PORT) $< > $<
bind-run: $(APPNAME)
	docker run \
	 --detach \
	 --publish $(HOST):$(PORT):$(PORT) \
	 --publish $(HOST):$(SSHPORT):$(SSHPORT) \
	 --workdir /app \
	 --mount type=bind,src="$(PWD)",target=/app \
	 node:18-alpine \
	 sh -c "apk add openssh && \
	  mv $(SSHDCONF) $(SSHDORIG) && \
	  sed 's/.*Port 22$$/Port $(SSHPORT)/' $(SSHDORIG) > $(SSHDCONF) && \
	  cat $(SSHDCONF) && \
	  ssh-keygen -A && \
	  /usr/sbin/sshd && \
	  mkdir -p /root/.ssh && \
	  echo $(USERPUB) >> /root/.ssh/authorized_keys && \
	  chmod 0700 /root/.ssh && \
	  chmod 0600 /root/.ssh/authorized_keys && \
	  yarn install && \
	  yarn run dev" \
	 > $<
	while read line; do \
	 echo $$line; \
	 if [ "$$line" = "Listening on port $(PORT)" ]; then break; fi \
	done \
	 < <(docker logs --follow $$(<$<))
view:
	$(BROWSER) $(HOST):$(PORT)/
connect attach ssh login:
	ssh -p $(SSHPORT) root@localhost
stop:
	if [ -s "$(APPNAME)" ]; then \
	 docker stop $$(<$(APPNAME)); \
	 docker wait $$(<$(APPNAME)); \
	fi
$(PIDFILE):
	@sudo echo sudo now enabled for '`sudo tee`' below >&2
	mitmdump --anticache \
	 --anticomp \
	 --listen-host $(PROXYHOST) \
	 --listen-port $(PROXYPORT) \
	 --allow-hosts 'redwoodcu\.org$$' \
	 --scripts filter.py \
	 --flow-detail 3 \
	 --save-stream-file mitmproxy.log &>mitmdump.log & \
	 echo $$! | sudo tee $@
proxy: $(PIDFILE)
	$(BROWSE) https://$(WEBSITE)/$(INDEXPAGE) $(LOGGING)
proxy.stop:
	if [ -f "$(PIDFILE)" ]; then \
	 sudo kill -s KILL $$(<$(PIDFILE)); \
	  sudo rm -f $(PIDFILE); \
	else \
	 echo Nothing to stop: mitmdump has not been running >&2; \
	fi
purge:  # stop with no opportunity to restart
	-$(MAKE) stop
	# truncate file containing the stopped container ID
	# same as :>$(APPNAME)
	>$(APPNAME)
clean:
	$(MAKE) stop
	if [ -s "$(APPNAME)" ]; then docker rm $$(<$(APPNAME)); fi
	if [ -f "$(APPNAME)" ]; then docker rmi $(APPNAME); fi
	rm -f $(APPNAME)
distclean: clean
	rm -f Dockerfile
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
