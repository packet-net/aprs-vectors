# Rulings on OPEN.md (aprs-vectors round-3 at cb5dcc0)

These are checked against each library's round-3 worktree at its current head (scratch copies, dump tools rebuilt). The new cases are in cases/encode.json; builder points are in the README's Builder rules. Libraries that cannot hold a record write `unsupported`, which is not a failure.

1. **Fewer than 5 values in a telemetry report, or none in base-91 telemetry:** `malformed`; more than the field holds is `too-long`. New case: encode/telemetry-report-with-no-analog-values, which all six already pass. Change: none at the round-3 heads. If cs and ts still say too-long on other lines, check them against encode/base91-telemetry-with-no-analog-values.
2. **T#MIC with an empty analog list:** `malformed`. An empty first channel needs a list to be in. Case: encode/mic-telemetry-with-no-analog-values. Change: **c**.
3. **Builder given a lower-case status locator:** it writes the locator in upper case, because a locator's case carries nothing. This is a README Builder rule. All six already build `IO91SX`. Change: none.
4. **GGA compressed weather with an out-of-range wind direction:** `value-out-of-range`. A place wanted twice keeps its own checks. Case: encode/gga-compressed-weather-with-wind-out-of-range. All six pass at the round-3 heads. Change: none.
5. and 6. **A course, speed or range in a place another field also wants:** it is judged in the checks of the form that place has (cs steps; a compressed course of 0 is `value-has-no-form`), before `extension-conflict`. Cases:
   - encode/compressed-course-0-beside-a-range: all pass.
   - encode/compressed-speed-past-the-steps-beside-a-range: all pass.
   - encode/compressed-weather-with-course-0: **rs, c, go** give extension-conflict and must change.
7. **Lower-case locator in a Mic-E report or a Maidenhead beacon (neutral data):** `malformed`, as in a status, because it reads back changed. Cases: encode/lower-case-mic-e-locator and encode/lower-case-maidenhead-beacon-locator. Change:
   - Mic-E: **cs, rs, go** write it; **c** says text-reads-as-field.
   - Maidenhead beacon: **cs, rs, go** write it.
8. **Text the neutral form leaves out is empty text** (new interpretation, "Absent text is empty text"):
   - No positioned symbol is `invalid-symbol`.
   - No name is `invalid-name`.
   - No addressee is `invalid-addressee`.
   - No query type is `invalid-code`.
   - A field needed only because another is there stays `missing-field` (a status symbol beside a locator, a message ID beside a reply-ack).
   - A library whose own data cannot hold the record writes `unsupported`.
   - Cases: position-without-a-symbol, message-without-an-addressee, object-without-a-name, directed-query-without-a-type, general-query-without-a-type.
9. **Directed query, or general query, with no type:** `invalid-code`, under item 8. Change: **cs, ts, c** for both; **py** for the general query (py cannot hold a directed query with no type). rs and go are already right.
10. and 14. **Base-91 telemetry on a weather report:** it has no place, so it is `field-not-allowed` and its own checks do not run (README rule R25). Cases: weather-with-six-telemetry-values and weather-with-telemetry-sequence-out-of-range. Change: **rs, py, ts, go**. cs and c are already right.
11. **README versus corpus/1149, fixed.** A compressed weather report's course or speed is `extension-conflict`, and so is a range beside wind or a GGA altitude. A range alone is written, and its cs bytes then carry no wind. Case: encode/compressed-weather-with-a-range-and-no-wind, which all six already write. Change: none.
12. and 15. **Builders refuse in the README order:** `value-out-of-range` (course 360.5, latitude -90.00001, altitude 999999.5, Mic-E speed 999.5) comes before the ambiguity edge's `value-has-no-form`. This is a README Builder rule. Change:
    - **rs, go** in all three probes.
    - **py, c** for the Mic-E pole with speed 999.5.
    - cs and ts are already right.
13. **Nested third-party ending in undecoded data:** `not-encodable`, first in the order. Case: encode/nested-third-party-ending-in-undecoded-data. Change: **py** (it gives invalid-third-party-header). rs and go cannot hold this data.
16. **Missing object or item name:** `invalid-name` (item 8). Change: none; py cannot hold the record.

Other discrepancies listed:
- Query with no type: settled by item 9.
- Go builder, telemetry comment with a CR: `invalid-character` (the README order). All six give that at the round-3 heads, so no change.
- Go builder at 180 degrees: settled by item 12.

## Per-library change list
- **cs:** item 7 (Mic-E and Maidenhead lower-case locator); item 9 (both query types).
- **rs:** item 6 (compressed weather with course 0); item 7 (Mic-E, Maidenhead); item 10 (telemetry on weather); item 12 (builder order).
- **py:** item 9 (general query); item 10; item 12 (Mic-E pole in the builder); item 13.
- **ts:** item 9 (both queries); item 10.
- **c:** item 2; item 6; item 7 (Mic-E); item 9 (both queries); item 12 (Mic-E pole in the builder). There are also 30 failing new cases in total at its round-3 head; that work is still in progress.
- **go:** item 6; item 7 (Mic-E, Maidenhead); item 10; item 12.

Failing new encode cases at the round-3 heads, leaving out `unsupported`:

| Library | Failing |
|---|---|
| cs | 4 |
| rs | 4 |
| py | 4 |
| ts | 4 |
| go | 4 |
| c | 30 |

These counts don't include the builder points, which no case can hold.
