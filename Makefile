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
	docker run --detach --publish $(HOST):$(PORT):$(PORT) $< > $<
bind-run: $(APPNAME)
	docker run --detach --publish $(HOST):$(PORT):$(PORT) $< \
	 --workdir /app \
	 --mount type=bind,src="$(PWD)",target=/app \
	 node:18-alpine \
	 sh -c "yarn install && yarn run dev" \
	 > $<
view:
	$(BROWSER) $(HOST):$(PORT)/
stop:
	if [ -s "$(APPNAME)" ]; then docker stop $$(<$(APPNAME)); fi
clean:
	$(MAKE) stop
	if [ -s "$(APPNAME)" ]; then docker rm $$(<$(APPNAME)); fi
	if [ -f "$(APPNAME)" ]; then docker rmi $(APPNAME); fi
	rm -f $(APPNAME)
distclean: clean
	rm -f Dockerfile
