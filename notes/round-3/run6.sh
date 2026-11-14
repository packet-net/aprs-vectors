#!/bin/bash
# run6.sh <dump|encode|build> <input.gz> <outprefix>
set -u
MODE=$1; IN=$(realpath "$2"); P=$(realpath -m "$3")
case $MODE in dump) F=""; CS=dump;; encode) F="--encode"; CS=encode;; build) F="--build"; CS=build;; esac
L=/tmp/r3/libs
(cd $L/aprs-cs && dotnet run --no-build --project tools/Packet.Aprs.Corpus -- diff $CS "$IN" "$P.cs.gz" > "$P.cs.log" 2>&1) &
(cd $L/aprs-rs && ./target/release/examples/diff_dump $F "$IN" "$P.rs.gz" > "$P.rs.log" 2>&1) &
(cd $L/aprs-py && PYTHONPATH=src python3 tools/diff_dump.py $F "$IN" "$P.py.gz" > "$P.py.log" 2>&1) &
(cd $L/aprs-ts && node scripts/diff-dump.mjs $F "$IN" "$P.ts.gz" > "$P.ts.log" 2>&1) &
(cd $L/aprs-c && zcat "$IN" | build/pdn_aprs_diffdump $F 2> "$P.c.log" | gzip -1 > "$P.c.gz") &
(cd $L/aprs-go && /tmp/r3/go-diffdump $F "$IN" "$P.go.gz" > "$P.go.log" 2>&1) &
wait
