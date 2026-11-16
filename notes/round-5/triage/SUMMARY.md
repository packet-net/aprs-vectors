# Round 5 triage: six-way run s20101, s20202, s20303 (vectors 1490ec9)

Referee's verdicts for every difference bucket in fuzz, faults, data and rbdata, in all three seeds. Every bucket is explained by one of nine causes below. Library numbering: #1 aprs-cs, #2 aprs-rs, #3 aprs-py, #4 aprs-ts, #5 aprs-c, #6 aprs-go. Quotations are from aprs-vectors README.md at 1490ec9 unless marked. Counts are lines (records), per seed s20101 / s20202 / s20303. Per-library instructions with reproducers are in aprs-cs.txt, aprs-rs.txt, aprs-py.txt, aprs-ts.txt, aprs-c.txt, aprs-go.txt beside this file.

| Cause | Set | Lines | Verdict | Must change |
|---|---|---|---|---|
| A1 ts compares a held packet with itself through a rounding allowance | fuzz | 486 / 479 / 472 | decided: the five are right | aprs-ts |
| A2 inner packet of a five-deep nest, taken out and written on its own | fuzz | 101 / 89 / 91 | NEEDS RULING (proposal: the five) | aprs-ts if the proposal is taken |
| F1 aprs-c misses a non-finite number | faults | 130 / 139 / 122 | decided: the five are right | aprs-c |
| F2 a non-finite number in a field the report has no place for | faults | 94 / 99 / 105 | NEEDS RULING (proposal: not-a-number) | aprs-py, aprs-cs if the proposal is taken |
| F3 inner Mic-E destination check against an inner header fault | faults | 12 / 10 / 16 | NEEDS RULING (proposal: after the rule checks) | aprs-c, aprs-rs, aprs-go if the proposal is taken; aprs-py either way |
| F4 aprs-cs judges deeper data before an inner header | faults, data | 10 / 8 / 14 | decided: the five are right | aprs-cs |
| F5 rs and go tools: inner header fault before undecoded inner data | faults, data | 2 / 0 / 0 | decided: four are right | aprs-rs, aprs-go |
| F6 aprs-cs tool: undecoded data past the fourth level | faults, data | 1 / 0 / 2 | decided: the five are right | aprs-cs |
| R1 aprs-cs: Mic-E comment that cannot be written, wrong code | rbdata | 0 / 1 / 0 | decided: the five are right | aprs-cs |

Not a difference: the fuzz own-check "re-encoded bytes do not read back" (113 / 103 / 94) is given by all six alike on the same lines (decode records have no `rounded`, RULED "Open for a later round").

---

## A1. aprs-ts compares a held packet with itself through a rounding allowance

**Buckets** (all `#1+#2+#3+#5+#6 | #4`, or `#1+#2+#3+#6 | #4` where aprs-c left the line out for its limits): `[position]` api.tnc2 469 / 471 / 456, api.ax25_refusal 411 / 405 / 400, api.ax25 63 / 68 / 58, api.tnc2_refusal 1 / 2 / 1, api.tnc2 with #5 out 4 / 0 / 1; `[object]` api.tnc2 9 / 3 / 10, api.ax25_refusal 9 / 1 / 8, api.ax25 0 / 2 / 2; `[item]` api.tnc2 3 / 3 / 4, api.ax25_refusal 3 / 3 / 4. Lines: position 474 / 473 / 458, object 9 / 3 / 10, item 3 / 3 / 4.

**What happens.** aprs-ts's pass-through writers (R29) read the held information field back under the destination written and compare it with the held data using `sameData`, which is the encoder's comparison with its rounding allowance. For a compressed report it rounds the held value to the cs step, even when the value was read from comment text that holds it in whole units. So identical data compares unequal and ts refuses `not-encodable` (which also replaces `ax25-cannot-carry` where the path has a q-construct). All 1,405 position, object and item lines were replayed through ts's own `compareData(held, held)`: every one fails on a value compared with itself, `range_miles` (an `RNG` in the comment of a compressed report: 34 vs 34.49) or `weather.wind_direction_degrees` / `wind_speed_mph` (wind written after a compressed position: 358 vs 0, 103 vs 104).

**Examples.**
- `N0CALL>APZ001:!/5L!!<*e7>  CRNG0034` (built for this triage; same shape as the fuzz lines). Five: tnc2 the line as received, ax25 `82a0b4606062e09c60868298986103f0212f354c21213c2a65373e202043524e4730303334`. ts: both refused `not-encodable` ("range_miles would read back as 34, not 34.49...").
- `N0CALL>APZ001:!/0L!!<*e7_ !G358/005g010t070` (s20101 line 17903). Five: tnc2 the line as received, ax25 `82a0b4606062e09c60868298986103f0212f304c21213c2a65375f2021473335382f3030356730313074303730`. ts: both refused `not-encodable`.

**Rule.** Read-back: "A field's reading depends on its header only through a Mic-E report's destination ... nothing else in the data form reads the header", and "So a field paired with a header under which it reads as other data is refused as `not-encodable`". Here the field does not read as other data: the same bytes under the same non-Mic-E destination give exactly the held data. The allowance is "(1) a number its form holds in steps is compared with the value given rounded once ... to the step of the form written"; the form written carries `RNG0034` and `358/005` in whole units, so even read literally the allowance changes nothing. Decided: the five are right.

**Who changes.** aprs-ts: a held field read back under its header compares the read data with the held data exactly when the held data was decoded from those bytes (or rounds only to the step of the field the value is actually carried in).

**Cases to add.** `envelope/pass-through-compressed-position-with-a-range-in-the-comment` (input `N0CALL>APZ001:!/5L!!<*e7>  CRNG0034`, `pass_through` tnc2 the same, ax25_hex above) and `envelope/pass-through-compressed-weather-with-wind-in-the-comment` (input `N0CALL>APZ001:!/5L!!<*e7_  C090/005g010t070`, tnc2 the same, ax25_hex `82a0b4606062e09c60868298986103f0212f354c21213c2a65375f2020433039302f3030356730313074303730`).

## A2. The inner packet of a five-deep nest, taken out and written on its own

**Buckets** (`[third-party]`, `#1+#2+#3+#6 | #4` or `#1+#2+#3+#5+#6 | #4`): api.inner.tnc2 and api.inner.ax25 at each of the four inner depths, with their `_refusal` keys, about 25 buckets per seed. Lines 101 / 89 / 91. Every input has five or more `}`.

**What happens.** A decoder reads four levels; the fifth `}` is not read and that packet is `unrecognized` with `error:invalid-third-party`. The inner packet at level 1, taken out, has one `}` fewer, so read on its own its innermost level decodes (a status, say): its reading differs from the held data at the bottom level. ts reads it back, sees different data and refuses every inner level `not-encodable` (tnc2 and ax25). The five write each inner packet as received.

**Example.** `N0CALL>APZ001:}A>B:}A>B:}A>B:}A>B:}A>B:>hi`. Five: inner tnc2 `A>B:}A>B:}A>B:}A>B:}A>B:>hi`, inner ax25 `844040404040e08240404040406103f07d413e423a7d413e423a7d413e423a7d413e423a3e6869`, then `A>B:}A>B:}A>B:}A>B:>hi`, `A>B:}A>B:}A>B:>hi`, `A>B:}A>B:>hi` deeper. ts: every inner level refused `not-encodable`; the outer line is written by all six. Fuzz example: s20101 line 1816 (a long run of `}A>B:`).

**Rule.** NEEDS RULING. For writing as received: "A function that writes out a packet the program already holds ... writes its information field as received and is not an encoder, but the header it writes is read back"; R29 "The header changes a reading only through a Mic-E destination"; interpretations (four deep) "It re-encodes as received, like any third-party packet whose inner packet holds an error". For refusing: the Read-back rule lists "a pass-through, and a third-party inner header at every depth" among calls that decode the field under the header written, and "It compares the result with the data given", which fails here. Neither names this case, and if refusing were right the code would be `does-not-read-back` (no header is at fault), not `not-encodable`.

**Proposal.** Write as received (the five). The difference comes from the decoder's four-level horizon, which counts from wherever reading starts, not from the bytes or the header; the held bytes are the packet as received; refusing would make every inner packet of a deep nest unwritable for no fault of its own. Wording: "A held field read back under the header written is compared with the held data down to the level the held data reached; a level held as `unrecognized` for an unread fifth `}` matches whatever the field decodes to there on its own." Then aprs-ts changes. If the ruling is to refuse, the five change, with `does-not-read-back`.

**Case to add.** `envelope/pass-through-inner-packet-of-a-five-deep-nest`: input `N0CALL>APZ001:}A>B:}A>B:}A>B:}A>B:}A>B:>hi`, `pass_through_inner` tnc2 `A>B:}A>B:}A>B:}A>B:}A>B:>hi`, ax25_hex `844040404040E08240404040406103F07D413E423A7D413E423A7D413E423A7D413E423A3E6869` (per the proposal).

## F1. aprs-c misses a non-finite number

**Buckets** (`#1+#2+#3+#4+#6 | #5`): telemetry-coefficients 60 / 72 / 56 (c `too-long`), telemetry 35 / 41 / 35 (c `invalid-character` or `too-long`), mic-e 12 / 12 / 8, position 9 / 5 / 10, item 7 / 4 / 9, object 4 / 4 / 2 (c `too-long`, `value-out-of-range`, `invalid-symbol`, `invalid-code`, `invalid-character`, `value-has-no-form`), third-party 3 of 15 / 1 of 10 / 2 of 17 (the rest of those buckets is F3). Also aprs-c's half of the `| #3+#5` buckets listed under F2.

**What happens.** Either the count is checked before the values (16 `EQNS.` coefficients with a NaN among the first 15 gives `too-long`), or the non-finite value is a list item beyond what the C field holds (a sixth analog value) and is never seen, so a later code wins. All via the library, not the tool.

**Examples.**
- s20101 line 662: `{"type":"telemetry-coefficients","addressee":"ABCDEFGHI","coefficients":[1.0,1.0,1.0,1.0,-Infinity,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0]}`. Five: `not-a-number`. c: `too-long` ("there are at most 15 coefficients").
- s20101 line 813: `{"type":"telemetry","sequence":"A1","analog":[1,2,3,4,5,-Infinity],"bits":"10000000","comment":"a\rb"}`. Five: `not-a-number`. c: `invalid-character`.

**Rule.** Refusal reasons order: "`invalid-addressee`, `invalid-name`, `invalid-timestamp`, `not-a-number`, `value-out-of-range`, `value-has-no-form`, `invalid-code`, `invalid-symbol`, `invalid-character`, `too-long`, ..."; Read-back: "a non-finite number is `not-a-number` wherever it is, never compared as absent"; Comparing implementations: NaN or infinity is a code "its value alone decides" for an input the implementation cannot hold. Decided.

**Who changes.** aprs-c, library and dump tool.

**Cases.** JSON cannot carry NaN (README: "`not-a-number` (JSON cannot carry NaN or infinity)"), so no case can pin this today. Proposal for the vectors: let an encode case name non-finite values to plant after parsing (for example `"nonfinite": {"coefficients[4]": "-Infinity"}` beside `encode`); then add `encode/non-finite-coefficient-before-too-many-coefficients` and `encode/non-finite-sixth-analog-value-before-too-many-values`. Until then the `--faults --nonfinite` runs are the check.

## F2. A non-finite number in a field the report has no place for

**Buckets.** `#1+#2+#4+#5+#6 | #3` position 55 / 62 / 67, object 8 / 4 / 5; `#2+#4+#5+#6 | #1+#3` position 21 / 19 / 22, object 3 / 7 / 3; `#1+#2+#4+#6 | #3` and `#1+#2+#4+#6 | #3+#5` position 4 / 3 / 3, object 1 / 2 / 3; `#2+#4+#6 | #1+#3` position 1 / 1 / 0; third-party (inner data) 1 / 1 / 2. Lines 94 / 99 / 105.

**What happens.** Every one of these records carries weather data (`weather: {}` on `_` included, which the cases treat as a weather report with no fields), and the non-finite number is in a field a weather report has no place for: base-91 telemetry (sequence, a value, bits), `altitude_feet` on an uncompressed weather report, or a voice frequency. aprs-rs, aprs-ts, aprs-c and aprs-go give `not-a-number`. aprs-py skips every check of such a field and gives whatever the other faults give (`value-out-of-range` from a latitude, `extension-conflict`, `field-not-allowed`, `invalid-code`, `invalid-symbol`). aprs-cs does the same for an altitude or a frequency but gives `not-a-number` for telemetry, so it is inconsistent with itself.

**Examples.**
- s20202 line 2414: `{"type":"position","timestamp":"090541/","messaging":true,"latitude":49.05833333333333,"longitude":-72.02916666666667,"symbol":"/_","weather":{"wind_direction_degrees":360,"wind_speed_mph":232,"rain_24h_in":1.96,"rain_midnight_in":1.01,"snow_24h_in":0.62,"extra":[{"letter":"v","value":"-01"}]},"telemetry":{"sequence":8281,"analog":[NaN]},"ambiguity":1,"dao":{"datum":"W","precision":"thousandths"}}`. cs, rs, ts, c, go: `not-a-number`. py: `field-not-allowed`.
- s20101 line 5824: `{"type":"position","latitude":-62.69733333333333,"longitude":109.89566666666667,"symbol":"/_","weather":{"wind_direction_degrees":220,"wind_speed_mph":4,"wind_gust_mph":5,"temperature_f":77,"humidity_percent":50},"altitude_feet":NaN,"comment":"\n"}`. rs, ts, c, go: `not-a-number`. cs, py: `field-not-allowed`.

**Rule.** NEEDS RULING. For `not-a-number`: Read-back "a non-finite number is `not-a-number` wherever it is, never compared as absent"; Comparing implementations names NaN among inputs whose code "its value alone decides" and calls the stand-in procedure "exact, since the left-out input cannot cause an earlier code and any later fault loses to it". For skipping: Refusal reasons "A field the report has no place for is `field-not-allowed` and that field's own checks (range, characters, length) do not run", "A field with no place gets none of its checks: base-91 telemetry on a weather report is `field-not-allowed` however many values it has", and "NaN or an infinity is `not-a-number` at every check that also catches it" (no check runs, so none catches it).

**Proposal.** `not-a-number` wherever the number is, a field with no place included. Reasons: NaN is not a value of any field, so it is "a field wrong on its own"; libraries whose types cannot hold NaN refuse it at the reader before they know which fields have a place, and the Comparing-implementations rule already relies on its code being decided by the value alone; deciding "has a place" first is itself unsettled for records with several faults (weather data under a symbol that is not `_`, an invalid symbol beside weather), which the other reading would also have to rule on; four of six already do it. Wording, after "that field's own checks (range, characters, length) do not run": "a non-finite number in it is still `not-a-number`, decided by its value alone". Then aprs-py and aprs-cs change. If ruled the other way, aprs-rs, aprs-ts, aprs-c and aprs-go change, aprs-cs changes for telemetry, and the "value alone" sentence must be amended.

**Cases.** As F1, they need the non-finite planting form: `encode/non-finite-telemetry-on-a-weather-report`, `encode/non-finite-altitude-on-an-uncompressed-weather-report`.

## F3. The inner Mic-E destination check against an inner header fault

**Buckets.** `[third-party] #1+#2+#3+#4+#6 | #5` 12 of 15 / 9 of 10 / 15 of 17 (c `not-encodable`, via its tool); s20202 `#1+#3+#4 | #2+#5+#6` 1; s20303 `#1+#2+#4+#5+#6 | #3` 1. Lines 12 / 10 / 16.

**What happens.** Third-party data whose inner packet is Mic-E under destination `S32U6T`, with an invalid inner path (`["TC+IP*"]`, or `["TCPIP","G4ABC*"]` with an unmarked entry before a used one) and some inner data fault. Where the data computes another destination (latitude 90, longitude 180, an ambiguity), aprs-c's tool gives `not-encodable` ("Mic-E data reads as other data under a destination it does not compute"); the others give `invalid-third-party-header`. aprs-rs and aprs-go do as c on one record (s20202 line 58011, computed `Y0000P`) but not on the others. aprs-py gives `not-encodable` for a NaN longitude (s20303 line 94076), where no destination can be computed at all.

**Examples.**
- s20101 line 7532: `{"type":"third-party","packet":{"source":"N0CALL","destination":"S32U6T","data":{"type":"mic-e","mic_e_message":"returning","latitude":33.42733333333334,"longitude":180.0,"symbol":"/j","course_degrees":1,"speed_knots":0},"path":["TC+IP*"]}}`. cs, rs, py, ts, go: `invalid-third-party-header`. c: `not-encodable`.
- s20202 line 58011: `{"type":"third-party","packet":{"source":"N0CALL","destination":"S32U6T","data":{"type":"mic-e","mic_e_message":"returning","latitude":-90.0,"longitude":-12.129,"symbol":"/","course_degrees":251,"speed_knots":20},"path":["TC+IP*"]}}`. cs, py, ts: `invalid-third-party-header`. rs, c, go: `not-encodable`.
- s20303 line 94076 (inner `longitude: NaN`, path `["A*","B*"]`): cs, rs, ts, c, go `not-a-number`; py `not-encodable`.

**Rule.** NEEDS RULING. The Refusal reasons order puts `not-encodable` first, before `invalid-third-party-header`, and `encode/nested-third-party-ending-in-undecoded-data` pins that for undecoded inner data. But the destination mismatch is described as what the read-back finds ("It decodes the information field written ... under the header it is written with ... So a field paired with a header under which it reads as other data is refused as `not-encodable`"), and the Read-back rule says "Every rule check on the data comes before it, in the Refusal reasons order ... the read-back judges only data no rule refuses". No text says which place the mismatch takes.

**Proposal.** The destination comparison is part of the read-back, after every rule check: an inner header fault gives `invalid-third-party-header`, a field fault its own code, and the mismatch `not-encodable` only for data no rule refuses. Reasons: a computed destination exists only for data whose latitude, longitude, message and SSID pass their checks, so placing it first makes the code depend on whether faulty fields happen to compute (py's NaN case shows the trap); the existing case and every R29 case have no other fault; `not-encodable` first stays for data with "nothing the call can write" on its own (undecoded inner data). Wording, in Refusal reasons: "`not-encodable` for a field under a header where it reads as other data is the read-back's finding and comes after every rule check; for undecoded data it is first." Then aprs-c (tool) changes on all of these, aprs-rs and aprs-go on 58011. aprs-py's 94076 is `not-a-number` under either reading (a NaN longitude computes no destination), so py changes either way. If ruled "first, whenever the data computes a destination", cs, py and ts change on 58011 and on the c-alone records whose destination is computable.

**Case to add.** `encode/third-party-inner-mic-e-under-another-destination-with-a-bad-inner-path`: the data of `encode/third-party-inner-mic-e-under-another-destination` with `"path": ["TC+IP*"]` added to the inner packet; expected per the ruling (proposal: `invalid-third-party-header`).

## F4. aprs-cs judges deeper inner data before an inner header

**Buckets.** `[third-party] #2+#3+#4+#5+#6 | #1`: faults 10 / 8 / 13 (cs `invalid-character`, `invalid-timestamp`, `invalid-message-id`, `invalid-addressee`, `symbol-mismatch`, `field-not-allowed`, `text-reads-as-field`, `information-field-too-long`, `not-a-number`), data 0 / 0 / 1 (s20303 line 91387).

**What happens.** The first inner packet's header is invalid (path `["TCPIP","G4ABC*"]` or `["TC+IP*"]`, or no destination) and the data one level further down has a fault of its own; cs reports the deeper data's code.

**Examples.**
- s20303 data line 91387: `{"type":"third-party","packet":{"source":"AB","data":{"type":"third-party","packet":{"source":"A","destination":"B","data":{"type":"telemetry","sequence":"005","analog":[199,0,255,73,123],"bits":"01101001","comment":" hi\u0001"}}}}}`. Five: `invalid-third-party-header`. cs: `invalid-character`.
- s20101 faults line 3664: the first inner packet has path `["TCPIP","G4ABC*"]`, the next level `telemetry-names` holding `{5}`. Five: `invalid-third-party-header`. cs: `invalid-character` ("PARM. entries must not contain ',' or '{'").

**Rule.** Refusal reasons: "the refusal names the first code that applies in this order: `not-encodable`; `invalid-address`, `invalid-path`, `invalid-third-party-header`; `invalid-addressee`, ..." and "A header given that no form can be (an address that is not one, a path no line or frame reads back, a bad third-party header) comes first"; "Every rule check applies to a third-party packet's inner data, at every depth, exactly as to top-level data". The order is over the whole record. Decided.

**Who changes.** aprs-cs.

**Case to add.** `encode/third-party-inner-header-before-a-deeper-data-fault` (the 91387 record, `invalid-third-party-header`).

## F5. aprs-rs and aprs-go tools: an inner header fault before undecoded inner data

**Buckets.** `[third-party] #1+#3+#4+#5 | #2+#6`: faults 1 / 0 / 0 (s20101 line 66266), data 1 / 0 / 0 (s20101 line 16552).

**Example.** s20101 data line 16552: `{"type":"third-party","packet":{"source":"AB","data":{"type":"third-party","packet":{"source":"A","destination":"B","data":{"type":"third-party","packet":{"source":"A","destination":"B","data":{"type":"unrecognized","reason":"malformed"},"diagnostics":["error:invalid-third-party"]}}}}}}`. cs, py, ts, c: `not-encodable`. rs, go: `invalid-third-party-header` via tool ("the third-party packet has no destination").

**Rule.** Refusal reasons order (`not-encodable` first) and `encode/nested-third-party-ending-in-undecoded-data` ("not-encodable, first in the order"); Comparing implementations: for undecoded inner data a tool reports "that result's code if it is earlier in the Refusal reasons order than the input's own code, and the input's own code otherwise". Decided.

**Who changes.** aprs-rs and aprs-go dump tools.

**Case to add.** `encode/inner-header-without-a-destination-before-undecoded-data` (the 16552 record, `not-encodable`).

## F6. aprs-cs tool: undecoded data beyond the fourth level

**Buckets.** `[third-party] #2+#3+#4+#5+#6 | #1`: data 1 / 0 / 0 (s20101 line 43145), faults 0 / 0 / 2 (s20303 lines 19798, 84033).

**Example.** s20101 data line 43145: five third-party levels, the fifth holding `{"type":"unrecognized","reason":"malformed"}`. Five: `invalid-third-party-header` ("nest at most 4 deep"). cs: `not-encodable` via tool ("an unrecognized inner packet has nothing to encode").

**Rule.** README: "an encoder refuses data nested deeper as `invalid-third-party-header` ... neither a decoder nor an encoder recurses past the fifth level"; interpretations: "It counts the levels as it goes and stops at the fifth, so it never recurses further than a decoder does". The undecoded data is never reached, so the stand-in rule does not apply to it. Decided.

**Who changes.** aprs-cs dump tool.

**Case to add.** `encode/five-deep-nest-ending-in-undecoded-data` (the 43145 record, `invalid-third-party-header`).

## R1. aprs-cs: a Mic-E comment that no form can write gets the wrong code

**Bucket.** s20202 rbdata `[mic-e] refusal #2+#3+#4+#5+#6 | #1`, 1 line (100992).

**Example.** `{"type":"mic-e","mic_e_message":"en-route","latitude":51.5,"longitude":-0.5,"symbol":"/>","speed_knots":10,"comment":">5}"}`. Straight on, `>` reads as a type code (comment `5}`); after `/`, `/>5}` reads as a Mic-E altitude; after a space, the space reads as a type code. Five: `text-reads-as-field`. cs: `does-not-read-back` ("would read back as different data (type_code)"), taken from the last form tried.

**Rule.** Read-back: "The refusal is the code of the named rule whose fault the read-back caught, where one does, `text-reads-as-field` when free text reads back changed, and `does-not-read-back` otherwise"; Refusal reasons: "free text that reads back changed is `text-reads-as-field` ... and anything else is `does-not-read-back`". The comment is the only thing that cannot be written, and it reads back changed. Decided. (Wording note: the rule does not say which form's finding names the code; "the code of the first form tried" would make it explicit.)

**Who changes.** aprs-cs.

**Case to add.** `encode/mic-e-comment-reading-as-a-type-code-or-an-altitude` (this record, `text-reads-as-field`).
