#!/bin/bash
# dumpall.sh <lines.hex.gz> <prefix>: runs the five dump tools, writes <prefix>.{cs,rs,py,ts,c}.jsonl.gz
set -u
L=$(realpath "$1"); P=$(realpath -m "$2")
(cd ~/src/packet.net && dotnet run -c Release --no-build --project tools/Packet.Aprs.Corpus -- diff dump "$L" "$P.cs.jsonl.gz" > "$P.cs.log" 2>&1) &
(cd ~/src/aprs-rs && ./target/release/examples/diff_dump "$L" "$P.rs.jsonl.gz" > "$P.rs.log" 2>&1) &
(cd ~/src/aprs-py && PYTHONPATH=src python3 tools/diff_dump.py "$L" "$P.py.jsonl.gz" --jobs 8 > "$P.py.log" 2>&1) &
(cd ~/src/aprs-ts && node scripts/diff-dump.mjs "$L" "$P.ts.jsonl.gz" > "$P.ts.log" 2>&1) &
(cd ~/src/aprs-c && zcat "$L" | build/pdn_aprs_diffdump | gzip -1 > "$P.c.jsonl.gz" 2> "$P.c.log") &
wait
