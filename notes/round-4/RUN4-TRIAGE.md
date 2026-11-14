# Round 4, run 4: triage

Run 4: vectors at 0c625fc, the six libraries at their latest `round-4` heads. `/tmp/r4run/s4505/` is clean (600,000 lines). `/tmp/r4run/s4606/` has 3 fuzz lines (9 buckets) and 1 recipes line. Verdicts follow the rule text, not the majority. Each case below was checked by running all six dump tools on it (`/tmp/r4-triage/run4-cases.json`, `run6.sh`): it matches every library judged right, field for field.

## 1. The four lines

| Seed, set, line | Input (short) | Split | Deciding rule | Verdict |
|---|---|---|---|---|
| s4606 fuzz 37394 | `` `f[Cl]=v/"4*}!wZo!PHG5132 `` | cs, rs, py, c, go give `data-extension-in-comment` \| ts does not | README Mic-E: "A PHG or RNG is straight after the type code only where it is so in the status text as sent"; "A `!DAO!` is five bytes as sent, so taking another element out never joins one" | ts wrong. As sent, the PHG follows the `!DAO!`, not the leading altitude, so it is late. A PHG straight after the leading altitude is in place (`mic-e/frequency-after-phg`), but here it gets there only by lifting the `!DAO!`. |
| s4606 fuzz 131069 | `;BREND/   *100045z4905.50NA07201.75W@101/047/HC/104^123/0980>065&0220%040` | cs, rs, py, c, go read the storm data \| ts leaves it as comment | Storm data needs the hurricane symbol. The only symbol rule that excludes an overlay is the signpost's ("needs the `\m` symbol and not an overlaid `m`"); an overlay character stands in for the alternate table `\`, so `A@` is the hurricane symbol | ts wrong (decoder, and the encoder refuses storm on `A@` as `symbol-mismatch`). The rest of the line, `&022` then `0%040`, all six read alike: tropical storm radius 22, no whole gale radius, comment `0%040`. |
| s4606 fuzz 194079 | `;BRENDA   *...@101/047/HC/104^123/0980>065&020%4.410/433.775040` | cs, rs, ts, c, go: storm ends at `&020`, comment `%4.410/433.775040`, identical \| py swallows `%4.4` and drops it (comment `10/433.775040`) | README data form: "Storm data's fields are digits"; the whole gale radius is optional (all six model it so) | py wrong. `4.4` is not a field, so the storm data ends before `%`, and nothing may be lost. |
| s4606 recipes 26841 | status, text `IO91SX/G` + 610 bytes | cs, py, ts, c, go: `text-reads-as-field` \| rs: `too-long` | IMPLEMENT revision A: the size is checked last, on the bytes written, "after every other check (read-back included)" | rs wrong. |

## 2. Cases to add

Fuzz 37394, with a clean header (the original's `multiple-used-markers` path is incidental). Its strict result follows `mic-e/an-rng-reached-only-by-lifting-an-altitude-is-late`: a strict decoder declines the late PHG and keeps it as text.
```json
{"id": "mic-e/phg-reached-only-by-lifting-a-dao-is-late", "description": "The PHG comes straight after the leading Mic-E altitude only once the !DAO! before it is lifted; in the status text as sent it follows the !DAO!, so it is a late data extension.", "source": "differential fuzzing 2026-11-14", "authority": "interpretation", "interpretations": ["where-a-mic-e-locator-is-read"], "input": {"info": "`f[Cl]=v/\"4*}!wZo!PHG5132", "destination": "T0QW8S"}, "expect": {"data": {"type": "mic-e", "mic_e_message": "in-service", "latitude": 40.297271062271065, "longitude": -74.05664285714286, "symbol": "/v", "course_degrees": 133, "speed_knots": 6, "altitude_feet": 62.33595800524934, "phg": {"power": 5, "height": 1, "gain": 3, "directivity": 2}, "dao": {"datum": "W", "precision": "base91"}}, "diagnostics": ["info:mic-e-missing-device-type", "warning:data-extension-in-comment"]}, "strict": {"data": {"type": "mic-e", "mic_e_message": "in-service", "latitude": 40.297271062271065, "longitude": -74.05664285714286, "symbol": "/v", "course_degrees": 133, "speed_knots": 6, "altitude_feet": 62.33595800524934, "dao": {"datum": "W", "precision": "base91"}, "comment": "PHG5132"}, "diagnostics": ["info:mic-e-missing-device-type"]}, "reencode": "equivalent", "canonical_info": "`f[Cl]=v/\"4*}PHG5132!wZo!"}
```
Fuzz 131069, the class in its plainest form (the full storm data on `A@`):
```json
{"id": "object-item/storm-data-on-an-overlaid-hurricane-symbol", "description": "An overlay on the alternate table's @ is still the hurricane symbol, so the storm data after the course and speed is read.", "source": "differential fuzzing 2026-11-14", "authority": "interpretation", "interpretations": ["an-area-df-bearing-or-storm-is-not-the-data-extension"], "input": {"info": ";BRENDA   *100045z4905.50NA07201.75W@101/047/HC/104^123/0980>065&020%040"}, "expect": {"data": {"type": "object", "name": "BRENDA", "timestamp": "100045z", "latitude": 49.09166666666667, "longitude": -72.02916666666667, "symbol": "A@", "course_degrees": 101, "speed_knots": 47, "storm": {"type": "hurricane", "sustained_wind_knots": 104, "gust_knots": 123, "central_pressure_mbar": 980, "hurricane_radius_nm": 65, "tropical_storm_radius_nm": 20, "whole_gale_radius_nm": 40}}}, "strict": "same", "reencode": "identical"}
```
Fuzz 194079:
```json
{"id": "object-item/storm-data-ends-before-a-whole-gale-radius-that-is-not-digits", "description": "The whole gale radius is optional and its field is digits: %4.4 is not one, so the storm data ends after the tropical storm radius and %4.4 starts the comment.", "source": "differential fuzzing 2026-11-14", "authority": "interpretation", "interpretations": ["an-area-df-bearing-or-storm-is-not-the-data-extension"], "input": {"info": ";BRENDA   *100045z4905.50N/07201.75W@101/047/HC/104^123/0980>065&020%4.410/433.775040"}, "expect": {"data": {"type": "object", "name": "BRENDA", "timestamp": "100045z", "latitude": 49.09166666666667, "longitude": -72.02916666666667, "symbol": "/@", "course_degrees": 101, "speed_knots": 47, "storm": {"type": "hurricane", "sustained_wind_knots": 104, "gust_knots": 123, "central_pressure_mbar": 980, "hurricane_radius_nm": 65, "tropical_storm_radius_nm": 20}, "comment": "%4.410/433.775040"}}, "strict": "same", "reencode": "identical"}
```
Recipes 26841, smallest form (field 257 bytes), as a build case and an encode case:
```json
{"id": "build/text-reads-as-field-before-info-size", "description": "Status text that starts with what reads as a locator and makes a 257-byte field is text-reads-as-field: the size is checked last, after the read-back.", "source": "differential run 2026-11-14", "authority": "interpretation", "interpretations": ["an-information-field-is-at-most-256-bytes", "which-refusal-a-record-with-two-faults-gets"], "input": {"build": {"station": {"source": "N0CALL"}, "report": "status", "args": {"text": "IO91SX/Gxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}}}, "expect": {"refused": true, "refusal": "text-reads-as-field"}}
```
```json
{"id": "encode/status-read-back-before-info-size", "description": "Status text that starts with what reads as a locator, in a 257-byte field, is text-reads-as-field: the size is checked last, after the read-back.", "source": "differential run 2026-11-14", "authority": "interpretation", "interpretations": ["an-information-field-is-at-most-256-bytes"], "input": {"encode": {"type": "status", "text": "IO91SX/Gxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}}, "expect": {"refused": true, "refusal": "text-reads-as-field"}}
```
Only if G1 below is ruled as recommended (storm fields are digits only):
```json
{"id": "object-item/storm-data-with-dots-in-a-field-is-text", "description": "Storm data's fields are digits; ... is not one (unlike a weather value), so none of it is storm data and it stays in the comment.", "source": "differential triage 2026-11-14", "authority": "interpretation", "interpretations": ["an-area-df-bearing-or-storm-is-not-the-data-extension"], "input": {"info": ";BRENDA   *100045z4905.50N/07201.75W@101/047/HC/...^123/0980>065&020%040"}, "expect": {"data": {"type": "object", "name": "BRENDA", "timestamp": "100045z", "latitude": 49.09166666666667, "longitude": -72.02916666666667, "symbol": "/@", "course_degrees": 101, "speed_knots": 47, "comment": "HC/...^123/0980>065&020%040"}}, "strict": "same", "reencode": "equivalent", "canonical_info": ";BRENDA   *100045z4905.50N/07201.75W@101/047HC/...^123/0980>065&020%040"}
```
```json
{"id": "object-item/storm-whole-gale-radius-of-dots-is-text", "description": "A whole gale radius of dots is not a field, so the storm data ends before it and %... is comment text.", "source": "differential triage 2026-11-14", "authority": "interpretation", "interpretations": ["an-area-df-bearing-or-storm-is-not-the-data-extension"], "input": {"info": ";BRENDA   *100045z4905.50N/07201.75W@101/047/HC/104^123/0980>065&020%..."}, "expect": {"data": {"type": "object", "name": "BRENDA", "timestamp": "100045z", "latitude": 49.09166666666667, "longitude": -72.02916666666667, "symbol": "/@", "course_degrees": 101, "speed_knots": 47, "storm": {"type": "hurricane", "sustained_wind_knots": 104, "gust_knots": 123, "central_pressure_mbar": 980, "hurricane_radius_nm": 65, "tropical_storm_radius_nm": 20}, "comment": "%..."}}, "strict": "same", "reencode": "identical"}
```

## 3. Fix lists

### aprs-ts

1. **A Mic-E PHG or RNG is "at the start" only where it is so in the status text as sent.**
   - Cause: in `src/decode/reports.ts` (around line 418), `startJoined` only accounts for `join`, the place of a lifted later altitude. But the text given to `liftMicEComment` is `pre.rest`, the status text with base-91 telemetry and the `!DAO!` already lifted (`liftTelemetryAndDao(text, joins)`). So `extensionAtStart` in `liftComment` (`src/decode/positioned.ts`) accepts any extension that reaches position 0 by lifting.
   - Fix: treat the extension at position 0 of `pre.rest` as in place only when nothing was removed before it: no range in `pre.removed` starts before its position in `text`, and no `join` lies there. That covers a `!DAO!`, base-91 telemetry and a later altitude alike.
   - Expected: `mic-e/phg-reached-only-by-lifting-a-dao-is-late` above. The same holds for `` `f[Cl]=v/"4*}|!!!!|PHG5132 `` (telemetry before the PHG) and `` `f[Cl]=v/"4*}!wZo!RNG0050 `` (an RNG); in both, the five give `data-extension-in-comment` and ts does not.
2. **An overlaid `@` is the hurricane symbol.**
   - Cause: `src/decode/positioned.ts:1143` reads storm data only for table `/` or `\`; `src/encode/position.ts:497` refuses storm data on any other table as `symbol-mismatch`. An overlay (`0`-`9`, `A`-`Z`) stands for the alternate table.
   - Fix: accept `/`, `\` or an overlay character with code `@`, in both places. Lines 1103, 495 and 499 test the area symbol `\l` the same way; no rule excludes an overlay there either, so check them against the other libraries before changing them. The signpost (`positioned.ts:771`, `encode/position.ts:498`) rightly excludes overlays.
   - Expected: `object-item/storm-data-on-an-overlaid-hurricane-symbol`; fuzz s4606 131069 as in section 1. Encode of that case's data: `written`, info = the case's input.

### aprs-py

1. **Storm fields are digits; a field that is not one ends the storm data, and nothing is dropped.**
   - Cause: `src/pdn_aprs/_comment.py:46`, `_STORM` matches every field with `[0-9.]{3}` or `[0-9.]{4}`, so `%4.4` matches. `_opt_int` (line 96) then turns a non-integer into `None`, while `st.end()` still consumes its bytes, so `%4.4` vanishes from the comment.
   - Fix: digits only, `[0-9]{3}` and `[0-9]{4}`. The optional `%` group then fails to match and its bytes stay in the comment. A required field that is not digits makes the whole match fail, so it is all comment text (`object-item/storm-data-with-a-space-in-a-field-is-text`).
   - Expected: `object-item/storm-data-ends-before-a-whole-gale-radius-that-is-not-digits`.
   - If G1 is ruled as recommended, `_storm_text` in `encode.py` (line 714) must also stop writing dots for an absent required field and refuse it as `missing-field`, as ts does.

### aprs-rs

1. **The size is checked after the read-back in every encoder.**
   - Cause: `src/status.rs:132-133` and `src/telemetry.rs:127-128` call `p.size(out.len()); p.finish()?;` before their read-back, so `finish` names `too-long` ahead of the read-back's `text-reads-as-field`. `encode.rs`, `message.rs`, `mic_e.rs` and `other.rs:473` already do it in the right order: `finish_faults()`, then the read-back, then `refusal::check_size`.
   - Fix: use that order in `status.rs` and `telemetry.rs`. The other `p.size(); p.finish()` sites (`other.rs` 509, 534, 570, 600, 640, 710) have no read-back after them, so they are fine.
   - Expected: `build/text-reads-as-field-before-info-size` and `encode/status-read-back-before-info-size`: `refused`, `text-reads-as-field`. Recipes s4606 26841: `text-reads-as-field`. Telemetry `{"type":"telemetry","sequence":"MIC1","analog":[1,2,3,4,5],"bits":"00000000","comment":240 x}`: the read-back's code, not `too-long` (see G2 for which code).

### Off-run, conditional on G1 (storm fields of dots)

- cs (`Internal/StormCodec.cs` `Group`), rs (`src/comment.rs` `storm`, the `field` closure), go (`comment.go` `storm`, `field`) and py take an all-dots (and, except py, an all-spaces) storm field as unknown. If G1 is ruled (a), read only digits. Their encoders write `...` for an absent required field (`StormCodec.Value`, py `n()`, rs/go likewise); they must refuse it as `missing-field`, as ts does.
- c writes `000` for an absent required storm field. Constructed: storm with no `sustained_wind_knots` is written `/HC/000^123/...`, which adds a value that was not given. That is wrong under either option: under (a) refuse `missing-field`, under (b) write `...`.

### Off-run: aprs-cs and a telemetry sequence starting MIC

cs writes `{"type":"telemetry","sequence":"MIC1","analog":[1,2,3,4,5],"bits":"00000000"}` as `T#MIC1,001,...`. That reads back (all six decoders agree) as sequence `MIC`, values `[1,1,2,3,4]`, `invalid-telemetry`, so cs breaks the Encoding rule's first sentence. The others refuse. With a 240-byte comment, cs also gives `too-long` ahead of the read-back. Fix: a read-back (or an explicit check) for a sequence starting `MIC` other than `MIC`, then size last. The code is G2.

## 4. Rule gaps

**G1. Storm fields of dots or spaces.** Not in run 4; found while checking 194079. README: "Storm data's fields are digits ...: unlike a weather value, a field holding a space is not one". cs, rs, py and go nevertheless read an all-dots field (`/HC/...^123/...`, `%...`) as unknown, and their encoders write dots for an absent field; ts and c read only digits.
- (a) Digits only (ts, c): all-dots fields make the storm data comment text; an absent required field in neutral data is `missing-field`.
- (b) All-dots as unknown, as weather has.
- Recommend (a). It is what the README says, and it is the contrast the sentence draws with weather. APRS12c ch. 12 gives the storm fields as digits only.
- Wording, if confirmed: "... are digits (not dots or spaces, unlike a weather value) ...". In Encoding: "storm data missing a required field is `missing-field`". The two dot cases in section 2 go with it.

**G2. Which code for a fixed-form field that reads back changed.** Encode `{"type":"telemetry","sequence":"MIC1",...}`: rs, py, ts and go give `text-reads-as-field`; c gives `does-not-read-back` without a comment and `text-reads-as-field` with one; cs writes it. A sequence is fixed-form text, and the Refusal reasons say "free text that reads back changed is `text-reads-as-field` ... anything else is `does-not-read-back`", but `does-not-read-back` is meant to have no case.
- Recommend `malformed`, by a named rule rather than the read-back. Fixed-form text "is `malformed` whatever is wrong with it", and a sequence starting `MIC` that is not `MIC` cannot be written as itself.
- Wording, Telemetry: "a sequence that starts `MIC` is `MIC` itself; any other is `malformed` for an encoder". Add an encode case with `"sequence":"MIC1"` expecting `malformed`.
