# Run 1 triage (vectors 10d4e25, after f2f6ab5)

This triage covers run 1 on the final library heads: cs 2a42cf9, rs 21e8a5a, py 59da5a0, ts 78c5049, c 7b680f3, go dc23ef6. "Line n" means line n of that run's input on tf@hyperv-gha:~/r3-diff/in. New cases are in cases/encode.json at 10d4e25. I checked them against the libraries' round-3 trees.

## Bucket by bucket

1. **Decode, case line 1904 and 27 fuzz lines: C alone reads deep third-party nesting as unrecognized.**
   - All 28 lines have an information field over 512 bytes (1,563 to 10,016 bytes). The 27 fuzz lines are exactly the 27 lines over 512 bytes in fuzz.gz.
   - C documents this limit: PDN_APRS_MAX_INFO is 512, and the decoder returns PDN_APRS_ERR_TOO_LONG ("which nothing on the air or on APRS-IS has").
   - Verdict: C's known limit, not a bug. C should list third-party/nested-2000-deep among its known differences.
2. **Case encode line 2190: a third-party packet with an inner header carrying `warning:multiple-used-markers`. C# writes it; the other five refuse.**
   - README: a packet whose inner header has a tolerated defect is refused, since the defect is part of its data. The code is `invalid-third-party-header`.
   - Verdict: C# bug. New case encode/third-party-inner-header-with-a-tolerated-defect.
   - The same packet without the diagnostic is clean data and is written by all six. New case encode/third-party-two-used-path-entries-without-the-warning.
3. **Faults encode, about 6,300 third-party lines: cs, py and ts say invalid-third-party-header; C names an inner code.**
   - The refusal order puts `invalid-third-party-header` (the header group) before any fault in the inner data.
   - Verdict: C bug. C must check the inner header before encoding the inner data.
   - Rust and Go are missing from the split because their data cannot hold a path entry such as `TC+IP*` ("path: not an address", 9,822 lines). That is allowed as `unsupported`, but it leaves this whole area untested for them; see the harness notes.
   - The 42 lines split as c against ts: ts is right, for the same reason. cs and py report those lines unsupported because the telemetry has no sequence.
4. **GGA compressed weather with an altitude of 1 foot or less, such as -99999.4, -0.5 or 0.4: cs, py and ts write; rs, c and go refuse.**
   - The Encoding rule says an altitude of 1 foot or less is written as `!!` (1 foot). In a compressed weather report, which has no comment, that nearest cs value is written alone and the report re-encodes `rounded`.
   - Verdict: writing is right. rs and go bug (they refuse with text-reads-as-field); C bug (does-not-read-back for -99999; it writes 0.4).
   - New cases encode/compressed-gga-weather-altitude-far-below-1-foot and -under-1-foot.
5. **2 lines plus 1 in the nonfinite run: GGA altitude beside wind on a non-weather symbol, with an area. Five say extension-conflict; C says field-not-allowed or symbol-mismatch.**
   - The refusal order puts `extension-conflict` first.
   - Verdict: C bug. New case encode/gga-weather-on-a-non-weather-symbol-with-wind.
6. **Faults build, 126,177 lines, mostly recipes giving one quantity in two units (feet and m, knots and km/h, F and C, in and mm).**
   - The rule, now precise in the README Builder rules:
     - A recipe is one input, so it gets `value-given-twice`.
     - Each value it gives is checked on its own.
     - The refusal is the first code in the order among those checks, the recipe's other faults and `value-given-twice`, which sits after `missing-field` and before `text-reads-as-field`.
     - A dump tool builds once with each unit and reports that ranking. It never builds the line from one unit, and never writes `unsupported`.
   - Verdicts:
     - **c** builds these lines, and **ts** builds some (both "build where cs, py refuse"; 597 lines differ in bytes, c taking altitude_feet and ts altitude_m). Both wrong: refuse.
     - **rs, go, ts** write `unsupported` for two units. Harness gap: refuse, ranked.
     - **py** names value-given-twice ahead of earlier codes: line 367 (speed_knots 799.5 with speed_kmh -1; the order gives value-out-of-range), lines 136 and 430 (altitude_m 304800 is out of range). py bug.
     - **cs** names value-given-twice where the other unit's value is out of range: mic-e line 6, line 260, item line 586, object line 724. py and c say value-out-of-range, and cs must check both units' values.
   - Code splits between extension-conflict and value-out-of-range:
     - A speed or PHG value out of range beside a conflicting extension is `value-out-of-range` (a place wanted twice keeps its own checks). Line 67 (speed_kmh 1851259.2 beside PHG): cs right; **py, c** wrong.
     - Line 89: range_miles 0 is valid, so the out-of-range value is elsewhere. cs and ts say value-out-of-range and are right; py and c wrong.
     - Line 160 (ambiguity edge against a real out-of-range value): the Builder refusal-order rule gives value-out-of-range. **py, c** wrong.
     - Line 250 and object line 733: cs says extension-conflict while py and c say value-out-of-range (altitude_m in range, so the out-of-range value is another argument). cs wrong.
7. **Nonfinite, 200k lines.**
   - cs, rs and ts dump tools cannot read the `NaN` and `Infinity` tokens. Harness gap: read them, and refuse with `not-a-number` in its place in the order.
   - Among py, c and go:
     - 1,228 third-party splits (py invalid-third-party-header, C value-out-of-range): C bug, as in item 3.
     - The GGA latitude -90 lines are item 4: C and Go wrong, py right.
     - Line 48426 (GGA altitude 0.4): Go wrong.
8. **Case encode "own" problems, 180 lines, identical in all six.** These are an artefact of how the run built its input: case-derived encode lines were marked `"exact": true`, but those cases round values or give NMEA without its fields. Run harness: mark case lines `exact: false`, or compare them with `expect.info`. No library is at fault.

## Per library

**cs (4 items, one of them harness)**
1. Refuse a third-party packet whose inner packet carries tolerated diagnostics (`invalid-third-party-header`). Case: encode/third-party-inner-header-with-a-tolerated-defect; run line 2190 of cases-enc.
2. In builds, check every value of a two-unit recipe before naming `value-given-twice`. Examples: faults-build mic-e line 6, mic-e line 260, item line 586, object line 724.
3. In builds, don't name `extension-conflict` ahead of another argument's out-of-range value. Examples: faults-build lines 250 and 733.
4. Harness: read the NaN and Infinity tokens.

**rs (2 items)**
1. Write a compressed GGA weather report whose altitude is 1 foot or less as `!!`. Cases: compressed-gga-weather-altitude-far-below-1-foot and -under-1-foot; run lines 412125, 488475, 622061 and 588185.
2. Harness: two-unit recipes are refused and ranked, not `unsupported`. Read NaN and Infinity.

Optional: hold an invalid third-party path entry, so header-first ordering gets tested.

**py (2 items)**
1. Builds: `value-given-twice` sits after `missing-field`. Name every earlier code first. Examples: faults-build lines 367, 508, 136, 430, 254, 205.
2. Builds: a value out of range beside a conflicting extension is `value-out-of-range`. Examples: line 67, and line 160 (ambiguity edge).
py was right on items 4 and 7.

**ts (2 items)**
1. Build: refuse two-unit recipes, ranked, instead of building them (597 byte differences, from altitude_m, in the faults-build buckets "c | ts" for tnc2 and again.data) or writing `unsupported`.
2. Harness: read NaN and Infinity.

Optional: refuse a status recipe with an hms timestamp as `invalid-timestamp` rather than `unsupported` (40,729 lines).

**c (6 items)**
1. Encode a third-party header before the inner data, so header faults rank first. Examples: faults lines 14, 54, 218, 1340, 68459; 1,228 nonfinite lines.
2. Write a compressed GGA weather altitude of 1 foot or less. Case: -far-below-1-foot; run line 412125.
3. An `extension-conflict` beside an area, or on a non-weather symbol, ranks first. Case: gga-weather-on-a-non-weather-symbol-with-wind; faults lines 72774, 968766; nonfinite line 38122.
4. Builds: refuse two-unit recipes, ranked, instead of building from altitude_feet. See the faults-build "cs+py | c" result buckets: 24,353 weather, 22,877 position, 13,808 mic-e lines.
5. Builds: a value out of range beside a conflicting extension or the ambiguity edge is `value-out-of-range`. Examples: lines 67 and 160.
6. Known limit, no change: decode lines over 512 bytes. Add third-party/nested-2000-deep to the known differences.

**go (2 items)**
1. Write a compressed GGA weather altitude of 1 foot or less. Cases as for rs; nonfinite line 48426.
2. Harness: two-unit recipes are refused and ranked, not `unsupported`.

Optional: as for rs, hold an invalid third-party path entry.

## Harness fixes by dump tool
- **cs, rs, ts:** read the NaN and Infinity tokens in encode and build input, then refuse with `not-a-number` ranked in the order.
- **rs, go, ts:** a recipe with one quantity in two units: build once with each unit, report the first code among both results and `value-given-twice`, and never write `unsupported`.
- **c, ts:** the same rule; never build such a recipe from one unit.
- **The run's case converter:** mark encode-case lines `exact: false`, or compare them with `expect.info`.
