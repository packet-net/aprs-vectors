# Points the round-3 vectors don't decide yet (collected from library agents)

From Go (aprs-go#1):
1. Comment telemetry / telemetry report with 0 or fewer than 5 analog values: cs, ts say too-long; go, rs, py, c say malformed. Ruling already says "too few is malformed"; needs a case for the empty list. (f5 n=35)
2. T#MIC with an empty analog list: go malformed, c value-has-no-form. (f5 n=895)
3. Builder given a lower-case status locator: rs, py, c, go upper-case it and build; encoder refuses neutral data with one (malformed). Rule whether a builder may normalise.
4. GGA compressed weather with out-of-range wind direction: py, ts, go value-out-of-range; cs, rs, c extension-conflict. "Wanted twice keeps its own checks" suggests value-out-of-range. (f5 n=126)
5. Compressed range beside course/speed: is the speed judged by the cs-byte form (value-out-of-range) there?

From Python (aprs-py#14):
6. Course/speed/range in the place compressed wind or a GGA altitude holds: own checks = general range only, or compressed-form checks (course 0 no form, speed steps)? py does form checks; go extension-conflict. (f5 n=6210, 6533, 329, 7043) Same question as 5.
7. Lower-case locator in a Mic-E report or Maidenhead beacon: only status has a case. py makes all three malformed; go writes the Maidenhead beacon upper-cased. Same question as 3.
8. Neutral data a typed model cannot hold (missing required fields, symbol not two characters): no stated refusal code.

Possible library discrepancies to recheck in the six-way run:
- Query with no type: go invalid-code, py missing-field (py cites case encode/query-without-a-type-and-radius-too-big). 38 lines of f5.
- Go builder: telemetry with CR in comment (go too-long vs invalid-character); 180-degree longitude plus ambiguity with out-of-range altitude/speed (go value-has-no-form vs value-out-of-range).

From C# (aprs-cs#11):
9. Directed query with no type: cs missing-field (following the general-query case); go, rs, ts invalid-code. No case for directed query.
10. Telemetry on a weather report: cs field-not-allowed without checks (no-place rule); other five value-out-of-range. No case.
11. README says a compressed weather report's range is extension-conflict, but corpus case 1149 needs one written when there is no wind. Contradiction in the vectors; cs follows the corpus.
12. Go builder (and maybe Rust): names the ambiguity edge (value-has-no-form) ahead of a real value-out-of-range (course 360.5, latitude -90.00001) in builder recipes. Check after six-way.
Note: cs added public AprsThirdPartyTraffic.Create(source, data, destination, path) (additive, fine for 1.1.0).

From TypeScript (aprs-ts#19):
13. Nested third-party ending in undecoded data: ts not-encodable (order first), py invalid-third-party-header. (58 lines, n=357)
14. Base-91 telemetry on a weather report: do its own checks run (too-long ahead of field-not-allowed)? go, py, ts yes; cs no (point 10).
15. Mic-E ambiguous position at the pole with out-of-range speed/altitude in builds: go, py stop at value-has-no-form; ts value-out-of-range (order first). (recipes n=464, 800)
16. Missing object/item name: treated as empty -> invalid-name (ts, go). Generator labels the fault name-length.
Split on 5/6: ts sides with py (cs-form checks), go extension-conflict. Query with no type: ts, py, cs missing-field; go, rs invalid-code.
