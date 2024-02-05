SHELL := /bin/bash
BROWSER ?= /usr/bin/mozilla-firefox
PACKAGE := $(notdir $(BROWSER))
TASKNAME := browse
# export what's needed for envsubst
export BROWSER PACKAGE
all: $(TASKNAME)
$(TASKNAME): Dockerfile Makefile
	docker build -t $@ $(<D)
	touch $@
%: %.template Makefile
	envsubst < $< > $@
