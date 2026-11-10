# Pre-1.0 API cleanup: implementation brief for one library

You implement the agreed 1.0 API for ONE APRS library (named in your prompt), working only in its checkout. Tom has accepted every recommendation, so there is nothing left to decide: if something in the documents is ambiguous, pick the reading most consistent with the other four libraries and say so in your report.

## What to implement
- `/home/tf/aprs-exact/api/DECISIONS.md`: every cross-cutting decision (1-11) as its "Changes" line says for your library, with the recommended option (decision 2 is option A; decision 5 is option A; decision 11 is option A). Also your library's own per-library decisions.
- `/home/tf/aprs-exact/api/AUTO.md`: every remove and fix item for your library. Where AUTO.md flags an item as conflicting with a decision, the decision wins.
- `/home/tf/aprs-exact/api/<repo>-proposals.md` and `<repo>-inventory.md`: the reviewer's detail behind both; use them for exact names and shapes.
Breaking changes are expected; removed or renamed things are removed, with no deprecation shims.

## Keep everything else working
- The vectors suite (`vectors` or `spec/aprs` submodule) passes with 0 failures and an empty known-differences list.
- The dump tool (decode with the API view, `--encode`, `--build`) keeps working and maps every recipe key it did before. Verify with the 100,000-line sets: run `--encode` on `/home/tf/aprs-exact/gaps/data.jsonl.gz` and `--build` on `/home/tf/aprs-exact/gaps/recipes.jsonl.gz` before you change anything (save to `/home/tf/aprs-exact/api/<repo>/before-*.gz`) and again at the end (`after-*.gz`), and compare the two with `python3 ~/src/aprs-vectors/tools/compare.py before after --names before after --input <input>`: they must agree on every line (same bytes, same results), except where a decision deliberately changes a result (say which, with counts). Also run decode over `/home/tf/aprs-exact/cases.hex.gz` before and after, which must agree except for API view keys you deliberately added.
- Examples, README (every code sample must compile or run against the new API), CHANGELOG under Unreleased with a clear "Breaking changes" list a user can follow to migrate. Do not bump the version, tag or release.
- The repo's lint, format, type and doc checks, and its CI configuration (look at `.github/workflows`), all clean.

## Process
- Branch `api-1.0` from an up-to-date `main`. Logical commits, each ending with exactly `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Push and open a PR to main titled "1.0 API cleanup", body: what changed in plain language, the breaking changes, the before/after verification numbers, one line per paragraph, ending with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. Wait for CI (`gh pr checks <n> --watch`) and fix failures. Do not merge.
- Container is memory-limited and five agents run at once: modest builds (Rust `-j 4`, `dotnet -m:2` then `dotnet build-server shutdown`, `make -j4`), one heavy job at a time, delete big scratch files when done.
- Never write an em dash (U+2014) or an en dash (U+2013) anywhere. Printable program output is plain ASCII. Do not hard-wrap markdown or commit/PR bodies.

## Report (short)
PR link and CI result; anything you could not do or read differently from the documents, and why; the before/after verification numbers.
