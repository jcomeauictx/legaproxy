# allow Bashisms
SHELL := /bin/bash
HOST ?= 127.0.0.1
PORT ?= 3000
BROWSER ?= firefox
APPNAME := getting-started
export HOST PORT
all: run view
$(APPNAME): Dockerfile Makefile
	docker build -t $@ $(<D)
	touch $@
%: %.template
	envsubst < $< > $@
run: $(APPNAME)
	docker run \
	 --detach \
	 --interactive \
	 --tty \
	 --publish $(HOST):$(PORT):$(PORT) $< > $<
bind-run: $(APPNAME)
	docker run \
	 --detach \
	 --interactive \
	 --tty \
	 --publish $(HOST):$(PORT):$(PORT) \
	 --workdir /app \
	 --mount type=bind,src="$(PWD)",target=/app \
	 node:18-alpine \
	 sh -c "yarn install && yarn run dev" \
	 > $<
	while read line; do \
	 echo $$line; \
	 if [ "$$line" = "Listening on port $(PORT)" ]; then break; fi \
	done \
	 < <(docker logs --follow $$(<$<))
attach:
	if [ -s "$(APPNAME)" ]; then \
	 docker attach $$(<$(APPNAME)); \
	else \
	 echo No active container >&2; \
	fi
view:
	$(BROWSER) $(HOST):$(PORT)/
stop:
	if [ -s "$(APPNAME)" ]; then \
	 docker stop $$(<$(APPNAME)); \
	 docker wait $$(<$(APPNAME)); \
	fi
purge:  # stop with no opportunity to restart
	-$(MAKE) stop
	# truncate file containing the stopped container ID
	# same as :>$(APPNAME)
	>$(APPNAME)
clean:
	$(MAKE) stop
	if [ -s "$(APPNAME)" ]; then docker rm $$(<$(APPNAME)); fi
	if [ -f "$(APPNAME)" ]; then docker rmi $(APPNAME); fi
	rm -f $(APPNAME)
distclean: clean
	rm -f Dockerfile
