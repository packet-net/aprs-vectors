# Round 5 (1.3.0): brief

One ruling, approved by Tom on 2026-11-15. Found by aprs-watch's comparison with Ham::APRS::FAP on live traffic, first full day on 1.2.0 (2.86 million packets compared, this one unexplained).

## The packet

`MC2BRB-1>APRS,WC4PEM-14,WC4PEM-4,WIDE2*,qAR,N4TDX:@R30549z2831.07N/08142.92W_015/001g006t058r000p000P000h-5b10170.DsVP`

A weather station in Florida whose timestamp has `R` where a digit should be. FAP skips the seven timestamp bytes and reads 28.5178333, -81.7153333, a weather station. All six libraries at 1.2.0 follow the README's "Timestamps that are not there" rule (the position straight after the DTI if that position decodes, else after seven bytes): `R30549z2831.0` happens to read as a compressed position, so they report 54.06038968, -81.16566997, symbol `R3`, course 64, speed 1.72 knots and no weather. The rule is obeyed and the answer is wrong.

## Why

Any 13 printable bytes that start with a symbol table character read as a compressed position, so "it decodes" is weak evidence. An uncompressed position has a strict shape (digits, a point, a hemisphere letter, twice over) that does not occur by accident. The rule for objects already asks whether the seven bytes look like a timestamp and a position follows them; the rule for position reports does not.

## Decision

In a `/` or `@` report whose timestamp is not valid (not six digits then `z`, `/` or `h`): when the seven bytes after the DTI end in `z`, `/` or `h` and an UNCOMPRESSED position follows them, the timestamp is garbled: the position is read after the seven bytes, with `malformed-timestamp` (tolerated), as it already is when the bytes after the DTI do not decode. Otherwise the rule is as before: the position straight after the DTI if that position decodes, else after seven bytes; when neither decodes, `malformed-timestamp`, an error.

"An uncompressed position follows" is judged as the README already judges a position for an object: on the position itself (latitude, symbol table, longitude, symbol code), under the options in force, not on anything after it.

Checked against the 2,454 cases at 1.2.0: four have this shape (corpus/0536, 0991, 1095, 1307) and all are already read after the seven bytes, because their first bytes do not decode as a compressed position. So no existing case changes; only packets where both readings decode are affected.

## To settle (vectors writer, from the spec and the existing rules; record in RULED.md)

- Whether a COMPRESSED position after seven timestamp-like bytes should also win over a compressed reading straight after the DTI. The brief says no (weak evidence either way, keep the existing order); confirm or argue.
- The strict result: with `malformed-timestamp` not tolerated, the report is rejected by it, as the four corpus cases are.
- What the report re-encodes to (the four corpus cases show the existing behaviour for a garbled timestamp; follow it).
- Whether the same question arises for a status report's or an object's timestamp; if the object rule already covers it, say so, and add a case only if one is missing.

## Cases

The live packet (as an observed case, source `APRS-IS 2026-11-14`, and as a rule case with header `N0CALL>APZ001` and a cut-down information field); the same with DTI `/`; with a seventh byte of `/` and of `h`; a compressed position with no timestamp whose seventh byte after the DTI is `z` and whose following bytes are NOT an uncompressed position (stays compressed, no diagnostic); a compressed position after seven timestamp-like bytes (per whatever is settled above); one where the seventh byte is not `z`, `/` or `h` (existing rule applies).

## Process

As round 4, smaller: vectors branch `round-5`, six libraries on `round-5`, six-way runs on fresh seeds (run.sh from round 4, with `--limits 5=...`), one reviewer per PR, merge libraries then vectors, bump PRs to 1.3.0 pinning the vectors merge commit, tags on Tom's word only. mutate.py should gain a mutation that damages one timestamp byte so the runs reach this rule. Comment on the aprs-watch issue when it is filed and when the fix is released.
