#!/usr/bin/env python3
"""Compares implementations' dumps of the same input, by the vectors' rules.

  python3 tools/compare.py A.jsonl.gz B.jsonl.gz [C.jsonl.gz ...] [--names A B C ...]
                           [--input input.gz] [--examples 3] [--json summary.json]

Each dump has one JSON object per input line, in the input's order, as the implementations' dump
tools write it in one of three modes (README, "Comparing implementations"): decode (packets),
encode (data from tools/generate.py) or build (recipes from tools/generate.py --recipes). The
mode is read from the records.

For every input line, each part of the records (the lenient data, the strict diagnostics, the
bytes written, each key of the API view, ...) is compared across the implementations that have
it, and where they differ the line goes in a bucket named by the data type, the part, and which
implementations side together. Objects must have the same keys; numbers agree within 1e-9;
diagnostics compare as multisets. A record whose result is `unsupported` is left out of the
comparison of that line. For encode and build dumps it also checks each implementation on its
own: bytes written for exact data must decode to that data, cleanly; a built line must decode
cleanly. `--input` is the input all the dumps read; with it, the report shows each bucket's
example inputs. Exits 1 if any line differs. Standard library only.
"""

import argparse
import gzip
import json
import sys
from collections import Counter, defaultdict


def norm(v):
    """A value with numbers cut to 9 significant digits, so that equal-within-1e-9 compares equal."""
    if isinstance(v, bool) or v is None or isinstance(v, str):
        return v
    if isinstance(v, (int, float)):
        if v != v:
            return "nan"
        r = float(f"{v:.9g}")
        return int(r) if r == int(r) and abs(r) < 1e15 else r
    if isinstance(v, dict):
        return {k: norm(x) for k, x in v.items()}
    if isinstance(v, list):
        return [norm(x) for x in v]
    return v


def key(v):
    return json.dumps(norm(v), sort_keys=True, ensure_ascii=False)


def diagnostics_key(ds):
    return json.dumps(sorted(ds or []))


def result_parts(prefix, r):
    """The comparable parts of a decode result."""
    if r is None:
        return {}
    if "header_error" in r:
        return {f"{prefix}.header_error": diagnostics_key(r["header_error"])}
    return {
        f"{prefix}.header": key(r.get("header")),
        f"{prefix}.data": key(r.get("data")),
        f"{prefix}.diagnostics": diagnostics_key(r.get("diagnostics")),
    }


def api_parts(prefix, api):
    parts = {}
    for k, v in (api or {}).items():
        if k == "inner":
            parts.update(api_parts(f"{prefix}.inner", v))
        else:
            parts[f"{prefix}.{k}"] = key(v)
    return parts


def parts_of(mode, r):
    if mode == "decode":
        p = {}
        p.update(result_parts("lenient", r.get("lenient")))
        p.update(result_parts("strict", r.get("strict")))
        p["reencode"] = json.dumps(r.get("reencode"))
        if r.get("reencode") not in ("refused", "none"):
            p["written"] = json.dumps([r.get("written"), r.get("written_destination")])
        p.update(api_parts("api", r.get("api")))
        return p
    p = {"result": r.get("result")}
    if mode == "encode":
        if r.get("result") == "written":
            p["info"] = json.dumps([r.get("info"), r.get("destination")])
            p.update(result_parts("again", r.get("again")))
    else:
        if r.get("result") == "built":
            p["tnc2"] = json.dumps(r.get("tnc2"))
            p.update(result_parts("again", r.get("again")))
    return p


def data_type(mode, recs, inp):
    if mode == "decode":
        for r in recs:
            lenient = r.get("lenient") or {}
            if "header_error" in lenient:
                return "header-error"
            if "data" in lenient:
                return lenient["data"].get("type", "?")
        return "?"
    if inp is not None:
        if mode == "encode":
            return (inp.get("data") or {}).get("type", "?")
        return inp.get("report", "?")
    return "?"


def without_inner_info(data):
    """Third-party data without its inner packet's diagnostics, which generated data cannot know
    in advance (only info ones get this far)."""
    if isinstance(data, dict) and isinstance(data.get("packet"), dict) and "diagnostics" in data["packet"]:
        data = dict(data, packet={k: v for k, v in data["packet"].items() if k != "diagnostics"})
    return data


def own_checks(mode, r, inp):
    """What is wrong with one implementation's record on its own, or None."""
    if mode == "encode" and r.get("result") == "written":
        again = r.get("again") or {}
        bad = [d for d in again.get("diagnostics", []) if not d.startswith("info:")]
        if "header_error" in again:
            bad = bad + again["header_error"]
        if bad:
            return "written bytes decode with " + ", ".join(sorted(set(bad)))
        inner = ((again.get("data") or {}).get("packet") or {}).get("diagnostics", [])
        inner_bad = [d for d in inner if not d.startswith("info:")]
        if inner_bad:
            return "written bytes decode with, in the inner packet, " + ", ".join(sorted(set(inner_bad)))
        if inp is not None and inp.get("exact") and key(without_inner_info(again.get("data"))) != key(without_inner_info(inp.get("data"))):
            a, b = norm(again.get("data")) or {}, norm(inp.get("data")) or {}
            keys = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
            return "written bytes decode to different data: " + ", ".join(keys)
    if mode == "build" and r.get("result") == "built":
        again = r.get("again") or {}
        bad = [d for d in again.get("diagnostics", []) if not d.startswith("info:")]
        if "header_error" in again:
            bad = bad + again["header_error"]
        if bad:
            return "built line decodes with " + ", ".join(sorted(set(bad)))
    return None


def show_input(mode, line):
    if line is None:
        return ""
    if mode == "decode":
        try:
            return json.dumps(bytes.fromhex(line.strip()).decode("latin-1"), ensure_ascii=True)[1:-1]
        except ValueError:
            return line.strip()
    return line.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("dumps", nargs="+")
    ap.add_argument("--names", nargs="+")
    ap.add_argument("--input", "--lines", dest="input")
    ap.add_argument("--examples", type=int, default=3)
    ap.add_argument("--json")
    ap.add_argument("--mode", choices=["decode", "encode", "build"], help="when there is no --input to tell encode from build")
    args = ap.parse_args()
    names = args.names or [f"#{i + 1}" for i in range(len(args.dumps))]
    if len(names) != len(args.dumps):
        sys.exit("give one name per dump")

    files = [gzip.open(p, "rt", encoding="utf-8") for p in args.dumps]
    inputs = gzip.open(args.input, "rt", encoding="utf-8", errors="replace") if args.input else None
    buckets = Counter()
    examples = defaultdict(list)
    own = Counter()
    own_examples = defaultdict(list)
    unsupported = Counter()
    mode = None
    total = differ = 0
    while True:
        raw = [f.readline() for f in files]
        if not any(raw):
            break
        if not all(raw):
            sys.exit("the dumps have different lengths")
        line = inputs.readline() if inputs else None
        recs = [json.loads(x.replace("-nan", "null")) for x in raw]
        ns = {r.get("n") for r in recs}
        if len(ns) != 1:
            sys.exit(f"out of step at line {total}: n = {sorted(ns, key=str)}")
        if mode is None:
            r0 = recs[0]
            if "lenient" in r0 or "reencode" in r0:
                mode = "decode"
            elif line is not None:
                mode = "build" if "report" in json.loads(line) else "encode"
            else:
                mode = args.mode or sys.exit("an encode or build dump needs --input (or --mode) to say which it is")
        inp = json.loads(line) if line is not None and mode != "decode" else None
        total += 1
        n = recs[0].get("n", total - 1)
        kind = data_type(mode, recs, inp)
        live = [i for i, r in enumerate(recs) if r.get("result") != "unsupported"]
        for i, r in enumerate(recs):
            if r.get("result") == "unsupported":
                unsupported[(names[i], r.get("reason", "?"))] += 1
            problem = own_checks(mode, r, inp)
            if problem:
                k = (names[i], kind, problem)
                own[k] += 1
                if len(own_examples[k]) < args.examples:
                    own_examples[k].append((n, show_input(mode, line)))
        parts = [parts_of(mode, recs[i]) for i in live]
        facets = sorted({k for p in parts for k in p})
        any_diff = False
        for facet in facets:
            groups = defaultdict(list)
            for i, p in zip(live, parts):
                if facet in p:
                    groups[p[facet]].append(names[i])
            if len(groups) < 2:
                continue
            any_diff = True
            sides = " | ".join(sorted(("+".join(g) for g in groups.values()), key=lambda s: (-s.count("+"), s)))
            k = (kind, facet, sides)
            buckets[k] += 1
            if len(examples[k]) < args.examples:
                examples[k].append((n, show_input(mode, line), {"+".join(g): v[:300] for v, g in groups.items()}))
        if any_diff:
            differ += 1

    print(f"{mode}: {total:,} lines; {total - differ:,} agree; {differ:,} differ. {len(buckets)} buckets.")
    if unsupported:
        print("unsupported (left out): " + ", ".join(f"{name} {reason} {c:,}" for (name, reason), c in unsupported.most_common(20)))
    for (kind, facet, sides), count in buckets.most_common():
        print(f"\n{count:,}  [{kind}] {facet}: {sides}")
        for n, shown, values in examples[(kind, facet, sides)]:
            print(f"    line {n}: {shown[:240]}")
            for who, v in values.items():
                print(f"      {who:<16} {v[:240]}")
    if own:
        print(f"\nEach on its own: {sum(own.values()):,} problems")
        for (name, kind, problem), count in own.most_common():
            print(f"\n{count:,}  {name} [{kind}] {problem[:200]}")
            for n, shown in own_examples[(name, kind, problem)]:
                print(f"    line {n}: {shown[:240]}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({
                "mode": mode, "lines": total, "differ": differ,
                "buckets": [{"type": k, "part": p, "sides": s, "count": c,
                             "examples": [{"n": n, "input": i, "values": v} for n, i, v in examples[(k, p, s)]]}
                            for (k, p, s), c in buckets.most_common()],
                "own": [{"implementation": nm, "type": k, "problem": pr, "count": c,
                         "examples": [{"n": n, "input": i} for n, i in own_examples[(nm, k, pr)]]}
                        for (nm, k, pr), c in own.most_common()],
                "unsupported": [{"implementation": nm, "reason": r, "count": c} for (nm, r), c in unsupported.most_common()],
            }, f, indent=1, ensure_ascii=False)
    return 1 if differ or own else 0


if __name__ == "__main__":
    sys.exit(main())
