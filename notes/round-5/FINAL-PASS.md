# Round 5 final pass: findings from the four reviews of the joining change, with rulings

No reviewer found a fault in the joining change itself in any library. What follows is rule wording, one rule gap, older defects the reviews turned up, and small hardening. Reproducers are under /tmp/r5-rev2-<repo>/ where noted.

## A. Rules (aprs-vectors)

A1. The exception's basis is overstated (interpretations around line 446 "it goes no further, because no other element may stand anywhere"; RULED R11). APRS12c ch. 5 says a !DAO! may appear anywhere in the comment too, and only recommends it last; the older line "a DAO, which comes last (APRS12c ch. 13)" overstates "MAY appear after". RULING: say honestly that the exception rests on ch. 6 together with live traffic (APRSdroid writes the altitude there; no sender puts a !DAO! or telemetry among a frequency's fields in 297 million lines), that ch. 18's 10-byte slots are positional so this is a moderate stretch, and that reading `/A=` as not part of the comment at all was considered and rejected because it would make `PHG2360/A=0001005/x` a PHGR and give a tone in `146.520MHz /A=000100T100`. Correct the ch. 13 line to what ch. 13 says.

A2. Mic-E: no stated order between a later Mic-E altitude and a `/A=`. Today `x/A=000100}` reads lenient as a Mic-E altitude taken from `100}` (406,417 ft), comment `x/A=000`, and strict as 100 ft. RULING: a whole `/A=` altitude is looked for BEFORE a later Mic-E altitude (the leading Mic-E altitude at the start of the status text is unaffected), consistent with "A /A= altitude wins over a Mic-E or compressed one": `x/A=000100}` is altitude 100 ft, comment `x}`, in lenient and strict alike. State the order in the README Mic-E rule and the interpretations section, add cases (this one; one where the later Mic-E altitude stands clear of the `/A=` and both are present; one where a Mic-E altitude at the start and a `/A=` are both present). All six libraries change.

A3. Weather software type and unit: "judged whole on the text left" plus "the start of a lifted element counts as the end" invites reading `t058xRSW|!!!!|abc` as software `x`, unit `RSW`, comment `abc`. The six give comment `xRSWabc`. RULING: keep the six's reading; word it "it must be the whole of the text left after the fields, and stand whole as sent"; add that case.

A4. G1 is stated only in interpretations. README: between a frequency and its fields, or between two fields, nothing but a whole `/A=` may stand, so a space before the `/A=` ends the fields.

A5. Add Mic-E cases: `146.520MHz/A=000100 T100 x` in status text (the exception applies) and `146.520MHz"4e} T100 x` (a Mic-E altitude cuts the fields).

A6. Two halves of a UTF-8 character with a lifted element between them join into one character in the comment (`PHG33\xC3!W12!\xA930` gives comment `PHG33é30`). RULING: that is right and should be stated: the comment is the bytes left, in order, and is decoded as text once, after lifting; text is not an element, so the principle does not apply to it. Add the case.

A7. The CHANGELOG wording in several libraries lists "before a voice frequency" among the exception's positions; check what the final rule sentence says after G2 and make IMPLEMENT.md give the one sentence the libraries should quote.

## B. Per library

All six: A2 (a whole `/A=` before a later Mic-E altitude). Performance: a decoder fed untrusted text must not go quadratic. Time a 200 KB comment of each of: repeated `{`, repeated `PHG1`, repeated `|!!|`, repeated `/A=000001`, repeated `!W12!`, repeated `"4e}` (Mic-E), in a position report and (where it applies) a Mic-E status text, and fix anything that is not roughly linear (well under a second for 200 KB), with a test that would catch a regression (a size-doubling ratio test, not a wall-clock limit). aprs-c is capped at 512 bytes and need only confirm.

aprs-go:
- comment.go:358 calls stationExtension(&found, c[i:t.pieceEnd(i)]) and pieceEnd (lifttext.go:51) scans to the next lifted place for every PHG/RNG/DFS candidate: quadratic, new in this round (200 KB of `PHG1`: 6.7 s, was 0.02 s). Cap the scan (an extension is at most 9 bytes). Reproducer /tmp/r5-rev2-aprs-go/repro-pieceend.sh.
- braces() is quadratic on a run of `{` (200 KB: 16 s), older.
- CHANGELOG: exception wording per A7.

aprs-rs:
- src/comment.rs:398: the brace search is quadratic on a run of `{` (100 KB: 4.3 s), older. Reproducer /tmp/r5-rev2-aprs-rs/long/brace1.hex.gz.

aprs-c:
- The boundary table (src/internal.h:186, 8 slots; at most 6 lifts today) has no test and no hard stop: if it were ever full, src/comment.c:49 would silently drop the boundary, which would allow a join. Make a full table an implementation-limit (limit name documented in limits.json and the header) rather than a dropped boundary, add a static assertion or comment tying the size to the number of lift kinds, and add a test with all six lifts in one comment (reproducer /tmp/r5-rev2-aprs-c/data/maxlift.hex.gz).
- pdn_aprs__cbuf_set (src/comment.c:11): the overflow branch sets n=0 but leaves nbrk unset; set it. mice.c:329 ignores the return value: check it.

aprs-ts:
- Decoded packets still share memory with the caller's buffer when the input is a Node Buffer: `Buffer#slice` returns a view, not a copy (src/header.ts:65 and :229). The 1.2.0 fix only covered a plain Uint8Array. Copy explicitly (for example `new Uint8Array(line.subarray(...))` or `Uint8Array.prototype.slice.call`), for every entry point, and add tests that use a real Buffer (and a subarray of one) and mutate it after decoding. Reproducer: node /tmp/r5-rev2-aprs-ts/own.mjs.
- With only the `missing-space-after-locator` tolerance turned off, a Mic-E status text with a locator with no space, then a PHG or RNG, then a later Mic-E altitude (`` `(_fn"Oj/IO91/GPHG3330h{55}ello ``) lifts the later altitude and warns mic-e-altitude-not-first before rejecting for the missing space (src/decode/reports.ts:408 against :433). The missing space is always met first (RULED R9): reject first, with no altitude warning, as aprs-py does.

aprs-cs:
- FrequencyCodec.TryRead two-argument overload (FrequencyCodec.cs:15) is unused: remove if not public API.
- CHANGELOG: exception wording per A7.

aprs-py: nothing beyond the items for all six.
