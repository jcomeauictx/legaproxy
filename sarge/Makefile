SHELL := /bin/bash
BROWSER ?= /usr/bin/mozilla-firefox
PACKAGE := $(notdir $(BROWSER))
TASKNAME := browse
SSHPORT := 3322
SSHDCONF := /etc/ssh/sshd_config
SSHDORIG := $(SSHDCONF).orig
USERPUB := $(HOME)/.ssh/id_rsa.pub
X11SOCKET := /tmp/.X11-unix/X0
TCPPID := /var/run/socat_x11.pid
DOCKERPID := /var/run/docker_sarge.pid
GATEWAY ?= $(subst ",,$(shell docker network inspect bridge | \
	 awk '$$1 ~ /^"Gateway":$$/ {print $$2}'))
# TIMESTAMP might be useful in image tag? or not.
TIMESTAMP := $(shell date '+%Y%m%d%H%M%S')
ifeq ($(SHOW_ENV),)
  # export what's needed for envsubst
  export BROWSER PACKAGE GATEWAY SSHPORT SSHDCONF SSHDORIG USERPUB
else
  # export everything so `make env` shows values
  export
endif
all: $(TASKNAME)
$(TASKNAME): Dockerfile Makefile ../es5-6.html
	$(MAKE) tcpopen
	$(MAKE) tmpclean
	cp ../es5-6.html tmp/
	# only mark with TASKNAME file if build successful
	-docker build --tag $@ $(<D) && touch $@
	$(MAKE) tcpclose tmpclean
bind-run: $(TASKNAME)
	docker run \
	 --detach \
	 --publish $(HOST):$(SSHPORT):$(SSHPORT) \
	 --workdir /app \
	 --mount type=bind,src="$(PWD)",target=/app \
	 node:$< \
	 sh -c "cat $(SSHDCONF) && \
	  mkdir -p /root/.ssh && \
	  echo $(USERPUB) >> /root/.ssh/authorized_keys && \
	  chmod 0700 /root/.ssh && \
	  chmod 0600 /root/.ssh/authorized_keys"
	 >> $<
	while read line; do \
	 echo $$line; \
	 if [ "$$line" = "Listening on port $(SSHPORT)" ]; then break; fi \
	done \
	 < <(docker logs --follow $$(<$<))
tcpopen:
	@sudo echo sudo now enabled for '`sudo tee`' below >&2
	socat TCP-LISTEN:6000,fork,bind=$(GATEWAY) UNIX-CONNECT:$(X11SOCKET) & \
	 echo $$! | sudo tee $(TCPPID)
tcpclose:
	-[ -f "$(TCPPID)" ] && kill $$(<$(TCPPID))
	sudo rm -f $(TCPPID)
%: %.template Makefile
	envsubst < $< > $@
env:
	$@
tmpclean:
	find tmp/ -not -type d -and -not -name README.md -delete
	-find tmp/ -mindepth 1 -type d | xargs --no-run-if-empty rmdir
clean: tcpclose tmpclean
	$(MAKE) stop
	if [ -s "$(TASKNAME)" ]; then docker rm $$(<$(TASKNAME)); fi
distclean: clean
	-docker rmi $(TASKNAME):$(TASKNAME)
	rm -f $(TASKNAME)
stop:
	if [ -s "$(TASKNAME)" ]; then \
	 docker stop $$(<$(TASKNAME)); \
	 docker wait $$(<$(TASKNAME)); \
	fi
