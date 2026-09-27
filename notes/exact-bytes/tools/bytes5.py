#!/usr/bin/env python3
"""bytes5.py <prefix> [idx.json]: where the five encoders write different bytes for the same lenient data.
Groups by which implementations side together; with an index of cases, also checks canonical_info."""
import gzip, json, sys, collections
NAMES = ["cs", "rs", "py", "ts", "c"]
P = sys.argv[1]
idx = json.load(open(sys.argv[2])) if len(sys.argv) > 2 and sys.argv[2] else None
files = {n: gzip.open(f"{P}.{n}.jsonl.gz", "rt") for n in NAMES}
lines = gzip.open(sys.argv[3] if len(sys.argv) > 3 else f"{P}.hex.gz", "rt") if True else None
buckets = collections.defaultdict(list)
canon = collections.Counter(); canon_bad = collections.defaultdict(list)
total = 0
def show(r):
    if r.get("reencode") in ("refused", "none"):
        return r["reencode"]
    w = bytes.fromhex(r.get("written", "")).decode("latin-1")
    d = r.get("written_destination")
    return (f"[{d}] " if d else "") + w + ("" if r["reencode"] in ("identical", "equivalent") else f"  <{r['reencode']}>")
for n, hexline in enumerate(lines):
    total += 1
    recs = {x: json.loads(files[x].readline().replace("-nan", "null")) for x in NAMES}
    outs = {x: show(recs[x]) for x in NAMES}
    typ = (recs["cs"].get("lenient", {}).get("data") or {}).get("type", "?")
    if len(set(outs.values())) > 1:
        groups = collections.defaultdict(list)
        for x in NAMES:
            groups[outs[x]].append(x)
        sides = " | ".join(sorted(("+".join(g) for g in groups.values()), key=lambda s: (-len(s), s)))
        buckets[(typ, sides)].append((n, bytes.fromhex(hexline.strip()), groups))
    if idx:
        c = idx[n]
        if c["reencode"] == "equivalent" and c["canonical_info"] is not None:
            for x in NAMES:
                ok = recs[x].get("reencode") in ("equivalent", "identical") and bytes.fromhex(recs[x].get("written", "")) == c["canonical_info"].encode("utf-8")
                canon[(x, ok)] += 1
                if not ok:
                    canon_bad[x].append(c["id"])
print(f"{sum(len(v) for v in buckets.values())} of {total} lines: the encoders write different bytes")
for (typ, sides), ex in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
    print(f"\n{len(ex):6d}  {typ:<16} {sides}")
    for n, line, groups in ex[:int(sys.argv[4]) if len(sys.argv) > 4 else 2]:
        cid = f" {idx[n]['id']}" if idx else ""
        print(f"        #{n}{cid}  in: {line.decode('latin-1')!r}")
        for out, g in groups.items():
            print(f"          {'+'.join(g):<14} {out!r}")
if idx:
    print("\ncanonical_info matches (equivalent cases):")
    for x in NAMES:
        print(f"  {x}: {canon[(x, True)]} match, {canon[(x, False)]} do not")
    json.dump(canon_bad, open(f"{P}.canon_bad.json", "w"), indent=1)
