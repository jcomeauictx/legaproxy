SHELL := /bin/bash
BROWSER ?= /usr/bin/mozilla-firefox
PACKAGE := $(notdir $(BROWSER))
TASKNAME := browse
# Xorg on Debian (Bookworm at least) doesn't listen on tcp
GATEWAY ?=
# get rid of quotes (if any) on GATEWAY
X11 := $(shell echo $(GATEWAY):0)
# export what's needed for envsubst
export BROWSER PACKAGE GATEWAY X11
all: $(TASKNAME)
$(TASKNAME): Dockerfile Makefile
	docker build --tag $@ \
	 --network host \
	 $(<D)
	touch $@
%: %.template Makefile
	envsubst < $< > $@
env:
	$@
