set -e
S=${1:-4101}; R=/home/tf/src/aprs-r4; V=$R/aprs-vectors/tools; D=/tmp/r4run/s$S; mkdir -p $D; cd $D
python3 $V/mutate.py - fuzz.hex.gz --count 200000 --seed $S >/dev/null
python3 $V/generate.py data.jsonl.gz --count 100000 --seed $S >/dev/null
python3 $V/generate.py recipes.jsonl.gz --recipes --count 100000 --seed $S >/dev/null
python3 $V/generate.py faults.jsonl.gz --faults --nonfinite 0.2 --count 100000 --seed $S >/dev/null
python3 $V/generate.py frecipes.jsonl.gz --recipes --faults --nonfinite 0.2 --count 100000 --seed $S >/dev/null
if [ ! -f /tmp/r4run/built ]; then
(cd $R/aprs-ts && npm ci >/dev/null 2>&1 && npm run build >/dev/null 2>&1)
(cd $R/aprs-rs && cargo build -q --release --example diff_dump -j3 2>&1 | tail -2)
(cd $R/aprs-go && go build -o /tmp/r4run/godump ./cmd/aprs-diffdump)
(cd $R/aprs-py && { [ -d .venv ] || python3 -m venv .venv; } && .venv/bin/pip -q install -e . >/dev/null 2>&1)
(cd $R/aprs-c && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release >/dev/null && cmake --build build -j3 >/dev/null 2>&1; ls build/pdn_aprs_diffdump >/dev/null)
(cd $R/aprs-cs && dotnet build -c Release tools/Packet.Aprs.Corpus -v q 2>&1 | grep -E "error|Warn.*[1-9] Warn|Elapsed" | head -3)
touch /tmp/r4run/built; fi
CS=$R/aprs-cs/tools/Packet.Aprs.Corpus/bin/Release/net10.0/aprs-corpus.dll
run(){ n=$1; m=$2; csm=$3; f=$D/$4
  (cd $R/aprs-py && .venv/bin/python tools/diff_dump.py $m $f $D/$n.py.gz >/dev/null 2>$D/$n.py.err) &
  (cd $R/aprs-ts && node scripts/diff-dump.mjs $m $f $D/$n.ts.gz >/dev/null 2>$D/$n.ts.err) &
  (cd $R/aprs-rs && target/release/examples/diff_dump $m $f $D/$n.rs.gz >/dev/null 2>$D/$n.rs.err) &
  (/tmp/r4run/godump $m $f $D/$n.go.gz >/dev/null 2>$D/$n.go.err) &
  (zcat $f | $R/aprs-c/build/pdn_aprs_diffdump $m 2>$D/$n.c.err | gzip > $D/$n.c.gz) &
  (dotnet $CS diff $csm $f $D/$n.cs.gz >/dev/null 2>$D/$n.cs.err) &
  wait
  python3 $V/compare.py $n.cs.gz $n.rs.gz $n.py.gz $n.ts.gz $n.c.gz $n.go.gz --input $4 --json $n.json > $n.txt 2>&1 || true
  echo "== $n"; head -3 $n.txt | cut -c1-600; for e in $n.*.err; do [ -s $e ] && { echo "  ERR $e:"; tail -2 $e | cut -c1-200; }; done; true
}
run fuzz "" dump fuzz.hex.gz
run data --encode encode data.jsonl.gz
run recipes --build build recipes.jsonl.gz
run faults --encode encode faults.jsonl.gz
run frecipes --build build frecipes.jsonl.gz
