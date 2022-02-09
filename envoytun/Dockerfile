# ---- python 3.10 ------------------------------------------------------
FROM python:3.10-bullseye as base

# ---- boringtun (wireguard) ---------------------------------------
FROM rust:1.54-slim-buster AS builder
WORKDIR /src
COPY boringtun .
RUN cargo build --release \
    && strip ./target/release/boringtun

# ---- build -------------------------------------------------------
FROM base AS compile-image
WORKDIR /app
COPY --from=builder /src/target/release/boringtun /app

ARG DEBIAN_FRONTEND=noninteractive
ENV WG_LOG_LEVEL=info \
    WG_THREADS=4

RUN apt-get update
RUN apt install software-properties-common -y
RUN apt-get install -y --no-install-recommends \
    wireguard \
    build-essential \
    iproute2 \
    iptables \
    tcpdump \
    openresolv \
    iputils-ping \
    curl \
    net-tools \
    gcc \
    software-properties-common \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/* /var/lib/apt/lists/*
RUN python -m venv /app
RUN python 
ENV PATH="/app/bin:$PATH"

COPY requirements.txt .
COPY addPeer.py .
COPY envoytun.sh .

RUN pip install --upgrade pip
# pip install is fast here (while slow without the venv) :
RUN pip install -r requirements.txt
CMD ./envoytun.sh


#FROM envoyproxy/envoy:v1.20-latest
#COPY --from=compile-image /app/env /app/env
#
#WORKDIR /app/env
#

#
#RUN mkdir -p /etc/envoy
#COPY envoy.yaml /etc/envoy/envoy.yaml
#RUN chmod go+r /etc/envoy/envoy.yaml
#
#COPY requirements.txt .
##COPY addPeer.py .
#COPY envoytun.sh .
#
#COPY phronesis-dev-f169beb7eb5a.json .
#ENV PATH="/app/bin:$PATH"
#
## -v ~/.config:/root/.config


