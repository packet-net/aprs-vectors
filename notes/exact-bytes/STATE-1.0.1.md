# State of the APRS 1.0.1 round (refusal reason codes), 2026-11-11 evening

Read this first when resuming. Tom asked for this work and has given standing permission to merge and release it ("Do all of these", then "just add this to 1.0", so it ships as 1.0.1, additive).

## Done already
- 1.0.0 of all five libraries and the vectors is released (2026-11-11 04:00 UTC). aprs-vectors#17 closed.
- packet.net stale `exact-bytes` branch deleted.
- pdn-ax25-tools#80 (Packet.Aprs 1.0.0) reviewed and merged.
- Local and proxmox0 scratch are NOT yet cleaned (they are still needed until 1.0.1 ships).

## 1.0.1: shared machine-readable refusal reason codes
Design and rulings: `/home/tf/aprs-exact/reasons/DESIGN.md` (26 codes; Rulings R1-R28 at the end; R1 is the order that picks one code when a record has several faults). Per-library fix lists FIXES.md to FIXES5.md beside it. Not in git: copy DESIGN.md into this folder if the scratch is at risk.

Open PRs, all on branch `refusal-codes`, all reviewed by Opus with review fixes applied, CI green:
- packet-net/aprs-vectors#19 (head 380ca82): codes.json `refusals`, schema keys `refusal` and `reencode_refusal`, check.py with REFUSALS_REQUIRED = True and an exemption list (not-a-number, invalid-address, ax25-cannot-carry, tnc2-cannot-carry, value-given-twice, not-encodable, does-not-read-back), compare.py, README "Refusal reasons" rule with R1-R28, every refused case carries its code.
- packet-net/aprs-cs#8, aprs-rs#18, aprs-py#12, aprs-ts#17, aprs-c#12: each pins vectors 380ca82 (pin commits: cs c256a0a, rs 21a9456, py 6c23e52, ts 80854d6, c 6ae953c). All suites pass on 380ca82.

Verification so far: on the 100,000-line sets all five agree on every code and every byte. Fresh-seed 1M runs found shrinking residues each round (seed 10: 95/33/485, seed 11: 9 encode + 1 fuzz), all ruled and fixed. A final confirming run on seed 12 was started on root@proxmox0: `/root/aprs-exact/r15.log` ends with RUN DONE; results in `/root/aprs-exact/runs/r15-{enc,build,fuzz,cases}.txt` (first line of each gives agree/differ counts).

## Next steps
1. Read r15 results. If anything differs: rule it by DESIGN.md and its Rulings (spec first, then reasoning, never majority; a write versus refuse difference is decided by the vectors' Encoding rule: write an equivalent form or refuse), send fixes to each library on its refusal-codes branch, add a vectors case for any new rule, re-pin, and rerun on fresh seeds (generate on proxmox0: `python3 aprs-vectors/tools/generate.py dataN.jsonl.gz --count 1000000 --seed N`, same with `--recipes`, and `mutate.py pass3-2026-09-27-lines.hex.gz fuzzM.hex.gz --seeds 50000 --count 2000000 --seed M`; sync ~/src/aprs-* to /root/aprs-exact with rsync excluding target, build*/, node_modules, bin, obj; run `FUZZ=fuzzM.hex.gz ./run.sh rNN dataN.jsonl.gz recipesN.jsonl.gz` with setsid nohup). Repeat until a fresh run is clean.
2. When clean: merge the five library PRs (--merge, --delete-branch), then aprs-vectors#19 last with a merge commit (keeps 380ca82 reachable).
3. Release 1.0.1: one version-bump PR per library (cs: tag only, version from tag; rs Cargo.toml+lock; py `__version__`; ts package.json+lock; c `PDN_APRS_VERSION` in include/pdn_aprs.h, regenerate dist), CHANGELOG Unreleased becomes 1.0.1, merge, then an annotated tag v1.0.1 on the merge commit's full SHA; watch each publish workflow and confirm the registry shows 1.0.1 (NuGet and npm lag a few minutes). Vectors: tag v1.0.1 on its merge commit; its release workflow attaches the zip.
4. packet.net#970 (Packet.Aprs 0.55.0 to 1.0.0, pin only): merge was blocked by the auto-mode classifier, and CI fails on an unrelated new NuGet advisory (System.Formats.Cbor 9.0.0, GHSA-vmv3-wvjp-wqpj, patched 9.0.24) that breaks every packet.net restore. Tell Tom; do not work around the block. Bump to 1.0.1 there too if he wants.
5. Cleanup last: delete /home/tf/aprs-exact scratch (keep nothing large), and /root/aprs-exact on proxmox0 (toolchains plus a 720 MB capture copy). Keep the `exact-bytes-notes` branch as the record.
6. Update aprs-vectors issue trail and the memory note aprs-exact-bytes-round.md, and tell Tom in a few lines.

## Rules that still apply
No em or en dashes anywhere; no hard-wrapped markdown or commit/PR bodies; commit trailers `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` (Sonnet agents use Sonnet 5.5); review sub-agents on Opus, writers may be Sonnet; heavy runs on proxmox0, never this LXC; aprs-ts's dump loads an uncommitted dist/ (run.sh rebuilds it).
