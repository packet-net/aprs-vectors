# Round 4, run 2: triage of the six-way differences

Run 2: vectors at fe7d451 (IMPLEMENT.md "Revisions after run 1", A to G), the six libraries at their new `round-4` heads, two seeds: `/tmp/r4run/s4101/` and `/tmp/r4run/s4202/`. Library numbers as in compare.py: #1 cs, #2 rs, #3 py, #4 ts, #5 c, #6 go. A line is named by set, seed and `n` (the 0-based input line). Verdicts follow the rule text, not the majority. Helpers in `/tmp/r4-triage/`: `D=/tmp/r4run/s4202/ python3 get.py <set> <n>...` prints a line and the six records; `run6.sh <dump|encode|build> <file>` runs the six dump tools on a small file.

19 buckets in all, from 240 differing lines. All of fuzz, data and recipes agree at s4101, as do data and recipes at s4202.
- 8 buckets (231 lines, frecipes in both seeds) come from one dump-tool step: a recipe giving a quantity in two units, whose one-unit builds are too long only for size. The tools of cs, py, ts, c and go report `too-long`; by revision A the answer is `value-given-twice`, which rs gives. A wording fix in the README goes with it (G1).
- 6 buckets are aprs-c bugs (weather values that are NaN, and `s..6` read as a field).
- 2 buckets are aprs-py bugs.
- 3 buckets (one fuzz line) are a rule gap, G2: a Mic-E PHG straight after a locator with no space. I recommend that ts change.

## 1. Buckets

| # | Seed, set | Count | Split | Example (line: input, short) | Deciding rule | Verdict |
|---|---|---|---|---|---|---|
| B1 | s4101 faults | 3 | position refusal: five \| c | 7674: compressed weather, longitude -180.0001, `wind_speed_mph` -Infinity | Refusal reasons: `not-a-number` before `value-out-of-range`; "NaN or an infinity is `not-a-number` at every check that also catches it" (the wind has a place: cs bytes, or `DDD/SSS` uncompressed) | c: `not-a-number` |
| B2 | s4101 faults | 2 | object refusal: five \| c | 39564: compressed weather object, longitude -180.0001, `wind_direction_degrees` -Infinity | as B1 | c: `not-a-number` |
| B3 | s4101 frecipes | 51 | position refusal: cs+py+ts+c+go `too-long` \| rs `value-given-twice` | 3001: speed in knots and km/h, altitude in feet and metres, 239-byte comment; each one-unit build is only over 256 bytes | Builder rule "One quantity, one value": the first code in the order among both results and `value-given-twice`; revision A: size is checked last, after every other check, so a size `too-long` ranks after `value-given-twice` | rs right; the dump tools of cs, py, ts, c, go change (G1) |
| B4 | s4101 frecipes | 28 | mic-e refusal: same | 7169: speed in km/h and knots, 255-byte comment | as B3 | as B3 |
| B5 | s4101 frecipes | 27 | object refusal: same | 6074: altitude in feet and metres, 251-byte comment | as B3 | as B3 |
| B6 | s4101 frecipes | 11 | item refusal: same | 9503 | as B3 | as B3 |
| B7 | s4202 fuzz | 1 | position lenient.data: five \| c | 119262: `!4903.50N/07201.75W_220/004g005077s..6` | README Weather: a run-on value is dropped only before a defined field "with a value"; "only a run of dots may be shorter, when no digit follows it (`s..6` is not a field)" | c: gust 5, fields end, comment `077s..6` |
| B8 | s4202 fuzz | 1 | position lenient.diagnostics: same | 119262 | as B7 | c: `[warning:incomplete-weather, warning:weather-comment]` |
| B9 | s4202 fuzz | 1 | position strict.diagnostics: same | 119262 | as B7 | c: strict `incomplete-weather` |
| B10 | s4202 fuzz | 1 | mic-e lenient.data: five \| ts | 167059: `` 'C=?] \x1c#S]IO91/GPHG3330PH}#SlW1= `` | README Mic-E: a PHG "straight after a locator and its space" is lifted before a later altitude is looked for; this PHG follows the locator with no space (`missing-space-after-locator`) | Rule gap G2. Recommended: the five right (PHG 3330, comment `PH}#SlW1`, no altitude); ts changes |
| B11 | s4202 fuzz | 1 | mic-e lenient.diagnostics: same | 167059 | as B10 | ts: `[warning:missing-space-after-locator]` only |
| B12 | s4202 fuzz | 1 | mic-e written: same | 167059 | as B10 | ts: written `` 'C=?] \x1c#S]IO91/G PHG3330PH}#SlW1= `` |
| B13 | s4202 faults | 4 | position refusal: five \| c | 58292: uncompressed weather position, latitude 90.00008333, `wind_direction_degrees` Infinity | as B1 | c: `not-a-number` |
| B14 | s4202 faults | 1 | third-party refusal: cs+rs+ts+c+go \| py | 88111: inner uncompressed weather position with `altitude_feet` NaN | Refusal reasons: "A field with no place gets none of its checks" (an altitude on an uncompressed weather report has no place) | py: `field-not-allowed` |
| B15 | s4202 faults | 1 | object result: five refused \| py written | 90612: compressed GGA object, longitude 180.0, `altitude_feet` -Infinity | as B1 (the GGA altitude has a place in the cs bytes) | py: `refused`, `not-a-number` (py writes it, reading back an altitude of 1 ft) |
| B16 | s4202 frecipes | 61 | position refusal: cs+py+ts+c+go \| rs | 565: altitude in feet and metres, 236-byte comment | as B3 | as B3 |
| B17 | s4202 frecipes | 22 | object refusal: same | 3281 | as B3 | as B3 |
| B18 | s4202 frecipes | 21 | mic-e refusal: same | 3141: altitude in feet and metres, 256-byte comment | as B3 | as B3 |
| B19 | s4202 frecipes | 10 | item refusal: same | 27271 | as B3 | as B3 |

In B3 to B6 and B16 to B19 every one-unit build is refused only for its size (the five give `too-long` with the byte count). rs ranks a size `too-long` last (`outcome` and `is_size` in `aprs-rs/tests/vectors/build.rs`), and so gives `value-given-twice`.

## 2. Fix lists

Each list stands alone. Expected results are the record's `result` and `refusal` (encode, build) or the named decode fields.

### aprs-cs

1. Dump tool, build mode, a quantity in two units: when the one-unit builds are refused only for the 256-byte size, the record is `value-given-twice`. Revision A puts the size after every other check, so a size `too-long` ranks after `value-given-twice`. A field over its own limit (more than 5 analog values, message text over 67) keeps its place. cs needs a way to tell the two apart, for example a flag on the refusal, or the reason as rs does.
   - frecipes s4101 3001, position with `speed_knots` 10 and `speed_kmh` 18.52, `altitude_feet` 100 and `altitude_m` 30.48, 239-byte comment: `refused`, `value-given-twice` (cs: `too-long`, 282 bytes).
   - frecipes s4101 7169, Mic-E with `speed_kmh` 18.52 and `speed_knots` 10, 255-byte comment: `value-given-twice`.
   - frecipes s4202 565, position with `altitude_feet` 100 and `altitude_m` 30.48, 236-byte comment: `value-given-twice`.
2. Optional, to compare more records: section 5 (bulletin id, non-finite sequence and ambiguity).

### aprs-rs

No bucket. Optional, to compare more records: section 5 (symbol missing or malformed, inner path, Agrelo values, undecoded inner data, bulletin id, sequence, ambiguity).

### aprs-py

1. Dump tool, two units: as aprs-cs item 1. frecipes s4101 3001 and 7169, s4202 565: `value-given-twice`.
2. A field with no place gets none of its checks, inside a third-party packet too. faults s4202 88111, third-party with an inner uncompressed weather position (timestamp `092345z`, `/_`, weather values) and `altitude_feet` NaN: `refused`, `field-not-allowed` (py: `not-a-number`, "a weather report has no comment for an /A= altitude").
3. A compressed GGA altitude that is NaN or infinite is `not-a-number`, never written. faults s4202 90612, object `147.345`, compressed, compression `old`/`gga`, `altitude_feet` -Infinity: `refused`, `not-a-number` (py writes it, reading back an altitude of 1 ft).
4. Off-bucket: neutral data's empty string means absent (README data form: "empty strings ... are left out"). Constructed `t21.jsonl` line 0, `{"type":"telemetry","sequence":"","analog":[1,2,3,4,5],"bits":"00000000"}`: `missing-field` (py: `malformed`; cs, rs, c, go: `missing-field`). The generator never writes `""`, so no run shows it.
5. Off-bucket, whatever G3 rules: a fractional Agrelo bearing is not `not-a-number`. Constructed `t22.jsonl` line 1, `{"type":"agrelo-df","bearing_degrees":12.5,"quality":5}` (py: `not-a-number`, from a format error).

### aprs-ts

1. Dump tool, two units: as aprs-cs item 1. frecipes s4101 3001 and 7169, s4202 565: `value-given-twice`.
2. Mic-E, a PHG straight after the locator with the space missing is lifted before a later altitude is looked for (G2 as recommended). fuzz s4202 167059, `` 'C=?] \x1c#S]IO91/GPHG3330PH}#SlW1= ``, destination `SUSPU4`: locator `IO91`, `phg` power 3, height 3, gain 3, directivity 0, comment `PH}#SlW1`, no altitude, diagnostics `[warning:missing-space-after-locator]`, written `` 'C=?] \x1c#S]IO91/G PHG3330PH}#SlW1= `` (ts reads altitude `0PH}` and comment `PHG333#SlW1`).
3. Dump tool, encode: an empty string in neutral data is absent, not `unsupported`. Constructed `t21.jsonl` line 0 (`"sequence":""`): `missing-field` (ts: `unsupported`, "aprs-ts data has no sequence"); line 2 (position with `"comment":""`): `written` (ts: `unsupported`).

### aprs-c

1. `not-a-number` before every later code covers weather values too: wind direction, wind speed, gust and the other weather numbers, in cs bytes or `DDD/SSS`. Today c checks course, speed, range, altitude and NMEA fields first, but weather values only after the position's range.
   - faults s4101 7674, compressed weather position, longitude -180.0001, `wind_speed_mph` -Infinity: `not-a-number` (c: `value-out-of-range`).
   - faults s4101 39564, compressed weather object, longitude -180.0001, `wind_direction_degrees` -Infinity: `not-a-number`.
   - faults s4202 58292, uncompressed weather position, latitude 90.00008333, `wind_direction_degrees` Infinity: `not-a-number`. Also s4101 15879, 41075, 64768; s4202 4425, 29894.
2. Run-on weather value: `s..6` is not a field (a short run of dots with a digit after it), so it does not qualify as the defined field after a run (README Weather). fuzz s4202 119262, `!4903.50N/07201.75W_220/004g005077s..6`: weather `{wind_direction_degrees 220, wind_speed_mph 4, wind_gust_mph 5}`, comment `077s..6`, lenient `[warning:incomplete-weather, warning:weather-comment]`, strict `incomplete-weather` (c drops the gust with `out-of-range-value`).
3. Dump tool, two units: as aprs-cs item 1. frecipes s4101 3001 and 7169, s4202 565: `value-given-twice`.

### aprs-go

1. Dump tool, two units: as aprs-cs item 1. frecipes s4101 3001 and 7169, s4202 565: `value-given-twice`.
2. Optional, to compare more records: section 5.

Fix items: cs 1, rs 0, py 3 (and 2 off-bucket), ts 2 (and 1 tool fix), c 3, go 1.

## 3. Rule gaps

**G1. Two units against the size check.** The builder rule "One quantity, one value" tells a one-unit dump tool to report "the first code in that order among both results and `value-given-twice`". Revision A moved the size check after every other check, but the README order still lists `too-long` once, before `value-given-twice`. So the five tools read a size `too-long` as winning.
- Options: (a) a size `too-long` ranks after every code, `value-given-twice` included (rs); (b) keep the literal order (cs, py, ts, c, go).
- Recommend (a). Revision A says the size is "checked last ... after every other check". `value-given-twice` is a check on the input, so it applies first. Under (b), the same recipe would give a different code depending on whether the builder takes both units in one call or the tool builds twice.
- Wording, end of the Refusal reasons `too-long` sentence: "...; `too-long` for the information field's 256 bytes is given only when no other code applies, `value-given-twice` included." In "One quantity, one value", add: "a result refused only for the information field's size counts after `value-given-twice`". Add a build case in cases/builder.json: a position with `altitude_feet` 100 and `altitude_m` 30.48 and a comment that takes each one-unit build to 257 bytes, expecting `value-given-twice`.

**G2. A Mic-E PHG straight after a locator whose space is missing.** fuzz s4202 167059. The Mic-E rule lifts a PHG "straight after the type code, or straight after a locator and its space" before a later altitude is looked for. Here the PHG follows `IO91/G` with no space.
- Options: (a) a tolerated missing space reads as if the space were there, so the PHG is lifted first, and `0PH}` inside `PHG3330PH}` is never an altitude (cs, rs, py, c, go); (b) the literal text: no space, so the altitude search comes first, takes `0PH}`, and `PHG333#` is left as text (ts).
- Recommend (a). `missing-space-after-locator` is a tolerated defect, and a tolerated defect is read as if it were not there; the encoder writes the space back (the five re-encode `equivalent`). The rule's own reason applies unchanged: the PHG's bytes are never read as an altitude (`mic-e/phg-before-a-later-altitude`). It also keeps one reading for `IO91/G PHG...` and `IO91/GPHG...`.
- Wording, README Mic-E: "straight after a locator and its space, or straight after the locator when the space is missing (`missing-space-after-locator`)". Add the decode case `` 'C=?] \x1c#S]IO91/GPHG3330PH}#SlW1= `` (destination `SUSPU4`).

**G3 (minor, no run shows it). A fractional Agrelo bearing.** An Agrelo bearing is not in the Encoding rule's list of values rounded to their step. On `{"type":"agrelo-df","bearing_degrees":12.5,"quality":5}`, ts rounds and writes `%013/5`, py gives `not-a-number`, and cs, rs, c, go are unsupported. The generator only makes whole or out-of-range bearings, so no bucket. Recommend adding "an Agrelo bearing" to the list of values between steps that are rounded (it is degrees, like a course), so 12.5 is `013`; py's `not-a-number` is wrong whichever way this is ruled.

**Not gaps (checked):** the fixers' note on `c220s00420s004`. All six read the second `s` as snowfall, because the dropped speed counts as known, and so drop the run-on speed (`_10090556c220s00420s004g005t077`: snowfall 4, temperature 77, `out-of-range-value`). In a position report, `s00420s004` (snowfall, then snowfall again) keeps the 1.1.0 reading. Both agree with revision D read as "the run's own field", not its letter. Worth saying so in the Weather rule: "the run's own field (not its letter: after a wind speed, `s` is snowfall)".

## 4. Dump tool artefacts

1. The two-unit combination in the dump tools of cs, py, ts, c and go (B3 to B6, B16 to B19; G1). It is a dump-tool step in the README, so it is fixed in each tool. Each needs its library to say when a `too-long` is for the field's size.
2. aprs-ts `scripts/diff-dump.mjs` line 322: a neutral key whose value is an empty string is reported as lost (`unsupported`). By the data form an empty string is absent. Treat it so, except `reply_ack`, which is the one place an empty string means something.
3. aprs-c `tests/recipe.c` `text_item`: a NUL in builder text is passed as 0x01 because the builder takes C strings. This is acceptable: every rule that judges the text (`invalid-character`, `invalid-name`, `field-not-allowed` for text with no place) gives the same code for either byte, and the tool says so in a comment. Leave as is, but never use the stand-in for a `built` record (it cannot be built either way).

## 5. Unsupported records that could be compared

A record can be reported without being held when the input the library cannot hold has a code its value alone decides. For example: `not-a-number` for NaN or infinity, `value-out-of-range` for a sequence of -1 or an Agrelo quality of 10, `invalid-addressee` for a two-character bulletin id, `invalid-symbol` for an absent or one-character symbol. Then the honest procedure, in the library's neutral-form reader or the dump tool, is this. Build or encode the record with that input left out, or replaced by a valid stand-in. If that is refused with a code earlier in the Refusal reasons order than the input's own code, report it. Otherwise report the input's own code. This is exact because the left-out input cannot cause an earlier code, and any later fault, the size included, loses to it.
- **Comparable by that procedure** (all the large counts): rs's absent symbol (1,792 in faults, `invalid-symbol`); rs and go's symbol not a table and code (about 1,760, `invalid-symbol`); the bulletin id of two or more characters (cs, rs, go about 1,700 each, c about 870, `invalid-addressee`); rs and go's sequence outside 0-65535 (about 2,500, `not-a-number` or `value-out-of-range`); cs's non-finite sequence (about 1,140) and the non-finite ambiguity in cs and rs (about 270, `not-a-number`); rs and go's negative Agrelo bearing or quality (about 560, `value-out-of-range`, or `not-a-number` first when either is non-finite); py's ack or reject with a `message_id` (about 85, `field-not-allowed`, which all five others give).
- **Definite outright:** rs and go's third-party inner path entry that is not an address (about 975) is `invalid-third-party-header`. That is the first code an encode record can get unless its inner data is undecoded, which is `not-encodable`. rs and go's undecoded inner data (about 325) is `not-encodable`, the first code in the order. The README allows leaving it out, but it can be reported as refused at no cost.
- **Only honest answer is to leave it out:** none of the remaining top reasons. A fractional Agrelo bearing would be, until G3 is ruled.
