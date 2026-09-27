#!/usr/bin/env python3
"""Writes every decode case's input as a hex TNC2 line (cases.hex.gz) and an index (cases.idx.json)."""
import glob, gzip, json, sys
V = sys.argv[1]

def ax25_to_tnc2(frame):
    addrs = []
    i = 0
    while True:
        a = frame[i:i + 7]
        call = bytes(b >> 1 for b in a[:6]).decode("latin-1").rstrip()
        ssid = (a[6] >> 1) & 0x0F
        h = a[6] & 0x80
        addrs.append((call + (f"-{ssid}" if ssid else ""), h))
        i += 7
        if a[6] & 1:
            break
    info = frame[i + 2:]
    dest, src = addrs[0][0], addrs[1][0]
    path = [c + ("*" if h else "") for c, h in addrs[2:]]
    return (src + ">" + dest + "".join("," + p for p in path) + ":").encode() + info

out, idx = [], []
for f in sorted(glob.glob(f"{V}/cases/*.json")):
    for c in json.load(open(f))["cases"]:
        i = c["input"]
        if "encode" in i:
            continue
        if "tnc2" in i:
            line = i["tnc2"].encode("utf-8")
        elif "tnc2_hex" in i:
            line = bytes.fromhex(i["tnc2_hex"])
        elif "ax25_hex" in i:
            line = ax25_to_tnc2(bytes.fromhex(i["ax25_hex"]))
        else:
            info = i["info"].encode("utf-8") if "info" in i else bytes.fromhex(i["info_hex"])
            hdr = i.get("source", "N0CALL") + ">" + i.get("destination", "APZ001")
            if i.get("path"):
                p = i["path"]
                hdr += "," + (",".join(p) if isinstance(p, list) else p)
            line = hdr.encode("latin-1") + b":" + info
        out.append(line.hex())
        idx.append({"id": c["id"], "reencode": c.get("reencode"), "canonical_info": c.get("canonical_info"), "file": f.split("/")[-1]})
with gzip.open("cases.hex.gz", "wt") as g:
    g.write("\n".join(out) + "\n")
json.dump(idx, open("cases.idx.json", "w"))
print(len(out), "cases")
