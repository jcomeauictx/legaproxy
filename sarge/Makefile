SHELL := /bin/bash
HOST ?= 127.0.0.1
BROWSER ?= /usr/bin/mozilla-firefox
PACKAGE := $(notdir $(BROWSER))
TASKNAME := browse
TAG := $(TASKNAME)\:latest
IMAGES ?= $(HOME)/mnt/docker-images
CONTAINERS ?= $(HOME)/mnt/docker-containers
CONTAINER := $(notdir $(CURDIR))-$(TASKNAME)
SSHPORT := 3322
SSHDCONF := /etc/ssh/sshd_config
SSHDORIG := $(SSHDCONF).orig
USERPUB := $(shell cat $(HOME)/.ssh/id_rsa.pub)
X11SOCKET := /tmp/.X11-unix/X0
TCPPID := /var/run/socat_x11.pid
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
all: bind-run ssh
$(IMAGES)/$(TAG): $(IMAGES)/README
	$(MAKE) tcpopen
	# only mark with TASKNAME file if build successful
	-docker build --tag $(@F) .
	$(MAKE) tcpclose
$(IMAGES)/README:
	systemctl --user start dockerfs
	time.sleep(10)
delay:
	@echo Waiting for image to fully launch before connect attempt
	sleep 5
bind-run: $(CONTAINERS)/$(CONTAINER)
$(CONTAINERS)/$(CONTAINER): $(IMAGES)/$(TAG)
	docker run \
	 --detach \
	 --publish $(HOST):$(SSHPORT):$(SSHPORT) \
	 --workdir /app \
	 --name $(@F)
	 --mount type=bind,src="$(PWD)",target=/app \
	 $(<F)
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
clean: tcpclose
	$(MAKE) stop
	-docker rm $(CONTAINER)
distclean: clean
	-docker rmi $(TAG)
stop:
	-docker stop $(CONTAINER)
connect attach: | $(CONTAINERS)/$(CONTAINER)
	docker exec --interactive --tty $(<F) /bin/bash
ssh login: delay | $(TASKNAME)
	ssh $(SSHOPTS) -Y -p $(SSHPORT) \
	 -oStrictHostKeyChecking=no \
	 -oUserKnownHostsFile=/dev/null \
	 -oKexAlgorithms=+diffie-hellman-group1-sha1 \
	 -oHostKeyAlgorithms=+ssh-rsa \
	 -oPubkeyAcceptedKeyTypes=+ssh-rsa \
	 root@localhost
