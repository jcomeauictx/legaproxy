# allow Bashisms
SHELL := /bin/bash
HOST ?= 127.0.0.1
PORT ?= 3000
export HOST PORT
all: run
getting-started: Dockerfile Makefile
	docker build -t $@ $(<D)
	touch $@
%: %.template
	envsubst < $< > $@
run: getting-started
	docker run --detach --publish $(HOST):$(PORT):$(PORT) $< > $<
stop:
	-docker stop $$(<getting-started)
clean:
	$(MAKE) stop
	-docker rm $$(<getting-started)
	-docker rmi getting-started
	rm -f getting-started
distclean: clean
	rm -f Dockerfile
