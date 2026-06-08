FROM nousresearch/hermes-agent:latest

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        sudo \
        wget \
        ca-certificates \
        jq \
        iproute2 \
        iputils-ping \
    && rm -rf /var/lib/apt/lists/*
