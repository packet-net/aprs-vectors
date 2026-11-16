# Read-back audit (2026-11-15) and ruling

An audit of all six libraries at their round-5 heads asked whether the published claim holds: "Before returning a packet, each encoder decodes what it wrote and checks it matches the data it was given."

## What the audit found

| Library | Read-back design |
|---|---|
| aprs-c | One unconditional final check on every information field written: encode.c:91 decodes and compares (equal.c:188), called at encode.c:2780 and 2731. Full data, numbers within rounding. |
| aprs-ts | Nearly: encodeShaped runs `check` on every type except NMEA (src/encode/index.ts:224, 277). Compares the full neutral shape and strings; numbers only for NMEA. |
| aprs-py | Per type: `_with_comment` and `_checked` (encode.py:348, 404). None for third-party (inner only), user-defined or Agrelo (1767, 1806, 1830). Numbers compared only for NMEA. |
| aprs-rs, aprs-go | Mixed, per type. Positioned (rs encode.rs:913, go encode.go:948), message, status, telemetry, positionless weather, NMEA and Mic-E each have their own. None for raw weather, Maidenhead, query, capabilities, third-party, user-defined, test or Agrelo (rs other.rs:486-633, go other.go:583-745). Positioned data compares comment, PHG, DFS, area, DF bearing, storm, telemetry, frequency fields, signpost, DAO datum, weather text parts, altitude and range; NOT position, course, speed or timestamp; only errors count, not warnings. |
| aprs-cs | Conditional. Non-Mic-E positioned data is read back only when a comment-alone heuristic fires (CommentCodec.cs:657-672, used at AprsData.cs:102). Mic-E always (AprsData.cs:106, since 19a5820), messages (112), NMEA (AprsOtherData.cs:161). Status, telemetry, weather, raw weather, Maidenhead, query, capabilities, third-party, user-defined, test and Agrelo: rule checks only, no decode. Positioned compare: comment, frequency, PHG, signpost, area, and only the PRESENCE of altitude, DAO, telemetry, RNG, DFS. |

Wrong bytes found:
1. aprs-cs, weather extra fields (WeatherCodec.cs:517-519), written with no check. `AdditionalFields = [('#',"123")]` beside a pressure writes `...b10132#123`, which reads back cleanly as a rain raw counter of 123 and no extras; `('h',"50")` reads back as humidity 50; `('A',"A00")` as software and unit `AA00`. The other five refuse all 76 such records. Reproducer: readback-audit/csrepro/Program.cs, wx.jsonl.gz.
2. All six, the TNC2 header path. A path given as WIDE1-1 not used, then N0CALL-1 used, is written `N0CALL>APZ001,WIDE1-1,N0CALL-1*:>hi` and reads back with WIDE1-1 marked used (a path entry before a used one is used). No library decodes the header it wrote. The AX.25 frame reads back correctly. Reproducer: readback-audit/hdr.jsonl.gz.

The audit ran 1.3 million crafted encode and build records through all six (generators in readback-audit/gen_*.py; checker own.py) and found no other wrong bytes. So the gap is in the guarantee, not (beyond the two faults) in today's output: where there is no final check, correctness rests on every per-field rule being right, which is exactly what failed in aprs-cs twice.

## Ruling (coordinator; makes the published claim true)

R-RB1. Every public entry point that writes bytes from data (encode an information field, encode or build a packet, in every report type, third-party included) ends with ONE unconditional final read-back: decode the bytes written, leniently, under a well-formed header (for Mic-E, the destination the encoder computed), and compare with the data given. If they do not match, the encoder tries the next equivalent form the rules allow, and if none matches it refuses; it never returns bytes that failed the read-back. No heuristic decides whether the check runs.

R-RB2. "Matches" means: the decode has no diagnostics (no warning, no error; an info the rules attach to the form itself, such as obsolete-format for a form the data asks for, is allowed and must be named); every field of the neutral form present in the data is present in the decode and equal, and no field is present in the decode that the data did not give, with exactly these allowances, each already a rule: a number that the form holds in steps equals the given value rounded to that step ("Values between steps are rounded"); values another field determines; the cs-byte and DAO digit choices the rules leave to the encoder. The vectors writer states the comparison precisely, taking aprs-c's equal.c as the model since it already does this, so that all six compare the same things.

R-RB3. The header: writing a TNC2 line or an AX.25 frame from a header is checked the same way: the header written must read back to the same source, destination and path (entries and used marks). A path that TNC2 cannot express (an entry not marked used before one that is) is refused when writing TNC2 with the existing refusal `tnc2-cannot-carry`; AX.25 carries it. Pass-through writers of a decoded packet's information field still write that field as received (they are not encoders), but the HEADER they write is subject to this check.

R-RB4. The refusal when no rule names why the read-back failed: the existing fallback code in the Refusal reasons order (check its name in codes.json; aprs-cs calls it DoesNotReadBack). The order is unchanged: the read-back is the last check before the size check, as now.

R-RB5. The audit's generators become a shared tool (tools/readback_shapes.py or similar, deterministic for a seed, standard library only) so every future round runs them: element-shaped text at the start and end of every text field of every report type, partial element text beside every element, every user-defined id and type, Agrelo values, weather extras, and header paths.
