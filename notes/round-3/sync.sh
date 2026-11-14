#!/bin/bash
# copy the round-3 vectors into each scratch library clone
V=/home/tf/src/aprs-vectors-r3
for r in aprs-rs aprs-py aprs-ts aprs-c aprs-go; do mkdir -p /tmp/r3/libs/$r/vectors; rsync -a --delete --exclude .git $V/ /tmp/r3/libs/$r/vectors/; done
mkdir -p /tmp/r3/libs/aprs-cs/spec/aprs; rsync -a --delete --exclude .git $V/ /tmp/r3/libs/aprs-cs/spec/aprs/
