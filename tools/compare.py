#!/usr/bin/env python3
"""Compares two implementations' decodings of the same capture, by the vectors' rules.

  python3 tools/compare.py A.jsonl.gz B.jsonl.gz [--names A B] [--lines lines.hex.gz]
                           [--examples 3] [--json summary.json]

Each input has one JSON object per line, in the same order, as the implementations' differential
dumps write it (packet.net `aprs-corpus diff dump`, aprs-rs `examples/diff_dump.rs`):

  {"n": 0, "lenient": R, "strict": R, "reencode": "identical|equivalent|refused|fails|none"}

where R is {"header", "data", "diagnostics"} in the vectors' neutral form, or {"header_error": [...]}.
`--lines` is the capture both read (one hex TNC2 line per line, gzip); with it, the report shows
each bucket's example packets.

Objects must have exactly the same keys, numbers agree within 1e-9, diagnostics compare as
multisets. Disagreements are grouped into buckets by a stable signature: the first
implementation's data type, and which fields and diagnostics differ. When one side re-encodes
byte for byte and the other only equivalently, both round-trip and the encoders merely write
different bytes: that is counted separately as an encoder choice, not a disagreement. Standard
library only.
"""

import argparse
import gzip
import json
import sys
from collections import Counter, defaultdict


def number_equal(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, int) and isinstance(b, int):
        return a == b
    scale = max(abs(a), abs(b))
    return abs(a - b) <= 1e-9 * (scale if scale >= 1 else 1)


def value_differences(a, b, path, out):
    """Signatures of where a and b differ: the path, with list indices dropped."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in a.keys() | b.keys():
            p = f"{path}.{k}"
            if k not in b:
                out.add(f"{p} (only A)")
            elif k not in a:
                out.add(f"{p} (only B)")
            else:
                value_differences(a[k], b[k], p, out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.add(f"{path} (length)")
        else:
            for x, y in zip(a, b):
                value_differences(x, y, f"{path}[]", out)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        if not number_equal(a, b):
            out.add(path)
    elif a != b:
        if path.endswith(".type") or path.endswith(".reason"):
            out.add(f"{path}: {a} vs {b}")
        else:
            out.add(path)


def diagnostic_differences(a, b, path, out):
    ca, cb = Counter(a or []), Counter(b or [])
    for d in sorted((ca - cb).elements()):
        out.add(f"{path} only A: {d}")
    for d in sorted((cb - ca).elements()):
        out.add(f"{path} only B: {d}")


def result_differences(a, b, path, out):
    if "header_error" in a or "header_error" in b:
        if "header_error" in a and "header_error" in b:
            diagnostic_differences(a["header_error"], b["header_error"], f"{path}.header_error", out)
        else:
            out.add(f"{path}: header error only {'A' if 'header_error' in a else 'B'}")
        return
    value_differences(a.get("header"), b.get("header"), f"{path}.header", out)
    value_differences(a.get("data"), b.get("data"), f"{path}.data", out)
    diagnostic_differences(a.get("diagnostics"), b.get("diagnostics"), f"{path}.diagnostics", out)


def data_type(r):
    if "header_error" in r:
        return "header-error"
    return r.get("data", {}).get("type", "?")


def read_examples(lines_path, wanted):
    found = {}
    if not wanted:
        return found
    with gzip.open(lines_path, "rt", encoding="ascii") as f:
        for i, line in enumerate(f):
            if i in wanted:
                found[i] = bytes.fromhex(line.strip()).decode("latin-1")
                if len(found) == len(wanted):
                    break
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--names", nargs=2, default=["A", "B"])
    ap.add_argument("--lines")
    ap.add_argument("--examples", type=int, default=3)
    ap.add_argument("--json")
    args = ap.parse_args()

    buckets = Counter()
    choices = Counter()
    examples = defaultdict(list)
    total = differ = 0
    parts = Counter()
    with gzip.open(args.a, "rt", encoding="utf-8") as fa, gzip.open(args.b, "rt", encoding="utf-8") as fb:
        for la, lb in zip(fa, fb):
            ra, rb = json.loads(la), json.loads(lb)
            if ra["n"] != rb["n"]:
                sys.exit(f"out of step at A {ra['n']}, B {rb['n']}: the dumps must read the same lines")
            total += 1
            out = set()
            result_differences(ra["lenient"], rb["lenient"], "lenient", out)
            result_differences(ra["strict"], rb["strict"], "strict", out)
            if {ra["reencode"], rb["reencode"]} == {"identical", "equivalent"}:
                # Both round-trip; they only write different bytes. An encoder's choice, not a disagreement.
                choices[(data_type(ra["lenient"]), f"{ra['reencode']} vs {rb['reencode']}")] += 1
            elif ra["reencode"] != rb["reencode"]:
                out.add(f"reencode: {ra['reencode']} vs {rb['reencode']}")
            if not out:
                continue
            differ += 1
            for part in ("lenient", "strict", "reencode"):
                if any(s.startswith(part) for s in out):
                    parts[part] += 1
            key = (data_type(ra["lenient"]), tuple(sorted(out)))
            buckets[key] += 1
            if len(examples[key]) < args.examples:
                examples[key].append(ra["n"])
        if fa.readline() or fb.readline():
            sys.exit("the dumps have different lengths")

    raw = read_examples(args.lines, {n for ns in examples.values() for n in ns}) if args.lines else {}
    a, b = args.names
    print(f"{total:,} packets; {total - differ:,} agree; {differ:,} differ "
          f"(lenient {parts['lenient']:,}, strict {parts['strict']:,}, reencode {parts['reencode']:,}). A is {a}, B is {b}.")
    print(f"{len(buckets)} buckets.")
    if choices:
        print(f"Encoder choices (both re-encode to the same data, one byte for byte), not counted: "
              + ", ".join(f"{kind} {how} {count:,}" for (kind, how), count in choices.most_common()) + ".")
    for (kind, sig), count in buckets.most_common():
        print(f"\n{count:,}  [{kind}]")
        for s in sig:
            print(f"    {s}")
        for n in examples[(kind, sig)]:
            line = raw.get(n)
            shown = json.dumps(line, ensure_ascii=True)[1:-1] if line is not None else ""
            print(f"    e.g. line {n}: {shown[:200]}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"packets": total, "differ": differ,
                       "encoder_choices": [{"type": k, "reencode": h, "count": c} for (k, h), c in choices.most_common()],
                       "buckets": [
                {"type": k, "differences": list(s), "count": c, "examples": examples[(k, s)]}
                for (k, s), c in buckets.most_common()]}, f, indent=1)
    return 1 if differ else 0


if __name__ == "__main__":
    sys.exit(main())
