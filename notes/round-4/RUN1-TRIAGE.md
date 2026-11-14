# Round 4, run 1: triage of the six-way differences

Run: `/tmp/r4run/run.sh 4101`, output in `/tmp/r4run/s4101/`. Library numbers as in compare.py: #1 cs, #2 rs, #3 py, #4 ts, #5 c, #6 go. "Line n" is the 0-based line of the set's input file, which is also the record's `n`. Verdicts follow the rule text in aprs-vectors `round-4` and the coordinator's rulings below, not the majority. Helpers in `/tmp/r4-triage/`: `get.py <set> <n>...` prints a line and the six records; `run6.sh <dump|encode|build> <file.jsonl>` runs all six dump tools on a small file.

Coordinator's rulings (after the first version of this file):
- **Size is the last check, on the bytes actually written.** A record any other check refuses gets that check's code. Only a record with no other fault, whose information field as written is over 256 bytes, is `too-long` for its size. A field over its own limit (message text over 67, a project title over 23, more than 5 analog values, more than 15 coefficients) keeps `too-long` at its existing place in the order. Nothing is measured hypothetically.
- G4: `value-has-no-form`. G5: `missing-field`. G6: wording made explicit as read here. G7: five empty channels. G3: the README order stands.

All 65 buckets are now decided: 65 library bugs, no open rule gap and no dump tool artefact. Section 4 lists two artefacts found outside the buckets. Under the size ruling the majority was wrong in all or part of 14 buckets (Z12, Z14, D2, D5, R7 in part, R1 in part, R10, F6, F7, F8, F10, F11, P15, P17).

## 1. Buckets

Split: the side named first in compare.py output | the other side. "Must change" names the libraries that must change.

| # | Set | Count | Split | Example (line: input, short) | Deciding rule | Verdict |
|---|---|---|---|---|---|---|
| Z1 | fuzz | 47 | position lenient.data: cs+rs+py+ts \| c+go | 14689: `!4540.62N/01212.52E_000/000g000t05700t057r000b10200h70v-01` | README Weather: a run-on value is dropped only when followed by "a defined field the run goes on to read (a letter APRS12c defines, not already read, with a value)"; the fields end "at a defined field already read"; the dropped value "counts as present" | c, go: a run followed by its own letter (`t05700t057`, `l00808L010`) keeps the 1.1.0 rule: `t057` read, fields end, `00t057r000...` is weather-comment |
| Z2 | fuzz | 47 | position lenient.diagnostics: same | 17654: `...t077l00808L010` | as Z1 | c, go: no `out-of-range-value`; luminosity 1008, comment `08L010` |
| Z3 | fuzz | 34 | weather lenient.data: cs+rs+py+ts \| c+go | 23516: `_10090556c220s004g005t42005t4294967295` | as Z1 | c, go: temperature_f 420, comment `05t4294967295` |
| Z4 | fuzz | 30 | weather lenient.diagnostics: same | 21208: `_09252040c...s...g...t075h58075h58b09970` | as Z1 | c, go: humidity 58, comment `075h58b09970` |
| Z5 | fuzz | 23 | weather strict.diagnostics: cs+py+ts+c+go \| rs | 38119: `_10090556c220s004g005t077h1234b101334b10132` | README "The order of checks": "a defect later in the packet never changes the diagnosis of one before it" | rs: strict must reject by `out-of-range-value` (the run-on `h1234`), as its own lenient reading has it; a later field of non-standard width must not stop the run qualifying |
| Z6 | fuzz | 21 | weather strict.diagnostics: cs+rs+py+ts \| c+go | 21208 (Z4) | as Z1 | c, go: strict `weather-comment` |
| Z7 | fuzz | 16 | position strict.diagnostics: cs+rs+py+ts \| c+go | 14689 (Z1) | as Z1 | c, go: strict `weather-comment` |
| Z8 | fuzz | 9 | mic-e reencode_refusal: cs+py+c+go \| rs+ts | 79: `` `:E9l!f[/">4D}Kenwood  TH-72 Op.Mustafa 73= `` | Ruled (G4): a Mic-E altitude with no type code whose first byte is a type code character is `value-has-no-form` | rs, ts right; cs, py, c, go change |
| Z9 | fuzz | 7 | object lenient.data: cs+rs+py+ts \| c+go | 63998: `;KC0QBU-13*252102z3855.18N/09440.66W_000/000g000t064r000p044000p044P045h72b10205` | as Z1 | c, go |
| Z10 | fuzz | 7 | object lenient.diagnostics: same | 6527 | as Z1 | c, go |
| Z11 | fuzz | 7 | position strict.diagnostics: cs+py+ts+c+go \| rs | 60570: `!4903.50N/07201.75W_220/004g005t2147483647r3647r000` | as Z5 | rs: strict `out-of-range-value` |
| Z12 | fuzz | 4 | capabilities reencode_refusal: rs+py+ts+go \| cs | 13152: `<C1,...,CMAND POS12,...` (259-byte field; token with a space) | Size rule (ruling): size is checked last, on bytes written; any other fault wins; a capability token with a space is `malformed` | cs right (`malformed`); rs, py, ts, go change |
| Z13 | fuzz | 3 | object strict.diagnostics: cs+rs+py+ts \| c+go | 69084: `;BRENDA   *092345z4903.50N/07201.75W_220/004g00504g005b0990` | as Z1 | c, go: strict `incomplete-weather` |
| Z14 | fuzz | 3 | capabilities reencode_refusal: rs+py+ts+go \| cs+c | 11989: `<C1,...,C320C33,...C5,,C51,...` (262 bytes) | as Z12 | cs, c right (`malformed`); rs, py, ts, go change |
| D1 | data | 6 | telemetry info: cs+py+ts+c+go \| rs | 55448: `{"type":"telemetry","sequence":"841","analog":[-5.40694e+75,1,255,null,0],"bits":"00110100"}` | Encoding, numbers given without their text: "the shortest decimal that reads back as the same number ... 1e61 as `1` and 61 zeros" | rs: `T#841,-540694` + 70 zeros + `,001,255,,000,00110100` (rs writes `-5406940000000000000006...`) |
| D2 | data | 2 | telemetry refusal: rs+py+ts+c+go \| cs | 48368: `{"type":"telemetry","sequence":"418","analog":[0,1.05886e+241,98.13,0,-1]}` (no bits) | Size rule (ruling): size is checked last, on bytes written; any other fault wins; no bits is `missing-field` | cs right (`missing-field`); rs, py, ts, c, go change |
| D3 | data | 1 | position refusal: cs+rs+py+ts+go \| c | 779: position, 229-byte comment holding `/A=001234` | Size rule (ruling): size is checked last, on bytes written; any other fault wins | c: `text-reads-as-field` (c gives `too-long`) |
| D4 | data | 1 | third-party info: cs+py+ts+c+go \| rs | 23559 (inner telemetry, 5.74043e+73) | as D1 | rs |
| D5 | data | 1 | third-party refusal: cs+rs+py+c+go \| ts | 81196: third-party, inner compressed item with an area (no place) and a 228-byte comment | Size rule (ruling): size is checked last, on bytes written; any other fault wins; a 7-byte extension on a compressed report is `field-not-allowed` | ts right (`field-not-allowed`); cs, rs, py, c, go change |
| R1 | recipes | 85 | object refusal: cs+py+ts+c \| rs+go | 1507: `object {"name":"TOOLONGNAME","latitude":-49.58,"longitude":-27.17,"altitude_m":1443.5}` (no symbol, no timestamp) | Refusal reasons order: `invalid-name`, ..., `value-has-no-form`, `invalid-code`, `invalid-symbol`, ..., `missing-field`; and the size rule | 83 lines: rs, go change (`invalid-name`, `value-has-no-form`; they give `invalid-symbol` first). 2 lines (30446, 75415: no timestamp, long comment): `missing-field`, rs, go right; cs, py, ts, c change (they give `too-long`) |
| R2 | recipes | 53 | status refusal: cs+py \| rs+go (ts unsupported, c builds) | 2295: `status {"symbol":"/-"}` | Ruled (G5): a status symbol with no locator is `missing-field` | rs, go right; cs, py change; ts must refuse, not mark unsupported |
| R3 | recipes | 53 | status result: cs+rs+py+go refused \| c built | 1: `status {"text":"Net Control Center","symbol":"/>"}`; c builds `>Net Control Center`, dropping the symbol | Ruled (G5) | c: `refused`, `missing-field` |
| R4 | recipes | 39 | mic-e refusal: cs+py+ts+c \| rs+go | 6384: `mic-e {"latitude":-90.0,"longitude":180.0}` | as R1 | rs, go: `value-has-no-form` |
| R5 | recipes | 24 | item refusal: cs+py+ts+c \| rs+go | 1026: `item {"name":"AB",...}` (no symbol) | as R1 | rs, go: `invalid-name` |
| R6 | recipes | 22 | telemetry tnc2: cs+py+ts+c+go \| rs | 8944: analog `[0,-2.36807e+73,999,999,1]` | as D1 | rs: `-236807` + 68 zeros |
| R7 | recipes | 21 | telemetry refusal: cs+py+ts+c+go \| rs | 16770: `telemetry {"analog":[null,1,1,1e+308,null],"bits":"10001011"}` (no sequence) | Size rule (ruling): size is checked last, on bytes written; any other fault wins; no sequence is `missing-field`; `invalid-character` is before `missing-field` | 11 lines with no other fault (16770, 18625, 32672, 44101, 54275, 61928, 64864, 69712, 78112, 81922, 90683): `missing-field`, rs right, cs, py, ts, c, go change. 10 lines with a control character (2648, 32664, 40858, 48636, 69078, 69080, 72174, 79356, 95789, 99949): `invalid-character`, rs changes |
| R8 | recipes | 15 | position refusal: cs+py+ts+c \| rs+go | 489: `position {"latitude":-61.0251231,"longitude":9.7028838,"course_degrees":0,"compressed":true}` | as R1 | rs, go: `value-has-no-form` |
| R9 | recipes | 13 | weather refusal: cs+py+ts+c \| rs+go | 962: `weather {"humidity_percent":0,"temperature_c":0}` | as R1 (`value-has-no-form` before `missing-field`) | rs, go: `value-has-no-form` |
| R10 | recipes | 4 | status refusal: rs+py+ts+c+go \| cs | 31978: status with timestamp, locator `IO91SX`, symbol, 245-byte text | Size rule (ruling): size is checked last, on bytes written; any other fault wins; a locator status has no timestamp: `field-not-allowed` | cs right; rs, py, ts, c, go change |
| R11 | recipes | 2 | object refusal: cs+rs+py+ts+c \| go | 26732: `object {"name":"  SPACED","latitude":-90.0,"longitude":-180.0,"symbol":"/l",...,"ambiguity":2}` | as R1 | go: `value-has-no-form` |
| F1 | faults | 376 | nmea refusal: cs+rs+py+ts+go \| c | 33: `{"type":"nmea","sentence":"gprmc,1","course_degrees":NaN,"comment":"a\rb"}` | Refusal reasons: `not-a-number` first among field checks; "NaN or an infinity is `not-a-number` at every check that also catches it" | c: `not-a-number` |
| F2 | faults | 59 | position refusal: cs+rs+py+ts+go \| c | 7406: compressed GGA weather position, `altitude_feet` NaN | as F1 | c |
| F3 | faults | 21 | object refusal: same | 325 | as F1 | c |
| F4 | faults | 16 | item refusal: same | 105 | as F1 | c |
| F5 | faults | 14 | position refusal: rs+py+ts+c+go \| cs | 5380: uncompressed weather, latitude -90.00008333, `altitude_feet` NaN, telemetry | Refusal reasons: "A field with no place gets none of its checks" (an altitude on an uncompressed weather report has no place) | cs: `value-out-of-range` (667, 3284: `field-not-allowed`) |
| F6 | faults | 14 | telemetry refusal: rs+py+ts+go \| cs+c | 6027: sequence `A B`, 4 values, 264-byte comment | Size rule (ruling): size is checked last, on bytes written; any other fault wins; a bad sequence, 4 values or bad bits are `malformed` | cs, c right (`malformed`); rs, py, ts, go change |
| F7 | faults | 7 | telemetry refusal: rs+py+ts+go \| cs | 9001: `{"sequence":"12,3","analog":[1e+308,1,0.25,147,-1],"bits":"000000000"}` | as F6 | cs right (`malformed`); rs, py, ts, go change |
| F8 | faults | 3 | telemetry refusal: rs+ts+go \| c (cs, py unsupported) | 87076: no sequence, 4 values, 246-byte comment | as F6 (`malformed` is before `missing-field`) | c right (`malformed`); rs, ts, go change |
| F9 | faults | 3 | third-party refusal: cs+rs+py+ts+go \| c | 43836: inner nmea, latitude -Infinity, comment `a\rb` | as F1 | c: `not-a-number` |
| F10 | faults | 2 | item refusal: rs+py+ts+c+go \| cs | 47461: item with storm data, area, `!DAO!` on ambiguity 2, 300-byte comment | Size rule (ruling): size is checked last, on bytes written; any other fault wins; storm with an area is `extension-conflict`, before `field-not-allowed`. 58074: F5 rule | 47461: cs right (`extension-conflict`), rs, py, ts, c, go change. 58074: cs changes (`field-not-allowed`) |
| F11 | faults | 1 | object refusal: rs+py+ts+go \| cs+c | 17042: object, base-91 telemetry with no values | as F6 | cs, c right (`malformed`); rs, py, ts, go change |
| F12 | faults | 1 | position refusal: py+ts+c+go \| cs (rs unsupported) | 18284: weather position, no symbol, `altitude_feet` -Infinity | as F5 | cs: `invalid-symbol` |
| F13 | faults | 1 | mic-e refusal: cs+rs+ts+c+go \| py | 35223: Mic-E with PHG and RNG, `!DAO!` on ambiguity 3, 222-byte comment | Size rule (ruling): size is checked last, on bytes written; any other fault wins; PHG and RNG together are `extension-conflict` | py changes (`extension-conflict`) |
| F14 | faults | 1 | position refusal: cs+rs+py+ts+go \| c | 41650: longitude -180.0001, `speed_knots` -Infinity | as F1 | c |
| F15 | faults | 1 | position result: five refused \| c written | 59598: compressed GGA weather, `altitude_feet` Infinity | as F1 | c: refuse `not-a-number` (c writes cs bytes `{{` for an infinite GGA altitude, on any compressed report) |
| P1 | frecipes | 2,222 | position refusal: cs+py+ts+c \| rs+go | 1: `position {"latitude":74.65,"longitude":45.04,"comment":"73]Hello","speed_kmh":-1,"altitude_feet":999999.5}` | as R1 | rs, go: `value-out-of-range` |
| P2 | frecipes | 1,100 | mic-e refusal: same | 12: `mic-e {"latitude":Infinity,"longitude":180.00001,"altitude_feet":999999.4}` | as R1 | rs, go: `not-a-number` |
| P3 | frecipes | 996 | object refusal: same | 57 (`value-out-of-range`), 1094 (no timestamp: `value-out-of-range`, rs/go `missing-field`) | as R1 | rs, go |
| P4 | frecipes | 474 | item refusal: same | 213: `item {"name":"LEADER","latitude":8.8943668,"longitude":-180.00001,"speed_knots":-0.5}` | as R1 | rs, go: `value-out-of-range` |
| P5 | frecipes | 281 | weather refusal: same | 460 (no timestamp, wind direction -0.5) | as R1 | rs, go: `value-out-of-range` |
| P6 | frecipes | 230 | mic-e refusal: cs+rs+py+ts+c \| go | 578: `mic-e {...,"altitude_feet":-99999.5,"speed_kmh":-Infinity}` | as F1 | go: `not-a-number` |
| P7 | frecipes | 132 | telemetry refusal: cs+py+ts+c+go \| rs | 1300: `telemetry {"bits":"0000000x","comment":"a\rb"}` | as R7 | rs: `invalid-character` |
| P8 | frecipes | 104 | telemetry refusal: cs+py+ts+go \| rs | 332: `telemetry {"analog":[1,2,3,4,5,6],"bits":"0000000"}` | Refusal reasons: more than 5 values is `too-long`, before `missing-field` | rs: `too-long` |
| P9 | frecipes | 84 | position refusal: cs+rs+py+ts+go \| c | 2638: `position {...,"longitude":-180.00001,"speed_kmh":Infinity,...}` | as F1 | c: `not-a-number` |
| P10 | frecipes | 24 | object refusal: same | 3983 | as F1 | c |
| P11 | frecipes | 14 | item refusal: same | 10382 | as F1 | c |
| P12 | frecipes | 9 | object refusal: cs+rs+py+ts+c \| go | 21622: object `TOOLONGNAME`, no timestamp | as R1 | go: `invalid-name` (6669: `not-a-number`; 30610: `value-has-no-form`) |
| P13 | frecipes | 4 | position refusal: cs+py+ts \| rs+go (c unsupported) | 26624 | as R1 | rs, go: `not-a-number` |
| P14 | frecipes | 4 | item refusal: same | 40007 | as R1 | rs, go: `value-out-of-range` |
| P15 | frecipes | 3 | telemetry refusal: rs+py+ts+go \| cs | 25223: sequence 921, 4 values, bits `0000000`, 228-byte comment | as F6 | cs right (`malformed`); rs, py, ts, go change |
| P16 | frecipes | 2 | mic-e refusal: cs+py+ts \| rs+go | 3180 | as R1 | rs, go: `value-out-of-range` |
| P17 | frecipes | 2 | telemetry refusal: rs+py+ts+go \| cs+c | 24887: bits `0000000`, 249-byte comment | as F6 | cs, c right (`malformed`); rs, py, ts, go change |
| P18 | frecipes | 1 | mic-e refusal: cs+rs+py+ts \| go | 15645: latitude NaN, altitude_m -30480.2 | as F1 | go: `not-a-number` |
| P19 | frecipes | 1 | item refusal: cs+py+ts \| rs+go \| c | 30786: latitude -90.00001, course Infinity, no symbol | as F1 and R1 | rs, go, c: `not-a-number` |
| P20 | frecipes | 1 | position refusal: cs+py+ts \| rs+go \| c | 57333: longitude 180.00001, course NaN, no symbol | as F1 and R1 | rs, go, c: `not-a-number` |

## 2. Fix lists

Each list stands alone. Inputs are quoted short; the full line is `python3 /tmp/r4-triage/get.py <set> <n>`. The expected result is the record's `result` and `refusal` (encode, build) or the decode fields named.

### aprs-cs

1. **Size is the last check, on the bytes written; remove any measuring of a faulty record.** Today cs measures before `field-not-allowed` and `missing-field` in places: the builder counts a `000,` sequence that was not given, an inner third-party field counts its area bytes, and an object with no timestamp is measured first.
   - recipes 18625, `telemetry {"analog":[1,1e+225,12.5,999,1],"bits":"11001000"}` (no sequence): `refused`, `missing-field` (cs: `too-long`). Also recipes 16770, 69712, 81922.
   - recipes 30446, object `NINECHARS` with no timestamp and a long comment: `missing-field` (cs: `too-long`). Also 75415.
   - data 81196, third-party, inner compressed item with an area: `field-not-allowed` (cs: `too-long`).
   - Already right, keep: fuzz 13152 `malformed`, data 48368 `missing-field`, recipes 1803 `field-not-allowed`, faults 6027 and 9001 `malformed`, 47461 `extension-conflict`.
2. A field the report has no place for gets none of its checks, so no `not-a-number` on it (README Refusal reasons: "A field with no place gets none of its checks").
   - faults 5380, uncompressed weather position, latitude -90.00008333, `altitude_feet` NaN: `value-out-of-range`.
   - faults 667, weather position, comment `x !W12!`, `altitude_feet` -Infinity: `field-not-allowed`. Also 58074.
   - faults 18284, weather position with no symbol, `altitude_feet` -Infinity: `invalid-symbol`.
3. Mic-E altitude with no type code whose first byte is a type code character: `value-has-no-form` (ruling G4). fuzz 79, `` `:E9l!f[/">4D}Kenwood  TH-72 Op.Mustafa 73= ``: `reencode_refusal` `value-has-no-form` (cs: `text-reads-as-field`). Also fuzz 29151.
4. A status symbol with no locator is `missing-field` (ruling G5). recipes 2295, `status {"symbol":"/-"}`: `missing-field` (cs: `field-not-allowed`). Also recipes 1.

### aprs-rs

1. **Size is the last check, on the bytes written; remove any measuring of a faulty record.** Today rs measures before every later code: it gives `too-long` ahead of `malformed`, `missing-field`, `extension-conflict` and `field-not-allowed`, and counts a no-place timestamp and area bytes.
   - fuzz 13152, `<C1,...,CMAND POS12,...` (259 bytes): `reencode_refusal` `malformed` (rs: `too-long`). Also fuzz 11989.
   - data 48368, telemetry sequence 418, analog `[0,1.05886e+241,98.13,0,-1]`, no bits: `missing-field`.
   - recipes 1803, status with timestamp, locator `IO91`, symbol and 248-byte text: `field-not-allowed`.
   - faults 47461, item with storm data and an area: `extension-conflict`. faults 6027 (sequence `A B`): `malformed`. frecipes 25223 (bits `0000000`): `malformed`. data 81196: `field-not-allowed`.
   - Keep `too-long` for a field over its own limit: frecipes 332, `{"analog":[1,2,3,4,5,6],"bits":"0000000"}`: `too-long`.
2. Builder refusal order (README Refusal reasons; builder rule "Refusal order"): an absent symbol is `invalid-symbol`, and an absent object or positionless-weather timestamp or telemetry sequence is `missing-field`, each at its own place in the order, not checked first.
   - recipes 1507, `object {"name":"TOOLONGNAME","latitude":-49.58,"longitude":-27.17,"altitude_m":1443.5}`: `invalid-name`.
   - recipes 962, `weather {"humidity_percent":0,"temperature_c":0}`: `value-has-no-form`.
   - frecipes 1300, `telemetry {"bits":"0000000x","comment":"a\rb"}`: `invalid-character`; recipes 2648 likewise.
   - Keep `missing-field` where nothing earlier applies: recipes 16770, 18625, 30446 stay `missing-field`.
3. Big numbers written without their text: shortest round-trip digits, then zeros (Encoding, numbers given without their text).
   - data 55448: `T#841,-540694` + 70 zeros + `,001,255,,000,00110100`.
   - recipes 7187: analog `2.38662e+131` is `238662` + 126 zeros. recipes 8944: `-2.36807e+73` is `-236807` + 68 zeros.
4. Strict weather: a run-on value followed by a defined field with a value is `out-of-range-value` in strict too, whatever the later field's width (README "The order of checks": a later defect never changes the diagnosis of an earlier one). Lenient is already right.
   - fuzz 38119, `_10090556c220s004g005t077h1234b101334b10132`: strict `out-of-range-value` (rs: `weather-comment`).
   - fuzz 60570, `!4903.50N/07201.75W_220/004g005t2147483647r3647r000`: strict `out-of-range-value`.
   - fuzz 38321, `_10090556c22000s4g005t2147483647X12`: strict `out-of-range-value` (rs: `incomplete-weather`).
5. Neutral telemetry with no `sequence` is `missing-field`, not `malformed` (README "Absent text is empty text": only name, addressee, query type and symbol read as empty). Off-bucket: faults 2731, `{"type":"telemetry","analog":[-1,null,0.25,0,0],"comment":"¥2"}`: `missing-field` (rs: `malformed`). Also faults 13318, 14282.

### aprs-py

1. **Size is the last check, on the bytes written; remove any measuring of a faulty record.** Today py measures before every later code, counting the fields as given, a no-place timestamp and area bytes, both conflicting extensions, and a `000,` sequence the builder was not given.
   - faults 35223, Mic-E with PHG and RNG: `extension-conflict` (py: `too-long`).
   - recipes 18625, `telemetry {"analog":[1,1e+225,12.5,999,1],"bits":"11001000"}`: `missing-field`. Also 30446 (object, no timestamp): `missing-field`.
   - recipes 1803 (status with a timestamp beside a locator): `field-not-allowed`. data 48368 (no bits): `missing-field`. fuzz 13152: `reencode_refusal` `malformed`. faults 6027: `malformed`. faults 47461: `extension-conflict`. data 81196: `field-not-allowed`.
2. A status symbol with no locator is `missing-field` (ruling G5). recipes 2295, `status {"symbol":"/-"}`: `missing-field` (py: `field-not-allowed`).
3. Mic-E altitude with no type code whose first byte is a type code character: `value-has-no-form` (ruling G4). fuzz 79 and 29151: `reencode_refusal` `value-has-no-form`.

### aprs-ts

1. **Size is the last check, on the bytes written; remove any measuring of a faulty record.** Today ts measures before `malformed`, `missing-field` and `extension-conflict`, counts a no-place timestamp and a `000,` sequence the builder was not given. It already leaves an area on a compressed report out (data 81196 `field-not-allowed` is right).
   - fuzz 13152: `reencode_refusal` `malformed`. data 48368: `missing-field`.
   - recipes 1803: `field-not-allowed`. recipes 18625: `missing-field`. recipes 30446: `missing-field`.
   - faults 6027: `malformed`. faults 47461: `extension-conflict`.
2. Neutral telemetry with no `sequence` is `missing-field`, not `malformed`. Off-bucket: faults 2731: `missing-field` (ts: `malformed`).
3. Status locator and symbol must be given apart in the builder (ruling G5; README "a status symbol beside a locator"): a locator without a symbol, and a symbol without a locator, are both `refused`, `missing-field`, not `unsupported` (3,349 and 19 frecipes records, 66 and 54 recipes records today). recipes 2295, `status {"symbol":"/-"}`: `missing-field`.

### aprs-c

1. A run-on weather value followed by its own field's letter (`t05700t057`, `l00808L010`, `g00504g005`) keeps the 1.1.0 rule: that field is already read (README Weather, wording made explicit by ruling G6).
   - fuzz 17654, `!4903.50N/07201.75W_220/004g005t077l00808L010`: weather adds `luminosity_w_m2` 1008, comment `08L010`, lenient `[warning:weather-comment]`, strict `weather-comment`.
   - fuzz 23516, `_10090556c220s004g005t42005t4294967295`: `temperature_f` 420, comment `05t4294967295`, `[info:obsolete-format, warning:weather-comment]`, strict `weather-comment`.
   - fuzz 69084, `;BRENDA   *092345z4903.50N/07201.75W_220/004g00504g005b0990`: strict `incomplete-weather`.
2. `not-a-number` is checked before every later code (README Refusal reasons; "NaN or an infinity is `not-a-number` at every check that also catches it"). It beats `value-out-of-range`, `invalid-character`, `invalid-code`, `invalid-symbol`, `invalid-nmea`, `extension-conflict` and `field-not-allowed` of other fields. A compressed GGA altitude that is NaN or infinite is refused, never written as cs bytes `{{`.
   - faults 33, `{"type":"nmea","sentence":"gprmc,1","course_degrees":NaN,"comment":"a\rb"}`: `not-a-number` (c: `invalid-character`).
   - faults 41650, position, longitude -180.0001, `speed_knots` -Infinity: `not-a-number` (c: `value-out-of-range`).
   - faults 59598, compressed GGA weather, `altitude_feet` Infinity: `refused`, `not-a-number` (c: written). frecipes 2638 (`speed_kmh` Infinity): `not-a-number`.
3. **Size is the last check, on the bytes written; remove any measuring of a faulty record.** Today c checks the size after encoding but lets `too-long` override the deferred refusal (`encode.c` `pdn_aprs__encode_data`), and it counts a no-place timestamp and area bytes, and a `000,` sequence the builder was not given. It already gives `malformed` before size (Z14, F6, F8, F11, P17 are right).
   - data 779, position with a 229-byte comment holding `/A=001234`: `text-reads-as-field` (c: `too-long`).
   - data 48368: `missing-field`. recipes 1803: `field-not-allowed`. recipes 18625: `missing-field`. recipes 30446: `missing-field`. data 81196: `field-not-allowed`. faults 47461: `extension-conflict`.
4. The status builder must not drop a symbol given without a locator (ruling G5). recipes 1, `status {"text":"Net Control Center","symbol":"/>"}`: `refused`, `missing-field` (c: built `>Net Control Center`).
5. Neutral telemetry with no `sequence` is `missing-field`, not `malformed` ("needs a sequence"). Off-bucket: faults 2731: `missing-field`.
6. Mic-E altitude with no type code whose first byte is a type code character: `value-has-no-form` (ruling G4). fuzz 79 and 29151: `reencode_refusal` `value-has-no-form` (c: `text-reads-as-field`).

### aprs-go

1. A run-on weather value followed by its own field's letter keeps the 1.1.0 rule (ruling G6). fuzz 17654: luminosity 1008, comment `08L010`, strict `weather-comment`. fuzz 23516: `temperature_f` 420, comment `05t4294967295`. fuzz 69084: strict `incomplete-weather`.
2. Builder refusal order: an absent symbol is `invalid-symbol` and an absent timestamp `missing-field`, each at its place, not first. recipes 1507: `invalid-name`. recipes 962: `value-has-no-form`. recipes 26732 (`object {"name":"  SPACED","latitude":-90.0,"longitude":-180.0,...,"ambiguity":2}`, no timestamp): `value-has-no-form` (go: `missing-field`). frecipes 21622 (`TOOLONGNAME`, no timestamp): `invalid-name`. Keep `missing-field` where nothing earlier applies (recipes 30446).
3. Builder: `not-a-number` before range checks. frecipes 578, `mic-e {...,"altitude_feet":-99999.5,"speed_kmh":-Infinity}`: `not-a-number` (go: `value-out-of-range`). frecipes 15645 (latitude NaN): `not-a-number`. frecipes 6669 (object, `altitude_m` -Infinity, no timestamp): `not-a-number` (go: `missing-field`).
4. **Size is the last check, on the bytes written; remove any measuring of a faulty record.** Today go measures before `malformed`, `missing-field`, `extension-conflict` and `field-not-allowed`, and counts a no-place timestamp and area bytes.
   - fuzz 13152: `reencode_refusal` `malformed`. data 48368: `missing-field`. recipes 1803: `field-not-allowed`.
   - faults 47461: `extension-conflict`. faults 6027: `malformed`. frecipes 25223: `malformed`. data 81196: `field-not-allowed`.
   - Keep `too-long` for a field over its own limit: frecipes 332 (six analog values): `too-long`.
5. Neutral telemetry with no `sequence` is `missing-field`, not `malformed`. Off-bucket: faults 2731: `missing-field`.
6. Mic-E altitude with no type code whose first byte is a type code character: `value-has-no-form` (ruling G4). fuzz 79 and 29151.

Fix items: cs 4, rs 5, py 3, ts 3, c 6, go 6.

## 3. Rule gaps

All ruled. What remains is wording for aprs-vectors.

- **G1** (a left-out field's delimiter in the size): superseded by the size ruling; nothing is measured hypothetically.
- **G2** (do two conflicting extensions both count): superseded by the size ruling; `extension-conflict` wins (F13).
- **G3** (`invalid-symbol` and `missing-field` against `invalid-name` and `value-has-no-form`): ruled, the README order stands; rs and go change.
- **G4** (Mic-E altitude with no type code whose first byte is a type code character; Z8): ruled `value-has-no-form`. Wording: replace the Refusal reasons parenthetical "(whole metres, beyond the 6 digits of a `/A=`)" with "(a value no `/A=` holds exactly: not a whole number of feet, or beyond its 6 digits)". Add the decode case `` `:E9l!f[/">4D}Kenwood `` with `reencode_refusal` `value-has-no-form`.
- **G5** (builder status with a symbol and no locator; R2, R3): ruled `missing-field`. Wording, the `missing-field` list in Refusal reasons: "a status symbol beside a locator, or a locator beside a status symbol".
- **G6** (run-on value followed by its own letter; Z1 to Z4, Z6, Z7, Z9, Z10, Z13): ruled as read here. Wording, Weather: "...a letter APRS12c defines, not already read (the run's own field is read), with a value...". Add the case `_10090556c220s004g005t42005t4294967295` (temperature 420, comment `05t4294967295`).
- **G7** (builder telemetry with no analog values): ruled, five empty channels. Wording, Defaults: "a telemetry report given no analog values writes five empty channels" (`T#001,,,,,,00000000`); all six already do.
- **G8** (third-party size against the inner packet's later faults): superseded by the size ruling; the inner fault's code wins.
- New wording needed for the size ruling itself, in Encoding and Refusal reasons: `too-long` for the 256-byte field is given only when no other code applies, on the bytes written. Cases `encode/info-size-before-missing-field`, `encode/invalid-symbol-before-info-size`, `encode/info-size-before-field-not-allowed` and `encode/field-without-a-place-makes-no-bytes` need their expectations or names revised.

## 4. Dump tool artefacts

None of the 65 buckets is caused by a dump tool. Found outside them:

1. aprs-c `tools/diffdump.c` about line 847: a bulletin `id` that is not one character returns `PDN_APRS_ERR_REFUSED` with no refusal code (frecipes: 1,778 records `{"result":"refused","reason":"the encoder refuses this data"}`). compare.py compares `refusal` only among dumps that write it, so these were silently counted as agreeing. Fix: pass `id` `""` as 0, which the builder refuses as `invalid-addressee`; write `unsupported` for two or more characters, as cs, rs and go do.
2. aprs-c dump tool, encode: "extra has more fields than the C data holds" (data 4, faults 4) and "text is longer than the C field holds" (data 1) are written `unsupported`; they are capacities (8 extra weather fields, 512-byte field), so `implementation-limit` with a reason (README Encode records).
3. aprs-cs and aprs-ts dump tools write `n` as the line index, not the input's `n`. This does no harm on whole generated files, but breaks subset reruns. Echo the input's `n`.
4. Low priority, no effect seen: rs (`diff_dump.rs` `unwrap_or_default` on text, project), py (`args.get("text", "")`) and cs (`?? ""`) still fill absent text with an empty string. Absent and empty text build the same bytes, but IMPLEMENT item 4 says pass only the keys given.

## 5. Unsupported (left out, so not compared)

Counts are from run 1. "Cheap" means the library can already express the record, or should refuse it with a proper code at its place in the order.

| Lib | Set | Reason | Count | Verdict |
|---|---|---|---|---|
| cs | faults | telemetry with no `sequence` cannot be held | 590 | Medium: let the data hold an absent sequence; the encoder refuses `missing-field` at its place (others then check against it; rs, ts, c, go give `malformed` today, wrongly). |
| cs | frecipes | bulletin id not one character | 1,778 | Medium: take the id as text and refuse `invalid-addressee` (py, ts do). |
| cs | frecipes | sequence NaN or infinite | 1,140 | Medium: take a double; `not-a-number`, which is early in the order. |
| cs | frecipes | ambiguity NaN or infinite | 268 | As above. |
| rs, go | faults | symbol not a table and a code (`/`) | 1,779 | Cheap: hold the text and refuse `invalid-symbol` at its place (py, ts do). |
| rs | faults | symbol missing | 1,733 | Cheap: absent symbol is `invalid-symbol` ("Absent text is empty text"). |
| rs, go | faults | inner path entry not an address (`TC+IP*`) | 972 | Cheap: `invalid-third-party-header` (ts, c do). |
| rs, go | data, faults | third-party with undecoded inner data | 560, 357 | Allowed: README says not every library's data can hold it. Keep. |
| rs, go, c | faults | Agrelo bearing or quality negative | 351 + 195 (c 353 + 198) | Cheap: a signed field, then `value-out-of-range`. |
| rs, go | frecipes | sequence outside 0-65535 (-1, NaN, Infinity) | 2,456 | Medium: take a wider or float type; refuse `value-out-of-range` or `not-a-number`. |
| rs, go | frecipes | bulletin id not one character | 1,778 | As cs. |
| rs | frecipes | ambiguity non-finite | 268 | As cs. |
| py | faults | telemetry with no `sequence` (`TelemetryReport` requires it) | 590 | Cheap: make it optional; `missing-field`. |
| py | faults | ack or reject with a `message_id` (message-id-on-ack) | 77 | Cheap: the data form has it; add the field. |
| ts | recipes, frecipes | status locator without symbol | 66, 3,349 | Cheap: make `locator()`'s symbol optional and refuse `missing-field` (the rule: "a status symbol beside a locator"). |
| ts | recipes, frecipes | status symbol without locator | 54, 19 | Cheap, with G5: refuse `missing-field`. |
| c | faults | timestamp longer than the C field (`00010000` on a status) | 1,831 | Cheap: it is not a valid timestamp: `invalid-timestamp`. |
| c | faults | symbol not two characters | 1,785 | Cheap: `invalid-symbol`. |
| c | faults | bits longer than the C field (`000000000`) | 602 | Cheap: `malformed`. |
| c | recipes, frecipes | comment or text holding NUL | 405, 292 | Medium: a length-taking setter; `invalid-character`. |
| c | frecipes | analog not five values | 2,241 | Cheap: take a count; more is `too-long`, fewer `malformed`. |
| c | frecipes | sequence out of range, or not finite | 892 + 724 | Medium: take a wider or float type. |
| c | frecipes | ambiguity non-finite | 268 | As cs. |

Largest wins for comparison coverage: ts locator (3,349), c analog count (2,241), rs and go sequence (2,456), the bulletin id in cs, rs and go (1,778 each), and the c and rs/go symbol text (about 1,780 each).
