# Refusal reason codes (1.0.1)

Decision 5, option C: a shared, machine-readable list of the reasons an encoder or builder refuses, in the vectors, used by all five libraries. Additive only: the refusal type, its message text and every 1.0 signature stay as they are.

Inventory: about 1,000 rows over the five libraries (cs 179, rs 183, py 191, ts 225, C 213), from reading every refusal site in the encoders, builders, packet creation and AX.25 writing, plus the 58 `expect.refused` encode cases and the 289 decode cases with `reencode: "refused"`. MAP.md gives each row its code.

## The list

One code per rule a program could act on differently. 26 codes; the last is the fallback.

| id | meaning |
|---|---|
| `invalid-address` | A header address (source, destination, path entry, or a third-party one) is not 1-9 letters, digits or `-` in TNC2 text. |
| `ax25-cannot-carry` | An AX.25 frame cannot carry the header: a call over 6 characters or in lower case, an SSID over 15 or written with a leading zero, more than 8 path entries. |
| `tnc2-cannot-carry` | A TNC2 line cannot carry the packet: its information field is not UTF-8 text. |
| `invalid-third-party-header` | A third-party packet's inner header cannot be written as received: a bad inner address, used markers out of order, or a tolerated defect that is part of its data. |
| `invalid-addressee` | A message, bulletin, NWS bulletin, telemetry metadata or directed query addressee is empty, over 9 characters, holds a space or `:`, or is not the form its report needs (`NWS-`/`NWS_`, a group bulletin's digit). |
| `invalid-name` | An object or item name is the wrong length or holds a character a name cannot. |
| `invalid-message-id` | A message ID is empty, over 5 characters or not letters and digits, or an ack or reject carries the wrong kind of ID. |
| `padding-space` | Text starts or ends with a space that would be read back as padding (an object name, a capability value). |
| `too-long` | Free text or a list is longer than its field allows: message text over 67 characters, a project title over 23, more than 13 names, more than 5 analog values. |
| `malformed` | Text in a fixed-form field is not that form: a locator, a bit sense, telemetry bits, signpost text, a capability token, a weather extra field, too few telemetry values. |
| `invalid-character` | Free text holds a character its field cannot carry: a line break (or a field that would end in CR or LF), a `{` in message-like text, or a character outside printable ASCII where only that is allowed. |
| `text-reads-as-field` | Free text would read back as a structured element (an altitude, a `!DAO!`, telemetry, a frequency, PHG/RNG/DFS, a timestamp or locator, a Mic-E device suffix, a weather field), and no clean form avoids it. |
| `not-a-number` | A value is NaN or infinite. |
| `value-out-of-range` | A number is outside what its field holds, after rounding (latitude, speed, gust, snowfall, range, footprint, bearing, telemetry sequence, PHG and DFS digits, an SSID). |
| `value-has-no-form` | A value inside the range that no form reads back as: a course of 0 in Mic-E or compressed bytes, a humidity of 0, Mic-E telemetry 255, `T#MIC` with an empty first channel, a frequency between bands. |
| `value-given-twice` | A builder input was given in two units (Celsius and Fahrenheit, feet and metres, mm and inches). |
| `invalid-timestamp` | A timestamp has a field out of range, or is a format the report does not take (a status not DHM, MDHM outside a positionless weather report). |
| `missing-field` | The data lacks something its report or another field needs: an object's timestamp, a capability, a compressed course without its speed, wind direction without speed, a tone without a frequency, a GGA type without an altitude. |
| `invalid-symbol` | The symbol table or code is not a valid symbol. |
| `symbol-mismatch` | The symbol disagrees with the data: weather without `_`, `_` without weather, an area without `\l`, a DF bearing without `/\`, a signpost without `\m`. |
| `extension-conflict` | Two things want the one data extension or the cs bytes: course/speed with PHG, a DF bearing with RNG, a compressed course with a range, wind with a range, a weather report's wind with a course. |
| `field-not-allowed` | The report has no place for a field, or it contradicts another: a compressed report with PHG, area or ambiguity, Mic-E with weather or an area, weather with a comment, telemetry or frequency, a locator status with a timestamp, a `!DAO!` on an ambiguous position. |
| `invalid-code` | An enumerated value outside its set: a Mic-E message with mixed bits or custom over 6, a Mic-E type code, a beam heading or power code, a query type, a DAO datum, a compression type, a tone type. |
| `invalid-nmea` | An NMEA sentence is malformed, its checksum does not match, or a field given beside it disagrees with it. |
| `not-encodable` | The call has nothing it can write: undecoded data, or Mic-E through a call that cannot return the destination. |
| `does-not-read-back` | Fallback: the library's own read-back check found the bytes decode to different data and no rule above names why. |

The fallback is needed: four libraries end every encode with a read-back check, a safety net that cannot know which rule it caught, and a refusal must always carry a code. No case may expect it (check.py enforces this), so each one met in a dump is a bug to turn into a named rule.

Rule for the safety nets: a read-back failure where free text in the data reads back changed is `text-reads-as-field`; any other is `does-not-read-back`.

Where two codes fit (the tie-breaks MAP.md applies):

- Fixed-form text (locator, bit sense, telemetry bits) is `malformed` whatever is wrong with it, length or characters. Free text is `too-long` or `invalid-character`.
- PHG, DFS and DF digits are numbers: `value-out-of-range`, not `invalid-code`.
- One check that covers an in-range value with no form and an out-of-range one (course, humidity, Mic-E telemetry) splits: `value-has-no-form` for the first.
- An absent companion is `missing-field`, not `field-not-allowed`.
- Anything competing for the data extension or cs bytes is `extension-conflict`, not `field-not-allowed`.
- An NMEA problem of any kind is `invalid-nmea`.
- On the AX.25 path, an address the frame cannot carry is `ax25-cannot-carry`; on the TNC2 path, `invalid-address`.

Not refusals, so no code: missing builder input that stays a programming error (cs InvalidOperationException, py ValueError for no symbol), bad arguments (a KISS port, a symbol constructor, NULL in C), C's ERR_BUFFER and ERR_UNSUPPORTED (the library's fixed buffers, not an APRS rule). rs returns EncodeError for a missing position or symbol; there it is `missing-field`.

## The vectors

The list goes in codes.json as a new top-level array `refusals`, beside `codes`, each entry `{"id", "meaning"}`. It is one catalogue file, and `refusals` is a separate namespace from diagnostics (no `tolerable`). The description line gains one sentence saying so.

An encode case keeps `"refused": true` and adds `"refusal": "<id>"` beside it in `expect`. A decode case keeps `"reencode": "refused"` and adds a top-level `"reencode_refusal": "<id>"`. Keeping `refused: true` and `"refused"` means a 1.0 test harness reading the new files still works, apart from cs, whose harness lists the keys it knows and needs the two names added when its submodule moves.

schema.json: `expect.refusal` and case `reencode_refusal` use the existing `code` pattern; `refusal` requires `refused`, and `reencode_refusal` requires `reencode: "refused"` (an `if`/`then` each).

tools/check.py gains: every `refusal` and `reencode_refusal` names an id in `refusals`; neither appears without its refusal; no case names `does-not-read-back`; every refusal id except the fallback is named by at least one case (as tolerable codes are now); and, once the fill below is done, every refused case names its code.

Dump records: an encode or build record whose `result` is `refused` gains `"refusal": "<id>"` beside the existing `reason`. A decode record whose `reencode` is `refused` gains `"reencode_refusal": "<id>"`. The API view may add `"ax25_refusal"` when `ax25` is `"refused"`. README's three record sections and the case `expect` paragraph say so in a sentence each.

tools/compare.py: for encode and build, a refused record contributes a `refusal` part; for decode, a `reencode_refusal` part. Each part is compared only among the dumps that write it, as API view keys are now, so a 1.0.0 dump without the field still compares. `ax25_refusal` comes for free as an API view key.

Order of work, so nothing breaks:

1. Vectors PR: the `refusals` list, schema, check.py (codes optional), compare.py, README. No case changes yet.
2. Each library: the shape below, its codes per MAP.md, its dump tool writing the field, its submodule moved to step 1. Release 1.0.1.
3. Vectors PR: fill `refusal` and `reencode_refusal` on all 347 refused cases from the five 1.0.1 dumps where all five agree, settle the rest case by case (each disagreement is a MAP.md row to fix), and make the code required in check.py. Libraries move their submodule again in a later patch.

## The libraries

Each mirrors its own diagnostic-code idiom, adds one read-only property to the existing refusal type, and keeps the message text as it is (still not stable API). New codes may be added in later 1.x releases, so callers must allow an unknown one.

cs: `public enum AprsRefusalCode` in AprsRefusalCode.cs, PascalCase members with explicit values from 1 (as `AprsDiagnosticCode`), `DoesNotReadBack` last-numbered but documented as the fallback. `AprsEncodeException` gains `public AprsRefusalCode Code { get; }` and internal constructors taking it; the two message-only constructors stay and give `DoesNotReadBack`, so nothing outside the library changes. The dump tool maps names to kebab-case as it does for diagnostics.

rs: `#[non_exhaustive] pub enum RefusalCode` beside `Code` in diagnostics.rs (or refusal.rs), with `pub const fn id(self) -> &'static str` as `Code::id` has. `EncodeError` (already non_exhaustive with private fields) gains a `code: RefusalCode` field and `pub fn code(&self) -> RefusalCode`; `EncodeError::new` becomes `new(code, message)` internally. Exported from lib.rs.

py: `class RefusalCode(str, Enum)` in errors.py, values the kebab-case ids, as `DiagnosticCode`. `EncodeError.__init__(self, message, code=RefusalCode.DOES_NOT_READ_BACK)` sets `self.code`; existing `raise EncodeError("...")` calls stay valid while they are converted. Exported in `__all__` and the package root.

ts: `export type RefusalCode = 'invalid-address' | ...` in codes.ts, with `REFUSAL_MEANINGS: Readonly<Record<RefusalCode, string>>` and `REFUSAL_CODES`, as the diagnostic ones. `AprsEncodeError` gains `readonly code: RefusalCode`; `refuse(reason)` becomes `refuse(code, reason)`. Exported from index.ts.

C: `typedef enum pdn_aprs_refusal { PDN_APRS_REFUSAL_NONE = 0, PDN_APRS_REFUSAL_INVALID_ADDRESS, ... } pdn_aprs_refusal;` in pdn_aprs.h, values fixed once released and new ones only appended, plus `PDN_APRS_API const char *pdn_aprs_refusal_name(int refusal);` giving the kebab-case id, as `pdn_aprs_code_name` does. `pdn_aprs_encoded` gains `int refusal;` after `reason`: zero (NONE) on success and for every error that is not ERR_REFUSED. `pdn_aprs__refuse(e, code, reason)` and build.c `fail` take the code. `pdn_aprs_write_ax25`, which has no `encoded`, stays as it is.

C fix that comes with it: header address failures in `write_header_tnc2` and `write_header_ax25` return ERR_ARGUMENT today, though pdn_aprs.h (lines 1175 and 1391) promises ERR_REFUSED for an address that cannot be carried. In 1.0.1 they return ERR_REFUSED with `invalid-address` or `ax25-cannot-carry`, as the header already documents; NULL pointers stay ERR_ARGUMENT.

## Rulings

From the five-way comparison of the 1.0.1 dumps (enc5.txt, build5.txt; per-library changes in FIXES.md). Where a ruling and a MAP.md row differ, the ruling wins. No new code was needed.

1. Several faults: the refusal names the first code that applies in this order: not-encodable; invalid-address, ax25-cannot-carry, tnc2-cannot-carry, invalid-third-party-header; invalid-addressee, invalid-name, invalid-timestamp, not-a-number, value-out-of-range, value-has-no-form, invalid-code, invalid-symbol, invalid-character, too-long, padding-space, malformed, invalid-message-id, invalid-nmea; extension-conflict, field-not-allowed, symbol-mismatch, missing-field, value-given-twice; text-reads-as-field; does-not-read-back. Reason: DESIGN gave no order and most buckets were data with two faults; the header is written first, a field wrong on its own is wrong whatever else is given, what the frame cannot hold comes before the symbol and companions, and the safety net is last.
2. A Mic-E device suffix the device database does not know for the type code is `invalid-code` (an enumerated value outside its set), not `text-reads-as-field`: the suffix is not free text.
3. A single space is a Mic-E type code (interpretations.md, "Mic-E type codes"), so a suffix after it follows ruling 2, not `missing-field`.
4. A telemetry report with no bits at all is `missing-field` (a part its report needs is absent); `malformed` stays for bits given that are not eight 0 or 1 characters.
5. A capability token is fixed-form (DESIGN's `malformed` row): empty, or holding a space, comma, `=` or control character, it is `malformed`; a capability value stays free text (`invalid-character`, `padding-space`).
6. A telemetry project title over 23 characters is `too-long`, as DESIGN's `too-long` row says; MAP's `malformed` rows for it yield.
7. Bit sense, telemetry bits and a telemetry report's sequence text (letters and digits, or MIC) holding a wrong character are `malformed` by the fixed-form tie-break; MAP's `invalid-character`, `invalid-code` and `invalid-message-id` rows for them yield.
8. NaN or an infinity is `not-a-number` at every check that also catches it; MAP rows that file "or NaN" under `value-out-of-range` split.
9. A directed query target is an addressee: wrong length or a bad character is `invalid-addressee`, not `invalid-address` or `too-long`.
10. `_` with no weather data is `symbol-mismatch` whatever else the data holds: a report is a weather report only when it carries weather, so the weather report rules (no comment, wind in the extension or cs bytes) apply only then.
11. Storm data without the hurricane symbol is `symbol-mismatch`: DESIGN's list gives examples and this is the same rule.
12. Uncompressed weather with course/speed, PHG, RNG, DFS, an area, a DF bearing or storm data is `extension-conflict` (the wind holds the data extension); compressed, the wind holds the cs bytes, so course/speed, a range or a GGA altitude is `extension-conflict` and a 7-byte extension is `field-not-allowed` (a compressed report has no data extension).
13. An altitude on a compressed weather report is `extension-conflict` when the compression type says GGA (the cs bytes wanted twice) and `field-not-allowed` otherwise (its `/A=` needs the comment a weather report lacks).
14. A compressed report's course/speed and range live in the cs bytes, so they never count toward "one data extension": a compressed report is refused for a 7-byte extension (`field-not-allowed`) or for course/speed with a range (`extension-conflict`), never for "two extensions".
15. A message whose addressee makes it read back as a bulletin or NWS bulletin (`BLN...`, `NWS-...`) is `invalid-addressee` (not the form a message needs), not `text-reads-as-field`.
16. For the safety-net rule, a weather report's software type, unit and extra fields are free text: when they read back changed the code is `text-reads-as-field`.
17. A safety net that catches a fault a named rule covers (an NMEA field that disagrees, T#MIC with an empty first channel, an ambiguous position centred past a pole, a `!DAO!` on an ambiguous position, an unknown device suffix) reports that rule's code, and the library adds the named check before the read-back.
18. A read-back that loses a field follows DESIGN's safety-net rule like any other (`text-reads-as-field` when free text changed, else `does-not-read-back`), never `field-not-allowed`.
19. An altitude given in feet and in metres to a builder is a refusal with `value-given-twice`, as DESIGN's row says; C's ERR_ARGUMENT and MAP's `field-not-allowed` row (build.c:255) yield.
20. R10 does not reach Mic-E: Mic-E cannot carry weather and the corpus re-encodes Mic-E reports with a `_` symbol, so a Mic-E `_` is no fault and such a report is refused only for its other faults (a status text that reads back changed is `text-reads-as-field`). This withdraws FIXES.md rows cs8, rs6 (its `_` part), ts12 and c17.
21. A DF bearing and storm data together are `extension-conflict`: both extend the one course/speed, and only one can follow it.
22. A course/speed on the area symbol `\l` with no area is `symbol-mismatch`: the symbol makes the extension read back as an area, so the symbol disagrees with the data (the converse of "an area without `\l`").
23. The check for an ambiguity box centred past a pole or 180 degrees applies only to a form that writes ambiguity (uncompressed and Mic-E); on a compressed report ambiguity is already `field-not-allowed` and that check does not run.
R24. A compressed GGA altitude on a weather report is legitimate (the vectors write it), so it never causes extension-conflict by itself: a compressed GGA weather report refused only for comment-borne data (telemetry and so on) is field-not-allowed; extension-conflict applies when something else also wants the cs bytes (a range, course or speed beside the GGA altitude).
R25. A field the report has no place for is `field-not-allowed`, and that field's own checks (range, characters, length) do not run, as R23 already says for ambiguity: a comment on a weather report is `field-not-allowed` even when it holds a line break, and a non-GGA altitude on a compressed weather report (it would need a `/A=`) is `field-not-allowed` even past 999999 feet. A field whose place exists but is wanted twice (a range in cs bytes that hold the wind or a GGA altitude) is still range-checked first, by R1. Example cases: encode `{"type":"weather","timestamp":"10090556","weather":{"temperature_f":77},"comment":"\n"}` refused `field-not-allowed`; encode `{"type":"position","latitude":19.4,"longitude":-78.7,"symbol":"/_","compressed":true,"altitude_feet":7305960,"weather":{"temperature_f":-1}}` refused `field-not-allowed`.
R26. R15 covers only an addressee in a bulletin form (`BLN` then 0-9 or A-Z, or `NWS-`/`NWS_`); any other addressee starting `BLN` (`BLNe`, `BLN-`) is a station, and its message is judged on its text: `?WX` to it reads back as a directed query, `text-reads-as-field`. Example case: encode `{"type":"message","addressee":"BLNe","text":"?WX"}` refused `text-reads-as-field`.
R27. R22 narrowed: a course/speed on `\l` with no area is `symbol-mismatch` only when a course is given, since `ddd/sss` reads back as an area. A speed alone is written `.../sss`, which all five decoders read back cleanly as a speed on `\l`, so by the Encoding rule (write an equivalent form or refuse) it is written, and the report is refused only for its other faults. Cases: encode `{"type":"position","latitude":32.84108241758242,"longitude":-97.31199450549451,"symbol":"\\l","speed_knots":12}` expect info `!3250.46N\09718.72Wl.../012`; encode the same with `"course_degrees":1,"speed_knots":1` refused `symbol-mismatch`.
R28. A Mic-E altitude with no type code whose only form is the Mic-E altitude bytes (whole metres, beyond the 6 digits of a `/A=`), and whose first byte is a type code character (`` ` `` `'` `>` `]` or space), reads back with a type code and so has no form: `value-has-no-form`. It is a value with no form, not free text (no comment changed), so it is not `text-reads-as-field`, and not the `does-not-read-back` fallback. Case: encode `{"type":"mic-e","mic_e_message":"en-route","old_data":true,"latitude":47.20366666666666,"longitude":-122.50216666666667,"symbol":"Wv","course_degrees":26,"speed_knots":0,"altitude_feet":1597896.9816272964}` refused `value-has-no-form` (487039 m, whose first altitude byte is `]`).
