# Exact bytes, differential encoders, builders and APIs: brief for each implementation

You own one APRS implementation: packet.net (C#, Packet.Aprs), aprs-rs, aprs-py, aprs-ts or aprs-c, each checked against the language-neutral conformance vectors in packet-net/aprs-vectors (a submodule). All five agree on every decode over 11 million real packets and millions of fuzzed ones. This round tightens three things the old tests could not see:

1. **Exact bytes.** The vectors' `canonical_info` becomes binding: an encoder writes exactly those bytes. Only packet.net checked it; the other four accepted any bytes that decode back to the same data, which hid real encoder differences.
2. **Differential testing of the builders and the API**, not just the neutral data form.
3. **A data-first fuzz mode**: random data in the neutral form, encoded by all five and compared, instead of only mutated packets.

The lead (me) owns the vectors repo and every ruling. You own your implementation.

## Where things are

- Vectors: `~/src/aprs-vectors`, branch `exact-bytes`. Read its README section "Comparing implementations" (the dump formats, the API view, the recipe format): that is your spec for the tooling. The README's "Rules the cases rely on", especially **Encoding**, is the spec for your encoder.
- The first batch of byte rulings: `/home/tf/.claude/jobs/a4805be3/tmp/exact/rulings-1.md`. Implement every ruling that applies to you. The vectors branch will get the matching cases and README text shortly; I will tell you the commit to pin.
- Your repo is already on a local branch `exact-bytes` (from origin/main) with an uncommitted change I made to your decode dump tool: it now writes `written` (and `written_destination` for Mic-E). Keep it, and commit it as part of your work.
- Inputs for checking your work (read-only, shared):
  - `/home/tf/.claude/jobs/a4805be3/tmp/exact/cases.hex.gz`: every decode case's input as a hex TNC2 line (1,812 lines), index in `cases.idx.json` (case id, reencode, canonical_info).
  - `/home/tf/.claude/jobs/a4805be3/tmp/exact/fuzz8.hex.gz`: 2,000,000 fuzzed lines. The five implementations' decode dumps of it from before any change are `fuzz8.{cs,rs,py,ts,c}.jsonl.gz` next to it, and `fuzz8.bytes.txt` lists where the bytes differ.
  - `bytes5.py` there compares written bytes five ways (`python3 bytes5.py <prefix> [idx.json] <lines.hex.gz> [examples]` over `<prefix>.{cs,rs,py,ts,c}.jsonl.gz`).
- **Disk is tight** (the disk filled up once today). Write your own dumps under `/home/tf/.claude/jobs/a4805be3/tmp/exact/<your-name>/`, use `--limit` or the 2M fuzz set, never dump the 11M capture to disk (I run that one, streamed), and delete large outputs you no longer need. Keep at least 12 GB free (`df -h ~`); a data collector pauses below 10 GB.

## What to do

### 1. Binding canonical bytes in your vectors test runner

- For `reencode: "equivalent"`: the bytes written must equal `canonical_info` byte for byte (after the case's data re-encodes cleanly, as now).
- A new `reencode` value, `rounded`: the encoder must write `canonical_info` exactly; the data read back differs from the original by the rounding the Encoding rule describes, so do not compare the data.
- Encode cases (`input.encode`) already give exact bytes; keep checking them exactly.
- Do not paper over failures with your known-differences list: fix the encoder. If you believe a ruling is wrong, say so in your report with the spec text, and list the case as a known difference with that reason meanwhile.

### 2. Decode dump: the API view

Add `api` to each decode record (README "The API view"). Read it through your library's public API as a program would, not through the neutral-form converter the tests use. Write only the keys your API offers. For a third-party packet, `inner` holds the same view of the inner packet.

### 3. Encode mode

Your dump tool gets an encode mode (README "Encode records"): read `{"n", "data", "exact"}` lines, convert `data` from the neutral form to your own data (your test runner already has this converter for encode cases), encode it, and write `{"n", "result", "info", "destination", "again", "reason"}`. `again` is the written bytes decoded leniently under `N0CALL>` + the destination (Mic-E: the computed one; otherwise `APZ001`). Until `tools/generate.py` lands, test with the cases' own data: every decode case's `expect.data` is valid input (`jq`/a few lines of script to extract them).

### 4. Build mode

Your dump tool gets a build mode (README "Build records"): read recipes, call your builder the way a program would, and write `{"n", "result", "tnc2", "again", "reason"}`. Map every recipe key your builder can express; report `unsupported` with a reason naming the key for anything it cannot. Do not add builder features in this round just to cover recipe keys, unless one is a plain gap next to features you already have (for example km/h beside knots): say what you added.

### 5. The byte rulings

Implement rulings-1.md. Then dump `cases.hex.gz` and `fuzz8.hex.gz` again and check your written bytes against the other implementations' old dumps: every remaining difference should be one where you are right by a ruling and they have yet to change. List any you cannot explain.

## Rules of the road

- Settle nothing by majority or by what packet.net does: the spec (APRS12c, UAP) is the tie-breaker, then reasoning. If your implementation disagrees with a ruling, argue from the spec in your report.
- Match the surrounding code's style. Keep the dump tools in the places the README names, with the command lines it shows: decode is the default; `--encode` and `--build` (packet.net: `diff dump|encode|build`) select the other modes. aprs-c's tool reads stdin and writes stdout, plain JSON lines.
- User rules: never write an em dash or en dash anywhere; printable output is plain ASCII; do not hard-wrap commit or PR bodies or markdown (one line per paragraph).
- Commit on the `exact-bytes` branch in logical commits, with these trailers:
  ```
  Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01EMmt8uajfDEAxyqG6fWzUT
  ```
  Push the branch. Do not open a pull request, do not merge, do not tag or release anything.
- Leave the vectors submodule where it is until I give you a commit to pin (your runner's new checks will fail on cases the vectors have not updated yet; that is expected until then).
- Report back: what you changed (briefly), your branch head, what the new tests say, any ruling you disagree with and why, anything you found that the rulings do not cover, and which recipe keys you report as unsupported.
