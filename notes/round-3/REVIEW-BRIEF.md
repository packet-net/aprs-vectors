# Round 3 PR review brief

You are reviewing one pull request in a round of changes to six APRS libraries (C#, Rust, Python, TypeScript, C, Go) and their shared test cases (packet-net/aprs-vectors). Background: https://m0lte.uk/posts/aprs-libraries/. The rules are in the vectors' README (case format, Encoding rule, Refusal reasons order, Builder rules) and interpretations.md, on vectors branch round-3 head cb5dcc0 (worktree /home/tf/src/aprs-vectors-r3; PR packet-net/aprs-vectors#24). This round ships as 1.1.0 of all seven repos: additive API changes are fine, breaking ones are not (flag any). The library PRs all pass every case; a six-way differential run is going on separately, so don't re-prove case conformance.

Focus on:
1. Correctness beyond the cases: does the change implement the rule generally, or only for the case's exact shape? Look for checks that run in the wrong order for neighbouring report types, fields the rule should cover but the code misses, regressions in untouched paths, crashes on hostile input (deep nesting, long lines, odd bytes), memory or recursion blow-ups.
2. Public API: anything breaking for 1.x callers; new public surface that should not be public; docs on new surface.
3. Test runner changes: could a runner change make a failure pass silently (skips, swallowed exceptions, loosened comparisons)? Every new skip must be justified.
4. CHANGELOG accuracy, README accuracy. No em or en dashes anywhere; markdown not hard-wrapped.

Constraints: this machine is shared and OOMs; don't run Release builds or full suites in parallel; small targeted tests are fine. Don't push or comment on GitHub. Report concisely: findings ranked by severity with file:line, the concrete failure, a suggested fix; or "good to merge".
