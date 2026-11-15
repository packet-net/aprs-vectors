# Round 5 (1.3.0): what each library implements

One decoder change, the same in all six libraries. Vectors: branch `round-5` of aprs-vectors (README, Rules the cases rely on, "Timestamps that are not there"; interpretations.md, "A garbled timestamp before an uncompressed position").

## After the final run (read first)

Three-seed run at vectors 1ada816: the data agrees in all six; three re-encode classes remain, each a lone library against five, and the five are right in each (RULED.md R14). Seven cases; the others pass them already.

- **aprs-cs** (encoder): a Mic-E comment holding a second `/A=` as text (`A=-00016}`) is refused. Write the altitude, then the comment after a `/`: the `/` makes the second `/A=` whole again, so its digits are not a later Mic-E altitude, and it reads back the same (README Encoding: refuse only data no clean form holds). Cases: `mic-e/second-altitude-is-text-written-after-a-slash` (identical), `mic-e/second-altitude-after-a-late-phg-is-written-after-a-slash`, `encode/mic-e-text-altitude-after-an-altitude-takes-a-slash`.
- **aprs-py** (encoder and builder): a Mic-E comment starting with `/` is refused where the `/` delimiter would make a later Mic-E altitude with its first bytes (`//x}`, `//=}`, `//{}`). Write a space instead, the only clean form (README Encoding, separating space). Cases: `mic-e/comment-starting-with-a-slash-after-an-altitude-takes-a-space`, `mic-e/comment-starting-with-a-slash-after-a-locator-and-an-altitude-takes-a-space`, `build/mic-e-comment-starting-with-a-slash-takes-a-space`.
- **aprs-rs, aprs-ts, aprs-c, aprs-go:** move the pin.

## Final pass

Vectors `round-5` at 1ada816 (1ada816457f86e596d1ea9dcf7706d15c28ebb2c). The rulings on FINAL-PASS.md section A (RULED.md R13). One behaviour change, the same in all six; the rest is wording and cases that pass already.

**A2, what a decoder changes (Mic-E status text only).** When you look for a later Mic-E altitude (only when there is none at the start), skip any run of three base-91 characters and `}` that shares a byte with a `/A=` standing whole as sent (`/A=` and six digits, or `-` and five), and keep searching after it, exactly as you already skip a locator's bytes and a PHG/RNG/DFS's at the start. No reordering: later Mic-E altitude, then telemetry and `!DAO!`, then `/A=` and the rest, as now; a `/A=` inside a valid telemetry block stays telemetry. A `/A=` that is not whole (five digits) protects nothing. Strict takes no later altitude, as now. The full order with this exclusion is in the README Mic-E rule.

Encoder: no new rule. A comment after a `/A=` in Mic-E status text now reads back clean with no space where `00x}` used to make a Mic-E altitude, so the canonical form drops that space (`/A=000100x}`).

Cases expected to fail in all six today (aprs-py and aprs-go do; a prototype of the change in aprs-py passes every case):
- `mic-e/altitude-before-a-later-mic-e-altitude-it-overlaps` (`x/A=000100}`: 100 feet, comment `x}`, written `/A=000100x}`)
- `mic-e/later-mic-e-altitude-clear-of-an-altitude` (`x/A=000100}y"4e}z`: `"4e}` lifted with its warning, 100 feet, comment `x}yz`)
- `mic-e/leading-mic-e-altitude-and-an-altitude` (reading unchanged; fails only on the canonical form, `/A=000100x}` with no space)

Pass today and must keep passing: `mic-e/altitude-inside-telemetry-is-telemetry`, `mic-e/later-mic-e-altitude-overlapping-a-five-digit-altitude-is-taken` (A2 limits), `mic-e/tone-after-an-altitude-after-a-frequency`, `mic-e/mic-e-altitude-between-a-frequency-and-its-tone-cuts-it-off` (A5), `weather/software-and-unit-before-telemetry-and-text-is-text` (A3), `position/utf-8-character-split-by-a-dao-joins-in-the-comment` (A6: the comment is the bytes left, decoded once after lifting).

No existing case changes (every case decodes the same with and without the prototype).

**The exception sentence.** Quote it in your CHANGELOG in place of any wording that lists "before a voice frequency" among the exception's positions (aprs-go, aprs-cs, aprs-rs and aprs-c have it today):

> The `/A=` lifted as the altitude may stand between a voice frequency and its first field, or between two of its fields, without cutting them off; nothing else may stand there, so a space before the `/A=` ends the fields, and a `/A=` inside any element splits it.

**Generator.** `tools/mice_shapes.py` now makes a `/A=` overlapping a later Mic-E altitude in both modes, and `--comments` writes Mic-E status text too; run both through your decode dump.

**Your own items** (performance on long runs of candidate elements, and each library's defects): FINAL-PASS.md section B, under your library's name. Performance is tested in the libraries, not by a case.

## After the joining run (read first)

Vectors `round-5` at 0445b8c. Seven rulings from the six-way run's triage (RULED.md R12), each in the README's Comments, Weather or Encoding rule and in interpretations "Lifting an element never joins the text either side of it". 21 new cases; aprs-cs, aprs-rs and aprs-ts pass all of them and only move their pin.

- **aprs-go** (decoder, `frequencyAt` in comment.go, the `field` closure): a frequency's field is its space and value as one run, so test `t.whole(start+at, start+at+5)` (space and four bytes) rather than from `start+at+1`, keeping the allowance for a lifted `/A=` before the space. Today it reads a field across a lifted `!DAO!`, telemetry, late PHG/RNG/DFS or braces between the space and the value, and across a `/A=` there (G1). Cases: `position/tone-after-a-space-and-a-dao-is-text`, `position/tone-after-a-space-and-telemetry-is-text`, `position/offset-after-a-space-and-a-dao-is-text`, `position/tone-after-a-space-and-a-late-range-is-text`, `object/tone-after-a-space-and-a-signpost-is-text`, `position/tone-after-an-altitude-with-its-space-before-the-altitude-is-text`, `position/offset-after-an-altitude-with-its-space-before-the-altitude-is-text`.
- **aprs-c** (encoder, `put_comment_part` in src/encode.c, the `starts_freq_field(c, n) > last` branch): it judges free text after a frequency without looking at what the caller wrote in between. After a `/A=` written after the frequency or its fields, write the comment straight on, with neither space nor `/` (G3). After braces, take the ordinary path: one space, then the comment, with a `/` only where it would not read back without one. Cases: `position/text-reading-as-an-offset-after-a-tone-and-an-altitude`, `position/offset-after-an-altitude-with-its-space-before-the-altitude-is-text` (canonical), `object/text-after-a-frequency-and-a-signpost-takes-its-space`, `object/text-after-a-tone-and-a-signpost-takes-no-slash`, `object/tone-after-a-space-and-a-signpost-is-text` (canonical), `encode/text-after-a-frequency-and-a-signpost-takes-its-space`.
- **aprs-py** (decoder, `_frequency` in src/pdn_aprs/_comment.py): when the first non-empty fragment is exactly one space or `/`, look for the frequency at offset 0 of the next non-empty fragment and drop the delimiter with it; the frequency must still stand whole in one fragment (G2). Cases: `position/frequency-after-a-slash-and-telemetry`, `mic-e/frequency-after-a-slash-and-a-later-altitude`.
- **aprs-cs, aprs-rs, aprs-ts:** move the pin.

All six pass already and must keep passing: `position/spaces-either-side-of-an-altitude-after-a-frequency`, `position/leading-space-before-telemetry` (W1), `position/phg-rate-split-by-a-dao-is-text`, `position/phg-rate-after-an-altitude-is-text` (W2), `weather/software-and-unit-after-a-dao` (W3), `position/second-altitude-is-text`, `position/whole-altitude-after-one-split-by-a-dao`, `position/second-altitude-after-a-space-is-text` (W4).

`tools/compare.py` now compares a third-party packet's inner diagnostics as a multiset; dump tools need no change.

## Lifting never joins (read first; supersedes anything below that reads a joined element)

**The rule** (README Comments rule; interpretations "Lifting an element never joins the text either side of it"). In every report, position, object, item, weather and Mic-E status text, an element is recognised only where its bytes stand whole as sent (Mic-E: once 0xFF padding is removed). The order of lifting only settles overlaps; once an element is lifted, nothing is read across the place it came from, and where an element must be followed by a space or the end, the start of a lifted element counts as the end. Exception (the sentence in Final pass above supersedes this round's earlier wording): The `/A=` lifted as the altitude may stand between a voice frequency and its first field, or between two of its fields, without cutting them off; nothing else may stand there, so a space before the `/A=` ends the fields, and a `/A=` inside any element splits it.

**What a decoder changes.**
1. Wherever an element is lifted from the comment (telemetry, `!DAO!`, `/A=`, braces, a late PHG/RNG/DFS, a later Mic-E altitude), leave a boundary at its place that no later recogniser may span (a sentinel character in a working copy of the text does it), instead of splicing the text together. Recognise telemetry, `!DAO!`, `/A=`, braces, PHG/RNG/DFS, the frequency and its fields, weather fields and the weather software type and unit only within one piece.
2. A frequency's field (`Txxx`, offset, range) may follow the boundary of a lifted `/A=` (and only a `/A=`), with its leading space after it; a field is complete when followed by a space, the end or any boundary. The frequency is still read at the start of the text left once the elements before it are lifted.
3. Judge on the text left, boundaries ignored, only: the Mic-E locator's space, the one space dropped after a frequency and its fields, and the comment's one leading space or `/`. The comment is the text left with the boundaries removed.
4. Mic-E strict: remove the check that rejects by `mic-e-altitude-not-first` when an altitude is left across a lifted place, and its precedence against a locator's missing space. A strict decoder reads a later altitude as text and never rejects by that code.

Where each library joins today, as established by running all six on the new cases (every library fails the same set): aprs-py `_comment.py` (`lift_telemetry_dao`, `_lift_rest`, `lift_comment`, `_frequency`) and `_decode.py` (`_mic_e` strict block, positioned weather tail); aprs-cs `Internal/CommentCodec.cs` (`ExtractTelemetry`, `ExtractDao`, `ExtractFrequency`) and `Internal/MicECodec.cs` (`TrailerLiftJoinsAltitude`); aprs-rs `comment.rs` (`lift_telemetry_and_dao`, `late_extension`) and `mic_e.rs`; aprs-ts `decode/positioned.ts` (`liftTelemetryAndDao`, `liftComment`, `liftMicEComment`, `frequencyAt`); aprs-c `pdn_aprs__lift_telemetry_dao`, `pdn_aprs__lift_altitude`, `pdn_aprs__lift_comment_start` and `mice.c`; aprs-go `comment.go` (`liftTelemetryAndDAO`, `lateExtension`, `frequencyAt`) and `mice.go`. These are the places to start, not a complete list.

**Encoder.** No new rule: a decoded comment that holds text that would read back as an element (`PHG3330`, `/A=000123`, `{55}`, a telemetry block) re-encodes `refused`, `text-reads-as-field` by the existing read-back. A comment after a frequency whose leading text would read as one of its fields is written straight after (`146.520MHz/A=000100T100 x`), as the Encoding rule already says.

**Changed cases** (all six fail them today): `mic-e/altitude-is-looked-for-before-the-dao-is-lifted`, `mic-e/strict-rejects-an-altitude-joined-across-telemetry-and-a-dao`, `mic-e/strict-rejects-an-altitude-joined-across-the-dao` (strict now reads), `mic-e/an-rng-reached-only-by-lifting-an-altitude-is-late` (no RNG), `mic-e/telemetry-split-by-an-altitude-is-text`, `mic-e/telemetry-split-by-an-altitude-then-two-spaces`, `mic-e/phg-split-by-an-altitude-after-a-locator-is-text`, `mic-e/phg-split-by-a-dao-after-a-locator-is-text`, `mic-e/strict-reads-text-left-across-a-dao-without-a-locator`, `mic-e/strict-reads-text-left-across-telemetry-after-a-locator-with-its-space`.

**Renamed, values unchanged** (round-5 ids; update any skip list): `mic-e/strict-missing-space-when-the-first-altitude-left-does-not-cross` -> `mic-e/strict-missing-space-before-a-later-altitude-and-a-dao`, `mic-e/strict-missing-space-when-an-altitude-across-telemetry-is-not-the-first` -> `mic-e/strict-missing-space-before-a-later-altitude-and-telemetry`, `mic-e/strict-missing-space-when-the-first-altitude-left-is-whole` -> `mic-e/strict-missing-space-before-a-whole-altitude-and-telemetry`, `mic-e/strict-missing-space-before-an-altitude-left-across-a-dao` -> `mic-e/strict-missing-space-before-text-left-across-a-dao`.

**New cases.** All six fail: `position/phg-split-by-telemetry-is-text`, `position/rng-split-by-a-dao-is-text`, `position/dfs-split-by-telemetry-is-text`, `position/altitude-split-by-a-dao-is-text`, `position/frequency-split-by-an-altitude-is-text`, `position/tone-split-by-an-altitude-is-text`, `position/tone-after-a-dao-after-a-frequency-is-text`, `position/tone-after-telemetry-after-a-frequency-is-text`, `object/signpost-split-by-a-dao-is-text`, `weather/software-and-unit-split-by-a-dao-is-text`, `mic-e/phg-split-by-telemetry-is-text`, `mic-e/altitude-split-by-a-mic-e-altitude-is-text`. All six pass already and must keep passing (the exception and limits): `position/tone-after-an-altitude-after-a-frequency`, `position/offset-after-an-altitude-between-two-fields`, `position/frequency-after-a-phg-and-an-altitude`, `weather/field-split-by-telemetry-is-text`, `mic-e/dao-split-by-telemetry-is-text`, `corpus-finding/aprsdroid-tone-and-offset-after-an-altitude`, `corpus-finding/aprsdroid-tone-after-an-altitude`, `corpus-finding/aprsdroid-offset-in-the-wrong-unit-after-an-altitude`.

**Generator.** Run `python3 tools/mice_shapes.py comments.hex.gz --comments --count 20000 --seed N` as well as the Mic-E set through your decode dump; the six-way comparison on both should be clean.

**Done** means your own suite passes at the vectors `round-5` head with no new skips or known differences, and the six-way runs (fuzz, Mic-E shapes, comment shapes) agree.

## Second-look review (read first): text and cases only

No behaviour changes. The README and interpretations now say what all six already do: the strict altitude check counts any run crossing a lifted place; PHG, RNG and DFS bytes after the type code or locator are never an altitude; "as sent" is after 0xFF padding is removed; DFS goes with PHG and RNG; joined readings are provisional (interpretations, Text joined across a lifted element). Six new cases, all passing in all six at the round-5 heads: `mic-e/strict-reads-text-left-across-a-dao-without-a-locator`, `mic-e/strict-reads-text-left-across-telemetry-after-a-locator-with-its-space`, `mic-e/strict-altitude-search-skips-a-phg-after-the-type-code`, `mic-e/dao-is-read-once-0xff-padding-is-removed`, `mic-e/dfs-straight-after-a-locator-missing-its-space`, `mic-e/phg-split-by-a-dao-after-a-locator-is-text`. Libraries only move their pin.

## Latest: strict rejection with a locator missing its space and a later altitude (read first)

Strict rejects by `mic-e-altitude-not-first` only when a run of three base-91 characters and `}` in the text left (telemetry and `!DAO!` lifted) crosses a lifted place, never using the bytes of a locator or of a PHG, RNG or DFS straight after the type code or locator; and when the locator also lacks its space, `missing-space-after-locator` is met first and wins (README Mic-E; interpretations "A packet is read in order").

- **aprs-ts:** do not count a run that uses locator bytes: `mic-e/strict-missing-space-when-an-altitude-would-take-locator-bytes`, `mic-e/strict-missing-space-when-the-altitude-left-needs-a-locator-byte`; and the four below.
- **aprs-py and aprs-ts:** let the missing space win when the locator lacks it, whatever altitude crosses a place: `mic-e/strict-missing-space-before-a-later-altitude-and-a-dao`, `mic-e/strict-missing-space-before-a-later-altitude-and-telemetry`, `mic-e/strict-missing-space-before-a-whole-altitude-and-telemetry`, `mic-e/strict-missing-space-before-text-left-across-a-dao`.
- **aprs-cs, aprs-rs, aprs-c, aprs-go:** pass all six already.
- **aprs-ts, also:** a PHG or RNG after a leading altitude and the locator, reached only once a `!DAO!` or telemetry is lifted, is late (item 4 below, on this path too).

## The rule

In a `/` or `@` report whose seven bytes after the DTI are not 6 digits then `z`, `/` or `h`:

1. If the seventh byte (offset 7 of the information field) is `z`, `/` or `h` and an UNCOMPRESSED position decodes at offset 8, read the position at offset 8, with `malformed-timestamp` (tolerated: a warning leniently, an error that rejects strictly).
2. Otherwise, as at 1.2.0: the position at offset 1 if it decodes, else at offset 8, either with `malformed-timestamp` (tolerated); if neither decodes, `malformed-timestamp`, an error.

"Decodes" is judged exactly as your object rule already judges it: on the position alone (8-byte latitude, symbol table, 9-byte longitude, symbol code), in a scratch context under the options in force, never on the comment, extensions or weather after it. "Uncompressed" means the first byte at offset 8 is a digit and the 19 bytes decode as an uncompressed position; a compressed position at offset 8 does not trigger step 1.

## What to change

Where your decoder does, at 1.2.0 (aprs-py `_position`, for shape):

```
if timestamp-shaped(s[1:8]): ...                  # unchanged
elif position_decodes(s, 1): defect(MALFORMED_TIMESTAMP); pos = 1
elif position_decodes(s, 8): defect(MALFORMED_TIMESTAMP); pos = 8
else: fail(MALFORMED_TIMESTAMP)
```

insert one branch before the offset-1 test:

```
elif s[7] in "z/h" and s[8] is a digit and position_decodes(s, 8):
    defect(MALFORMED_TIMESTAMP); pos = 8
```

Nothing else changes: no new code, no change to objects, status reports, the encoder or the dump tool. The data has no timestamp, so it re-encodes as before (`=` for `@`, `!` for `/`). Guard the index: a field shorter than 9 bytes cannot take the new branch. If your `position_decodes` dispatches on the first byte (digit: uncompressed, else compressed), the digit test above is what keeps a compressed position at offset 8 out.

## New cases

Expected to fail at 1.2.0 and pass with the change:

- `position/garbled-timestamp-before-an-uncompressed-position`
- `position/garbled-timestamp-before-an-uncompressed-position-without-messaging`
- `position/garbled-local-timestamp-before-an-uncompressed-position`
- `position/garbled-hms-timestamp-before-an-uncompressed-position`
- `differential/garbled-timestamp-before-an-uncompressed-position` (the live packet)

Already pass at 1.2.0 and must still pass (they pin what does not change):

- `position/compressed-without-timestamp-seventh-byte-z`
- `position/garbled-timestamp-before-a-compressed-position` (a compressed position after the seven bytes does not win)
- `position/seven-bytes-not-ending-in-a-time-indicator-before-an-uncompressed-position`
- `position/garbled-timestamp-before-a-position-that-does-not-decode`

No existing case changes.

## From the six-way run and the reviews

1. **All six: the tolerance check.** For a case whose lenient diagnostics name exactly one tolerable code, turn off only that tolerance and decode. If the case's `strict` is a reading, or `{"rejected_by": X}` with X that same code, the result must equal `strict`, as before. If `strict` is `{"rejected_by": X}` with X a different code, the result must be a reading (data not `unrecognized`) whose diagnostics include `warning:X`. No case is skipped (README, Checking a case).
2. **All six: the Mic-E locator's space.** Judge it on your decoder's own result, never on a separate trial removal: the status text after the locator once every element your decoder lifts for the data (later altitude, base-91 telemetry, `!DAO!`) is out, in the same order with the same refusals (a `!DAO!` that exists only by joining across a lifted altitude is not lifted). A PHG or RNG straight after the locator still needs the space. When the locator has its space, that space is the separator and not comment; the comment then loses at most one further leading space or `/`. Failing at the round-5 heads:
   - aprs-cs: `mic-e/locator-space-with-a-dao-only-joined-across-an-altitude` (warning and the space in `!W12! hi`).
   - aprs-rs, aprs-py, aprs-go: `mic-e/locator-space-with-a-dao-only-joined-across-an-altitude` (warning), `mic-e/two-spaces-after-the-locator-and-a-later-altitude`, `mic-e/telemetry-split-by-an-altitude-then-two-spaces`, `mic-e/two-spaces-after-the-locator-and-telemetry` (comment `x`, written `IO91/G x`).
   - aprs-c: the three two-spaces cases.
   - aprs-ts: none.
   Must keep passing: `mic-e/telemetry-split-by-an-altitude-is-text`, `mic-e/locator-space-judged-after-a-later-altitude`, `mic-e/locator-space-judged-after-an-altitude-and-telemetry`, `mic-e/locator-space-judged-after-a-dao-and-an-altitude`.
3. **New timestamp case** `position/garbled-timestamp-before-a-lower-case-hemisphere` (all six pass at the round-5 heads).
4. **aprs-ts: locator and PHG or RNG as sent** (README Mic-E; interpretations "Where a Mic-E locator is read"). A locator is read only at the start of the status text as sent or straight after a leading altitude as sent: never once a `!DAO!`, telemetry or altitude before it is lifted, and not after a later altitude. A PHG, RNG or DFS after the locator that is there only once something between them is lifted is late: `data-extension-in-comment` (one split by a lifted element is the provisional reading in interpretations, Text joined across a lifted element). Cases: `mic-e/locator-not-at-the-start-until-a-dao-is-lifted`, `mic-e/locator-not-at-the-start-until-a-dao-and-telemetry-are-lifted`, `mic-e/locator-straight-after-a-later-altitude-is-text`, `mic-e/locator-not-straight-after-the-altitude-until-telemetry-is-lifted`, `mic-e/phg-after-a-locator-only-once-a-dao-is-lifted-is-late`, `mic-e/rng-after-a-locator-only-once-telemetry-is-lifted-is-late`, `mic-e/phg-after-a-locator-only-once-an-altitude-is-lifted-is-late`, `mic-e/phg-split-by-an-altitude-after-a-locator-is-text`. The other five pass them.
5. **All six runs: `tools/mice_shapes.py`.** Run its output through your decode dump with the fuzzed packets; the six-way comparison on it should be clean.

## Done means

Your own test suite passes with the vectors submodule at the `round-5` head (and later at the vectors merge commit), with no new skips and no new entries in `tests/known-differences.txt`; the dump tool needs no change. `tools/mutate.py` now damages single timestamp bytes (op 10), so the six-way runs on fresh seeds reach this rule; differences in the `malformed-timestamp` bucket there are this change not yet made, or made differently.
