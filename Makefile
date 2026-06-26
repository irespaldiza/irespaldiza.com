.SILENT:
.NOTPARALLEL:

.PHONY: all site pdf clean local-site local-pdf local-all local-clean docker-build docker-site docker-pdf docker-all docker-clean

all:
	$(MAKE) docker-all

site:
	$(MAKE) docker-site

pdf:
	$(MAKE) docker-pdf

clean:
	$(MAKE) docker-clean

local-site:
	scripts/build.py site

local-pdf:
	scripts/build.py pdf

local-all:
	scripts/build.py all

local-clean:
	scripts/build.py clean

docker-build:
	docker build --quiet -t irespaldiza-career-repo .

docker-site: docker-build
	docker run --rm -u "$$(id -u):$$(id -g)" -e HOME=/tmp -e CHROME=/usr/bin/chromium -e CHROME_EXTRA_ARGS="--no-sandbox --disable-dev-shm-usage" -v "$$(pwd):/repo" -w /repo irespaldiza-career-repo site

docker-pdf: docker-build
	docker run --rm -u "$$(id -u):$$(id -g)" -e HOME=/tmp -e CHROME=/usr/bin/chromium -e CHROME_EXTRA_ARGS="--no-sandbox --disable-dev-shm-usage" -v "$$(pwd):/repo" -w /repo irespaldiza-career-repo pdf

docker-all: docker-build
	docker run --rm -u "$$(id -u):$$(id -g)" -e HOME=/tmp -e CHROME=/usr/bin/chromium -e CHROME_EXTRA_ARGS="--no-sandbox --disable-dev-shm-usage" -v "$$(pwd):/repo" -w /repo irespaldiza-career-repo all

docker-clean: docker-build
	docker run --rm -u "$$(id -u):$$(id -g)" -e HOME=/tmp -e CHROME=/usr/bin/chromium -e CHROME_EXTRA_ARGS="--no-sandbox --disable-dev-shm-usage" -v "$$(pwd):/repo" -w /repo irespaldiza-career-repo clean
