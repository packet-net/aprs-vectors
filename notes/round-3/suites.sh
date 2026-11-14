#!/bin/bash
L=/tmp/r3/libs; O=/tmp/r3/suite
mkdir -p $O
(cd $L/aprs-go && go test -count=1 ./... > $O/go.log 2>&1; echo "exit $?" >> $O/go.log)
(cd $L/aprs-rs && RUST_MIN_STACK=268435456 cargo test --locked > $O/rs.log 2>&1; echo "exit $?" >> $O/rs.log)
(cd $L/aprs-py && python3 -m venv .venv >/dev/null 2>&1; .venv/bin/pip -q install -e . pytest >/dev/null 2>&1; .venv/bin/python -m pytest -q -p no:cacheprovider > $O/py.log 2>&1; echo "exit $?" >> $O/py.log)
(cd $L/aprs-ts && npm test > $O/ts.log 2>&1; echo "exit $?" >> $O/ts.log)
(cd $L/aprs-c && cmake --build build -j4 >/dev/null 2>&1; ctest --test-dir build --output-on-failure > $O/c.log 2>&1; echo "exit $?" >> $O/c.log; build/pdn_aprs_vectors vectors tests/known-differences.txt > $O/c-vectors.log 2>&1)
(cd $L/aprs-cs && dotnet test Packet.Aprs.slnx > $O/cs.log 2>&1; echo "exit $?" >> $O/cs.log)
echo ALLDONE > $O/done
