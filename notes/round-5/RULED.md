# Round 5: details settled by the vectors writer

Each point the brief left open, how it was settled and why. Branch `round-5` of aprs-vectors. The reasoning is also in interpretations.md under "A garbled timestamp before an uncompressed position".

## R1. A compressed position after seven timestamp-like bytes: confirmed, it does not win

The brief's choice stands: only an uncompressed position after the seven bytes overrules the reading straight after the DTI. A compressed position is 13 bytes that start with a symbol table character and stay within base-91 (APRS12c ch. 9), so its decoding is equally weak evidence at either offset, and the existing order (straight after the DTI first) is kept. Two further reasons:

1. A `/` or `@` report with no timestamp and a compressed position has the second byte of its compressed longitude in seventh place, which is `z`, `/` or `h` about one time in thirty; letting a compressed reading from byte eight win would misread some of those, while the gain is only the rarer report whose damaged first byte happens to be a symbol table character and which is followed by a compressed position.
2. Live traffic does not need it. Over 297 million APRS-IS lines (40 days, 2026-10-01 to 2026-11-14, from /home/tf/aprs-corpus), aprs-py 1.2.0 with the ruling patched in changes 21 packets from 13 stations (the reviewer's independent count), every one a damaged first byte before the station's own uncompressed position; with a compressed position after the seven bytes also winning, it changes the same 21 and no others. (A first count gave 20 from 12: it left out 2026-10-14.).

The object rule takes a compressed position after timestamp-like bytes too; that is unchanged and not made consistent here, since an object "always has a timestamp" (APRS12c ch. 11) and objects without one are the spec's own examples (interpretations.md, Errata), a different trade.

Cases: `position/garbled-timestamp-before-a-compressed-position`, `position/compressed-without-timestamp-seventh-byte-z`.

## R2. The strict result

Rejected by `malformed-timestamp`, as the four corpus cases are. Every path through the rule gives `malformed-timestamp` (tolerated, so a strict decoder rejects) or the same code as an error, and the timestamp is met first, before anything in the position. Under strict options the uncompressed position after the seven bytes may not decode (a lower-case hemisphere, say) where it does leniently; the strict result is the same rejection either way.

## R3. What the report re-encodes to

As every garbled timestamp does: the data has no timestamp, so it re-encodes as a report without one, `=` for `@` and `!` for `/`, `equivalent` with that `canonical_info` (`corpus/0536`, `deviation/missing-timestamp`). The live packet keeps `h-5b10170.DsVP` as `weather-comment` text, so it re-encodes `refused`, `field-not-allowed`, as `corpus/1215` and `corpus/1307` (same software, same shape) do.

## R4. Status and object timestamps

- **Status:** the question does not arise. A status report (`>`) has no position, so nothing competes with the seven bytes: a timestamp that is not six digits then `z` is status text, as at 1.2.0, with no diagnostic. No rule change and no case.
- **Objects:** already covered. The object rule asks whether the seven bytes look like a timestamp (six digits, or ending `z`, `/` or `h`) and a position follows, and reads after them when so, whatever an object-without-timestamp reading would give. `object/garbled-timestamp` is exactly the case where both readings decode (`ABCDEFz5301.` reads as a compressed position straight after the name; checked with aprs-py), and `deviation/object-with-garbled-timestamp` and `object/garbled-timestamp-judged-on-the-position` pin the rest. No case added.

## R5. Smaller points the wording needed

1. **The time indicator is required; six digits are not enough.** The object rule also accepts six digits and any seventh byte. For a position report that adds nothing: six digits after the DTI never read as a position (a compressed position never starts with a digit, an uncompressed one has its point fifth), so the existing rule already skips them. Case: `position/seven-bytes-not-ending-in-a-time-indicator-before-an-uncompressed-position` (two damaged bytes; the compressed reading stands).
2. **Only a compressed reading is ever overruled.** An uncompressed position straight after the DTI has a minutes digit (or an ambiguity space) in seventh place, never `z`, `/` or `h`.
3. **"An uncompressed position follows" is the whole position**, latitude, symbol table, longitude and symbol code, as for an object. Case: `position/garbled-timestamp-before-a-position-that-does-not-decode` (longitude hemisphere `X`).
4. **Existing cases:** none changes. A script decoded all 2,054 decode cases with aprs-py 1.2.0 and with the ruling patched in, lenient and strict: no difference. The four the brief names (corpus/0536, 0991, 1095, 1307) are confirmed already read after the seven bytes.
5. **README "Whether a position follows" sentence** now covers report and object alike ("or decodes": the reading straight after the DTI is judged the same way, on the position alone).

## R6. The tolerance check when strict rejects by another code

Turning off only the tolerance a case used can change how the rest of the packet is read and bring out another, still tolerated, defect: in `mic-e/telemetry-split-by-an-altitude-is-text` the altitude is then not lifted, no telemetry is left, and the locator's missing space is a warning, while strict rejects by it. The check is not skipped (the reviewer's form, adopted): for a case whose lenient diagnostics name exactly one tolerable code, when `strict` is a reading or is rejected by that code the check must give the `strict` result, as always; when `strict` is rejected by a different code the check must give a reading whose diagnostics include that code as a warning. A first proposal (check only when strict is rejected by that same code) would have dropped 61 valid checks, the cases whose strict result is a full reading (late data extensions, `position-not-at-start`, later Mic-E altitudes). check.py's both-sides coverage counts only the first kind, since a rejection by another code does not show that tolerance's strict side.

## R7. The Mic-E locator's space

Rule as written (README Mic-E, interpretations "Where a Mic-E locator is read"): the space is judged on the decoder's own result, the status text after the locator with every element the decoder lifts under the options in force taken out (later altitude, base-91 telemetry, `!DAO!`), lifted as for the data; an element that would exist only by joining the text either side of a lifted one is not lifted; a PHG or RNG straight after the locator is read in the separator's place and needs the space (unchanged: `IO91/GPHG3330 hello` keeps its warning in all six). When the locator has its space, that space is the separator, and the comment then loses at most one further leading space or `/`.

Decided from the existing rules, not stated before:
1. **Two spaces after the locator give the comment `x`, not ` x`.** The separator is not the comment's one dropped delimiter: `mic-e/lower-case-locator-missing-its-space` writes `X` as `IO91/G /X`, and "Where a voice frequency goes" says ` /X` is written after a locator; both read back as `X` only if the separator and the dropped `/` are two different bytes. `mic-e/comment-starting-with-a-space-after-a-phg` (no separator there, two spaces after a PHG, comment ` W...`) agrees. So `IO91/G  x` is `x`, with or without a lifted element between.
2. **A space then nothing** (`IO91/G"4e} |...|`): the locator has its space; no comment.
3. **A comment that is a `!DAO!` only once joined** (`!W12! hi` from `!W1"4e}2! hi`) is text, and re-encodes `refused`, `text-reads-as-field`, since written it reads back as a `!DAO!`.

Cases and who fails at the round-5 heads (dumps from builds of each head under /tmp/r5b):
- `mic-e/locator-space-judged-after-a-later-altitude`, `...-after-an-altitude-and-telemetry`, `...-after-a-dao-and-an-altitude`: all six pass.
- `mic-e/locator-space-with-a-dao-only-joined-across-an-altitude`: cs (drops the warning, comment `!W12!hi`), rs, py, go (drop the warning); ts and c pass.
- `mic-e/two-spaces-after-the-locator-and-a-later-altitude`, `mic-e/telemetry-split-by-an-altitude-then-two-spaces`, `mic-e/two-spaces-after-the-locator-and-telemetry`: rs, py, c, go give ` x` (and write `/ x`); cs and ts pass.
- `position/garbled-timestamp-before-a-lower-case-hemisphere`: all six pass.

## R8. Where a locator and a PHG or RNG are, as sent (targeted Mic-E run, aprs-ts alone against five)

1. **A locator is read only where it is as sent**: at the start of the status text (after any type code) or straight after a Mic-E altitude that is itself at the start. One that would be there only once a `!DAO!`, telemetry or an altitude before it is lifted is comment text; so is one straight after a later altitude (`!w3U!abc}Io91/G`), which the old wording ("straight after a Mic-E altitude") left open. Lifting an element never moves what follows it to a place it did not have. Wording now says "as sent". Cases: `mic-e/locator-not-at-the-start-until-a-dao-is-lifted`, `mic-e/locator-not-at-the-start-until-a-dao-and-telemetry-are-lifted`, `mic-e/locator-straight-after-a-later-altitude-is-text`, `mic-e/locator-not-straight-after-the-altitude-until-telemetry-is-lifted`.
2. **A PHG or RNG is straight after the locator only where it is so as sent.** The README said this for the type code only (round 4's `mic-e/phg-reached-only-by-lifting-a-dao-is-late`, `mic-e/an-rng-reached-only-by-lifting-an-altitude-is-late`); extended by a clause to the leading altitude and the locator, and to DFS. A PHG split by a lifted element is not stated as a rule but recorded as a provisional reading (interpretations, Text joined across a lifted element). Cases: `mic-e/phg-after-a-locator-only-once-a-dao-is-lifted-is-late`, `mic-e/rng-after-a-locator-only-once-telemetry-is-lifted-is-late`, `mic-e/phg-after-a-locator-only-once-an-altitude-is-lifted-is-late`, `mic-e/phg-split-by-an-altitude-after-a-locator-is-text`.
3. **What counts when the locator's space is judged**: only a later Mic-E altitude, base-91 telemetry and a `!DAO!` are taken out; a late PHG, RNG or `/A=` is comment content and counts as text, so `'IO91/G"4e}PHG3330` keeps `missing-space-after-locator` (as all five give).

Expected values are the five libraries' (identical data, diagnostics, strict result and bytes written in /tmp/r4run/mice), checked by hand against the rule.

## R9. Which code strict rejects by: a locator without its space and a later altitude

Strict declines a later Mic-E altitude, so it lifts none; it rejects by `mic-e-altitude-not-first` when the text left once telemetry and a `!DAO!` are lifted holds an altitude across a lifted place (README Mic-E; see R10.1 for which runs count). When the locator also lacks its space, "A packet is read in order" and the order-of-checks sentence do not pull apart: the second concerns elements a decoder lifts, and strict lifts no later altitude. Both the altitude check and the locator's space are judgements of the text left, met in reading order within it; the space is at the byte after the locator, and an altitude starts there at the earliest and is complete only at its `}`, so the missing space is always met first and strict rejects by `missing-space-after-locator` (as `mic-e/phg-after-a-locator-missing-its-space-then-an-altitude` already did). With the locator's space present, all six reject by `mic-e-altitude-not-first`. A run that needs a locator byte (`/G}`, `G"e}`) is never an altitude, so there is no altitude defect at all there.

Cases: `mic-e/strict-missing-space-when-an-altitude-would-take-locator-bytes`, `mic-e/strict-missing-space-when-the-altitude-left-needs-a-locator-byte`, `mic-e/strict-missing-space-before-a-later-altitude-and-a-dao`, `mic-e/strict-missing-space-before-a-later-altitude-and-telemetry`, `mic-e/strict-missing-space-before-a-whole-altitude-and-telemetry`, `mic-e/strict-missing-space-before-text-left-across-a-dao` (expected values cs, rs, c and go's, checked by hand; ts and py changed to match). The ts-alone lenient lines in that run were R8.2 on a path ts had not fixed (a PHG or RNG after a leading altitude and the locator), and a PHG split by a `!DAO!`, which is the joined reading below.

## R10. Second-look review: the text made to match the six

1. **The strict altitude check counts any run that crosses a lifted place**, not only the first. R9 first said "only the first run"; no library followed it, and all six reject as at 1.2.0. R9's conclusion stands, since a locator without its space is still always met first; the three R9 cases whose descriptions leaned on the "first run" reason (`...-first-altitude-left-does-not-cross`, `...-an-altitude-across-telemetry-is-not-the-first`, `...-first-altitude-left-is-whole`) keep their ids and expected values and now give the missing-space-first reason. New: `mic-e/strict-reads-text-left-across-a-dao-without-a-locator`, `mic-e/strict-reads-text-left-across-telemetry-after-a-locator-with-its-space`.
2. **The bytes of a PHG, RNG or DFS read straight after the type code or the locator are never part of an altitude**, as a locator's are. New: `mic-e/strict-altitude-search-skips-a-phg-after-the-type-code`.
3. **"As sent" is the status text once 0xFF padding is removed** (it follows from "Mic-E 0xFF padding is in the status text"). New: `mic-e/dao-is-read-once-0xff-padding-is-removed`.
4. **DFS goes with PHG and RNG** wherever the three belong together. New: `mic-e/dfs-straight-after-a-locator-missing-its-space`.
5. **Joined text** is in one place now, interpretations "Text joined across a lifted element". New provisional pin: `mic-e/phg-split-by-a-dao-after-a-locator-is-text`.

All six new cases pass in all six libraries at their round-5 heads (cs b670520, rs 783ac63, py d629c59, ts 0c6e685, c 8c2f843, go dffbb51; dumps from builds under /tmp/r5b).

## R11. Lifting an element never joins the text either side of it (owner's decision, option b)

Ruling: every element, in every kind of report, is recognised only where its bytes stand whole as sent (Mic-E: once 0xFF padding is removed), and nothing is read across the place an element was lifted from; where an element must be followed by a space or the end, the start of a lifted element counts as the end. The exception is the spec's: a `/A=`, which APRS12c ch. 6 lets stand "anywhere in the comment", does not cut a voice frequency off from what follows when it stands before the frequency, between it and its fields, or between two of its fields; it still splits any element it stands inside, and a `!DAO!` or telemetry between a frequency and its fields does cut them off. Interpretations, "Lifting an element never joins the text either side of it".

- **Comment and re-encoding.** The comment is the fragments left, in order, nothing marking the joins, with one leading space or `/` dropped as before. Where the text left would read back as an element (`PHG3330`, `/A=000123`, `{55}`, `|!:&0'p|`), the report re-encodes `refused`, `text-reads-as-field`; otherwise as usual.
- **Still judged on the text left**: a Mic-E locator's space, the one space dropped after a voice frequency and its fields, and the comment's leading delimiter. They place the comment and recognise no element, so they are not joining. (Judging them on adjacency instead was tried and rejected: it changes more cases and the spacing of APRSdroid comments for no gain.)
- **Strict Mic-E.** A later altitude is read as text by a strict decoder and nothing joins into one, so strict never rejects by `mic-e-altitude-not-first`; the R9/R10 rules for an altitude left across a lifted place are gone. The code stays tolerable, its strict side a different reading (as `data-extension-in-comment`'s is).
- **Single-tolerance check.** Its form for a strict rejection by another code stays. `mic-e/telemetry-split-by-an-altitude-is-text` now names two tolerable codes, so it leaves the check; four locator cases (`mic-e/locator-space-judged-after-a-later-altitude`, `...-after-an-altitude-and-telemetry`, `...-after-a-dao-and-an-altitude`, `mic-e/two-spaces-after-the-locator-and-a-later-altitude`) still need the form.
- **Live corpus.** 297,417,911 APRS-IS lines over 40 days (/home/tf/aprs-corpus, 2026-10-01 to 2026-11-14), compared with a patched aprs-py: with no exception 8,498 packets from 4 stations change, all APRSdroid writing `/A=` straight after the frequency (K7PIA-9 655 and K3WHO-5 7, real tone and offset that would be lost; VA3CRL-10 4,282 and VA3BPR-10 3,554, `-600` read as -6000 kHz either way); with the exception none changes. No joined telemetry, PHG, RNG, DFS, signpost or `/A=` occurs in live traffic. Reading ch. 18's layout as fields with an altitude allowed between them is a mild stretch; it goes no further, since nothing else may stand anywhere.
- **Renamed** (round-5 ids, unreleased): `mic-e/telemetry-left-once-an-altitude-is-lifted-then-a-spaced-comment` -> `mic-e/telemetry-split-by-an-altitude-is-text`, `mic-e/two-spaces-after-telemetry-left-once-an-altitude-is-lifted` -> `mic-e/telemetry-split-by-an-altitude-then-two-spaces`, `mic-e/phg-joined-across-an-altitude-after-a-locator-is-late` -> `mic-e/phg-split-by-an-altitude-after-a-locator-is-text`, `mic-e/phg-split-by-a-dao-after-a-locator-is-late` -> `mic-e/phg-split-by-a-dao-after-a-locator-is-text`, `mic-e/strict-rejects-an-altitude-left-across-a-dao-without-a-locator` -> `mic-e/strict-reads-text-left-across-a-dao-without-a-locator`, `mic-e/strict-rejects-an-altitude-left-across-telemetry-after-a-locator-with-its-space` -> `mic-e/strict-reads-text-left-across-telemetry-after-a-locator-with-its-space`, `mic-e/strict-missing-space-when-the-first-altitude-left-does-not-cross` -> `mic-e/strict-missing-space-before-a-later-altitude-and-a-dao`, `mic-e/strict-missing-space-when-an-altitude-across-telemetry-is-not-the-first` -> `mic-e/strict-missing-space-before-a-later-altitude-and-telemetry`, `mic-e/strict-missing-space-when-the-first-altitude-left-is-whole` -> `mic-e/strict-missing-space-before-a-whole-altitude-and-telemetry`, `mic-e/strict-missing-space-before-an-altitude-left-across-a-dao` -> `mic-e/strict-missing-space-before-text-left-across-a-dao`. The four released ids that change keep their ids, with descriptions saying so.

The 10 cases whose readings change (old and new, from aprs-py at the round-5 head and the reference reading):

```
- mic-e/altitude-is-looked-for-before-the-dao-is-lifted
    strict old: rejected error:mic-e-altitude-not-first
    strict new: {"comment": "\"13.7V7e}"} 
- mic-e/strict-rejects-an-altitude-joined-across-telemetry-and-a-dao
    strict old: rejected error:mic-e-altitude-not-first
    strict new: {"telemetry": {"sequence": 86, "analog": [3680]}, "comment": "654.57S/10742fl!3>/'\";X}3"} 
- mic-e/strict-rejects-an-altitude-joined-across-the-dao
    strict old: rejected error:mic-e-altitude-not-first
    strict new: {"comment": "654.57S/10742fl!X>/'\";X|!wII!}3"} 
- mic-e/an-rng-reached-only-by-lifting-an-altitude-is-late
    lenient old: {"range_miles": 11, "altitude_feet": 282.1522309711286, "comment": "45.500MHz JANEK"} mic-e-altitude-not-first,data-extension-in-comment
    lenient new: {"altitude_feet": 282.1522309711286, "comment": "RNG001145.500MHz JANEK"} mic-e-altitude-not-first
    written old: `0M`lg>>/`"4m}RNG001145.500MHz JANEK_1
    written new: REF text-reads-as-field
- mic-e/telemetry-split-by-an-altitude-is-text
    lenient old: {"telemetry": {"sequence": 25, "analog": [470, 6536, 56, 5292, 2667], "digital": 113}, "altitude_feet": 255.9055118110236, "comment": "DG2MM"} mic-e-altitude-not-first
    lenient new: {"altitude_feet": 255.9055118110236, "comment": "|!:&0hl!Y[/>='p| DG2MM"} mic-e-altitude-not-first,missing-space-after-locator
    written old: `(_fn"Oj/`"4e}IO91/G DG2MM|!:&0hl!Y[/>="7|
    written new: REF text-reads-as-field
- mic-e/telemetry-split-by-an-altitude-then-two-spaces
    lenient old: {"telemetry": {"sequence": 25, "analog": [470, 6536, 56, 5292, 2667], "digital": 113}, "altitude_feet": 255.9055118110236, "comment": "x"} mic-e-altitude-not-first
    lenient new: {"altitude_feet": 255.9055118110236, "comment": "|!:&0hl!Y[/>='p|  x"} mic-e-altitude-not-first,missing-space-after-locator
    written old: `(_fn"Oj/`"4e}IO91/G x|!:&0hl!Y[/>="7|
    written new: REF text-reads-as-field
- mic-e/phg-split-by-an-altitude-after-a-locator-is-text
    lenient old: {"phg": {"power": 3, "height": 3, "gain": 3, "directivity": 0}, "altitude_feet": 255.9055118110236, "comment": " "} mic-e-altitude-not-first,data-extension-in-comment
    lenient new: {"altitude_feet": 255.9055118110236, "comment": "PHG3330  "} mic-e-altitude-not-first
    written old: `(_fn"Oj/'"4e}IO91/G PHG3330/ 
    written new: REF text-reads-as-field
- mic-e/strict-reads-text-left-across-a-dao-without-a-locator
    strict old: rejected error:mic-e-altitude-not-first
    strict new: {"comment": "x\"4e}abc}"} 
- mic-e/strict-reads-text-left-across-telemetry-after-a-locator-with-its-space
    strict old: rejected error:mic-e-altitude-not-first
    strict new: {"telemetry": {"sequence": 25, "analog": [470, 6536, 56, 5306, 625]}, "comment": "x\"4e}hello}"} 
- mic-e/phg-split-by-a-dao-after-a-locator-is-text
    lenient old: {"phg": {"power": 3, "height": 3, "gain": 3, "directivity": 0}, "comment": "x"} data-extension-in-comment
    lenient new: {"comment": "PHG3330 x"} 
    written old: `(_fn"Oj/`IO91/G PHG3330x!W12!
    written new: REF text-reads-as-field
```

New cases: `position/phg-split-by-telemetry-is-text`, `position/rng-split-by-a-dao-is-text`, `position/dfs-split-by-telemetry-is-text`, `position/altitude-split-by-a-dao-is-text`, `position/frequency-split-by-an-altitude-is-text`, `position/tone-split-by-an-altitude-is-text`, `position/tone-after-an-altitude-after-a-frequency`, `position/offset-after-an-altitude-between-two-fields`, `position/frequency-after-a-phg-and-an-altitude`, `position/tone-after-a-dao-after-a-frequency-is-text`, `position/tone-after-telemetry-after-a-frequency-is-text`, `object/signpost-split-by-a-dao-is-text`, `weather/field-split-by-telemetry-is-text`, `weather/software-and-unit-split-by-a-dao-is-text`, `mic-e/phg-split-by-telemetry-is-text`, `mic-e/altitude-split-by-a-mic-e-altitude-is-text`, `mic-e/dao-split-by-telemetry-is-text`, and the observed `corpus-finding/aprsdroid-tone-and-offset-after-an-altitude` (APRS-IS 2026-10-01), `corpus-finding/aprsdroid-tone-after-an-altitude` (2026-10-02), `corpus-finding/aprsdroid-offset-in-the-wrong-unit-after-an-altitude` (2026-10-01). `PHG8270/A=000813147.490MHz` itself is `corpus/0039`, unchanged.

## R12. After the joining run: seven rulings (referee's triage, all recommendations accepted)

From RUN-JOIN-TRIAGE.md (six-way runs s10101 and s10202 at vectors 8ce4dac). Wording in the README rules and, for each decision, a paragraph in interpretations "Lifting an element never joins the text either side of it". Vectors 0445b8c.

1. **G1. A field is its space and value together as sent.** A `/A=` may stand before a field's space but not between the space and the value: `146.520MHz /A=000100T100` has no tone, and in `146.520MHz T100 /A=000100-060 x` the tone is read and `-060` is text. The exception lets an altitude stand anywhere; it does not pair a value with a space left on the other side of it. The README exception sentence now reads "between a voice frequency and its fields, or between two of its fields". Live traffic: 68,480 lines (APRS-IS, 2026-10-01 to 2026-11-15) put a space before a `/A=` after a frequency with text straight after it, mostly direwolf digipeaters' beacons; in none is that text a field (the triage's "never with the space before the `/A=`" was wrong; the conclusion, no live packet changes, stands). Cases: `position/tone-after-an-altitude-with-its-space-before-the-altitude-is-text`, `position/offset-after-an-altitude-with-its-space-before-the-altitude-is-text`, `position/spaces-either-side-of-an-altitude-after-a-frequency`.
2. **G2. A voice frequency is read at the start of the text left**, after at most one space or `/` judged on the text left like the comment's leading delimiter (the same byte, ch. 18's free text delimiter). Any lifted element may stand before the frequency, which `corpus/0493` and `object/signpost-frequency-and-altitude` already had; "before a voice frequency" left the exception sentence. Cases: `position/frequency-after-a-slash-and-telemetry`, `mic-e/frequency-after-a-slash-and-a-later-altitude`.
3. **G3. Free text a space would make read as a field, after a `/A=` written after a frequency or its fields, is written straight after the `/A=`** (`146.520MHz T100/A=000100-060 x`, re-encodes `identical`). Straight after a field with no `/A=` it takes a space and a `/` (`146.520MHz T100 /-060 x`). After braces, free text takes its space and no `/` unless needed, since braces cut it off from the frequency (aprs-c fault, no new rule). Cases: `position/text-reading-as-an-offset-after-a-tone-and-an-altitude`, `object/text-after-a-frequency-and-a-signpost-takes-its-space`, `object/text-after-a-tone-and-a-signpost-takes-no-slash`, `object/tone-after-a-space-and-a-signpost-is-text`, `encode/text-after-a-frequency-and-a-signpost-takes-its-space`.
4. **W1. The comment's one leading delimiter is judged on the text left** (already the rule; the README now gives ` |!!!!|x` and `/!W12!x`, comment `x`). Case: `position/leading-space-before-telemetry`.
5. **W2. A PHGR's rate byte and `/` count only where they follow the PHG's seven bytes as sent**; split off by a lift, the PHG is read and they are text (`PHG23605!W12!/x`: PHG 2360, comment `5/x`, written `PHG2360/5/x!W12!`). Cases: `position/phg-rate-split-by-a-dao-is-text`, `position/phg-rate-after-an-altitude-is-text`.
6. **W3. A weather software type and unit are judged whole on the text left after the fields**: a lift before or after changes nothing, one inside makes it text. The run-on clause says text after a lifted element "is not joined to the run's digits" instead of "is comment text on its own". Case: `weather/software-and-unit-after-a-dao`.
7. **W4. Of two `/A=`, the first that stands whole is the altitude; later ones are comment text**, their `/` treated like any other (FAP takes "the first occurrence", FAP.pm line 1192). Interpretations, Delimiters: "A `/` that begins the `/A=` lifted as the altitude is not a delimiter". The encoder writes the altitude before the free text, so a later `/A=` reads back as text. Cases: `position/second-altitude-is-text`, `position/whole-altitude-after-one-split-by-a-dao`, `position/second-altitude-after-a-space-is-text`.

Also the go decoder fault (a field read across a lifted `!DAO!`, telemetry, late extension or braces), no new rule: `position/tone-after-a-space-and-a-dao-is-text`, `position/tone-after-a-space-and-telemetry-is-text`, `position/offset-after-a-space-and-a-dao-is-text`, `position/tone-after-a-space-and-a-late-range-is-text`, `object/tone-after-a-space-and-a-signpost-is-text`.

No recommendation contradicted an existing rule or case. `tools/compare.py` compares nested diagnostics as multisets at every depth (doctest; check.py runs it).

## R13. Final pass: the rule text after four reviews (FINAL-PASS.md section A)

Vectors 1ada816.

1. **A1. The exception's basis, stated honestly.** APRS12c (fetched from wb2osz/aprsspec, APRS12c.pdf) ch. 6: "The altitude may appear anywhere in the comment"; ch. 5: "a 5 byte field !DAO! appearing anywhere in the position comment field", with "RECOMMENDATION: Recommend placing this option on the END of all other position comment text"; ch. 13: telemetry "MUST appear after the free-form comment text entered by the end-user, but before any DAO or Mic-E type codes. The DAO extension MAY appear after the Base91 Telemetry extension"; ch. 18: the frequency in "the first 10 bytes", then "2nd 10-BYTES Optional Added fields (with leading space)". So the spec's wording does not single out the `/A=`. Interpretations now says the exception rests on ch. 6 together with live traffic (APRSdroid writes the altitude there; no sender puts a `!DAO!` or telemetry among a frequency's fields in 297 million lines), that ch. 18's 10-byte slots are positional so this is a moderate stretch, and that reading a `/A=` as not part of the comment at all was considered and rejected (`PHG2360/A=0001005/x` would be a PHGR, `146.520MHz /A=000100T100` would have a tone). R11's "a mild stretch; it goes no further, since nothing else may stand anywhere" is withdrawn. The three places that said a DAO "comes last" or that telemetry and a DAO "go at the end" by ch. 13 now quote ch. 13 and ch. 5; the ch. 6 quotation is now verbatim ("may appear", not "may be").
2. **A2. The search for a later Mic-E altitude never uses the bytes of a `/A=` that stands whole as sent** (the one behaviour change; coordinator's second ruling, replacing a first draft that moved the `/A=` ahead of telemetry in Mic-E, rejected because the same bytes would be telemetry in every other report). No reordering: the README Mic-E rule states the whole order in one place (Rev 0 telemetry, type code and suffix; altitude at the start; locator; PHG/RNG/DFS at the start; later Mic-E altitude; telemetry and `!DAO!`; `/A=`; braces; late PHG/RNG/DFS; frequency) with this exclusion, as for a locator's bytes and a PHG's at the start. A `/A=` inside a valid telemetry block stays the block's bytes (`|!/A=000100|` is a valid block, so telemetry, no altitude); a later altitude overlapping a whole `/A=` inside bars would need its `}` inside them, and `}` is not base-91, so the exclusion and telemetry never meet. A `/A=` that is not whole is text and protects nothing. The locator's space is unaffected. Existing cases: none changes; a script found four Mic-E inputs with a `/A=` and a later-altitude candidate (`corpus/0657`, `corpus/1353`, `mic-e/an-altitude-from-a-later-a-is-written-back-as-a`, `mic-e/text-altitude-equal-to-the-bytes-altitude-is-written-back`), by hand two with the altitude at the start and two clear of the `/A=`, and all 2,090 decodable cases decode the same, lenient and strict, with the exclusion prototyped in aprs-py. Cases: `mic-e/altitude-before-a-later-mic-e-altitude-it-overlaps`, `mic-e/later-mic-e-altitude-clear-of-an-altitude` (the overlapping `100}` is skipped and `"4e}` after it lifted), `mic-e/leading-mic-e-altitude-and-an-altitude` (reading unchanged; canonical `/A=000100x}` without the space the old rule needed), `mic-e/altitude-inside-telemetry-is-telemetry`, `mic-e/later-mic-e-altitude-overlapping-a-five-digit-altitude-is-taken`. The clean case of a clear later altitude beside a `/A=` is `corpus/0657`.
3. **A3. A weather software type and unit must be the whole of the text left after the fields, and stand whole as sent** (README Weather; interpretations). Case: `weather/software-and-unit-before-telemetry-and-text-is-text` (`t058xRSW|!!!!|abc`, comment `xRSWabc`).
4. **A4 and A7. The exception sentence**, now in the README Comments rule, interpretations and IMPLEMENT.md, word for word: "The `/A=` lifted as the altitude may stand between a voice frequency and its first field, or between two of its fields, without cutting them off; nothing else may stand there, so a space before the `/A=` ends the fields, and a `/A=` inside any element splits it." It names no position before the frequency (G2: the frequency is read at the start of the text left). The CHANGELOGs of aprs-go, aprs-cs, aprs-rs and aprs-c list "before a voice frequency"; IMPLEMENT.md asks them to quote this sentence.
5. **A5. Mic-E cases**: `mic-e/tone-after-an-altitude-after-a-frequency` (`146.520MHz/A=000100 T100 x`, the exception applies) and `mic-e/mic-e-altitude-between-a-frequency-and-its-tone-cuts-it-off` (`146.520MHz"4e} T100 x`, comment `T100 x`, written `"4e}146.520MHzT100 x`).
6. **A6. The comment is the bytes left, in order, decoded as text once after lifting**; text is not an element, so two halves of a UTF-8 character either side of a lift make one character (README Comments; interpretations). Case: `position/utf-8-character-split-by-a-dao-joins-in-the-comment`.

`tools/mice_shapes.py`: the Mic-E mode has `/A=000100}` and `/A=-00016}` among its elements, and `--comments` writes Mic-E status text too, with Mic-E altitudes and those two among the lifted elements; at seed 7, 20,000 lines each, 3,087 and 1,284 lines have a `/A=` overlapping a later-altitude candidate. No long runs of repeated elements (performance is tested in the libraries).

Who fails today (aprs-py c1c8a73, aprs-go c238ed4, their own vector suites against these vectors): both fail three A2 cases (overlapping and clear: lenient and reencode; leading altitude: reencode only) and pass the other six, including the telemetry and five-digit A2 cases, as expected.

## R14. After the final run: three re-encode classes, the majority right in each

Three-seed run at vectors 1ada816 (/tmp/r4run/s12101, s12202, s12303); data agrees in all six.

1. **aprs-cs refuses a Mic-E comment holding a second `/A=` as text** (`>/A=000123/A=-00016}^`, comment `A=-00016}` by W4). Written `/A=000123A=-00016}`, `016}` would be a later Mic-E altitude (no whole `/A=` protects it); written `/A=000123/A=-00016}`, the second `/A=` is whole, so not part of an altitude, and is text again by W4, its `/` dropped as the delimiter: the same data. A clean form exists, so refusing breaks the Encoding rule; the five are right. Cases: `mic-e/second-altitude-is-text-written-after-a-slash`, `mic-e/second-altitude-after-a-late-phg-is-written-after-a-slash`, `encode/mic-e-text-altitude-after-an-altitude-takes-a-slash`.
2. **aprs-py refuses two Mic-E comments starting with `/` after a `/A=`** (`/x}^`, `/=}_1`). The interpretations' delimiter rule writes `/` before such a comment, but `//x}` and `//=}` are later Mic-E altitudes; ` /x}^` reads back as `/x}^` (one leading space dropped, ` /x}` holds a space so is no altitude). The Encoding rule's separating space applies: the five are right. Expected bytes worked by hand: `'IO91/G PHG3330/A=-00016 /x}^` and `IO91/G /A=000100 /=}_1`. Interpretations, Delimiters, and README Encoding now name this. Cases: `mic-e/comment-starting-with-a-slash-after-an-altitude-takes-a-space`, `mic-e/comment-starting-with-a-slash-after-a-locator-and-an-altitude-takes-a-space`.
3. **aprs-py refuses a Mic-E build with comment `/{}WX`**: the same fault. After the type code `'`, `//{}` would be a leading Mic-E altitude, straight on the `/` would be dropped, and ` /{}WX` reads back as `/{}WX`. Case: `build/mic-e-comment-starting-with-a-slash-takes-a-space` (`W1AW>S5294Y:`'<Hu f#/' /{}WX`).

aprs-go (3988a59) passes all seven; aprs-py (6503755) fails the three class 2 and 3 cases and passes the class 1 ones.

## Open for a later round

- None. The joined-text point (R10, provisional) is closed by R11.
