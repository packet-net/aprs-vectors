# Round 4 (1.2.0): brief

Tom approved these on 2026-11-14 ("go with your recommendations") after the 1.1.0 review. Tracking issue: packet-net/aprs-vectors#26. One release, 1.2.0, of the vectors and all six libraries, which also carries the review fixes and the licence change (MIT for the libraries, CC0 for the vectors) already merged to each main. Branch name `round-4` in all seven repos. No tags without Tom's word.

Rulings are settled from the spec and reasoning, never by majority. Where this brief leaves a detail open, the vectors writer settles it from the spec, writes the reasoning into interpretations.md, and lists it in notes/round-4/RULED.md; a point that cannot be settled that way goes in notes/round-4/OPEN.md for the coordinator.

## R1. An encoder refuses an information field over 256 bytes

- APRS12c ch. 3: the AX.25 information field is 1 to 256 bytes. Every encoder at 1.1.0 writes any length (a 2,000-character comment, a 309-digit telemetry number); only message text (67) is refused.
- Decision: an encoder or builder refuses data whose information field, as written, is over 256 bytes: `too-long`. It is checked on the bytes written, whatever the output form (TNC2, AX.25, KISS), so it also bounds number text. For a third-party packet the limit applies to the outermost information field. Where `too-long` sits in the Refusal reasons order is with the other "what the frame cannot hold" codes; settle the exact place and say so.
- Decoding keeps no limit (existing ruling). A received field over 256 bytes decodes as before and re-encodes `refused` with `too-long`. No new diagnostic.
- Cases: 256 written, 257 refused, for a status, a position comment, an object, a telemetry number, and a third-party wrapper that takes an inner packet over the limit. Check every existing case and refresh any whose re-encode result changes.

## R2. A library with a fixed capacity says so

- aprs-c holds 512 bytes of information field, 16 path entries, 64 capabilities and 8 unknown weather fields. At 1.1.0 it gave a different reading at each edge: an empty field, a header error, `invalid-capabilities`, or the ninth field moved into the comment (which changes the strict verdict).
- Decision: one new diagnostic code, `implementation-limit`, an error, not tolerable, listed in codes.json with the note that only an implementation with a fixed capacity gives it. Such an implementation never gives a different reading of the data: when a packet needs more than it holds, the header (if the limit is in the header) is a header error with `error:implementation-limit`, otherwise the data is `unrecognized` (`malformed`) with `error:implementation-limit`, in lenient and strict alike, and it re-encodes `none`. An implementation without the limit decodes the packet normally.
- compare.py leaves out, and counts per library, a record where a dump gives `implementation-limit`, as it does `unsupported`. A library's test runner treats a case its capacity cannot hold the same way, and lists the capacities in its README.
- Cases at each edge so an unlimited implementation is shown to accept them: 513-byte and 2,000-byte information fields, 17 path entries, 65 capabilities, 9 unknown weather fields.
- aprs-c: closes packet-net/aprs-c#16.

## R3. Control characters in text

- APRS12c gives text as printable ASCII (and UTF-8 by later practice). At 1.1.0 a NUL or other control character in a comment, status or message decodes with no diagnostic, strict included, and every encoder writes one raw. Only a trailing CR or LF is ruled on.
- Decision: in text a decoder reads as text (a comment, status text, message, bulletin or announcement text, a telemetry name, unit or title list, capability values, a query's text), a byte below 0x20 or the byte 0x7F is a defect: one `control-character-in-text` warning for the text (as `non-utf8-text` is one per text), tolerable, so strict rejects. The text is kept as sent. Bytes that are data, not text, are not judged: user-defined data, raw weather, undecoded and test data, Mic-E's fixed bytes and legacy telemetry, 0xFF padding. An encoder refuses such text as `invalid-character`.
- Settle from the existing rules where this meets them: the order against `non-utf8-text` and the structural checks (README "The order of checks"), a CR or LF inside text as opposed to trailing, a TAB (it is a control character: no exception unless the spec gives one), and whether an object or item name can hold one (the name rule may already exclude it).
- Every observed case whose text holds a control character gains the warning and a new strict result; refresh them and review the diff.

## R4. Builder defaults

- At 1.1.0 a Mic-E builder given nothing else writes "in service" and the non-messaging type code in Python, "off duty" and the messaging type code in TypeScript, C# and Go; an object built with no timestamp is stamped from the clock in C# and refused in Go.
- First survey what each of the six builders writes for every optional input left unset (messaging, Mic-E message, type code, timestamp, symbol, path, destination, ambiguity, compression) and record the table in notes/round-4/DEFAULTS.md.
- Decisions:
  - A builder never reads the clock. An object or timestamped report built with no timestamp given is refused as `missing-field` (an object's timestamp is already `missing-field` in codes.json). A library may offer a separate, explicit "now" helper.
  - A station that is not said to message does not: positions default to the non-messaging identifiers (`!`, `/`), and Mic-E to the `'` type code, per "Mic-E messaging from a builder".
  - The Mic-E message defaults to off duty, the standard message M0 and what a Mic-E radio sends until told otherwise.
  - Any other default the survey finds differing: the choice that writes the least the program did not ask for.
- Write the defaults into the README's builder rules. generate.py gains recipes that leave each optional input out, so the comparison sees defaults from now on.

## R5. A Mic-E altitude from a builder goes in the Mic-E altitude bytes

- At 1.1.0 C# and Go write an altitude given in feet as `/A=` in the status text and one given in metres in Mic-E's own altitude bytes. FAP (aprs.fi) and aprslib do not read `/A=` in a Mic-E report, so the first is invisible to them.
- Decision: a Mic-E builder writes an altitude in the Mic-E altitude bytes whatever unit it was given in, rounded once to the nearest metre from the value given ("Values between steps are rounded"). An encoder given neutral data does the same unless the data came from a `/A=` (settle how the data form tells them apart, or whether it needs to; if a decoded `/A=` in Mic-E must re-encode `identical`, say how).

## R6. A weather field that runs on by many digits

- Live 2026-11-14: `t2147483647` and `t4294967295` from a broken sensor. By the 1.1.0 rule the fields end there: 214 F is reported and the rest of the report (`7483647r000p000...`) becomes comment text with `weather-comment`.
- Decision: a fixed-width weather field whose digits run on by two or more, where the run is followed by a defined weather field or by the end of the information field, is a value out of range: `out-of-range-value` (tolerated), the value is dropped, and the fields carry on after the run. A run followed by anything else keeps the 1.1.0 rule (the field at its own width, the fields end, the rest is text), since digits at the start of a comment are common (`t0725.2V`).

## Not changed

- A temperature of 999 F stays as sent: APRS12c gives temperature no range.

## Also in the round

- compare.py prints the `unsupported` and `implementation-limit` counts per library beside every result, in the text and the JSON summary.
- aprs-c's dump tool reads NaN and Infinity tokens (it marked most non-finite lines unsupported at 1.1.0).
- generate.py makes telemetry values beyond 999 and up to 1e308, and records long enough to cross the 256-byte limit, so the runs reach R1 and the number text rule.
- Clean observed cases for the commonest live shapes with none, list to come from aprs-watch (the plain `=` position with a comment first).
- More cases that start from an AX.25 frame (15 at 1.1.0): at least one per data type.
- Helpers stay as they are; parity of KISS, telemetry scaling and timestamp resolution across libraries is not in this round.

## Process

1. Vectors writer: branch `round-4` in aprs-vectors with the rules (README), the reasoning (interpretations.md), codes.json, the cases and the tools.
2. Six library writers, each on `round-4` with the submodule at the vectors branch head, until their own suite passes.
3. Six-way runs on another machine (not the session's LXC) on fresh seeds: cases, fuzz, data, recipes, faults, non-finite. Every difference goes back to step 1 or 2. Never call a clean run proof.
4. One reviewer per PR, then merge; bump PRs; tags on Tom's word only, pinned to full SHAs.
