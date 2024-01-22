# allow Bashisms
SHELL := /bin/bash
HOST ?= 127.0.0.1
# wanted to change HTTPPORT to 3080, but found out it's hardcoded throughout
# the directory structure. Ain't worth it.
HTTPPORT ?= 3000
SSHPORT ?= 3022
BROWSER ?= firefox
APPNAME := getting-started
SSHDCONF := /etc/ssh/sshd_config
SSHDORIG := $(SSHDCONF).orig
export HOST HTTPPORT SSHPORT
all: bind-run view
$(APPNAME): Dockerfile Makefile
	docker build -t $@ $(<D)
	touch $@
%: %.template
	envsubst < $< > $@
run: $(APPNAME)
	docker run \
	 --detach \
	 --publish $(HOST):$(HTTPPORT):$(HTTPPORT) $< > $<
bind-run: $(APPNAME)
	docker run \
	 --detach \
	 --publish $(HOST):$(HTTPPORT):$(HTTPPORT) \
	 --publish $(HOST):$(SSHPORT):$(SSHPORT) \
	 --workdir /app \
	 --mount type=bind,src="$(PWD)",target=/app \
	 node:18-alpine \
	 sh -c "apk add openrc openssh && \
	  rc-update add sshd && \
	  mv $(SSHDCONF) $(SSHDORIG) && \
	  sed 's/.*Port 22$$/Port $(SSHPORT)/' $(SSHDORIG) > $(SSHDCONF) && \
	  cat $(SSHDCONF) && \
	  echo service sshd start && \
	  yarn install && \
	  yarn run dev" \
	 > $<
	while read line; do \
	 echo $$line; \
	 if [ "$$line" = "Listening on port $(HTTPPORT)" ]; then break; fi \
	done \
	 < <(docker logs --follow $$(<$<))
view:
	$(BROWSER) $(HOST):$(HTTPPORT)/
stop:
	if [ -s "$(APPNAME)" ]; then \
	 docker stop $$(<$(APPNAME)); \
	 docker wait $$(<$(APPNAME)); \
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
