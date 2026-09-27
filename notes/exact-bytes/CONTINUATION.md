# APRS exact-bytes round: continuation note (paused 2026-09-27)

Paused on Tom's word ("a bit token heavy for the allowance I have left"). Nothing is merged or released. All work is on pushed `exact-bytes` branches (unfinished work as commits titled WIP). This note, the brief, the rulings and the helper scripts are on aprs-vectors branch `exact-bytes-notes` (folder notes/exact-bytes); a local copy with a text copy of APRS12c is in ~/src/M0LTE.Aprs/.research/exact-bytes. This folder holds the brief, the rulings, the helper scripts and a text copy of APRS12c.

## The goal

Tom asked for the three follow-ups from the grading of the differential-fuzzing round:

1. Make the tests check exact bytes wherever the rules dictate them.
2. Differentially test the builders and APIs, not just the neutral data form.
3. Add a fuzz mode that starts from data and encodes it.

Standing rules still apply: settle every disagreement from the spec (APRS12c, UAP), then reasoning, never by what C# or a majority does; no em or en dashes; plain ASCII output; do not hard-wrap PR or commit bodies; merge and release only on Tom's word.

## What is done

**Measurement.** All five decode dumps now record the bytes the encoder writes (`written`, `written_destination`). Before any change, the five wrote different bytes for 14 of the vectors' 1,812 decode cases and 18,961 of 2,000,000 fuzzed packets (mutate.py seed 8). Only packet.net's runner compared `canonical_info`.

**aprs-vectors, branch `exact-bytes` (pushed, head 5a29825, not a PR yet):**
- README "Comparing implementations": the three dump modes (decode, encode, build), the API view, the recipe format.
- `tools/generate.py`: neutral data recombined from the cases' own decoded data, with numbers regenerated on each format's steps, awkward text, and a share marked `"exact": false`. With `--recipes`, builder recipes. About one generated report in five is correctly refused.
- `tools/compare.py`: N-way compare of decode, encode and build dumps; it also checks each encoder's round trip and each builder's clean decode.
- Batch-1 rulings E1-E12 in README, interpretations.md, schema (`reencode: "rounded"`), check.py (every equivalent or rounded case needs `canonical_info`), and cases (commits d09875b, c5eb1fd). The rulings with their spec basis are in `rulings-1.md` here:
  - E1: numbers kept as sent, footprints included.
  - E2: DAO digits on a compressed position follow the position.
  - E3: comment order is frequency, braces, `/A=`, text, telemetry, DAO. APRS12c ch. 18 puts the frequency in the first 10 bytes.
  - E4: a `/` goes after a 7-byte extension before a frequency, and none after a PHGR.
  - E5: Mic-E 190-199 knots is written `/`.
  - E6: a 0x1D comment after Rev 0 telemetry is written straight on.
  - E7: delimiters only where needed.
  - E8: snowfall under 1 is written `.dd`.
  - E9: cs rounding is mandatory, with halves away from zero and 358 rounding to north.
  - E10: a compressed speed byte `{` is written back.
  - E11: no size limit.
  - E12: a separating space is written, not refused.

## Where each implementation stands (all on local and pushed branch `exact-bytes` unless noted)

| Repo | State | Left to do |
|---|---|---|
| aprs-ts | **Finished batch 1.** Head 018452b, pushed, vectors pinned c5eb1fd. Runner binding, E1-E12 done, dump `api`, `--encode`, `--build`. 30 test failures, all the E3 cases the vectors have not updated yet. | Re-pin once the E3 cases land. |
| aprs-py | Head dacaa9a pushed ("Dump tool: the API view, and encode and build modes"), clean tree. Was about to write the README section for the dump tool. | Check `git log` against rulings-1.md; README section; tests. |
| packet.net | Head 9cac3dc0 pushed: a WIP commit (the DiffCommand.cs change) on top of 9969f2e9, which includes a docs/plan.md section 17 plan entry. Was adding tests for the new refusals and as-sent behaviours. | Review the WIP commit; finish tests; dispatch CI by hand (`gh workflow run ci.yml --ref exact-bytes`, plan-check.yml). |
| aprs-rs | Head 7cd0a89 pushed: one WIP commit holding all the round's work (13 files: CHANGELOG, README, examples/diff_dump.rs, src/data.rs, encode.rs, mic_e.rs, other.rs, position.rs, weather.rs, tests/builder.rs, tests/vectors/main.rs, neutral.rs, the vectors pin). Was rewriting the reading half of tests/vectors/neutral.rs to be fallible; it may not build. | Review the WIP commit, finish, split into proper commits if wanted. |
| aprs-c | Head a6206d8 pushed: 4 commits (71515e9, 899877a, a134a2b, 176d4c4: dump written bytes, E11, E1-E9, runner) and a WIP commit on top with tests/neutral.c and tools/diffdump.c (encode or build mode in progress; may not build). | Finish the dump modes, regenerate dist with tools/amalgamate.py. |

## Vectors work still owed for batch 1

- **E3 canonical updates.** About 30 cases still show `/A=` before the frequency in `canonical_info`: 28 corpus cases, `differential/text-after-frequency-and-altitude`, and the encode case `encode/every-optional-element-in-canonical-order` (its `expect.info`). Take the new bytes from aprs-ts (tmp dumps are disposable; re-run `node scripts/diff-dump.mjs` over the case lines) once a second implementation writes the same bytes, check them against the rule, and update the cases (tools/edit.py does in-place edits by case id).
- Then tell every implementation the new vectors commit to pin.

## Batch 2: questions already raised (rule them together, from the spec)

- **Course 0.** APRS12c ch. 7 gives a course as 001-360 (360 north, 000 unknown), and Mic-E 0 means unknown. Data holding course 0 is outside the field, so an encoder should refuse it; a builder given heading 0 should write 360. aprs-ts writes Mic-E 0 (reads back as no course); aprs-rs writes compressed c = 0 (reads back as 360).
- **Values between steps.** Proposed general rule: round to the nearest step the field holds, halves away from zero (Python round() is half-even, JS Math.round is half-up: both need care), for every field. aprs-ts refuses fractional `/A=` feet but rounds everything else. Decide whether snowfall that three characters cannot hold rounds or stays refused.
- **A DAO on an ambiguous position.** Refuse: it reads back with `dao-with-ambiguity` whatever its precision. aprs-ts writes `!W00!`.
- **A compressed speed without a course.** Refuse, as interpretations.md already says. aprs-rs writes course 0.
- **Course/speed plus a late PHG or RNG.** The decode rules read `090/013PHG5132`, but aprs-py and aprs-ts refuse "more than one data extension". Decide whether the encoder writes it.
- **Humidity 0.** `h00` means 100%, so 0 cannot be written.
- **Builder semantics**, once the build dumps are compared:
  - how ambiguity and a DAO apply to a raw GPS position (proposed: round to hundredths first, then blank);
  - unit conversions (km/h, metres, Celsius, mm);
  - timestamps from UTC;
  - telemetry sequence and value formatting;
  - defaults;
  - names out of range.
- **The API view.** aprs-ts gives no `device` for an inner packet and has no `ax25`, `has_errors` or `third_party` accessors (it writes only the keys it has).

## How to resume

1. Let each implementation finish batch 1 (the brief is `BRIEF.md` here; per-repo notes above). One agent per repo worked well; keep them to their own repo.
2. Update the E3 cases, commit to vectors `exact-bytes`, and have all five pin that commit.
3. Run the three comparisons with fresh inputs:
   - `python3 ~/src/aprs-vectors/tools/generate.py data.jsonl.gz --count 1000000 --seed 2`
   - `python3 ~/src/aprs-vectors/tools/generate.py recipes.jsonl.gz --recipes --count 1000000 --seed 2`
   - a fresh fuzz set with mutate.py seed 9 from the pass-3 capture
   - `tools/stream5.sh encode|build|dump <input> <report-prefix>`
   `stream5.sh` streams the five tools through named pipes into compare.py, so no dump reaches the disk. Check each tool's flag order against the script before the first run.
4. Rule everything from one run in **one** vectors commit (batch 2), then iterate. The main process lesson from last round: do not call a vectors commit final until the next run is clean.
5. Last, stream the 11,094,522-packet pass-3 capture through all five (decode mode, which checks `written` bytes and the API view).
6. Then open PRs (vectors last, with a merge commit, per the usual cross-implementation order) and ask Tom before merging or releasing.

## Files

- Here: `BRIEF.md` (agent brief), `rulings-1.md` (batch 1 with reasons), `APRS12c.txt` (text of the spec), and `tools/`:
  - `stream5.sh` and `dumpall.sh`: run all five dump tools.
  - `bytes5.py`: five-way written-bytes compare.
  - `cases2lines.py`: turns the vectors' decode cases into a lines file.
  - `edit.py`: in-place case edits by id.
  - `draft.py`, `pyenc.py`: draft cases and check generated data with a clean aprs-py (they point at a worktree that no longer exists; recreate one with `git -C ~/src/aprs-py worktree add --detach <dir> origin/main` and fix the path).
  - `insert.py`: appends cases to their files.
- Captures (the only copies): `~/src/M0LTE.Aprs/.research/captures/pass3-2026-09-27-lines.hex.gz` (11,094,522 lines) and `pass2-2026-09-26-lines.hex.gz`.
- Disk: the volume is shared and was at 98% today (the capture dumps filled it once). There are about 30 GB free now. The aprs-corpus collector pauses below 10 GB, so never write full dumps of the capture.
