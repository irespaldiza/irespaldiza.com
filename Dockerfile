FROM python:3.13-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       chromium \
       pandoc \
       fonts-dejavu \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /repo

COPY . /repo

RUN pip install --no-cache-dir -r requirements.txt

ENV HOME=/tmp
ENV CHROME=/usr/bin/chromium
ENV CHROME_EXTRA_ARGS="--no-sandbox --disable-dev-shm-usage"

ENTRYPOINT ["python", "scripts/build.py"]
