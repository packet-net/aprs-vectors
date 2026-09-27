#!/bin/bash
# stream5.sh <mode: dump|encode|build> <input.gz> <report-prefix>
# Runs the five dump tools into named pipes and compares them as they go, so no dump reaches the disk.
set -u
MODE=$1; IN=$(realpath "$2"); OUT=$(realpath -m "$3")
D=$(mktemp -d "${TMPDIR:-/tmp}/aprs-fifo.XXXX")
for n in cs rs py ts c; do mkfifo "$D/$n.gz"; done
case $MODE in dump) F=""; CS=dump;; encode) F="--encode"; CS=encode;; build) F="--build"; CS=build;; esac
(cd ~/src/packet.net && dotnet run -c Release --no-build --project tools/Packet.Aprs.Corpus -- diff $CS "$IN" "$D/cs.gz" > "$OUT.cs.log" 2>&1) &
(cd ~/src/aprs-rs && ./target/release/examples/diff_dump $F "$IN" "$D/rs.gz" > "$OUT.rs.log" 2>&1) &
(cd ~/src/aprs-py && PYTHONPATH=src python3 tools/diff_dump.py $F "$IN" "$D/py.gz" --jobs 6 > "$OUT.py.log" 2>&1) &
(cd ~/src/aprs-ts && node scripts/diff-dump.mjs $F "$IN" "$D/ts.gz" > "$OUT.ts.log" 2>&1) &
(cd ~/src/aprs-c && zcat "$IN" | build/pdn_aprs_diffdump $F 2> "$OUT.c.log" | gzip -1 > "$D/c.gz") &
python3 ~/src/aprs-vectors/tools/compare.py "$D/cs.gz" "$D/rs.gz" "$D/py.gz" "$D/ts.gz" "$D/c.gz" --names cs rs py ts c --input "$IN" --examples 3 --json "$OUT.json" > "$OUT.txt" 2>&1
wait
rm -rf "$D"
