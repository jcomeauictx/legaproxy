getting-started: Dockerfile Makefile
	docker build -t $@ $(<D)
	touch $@
