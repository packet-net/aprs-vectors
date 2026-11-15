# Round 5 review points, per library (beyond the shared Mic-E locator and tolerance-check work)

## aprs-ts
- CHANGELOG.md:5 says the Mic-E telemetry case "already passed"; it failed the tolerance check on main. Say "whose other checks already passed", or reword for the new check form.
- test/garbled-timestamp.test.ts:68-72 compares one line with itself; :63-66 only asserts what the latitude is not. Make both assert the expected reading.

## aprs-cs
- src/Packet.Aprs/Internal/MicECodec.cs:289 `text.RemoveAt(at)` deletes the locator's space after a later altitude is lifted and so changes the comment in ways the rule does not: follow the rule as now written (cases e, f, g pin the comment).
- CHANGELOG.md:5: says the runner "asserts how many cases it ran on" (it pinned the skipped case and a floor of 300); make it true for the new check form. Also say that a later altitude straight after the locator, then a spaced comment, no longer warns.

## aprs-rs
- src/mic_e.rs:294 `locator_space_ok` lifts a !DAO! that spans the altitude's join where comment::tail refuses it (case d).
- src/mic_e.rs:247-264: lenient diagnostics now come out of reading order (mic-e-altitude-not-first before missing-space-after-locator). The cases compare as a multiset, but keep reading order where the library promises it; say in your report whether it does.

## aprs-py
- src/pdn_aprs/_decode.py:952-958: the probe lifts any later Mic-E altitude; replace the probe with the decoder's own result (cases a to g).

## aprs-c
- tests/vectors.c:767 fails the run unless exactly one case skips the tolerance check: remove with the skip.

## aprs-go
- decode.go:128-130: one over-long re-wrapped doc comment line; tidy.
