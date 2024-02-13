SHELL := /bin/bash
BROWSER ?= /usr/bin/mozilla-firefox
PACKAGE := $(notdir $(BROWSER))
TASKNAME := browse
# export what's needed for envsubst
export BROWSER PACKAGE
all: $(TASKNAME)
$(TASKNAME): Dockerfile Makefile
	cp ../es5-6.html tmp/
	cp -a /tmp/.X11-unix tmp/
	@echo tmp/ before build:
	ls -alR tmp/
	-docker build --tag $@ \
	 $(<D) && touch $@
	$(MAKE) clean
%: %.template Makefile
	envsubst < $< > $@
env:
	$@
clean:
	find tmp/ -not -type d -and -not -name README.md -delete
	-find tmp/ -mindepth 1 -type d | xargs rmdir
distclean:
	rm -f $(TASKNAME)
