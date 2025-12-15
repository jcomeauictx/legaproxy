SHELL := /bin/bash
HOST ?= 127.0.0.1
BROWSER ?= /usr/bin/mozilla-firefox
PACKAGE := $(notdir $(BROWSER))
RELEASE := $(notdir $(CURDIR))
TASKNAME := browse
TAG := $(RELEASE)\:$(TASKNAME)
IMAGES ?= $(HOME)/mnt/docker-images
CONTAINERS ?= $(HOME)/mnt/docker-containers
CONTAINER := $(RELEASE)-$(TASKNAME)
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
all: bind-run capabilities
$(IMAGES)/$(TAG): $(IMAGES)/README Dockerfile
	$(MAKE) tcpopen
	-docker build --tag $(@F) .
	$(MAKE) tcpclose
$(IMAGES)/README:
	systemctl --user start dockerfs
	sleep 10
bind-run: $(CONTAINERS)/$(CONTAINER)
$(CONTAINERS)/$(CONTAINER): $(IMAGES)/$(TAG)
	@echo Attempting to run $(<F)... >&2
	docker run \
	 --detach \
	 --publish $(HOST):$(SSHPORT):$(SSHPORT) \
	 --workdir /app \
	 --name $(@F) \
	 --mount type=bind,src="$(PWD)",target=/app \
	 $(<F)
	@echo Waiting for image to fully launch before connect attempt
	-sleep 5
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
ssh login: $(CONTAINERS)/$(CONTAINER)
	ssh $(SSHOPTS) -Y -p $(SSHPORT) \
	 -oStrictHostKeyChecking=no \
	 -oUserKnownHostsFile=/dev/null \
	 -oKexAlgorithms=+diffie-hellman-group1-sha1 \
	 -oHostKeyAlgorithms=+ssh-rsa \
	 -oPubkeyAcceptedKeyTypes=+ssh-rsa \
	 root@localhost '$(SSH_COMMAND)'
capabilities:
	$(MAKE) SSH_COMMAND='mozilla-firefox /app/$@.html' ssh
push:
	-$(foreach remote, $(filter-out original, $(shell git remote)), \
	 git push $(remote);)
