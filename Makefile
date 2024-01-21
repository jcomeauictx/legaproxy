# allow Bashisms
SHELL := /bin/bash
HOST ?= 127.0.0.1
PORT ?= 3000
BROWSER ?= firefox
export HOST PORT
all: run view
getting-started: Dockerfile Makefile
	docker build -t $@ $(<D)
	touch $@
%: %.template
	envsubst < $< > $@
run: getting-started
	docker run --detach --publish $(HOST):$(PORT):$(PORT) $< > $<
view:
	$(BROWSER) $(HOST):$(PORT)/
stop:
	if [ -s "getting-started" ]; then docker stop $$(<getting-started); fi
clean:
	$(MAKE) stop
	if [ -s "getting-started" ]; then docker rm $$(<getting-started); fi
	if [ -f "getting-started" ]; then docker rmi getting-started; fi
	rm -f getting-started
distclean: clean
	rm -f Dockerfile
