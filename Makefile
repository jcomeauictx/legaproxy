# allow Bashisms
SHELL := /bin/bash
HOST ?= 127.0.0.1
PORT ?= 3000
export HOST PORT
all: run
getting-started: Dockerfile Makefile
	$(MAKE) clean
	docker build -t $@ $(<D)
	touch $@
%: %.template
	envsubst < $< > $@
run: getting-started
	docker run -dp $(HOST):$(PORT):$(PORT) $<
clean:
	-docker rmi $$(docker images | awk '$$1 ~ /^getting-started$$/ {print $$3}')
	rm -f getting-started
