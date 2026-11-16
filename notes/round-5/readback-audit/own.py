import sys, gzip, json, collections
sys.path.insert(0, "/home/tf/src/aprs-r4/aprs-vectors/tools")
import compare as C
mode, inp, dump = sys.argv[1], sys.argv[2], sys.argv[3]
cnt = collections.Counter(); ex = collections.defaultdict(list)
res = collections.Counter()
with gzip.open(inp, "rt") as fi, gzip.open(dump, "rt") as fd:
    for li, ld in zip(fi, fd):
        i = json.loads(li); r = json.loads(ld)
        res[r.get("result")] += 1
        w = C.own_checks(mode, r, i)
        if mode == "build" and r.get("result") == "built" and w is None:
            # compare text fields given with text read back
            a = (r.get("again") or {}).get("data") or {}
            args = i.get("args", {})
            for k_in, k_out in (("comment", "comment"), ("text", "text")):
                if k_in in args and args[k_in] != "":
                    got = a.get(k_out, a.get("comment") if k_out == "text" else None)
                    if got != args[k_in]:
                        w = f"build {k_in} reads back as {got!r}"
            st = i.get("station") or {}
            h = (r.get("again") or {}).get("header") or {}
            if "source" in st and h.get("source") != st["source"]:
                w = f"header source {h.get('source')!r}"
            if st.get("destination") and i.get("report") != "mic-e" and h.get("destination") != st["destination"]:
                w = f"header destination {h.get('destination')!r}"
            if (h.get("path") or []) != (st.get("path") or []):
                w = f"header path {h.get('path')!r}"
        if w:
            t = (i.get("data") or {}).get("type") or i.get("report")
            key = (t, w[:90])
            cnt[key] += 1
            if len(ex[key]) < 2:
                ex[key].append((li.strip()[:400], r.get("info") or r.get("tnc2") or r.get("line"), json.dumps((r.get("again") or {}).get("data"))[:400]))
print(res)
for k, v in cnt.most_common():
    print(v, k)
    for e in ex[k]:
        print("   IN ", e[0]); print("   OUT", e[1]); print("   BACK", e[2])
