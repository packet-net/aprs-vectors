# Round 4 (1.2.0): what each library implements

You are implementing round 4 of the APRS conformance vectors in one of the six libraries (aprs-cs, aprs-rs, aprs-py, aprs-ts, aprs-c, aprs-go). The rules live in packet-net/aprs-vectors, branch `round-4` (draft PR #29), head `4b7a7ec38c62463b2e7e4f40a323c2835b308ff1` at the time of writing; use the branch head. Work on a branch `round-4` in your library, with the vectors submodule moved to that commit. Do not change the vectors; if a case looks wrong, say so with the case id and your reasoning, and do not skip it.

Read in aprs-vectors: README.md "Rules the cases rely on" (the bullets named below) and "Comparing implementations", interpretations.md (the six new sections before "Where these decisions and Ham::APRS::FAP differ"), codes.json (two new codes). The rule text there is the authority; this sheet points to it.

## 1. Encoders refuse an information field over 256 bytes (R1)

- Rule: README Encoding ("An information field is 1 to 256 bytes ...") and Refusal reasons ("`too-long` has one place in the order ..."); interpretations.md "An information field is at most 256 bytes".
- An encoder or builder refuses data whose information field, as written, is over 256 bytes, with refusal `too-long`, whatever the output (TNC2, AX.25, KISS). Count bytes (UTF-8), number text included. For third-party data count the outermost field: `}` + inner header + `:` + inner field.
- `too-long` keeps its existing place in the refusal order (after `invalid-character`, before `padding-space`). When the record also has a fault later in the order, measure the size on the fields as given: a field with no place in the report, or one left out, makes no bytes; a malformed one makes the bytes given; a comment counts with any delimiter you would write.
- Decoding sets no limit. A decoded packet whose field is over 256 bytes re-encodes `refused`, `too-long`.
- Remove any statement in your README or docs that the encoder has no size limit.
- New cases: encode/status-of-256-bytes, encode/status-of-257-bytes, encode/status-of-256-bytes-in-utf8, encode/status-of-257-bytes-in-utf8, encode/position-comment-to-256-bytes, encode/position-comment-to-257-bytes, encode/object-comment-to-256-bytes, encode/object-comment-to-257-bytes, encode/telemetry-number-to-256-bytes, encode/telemetry-number-to-257-bytes, encode/third-party-to-256-bytes, encode/third-party-to-257-bytes, encode/nws-bulletin-of-257-bytes, encode/info-size-before-missing-field, encode/invalid-symbol-before-info-size, encode/info-size-before-field-not-allowed, encode/field-without-a-place-makes-no-bytes, status/information-field-over-256-bytes.
- Changed cases: corpus/0107, corpus/0157, corpus/0277, third-party/nested-2000-deep (re-encode now `refused`, `too-long`).

## 2. A fixed capacity says so (R2)

- Rule: README "Implementation limits"; interpretations.md "A library with a fixed capacity says so"; codes.json `implementation-limit` (error, not tolerable).
- Only a library with a fixed capacity (aprs-c: 512-byte field, 16 path entries, 64 capabilities, 8 extra weather fields) gives it. When a packet needs more: a limit in the header makes the header unusable with `error:implementation-limit`; any other makes the data `unrecognized` (`malformed`) with `error:implementation-limit`; lenient and strict alike; re-encode `none`. Never a different reading of the packet. List the capacities in your README.
- Your test runner skips a case whose decode result gives `implementation-limit`, the same way it skips a case your data model cannot hold (reported as skipped, with the reason). For aprs-c this is how status/information-field-of-513-bytes and the others below pass; it closes packet-net/aprs-c#16. Remove `tests/known-differences.txt` entries this replaces.
- Libraries without a capacity: nothing to change; these cases must pass as ordinary decodes.
- New cases: status/information-field-of-513-bytes, status/information-field-of-2000-bytes, envelope/seventeen-path-entries, capabilities/sixty-five-capabilities, weather/nine-extra-fields.

## 3. Control characters in text (R3)

- Rule: README "Control characters in text", "The order of checks" (last sentence of its structural checks part), Encoding ("Text that holds a control character ... is refused as `invalid-character`"); interpretations.md "Control characters in text"; codes.json `control-character-in-text` (warning, tolerable).
- In text read as text (comment, status text, message, bulletin and NWS bulletin text, telemetry names, units and project title, capability values, the free text a report leaves: weather-comment text, the comment after an NMEA checksum, a Maidenhead beacon or telemetry report comment), a byte below 0x20 or 0x7F gives one `warning:control-character-in-text` per text. TAB and a CR or LF inside the text count. The text is kept as sent. A strict decoder rejects it.
- Not judged: user-defined, raw weather, test and undecoded data, Mic-E fixed bytes and Rev 0 telemetry, 0xFF padding; object and item names, capability tokens, addressees, headers and NMEA sentences keep their own rules (a control character in an object name stays `invalid-object-name`).
- Order: judged last for its text, after the text's structure and after `non-utf8-text`. A capabilities report checks `free-text-capabilities` first.
- Third-party: the inner packet's text gets the warning on the inner packet; strict makes the inner packet `unrecognized` with `error:control-character-in-text`; the packet re-encodes `identical` (inner field as received).
- Encoders and builders refuse such text with `invalid-character` (no longer only CR and LF). A Mic-E status text starting with 0x1D is now refused, not written after a `/`.
- New cases: status/control-character-in-text, status/control-character-and-latin-1, position/tab-in-comment, position/carriage-return-inside-comment, position/del-in-comment, message/control-character-in-text, message/control-character-in-bulletin, message/control-character-in-nws-bulletin, telemetry-metadata/control-character-in-names, telemetry-metadata/control-character-in-project, telemetry/control-character-in-comment, weather/control-character-in-weather-comment, mic-e/control-character-in-status-text, nmea/control-character-after-the-checksum, maidenhead/control-character-in-comment, object/control-character-in-name, user-defined/control-characters-are-data, third-party/control-character-in-inner-text.
- Changed cases: capabilities/control-character-in-value, corpus/0034, 0266, 0272, 0286, 0437, 0591, 0657, 0686, 0697, 0707, 0710, 0713, 0774, 0783, 0817, 0826, 0845, 0862, 0864, 0884, 0901, 0931, 0961, 0966, 0968, 0981, 0990, 1000, 1011, 1026, 1040, 1059, 1118, 1121, 1155, 1169, 1184, 1185, 1197, 1208, 1212, 1222, 1237, 1251, 1254, 1281, 1282, 1285, 1294, 1297, 1310, 1328, 1368, differential/dao-last-one-wins, item/signpost-after-braces-that-do-not-qualify, mic-e/0x1d-comment-after-legacy-telemetry, mic-e/frequency-then-comment-starting-with-nul, mic-e/legacy-binary-telemetry-after-ff-padding, mic-e/legacy-binary-telemetry-too-short, telemetry-metadata/carriage-return-by-a-coefficient.

## 4. Builder defaults (R4)

- Rule: README builder rules "Timestamps" (last two sentences) and "Defaults"; interpretations.md "Builder defaults". The 1.1.0 survey with file and line for every library is in the round 4 notes (DEFAULTS.md); summary of what changes:
  - A builder never reads the clock. An object or positionless weather report built with no timestamp: refuse `missing-field` (C#, Python, TypeScript read the clock today; C gives `invalid-timestamp` for weather). A separate, explicit "now" helper is allowed.
  - Messaging not said: off (`!`, `/`, Mic-E `'`). TypeScript writes `` ` `` today.
  - Mic-E message not given: off duty (M0). Python writes in service today.
  - Symbol not given on a position, object, item or Mic-E report: refuse `invalid-symbol` (TypeScript writes `//` today; others refuse with other codes or exceptions: the refusal code must be `invalid-symbol`). Weather report: `/_`.
  - Telemetry report with no sequence: refuse `missing-field`. With no bits: write `00000000`, as five libraries do today; TypeScript's `bits` argument becomes optional. (Neutral data given to an encoder with no bits stays `missing-field`.)
  - Unchanged and now written down: no path, destination `APZ001`, no ambiguity, no compression, no message ID, reply-ack or group, alive, metadata addressed to the sending station, unset `c`/`s`/`g`/`t` written as dots, Mic-E speed 0.
- Dump tool, build mode: pass only the keys a recipe gives; never fill in an absent one (DEFAULTS.md lists the fills each dump tool does today: ts `messaging(a.messaging === true)` and its `unsupported` for a missing timestamp, py's explicit messaging, destination, path, bits and empty text, rs's sequence 0, c's absent `mic_e_message` as unsupported, cs's `text ?? ""`). A recipe may now omit any key except those the README's Build records list as required. The dump tool must not crash on a missing key (at 1.1.0 ts crashed on telemetry with no `analog`, py on telemetry with no `sequence`); a builder refusal is a `refused` record.
- No cases (a case cannot hold a builder recipe); checked by the six-way build runs.

## 5. Mic-E altitude (R5)

- Rule: README builder rule "Units" and Encoding ("A Mic-E report's altitude goes in the Mic-E altitude bytes ..."); interpretations.md "A Mic-E altitude goes in the Mic-E altitude bytes".
- Builder: an altitude in feet or metres goes in the Mic-E altitude bytes, rounded once to the nearest metre from the value given (1000 ft is 305 m). Outside -10000 to 743570 m: `value-out-of-range`. No `/A=` from a Mic-E builder.
- Encoder, decoded data: an altitude read from a `/A=` is written back as a `/A=` (unchanged; all six do this).
- Encoder, neutral data: `/A=` only when the value is a whole number of feet within six digits that the Mic-E bytes do not hold exactly (not a whole number of metres, or outside their range), each within 1e-6 of a whole number; otherwise the Mic-E bytes, rounded to the metre. 100.5 ft is 31 m in the Mic-E bytes (today all six write `/A=000101`); -50000 ft is `/A=-50000` (C#, Rust and Go refuse it today).
- New cases: encode/mic-e-altitude-between-feet-and-metres, encode/mic-e-altitude-below-the-mic-e-range, encode/mic-e-altitude-in-whole-feet, encode/mic-e-altitude-in-both-units, mic-e/slash-a-altitude-in-whole-feet, mic-e/slash-a-altitude-in-both-units.

## 6. Run-on weather fields (R6)

- Rule: README "Weather" (the sentence starting "One that runs on by two or more digits") and "Complete weather"; interpretations.md "A weather field that runs on by many digits".
- A fixed-width field whose digits run on by two or more, followed by the end of the information field or by a defined field the run goes on to read (a letter APRS12c defines, not already read, with a value): `warning:out-of-range-value`, the value dropped, the fields carry on after the run. Anything else after the run keeps the 1.1.0 rule. The dropped value counts as present for `incomplete-weather`.
- New cases: weather/run-on-value-then-fields, weather/run-on-value-at-the-end, weather/run-on-value-in-a-position-report, weather/run-on-humidity, weather/run-on-value-then-text, weather/run-on-value-then-an-extra-field, weather/run-on-value-then-a-field-already-read.
- Changed cases: corpus/0509, corpus/1227.

## 7. Other new cases (should pass already, except where noted)

- One AX.25 frame per data type: ax25/position, ax25/mic-e, ax25/object, ax25/item, ax25/message, ax25/ack, ax25/reject, ax25/bulletin, ax25/nws-bulletin, ax25/telemetry-names, ax25/telemetry-units, ax25/telemetry-coefficients, ax25/telemetry-bits, ax25/directed-query, ax25/status, ax25/telemetry, ax25/weather, ax25/raw-weather, ax25/nmea, ax25/maidenhead-beacon, ax25/query, ax25/capabilities, ax25/third-party, ax25/user-defined, ax25/test, ax25/agrelo-df, ax25/unrecognized.
- Clean live packets of the commonest shapes: corpus/1396 to corpus/1409.
- mic-e/locator-not-joined-across-an-altitude: aprs-ts reads `IO9"4-}1SX/G` as the locator IO91SX across the lifted altitude; fix it in aprs-ts (interpretations.md "Where a Mic-E locator is read").
- aprs-cs, refusal order (from LIBRARY-FINDINGS.md): `not-a-number` comes before `value-out-of-range` in the README's Refusal reasons order, but aprs-cs gives `value-out-of-range` instead of `not-a-number` for a record with both (compressed weather, longitude 180.00008333, altitude -Infinity; `generate.py --faults --nonfinite`, seed 288591650, line 474), which no case can hold.

## 8. Dump tool changes (all modes)

- Decode: nothing new to write; a library with a capacity gives `implementation-limit` in its lenient result as item 2 says.
- Encode and build: a new `result` value `implementation-limit` with a `reason`, for data beyond a fixed capacity (README "Encode records", "Build records").
- Build: item 4 (only the keys given; no crash on a missing one).
- aprs-c: read the non-standard JSON tokens `NaN`, `Infinity` and `-Infinity` in encode and build input (`generate.py --nonfinite` writes them); at 1.1.0 most such lines were marked unsupported.
- Your README: the 256-byte limit, the builder defaults that changed, the capacities (aprs-c), and the version 1.2.

## Breaking changes for callers

Each writer puts this list, for its own library, in its CHANGELOG under 1.2.0.

- Every library: an encoder or builder refuses an information field over 256 bytes (`too-long`); text with a control character is refused (`invalid-character`); a decoder gives `warning:control-character-in-text`, so a strict decoder now rejects such packets; a run-on weather value before a defined field is dropped with `out-of-range-value`.
- aprs-cs, aprs-py, aprs-ts: an object or positionless weather report built with no timestamp is refused (`missing-field`) instead of being stamped from the clock.
- aprs-py: `timestamp=True` (the time now) is gone; pass `datetime.now(timezone.utc)` as `timestamp`.
- aprs-ts: a position, object, item or Mic-E report built with no symbol is refused (`invalid-symbol`) instead of silently getting `//`.
- aprs-py: a Mic-E report built with no message is off duty, not in service.
- aprs-ts: a Mic-E report built without saying the station can message gets the type code `'`, not `` ` ``.
- Every library (all six wrote a `/A=` at 1.1.0): a Mic-E altitude given in feet goes in the Mic-E altitude bytes, rounded to the metre, instead of a `/A=` in the status text.
- aprs-c: a packet beyond its capacity is `implementation-limit` (header error or `unrecognized`) instead of the readings it gave at 1.1.0.
- aprs-cs, aprs-rs, aprs-go: neutral Mic-E data of -50000 ft is written as `/A=-50000` instead of refused; every library: neutral Mic-E altitudes that are neither whole feet nor whole metres go in the Mic-E bytes.

The time now stays one explicit call away in each library that read the clock, and the builder never calls it itself:
- aprs-cs: pass `AprsTimestamp.FromDateTime(DateTime.UtcNow)` (existing) to the timestamp argument.
- aprs-py: pass `datetime.now(timezone.utc)` (any `datetime` is already taken) as `timestamp`.
- aprs-ts: pass `new Date()` to `timestamp(...)`, or to `weather(..., at)` (both already take a `Date`).
- aprs-rs, aprs-c, aprs-go never read the clock; their builders already take an explicit time, so nothing changes.

## What done means

- Your own test suite passes against the vectors at the `round-4` head, with no new skips and no new entries in `known-differences` (aprs-c: capacity skips go through `implementation-limit`, item 2, and the old known differences they replace are removed).
- Every case listed above passes, lenient, strict, tolerance, re-encode and encode checks alike.
- Your dump tool runs `tools/generate.py --recipes --count 100000` output in build mode without crashing, and writes only `built`, `refused`, `unsupported` or `implementation-limit` records.
- Nothing tagged, no version bump merged; one PR on `round-4`.
