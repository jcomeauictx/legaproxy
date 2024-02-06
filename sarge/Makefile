SHELL := /bin/bash
BROWSER ?= /usr/bin/mozilla-firefox
PACKAGE := $(notdir $(BROWSER))
TASKNAME := browse
GATEWAY ?= $(shell docker network inspect bridge | \
	 awk '$$1 ~ /^"Gateway":$$/ {print $$2}')
# get rid of quotes on GATEWAY
X11 := $(shell echo $(GATEWAY):0)
# export what's needed for envsubst
export BROWSER PACKAGE GATEWAY X11
all: $(TASKNAME)
$(TASKNAME): Dockerfile Makefile
	docker build -t $@ $(<D)
	touch $@
%: %.template Makefile
	envsubst < $< > $@
env:
	$@
