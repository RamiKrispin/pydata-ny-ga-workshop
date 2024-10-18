#!/usr/bin/env bash

apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    wget \
    git \
    libgomp1 \
     && rm -rf /var/lib/apt/lists/*

