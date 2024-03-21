SHELL := /bin/bash
BROWSER ?= /usr/bin/mozilla-firefox
PACKAGE := $(notdir $(BROWSER))
TASKNAME := browse
X11SOCKET := /tmp/.X11-unix/X0
TCPPID := /var/run/socat_x11.pid
DOCKERPID := /var/run/docker_sarge.pid
GATEWAY ?= $(subst ",,$(shell docker network inspect bridge | \
	 awk '$$1 ~ /^"Gateway":$$/ {print $$2}'))
# export what's needed for envsubst
export BROWSER PACKAGE GATEWAY
all: $(TASKNAME)
$(TASKNAME): Dockerfile Makefile ../es5-6.html
	$(MAKE) tcpopen
	$(MAKE) tmpclean
	cp ../es5-6.html tmp/
	-docker build --tag $@ $(<D)
	touch $@
	$(MAKE) clean
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
distclean: clean
	-docker rmi $(TASKNAME):$(TASKNAME)
	rm -f $(TASKNAME)
