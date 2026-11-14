# Round 4: details settled by the vectors writer

Each point the brief left open, how it was settled and why. Branch `round-4` of aprs-vectors (PR #29). The reasoning is also in interpretations.md under the heading named.

## R1. 256-byte information field ("An information field is at most 256 bytes")

1. **Place of `too-long` in the Refusal reasons order: unchanged**, after `invalid-character` and before `padding-space`. A code has one place in the order, and `too-long` already had one for message text and project titles; moving it would change existing precedence cases the brief did not name. That place is already before what the frame cannot hold (`extension-conflict`, `field-not-allowed`) and the symbol and companions, which is what the brief asked for. See "What I think is wrong with the brief" in the report.
2. **The size when other faults are present** (needed because `too-long` comes before later codes): the bytes the data's fields make as given. A field the report has no place for (`field-not-allowed`) or one left out (`missing-field`) makes none; a malformed one makes the bytes given; a comment counts with any delimiter the Encoding rule writes. Cases: `encode/info-size-before-missing-field`, `encode/info-size-before-field-not-allowed`, `encode/field-without-a-place-makes-no-bytes`, `encode/invalid-symbol-before-info-size`.
3. **Bytes, not characters**: text counts as its UTF-8 bytes (`encode/status-of-257-bytes-in-utf8`).
4. **Third-party**: the outermost field counts, `}` + inner header + `:` + inner field (`encode/third-party-to-25[67]-bytes`). A decoded third-party packet still re-encodes with its inner field as received, so a received one over 256 bytes is `refused`, `too-long` (`third-party/nested-2000-deep`).
5. **NMEA and NWS bulletins**, which had "no length limit", now have none of their own beyond the field's 256 bytes (README text and the NMEA interpretation amended).

## R2. Implementation limits ("A library with a fixed capacity says so")

6. A dump record that hits a capacity: decode records are recognised by `error:implementation-limit` in the lenient `diagnostics` or `header_error`; encode and build records use a new `result` value, `implementation-limit`, with a `reason`. compare.py leaves both out and counts them (`left out:` line, `left_out` in --json).
7. The edge cases are decode cases an unlimited library passes; the expected `reencode` of the 513- and 2,000-byte fields is `refused`, `too-long` (R1).

## R3. Control characters ("Control characters in text")

8. **Order**: a text's control characters are judged last, after its structure and its encoding. So `non-utf8-text` comes before `control-character-in-text` (`status/control-character-and-latin-1`), and in a capabilities report `free-text-capabilities` comes first (keeps the existing strict result of `capabilities/control-character-in-value`). Reason: both encoding and control characters judge the whole text, and the bytes are read as characters before they are judged as characters; it also changes no existing strict result except where the new warning is the only defect.
9. **CR or LF inside text** is a control character; only one at the end of the information field is `trailing-line-break` (`position/carriage-return-inside-comment`).
10. **TAB**: no exception; the spec gives printable characters (`position/tab-in-comment`).
11. **Object and item names**: already printable ASCII by their own rule, so a control character there stays `invalid-object-name` / `invalid-item-name` (an error) and gets no new warning (`object/control-character-in-name`). Likewise a capability token (free text by its rule), an addressee, a header, an NMEA sentence.
12. **Capability values** are text: both `free-text-capabilities` and the new warning.
13. **"A query's text"**: neither query type in the data form has free text (a type, a footprint, a callsign target); query text that is not a query is message text and is covered there.
14. **Free text a report leaves** counts as text: `weather-comment` text, the comment after an NMEA checksum, a Maidenhead beacon's comment, a telemetry report's comment.
15. **Third-party**: an inner packet's text gets the warning on the inner packet; strict reads the inner packet as `unrecognized` with `error:control-character-in-text` (as every library already does for `non-utf8-text` there); the packet re-encodes `identical`, inner field as received (`third-party/control-character-in-inner-text`).
16. **Re-encode of a decoded packet**: `refused`, `invalid-character`, unless an earlier code in the order already applies, or the text is a weather report's comment, which has no place (`field-not-allowed` stands, as before).
17. **Mic-E 0x1D**: the Encoding rule's "status text starting with 0x1D is written after a `/`" and "after Rev 0 telemetry, a comment starting with 0x1D is written straight on" are replaced: such text is now refused (`invalid-character`).
18. Corpus case descriptions list their warnings; the ones that gained the warning were updated to list it.

## R4. Builder defaults ("Builder defaults"; survey in DEFAULTS.md)

19. **Symbol left out** (TypeScript wrote `//`): refused as `invalid-symbol`, as neutral data without one already is ("Absent text is empty text"); a weather report's symbol is `/_`.
20. **Telemetry bits left out**: the builder writes `00000000` (coordinator's ruling on OPEN 2): APRS12c ch. 13's report always carries the eight bits, a decoder gives `invalid-telemetry` without them, and all zeros is what a station with no digital channels sends. TypeScript's `bits` argument becomes optional. Neutral data with no bits stays `missing-field`. Sequence left out: `missing-field`.
21. **Positionless weather timestamp left out**: `missing-field` (C gave `invalid-timestamp`; three read the clock).
22. **Agreed defaults written into the rules**: no path, destination `APZ001`, no ambiguity, no compression, no message ID, reply-ack or group, alive, metadata to the sending station, unknown dots for an unset `c`/`s`/`g`/`t`, Mic-E speed 0.
23. Recipes: 15 percent of generated recipes leave out a random subset of optional inputs (and sometimes the station's destination or path); a dump tool passes only the keys given. Required keys are listed in the README's Build records.

## R5. Mic-E altitude ("A Mic-E altitude goes in the Mic-E altitude bytes")

24. **How neutral data tells the forms apart: by value.** A `/A=` holds whole feet, the Mic-E bytes whole metres. Neutral data goes in a `/A=` only when only a `/A=` holds it exactly (whole feet within six digits, not whole metres or outside -10000 to 743570 m), each judged within 1e-6 of a whole number. Otherwise the Mic-E bytes, rounded to the metre (100.5 ft is 31 m; 1250 ft = 381 m and 0 go in the Mic-E bytes).
25. **A decoded `/A=` re-encodes `identical`**, whatever its value, because decoded data knows where the altitude came from. This keeps the round 3 cases `mic-e/an-altitude-from-a-later-a-is-written-back-as-a` and `mic-e/text-altitude-equal-to-the-bytes-altitude-is-written-back` (altitude 0, written back as `/A=000000`) and matches all six libraries today (`mic-e/slash-a-altitude-in-both-units`: decoded `/A=001250` re-encodes identical; `encode/mic-e-altitude-in-both-units`: neutral 1250 ft goes in the Mic-E bytes).
26. **-50,000 ft** (C#, Rust, Go refused it; the others wrote `/A=`): goes in a `/A=`, the only form that holds it.
27. Builder: an altitude outside the Mic-E bytes' range is `value-out-of-range`, not moved to a `/A=`.

## R6. Run-on weather field ("A weather field that runs on by many digits")

28. **"A defined weather field"**: a letter APRS12c defines, not already read, with a value, that is, a field the run goes on to read. An extra field (undefined letter) or a defined field already read does not qualify (`weather/run-on-value-then-an-extra-field`, `...-then-a-field-already-read`).
29. **"The end of the information field"** is literal: a `!DAO!` or base-91 telemetry after the run is not the end (they are lifted only after the fields).
30. A dropped value counts as present for `incomplete-weather`, as a wind direction over 360 already does.
31. Applies to every fixed-width field, humidity included (`weather/run-on-humidity`).

## Changed cases (67), to check

- R1, re-encode now `refused`, `too-long`: corpus/0107, corpus/0157, corpus/0277, third-party/nested-2000-deep.
- R6: corpus/0509 (gust dropped, fields read on to `tU2k`, re-encode now `equivalent`), corpus/1227 (wind speed dropped, strict now `out-of-range-value`).
- R3, lenient gains `warning:control-character-in-text`; strict becomes `control-character-in-text` where it was `same` or a different reading whose text holds one; re-encode becomes `refused`, `invalid-character` unless an earlier refusal applies: capabilities/control-character-in-value, corpus/0034, 0266, 0272, 0286, 0437, 0591, 0657, 0686, 0697, 0707, 0710, 0713, 0774, 0783, 0817, 0826, 0845, 0862, 0864, 0884, 0901, 0931, 0961, 0966, 0968, 0981, 0990, 1000, 1011, 1026, 1040, 1059, 1118, 1121, 1155, 1169, 1184, 1185, 1197, 1208, 1212, 1222, 1237, 1251, 1254, 1281, 1282, 1285, 1294, 1297, 1310, 1328, 1368, differential/dao-last-one-wins, item/signpost-after-braces-that-do-not-qualify, mic-e/0x1d-comment-after-legacy-telemetry, mic-e/frequency-then-comment-starting-with-nul, mic-e/legacy-binary-telemetry-after-ff-padding, mic-e/legacy-binary-telemetry-too-short, telemetry-metadata/carriage-return-by-a-coefficient.
- Worth a reviewer's eye: corpus/0657, 1169, 1285 (strict was a different reading; that reading's text holds a control character, so strict now rejects); corpus/0713 (`missing-field` becomes `invalid-character`), 1169 (`extension-conflict` becomes `invalid-character`), 1184 (`too-long` becomes `invalid-character`), 1251 (`field-not-allowed` for a PHG on a compressed position becomes `invalid-character`).

Computed by a script from the rules (not by a library), then run against aprs-py, aprs-go and aprs-c at main: every failure is one of the new or changed cases, and every new case not about a new rule (the 27 AX.25 frames, the 14 live packets, the locator finding, the boundary cases already right) passes.
