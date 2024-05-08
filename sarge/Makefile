SHELL := /bin/bash
HOST ?= 127.0.0.1
BROWSER ?= /usr/bin/mozilla-firefox
PACKAGE := $(notdir $(BROWSER))
TASKNAME := browse
SSHPORT := 3322
SSHDCONF := /etc/ssh/sshd_config
SSHDORIG := $(SSHDCONF).orig
USERPUB := $(shell cat $(HOME)/.ssh/id_rsa.pub)
X11SOCKET := /tmp/.X11-unix/X0
TCPPID := /var/run/socat_x11.pid
DOCKERPID := /var/run/docker_sarge.pid
SSHOPTS ?=  # set to -vvv to debug
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
run: $(TASKNAME)
	docker run \
	 --detach \
	 $< > $<
bind-run: $(TASKNAME)
	docker run \
	 --detach \
	 --publish $(HOST):$(SSHPORT):$(SSHPORT) \
	 --workdir /app \
	 --mount type=bind,src="$(PWD)",target=/app \
	 $< > $<
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
	-if [ -s "$(TASKNAME)" ]; then docker rm $$(<$(TASKNAME)); fi
distclean: clean
	-docker rmi $(TASKNAME):$(TASKNAME)
	rm -f $(TASKNAME)
stop:
	-if [ -s "$(TASKNAME)" ]; then \
	 docker stop $$(<$(TASKNAME)); \
	 docker wait $$(<$(TASKNAME)); \
	fi
connect attach: | $(TASKNAME)
	docker exec --interactive --tty $$(<$|) /bin/bash
ssh login: | $(TASKNAME)
	ssh $(SSHOPTS) -Y -p $(SSHPORT) \
	 -oStrictHostKeyChecking=no \
	 -oUserKnownHostsFile=/dev/null \
	 -oKexAlgorithms=+diffie-hellman-group1-sha1 \
	 -oHostKeyAlgorithms=+ssh-rsa \
	 -oPubkeyAcceptedKeyTypes=+ssh-rsa \
	 root@localhost
