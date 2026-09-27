#!/usr/bin/env python3
"""Makes mutated APRS packets for differential fuzzing.

Reads seed packets (a capture's lines file, one hex-encoded TNC2 line per line, and the inputs of
every case here), and writes variants of them in the same form: cut short, bytes changed to ones
APRS gives meaning to, fields spliced in from other packets, numbers pushed to their limits, the
data type changed, letters' case flipped. Run each implementation's dump over the result and
compare them with compare.py; every disagreement is a rule the cases do not pin yet.

    python3 tools/mutate.py lines.hex.gz fuzz.hex.gz --seeds 50000 --count 2000000 --seed 1

Standard library only. The same arguments always give the same output.
"""

import argparse
import glob
import gzip
import json
import os
import random
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Bytes that mean something somewhere in APRS, weighted towards the structural ones.
SIGNIFICANT = (
    b"0123456789" * 3
    + b"/\\._ -*#!=@;:)>}{|~^`'\"$%&+,<?[]"
    + b"NSEWnsew"
    + b"zhcsgtrpPhbLlT"
    + b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    + bytes([0xFF, 0x1D, 0x1C, 0x00, 0x7F, 0x80, 0xC3, 0xA9, 0xE2, 0x0D])
)
DTIS = b"!=/@;)`':>T_#*$<?{}%,&+.[_"
BOUNDARIES = [b"0", b"00", b"000", b"9", b"99", b"999", b"360", b"361", b"90", b"91", b"180", b"181", b"59", b"60", b"100", b"1000", b"8280", b"8281", b"255", b"256", b"12", b"13", b"24", b"31", b"32"]
DIGITS = re.compile(rb"[0-9]+")


def seeds_from_cases():
    """The input of every case, as a whole TNC2 line."""
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, "cases", "*.json"))):
        with open(path, encoding="utf-8") as f:
            for case in json.load(f)["cases"]:
                i = case["input"]
                if "tnc2" in i:
                    out.append(i["tnc2"].encode("utf-8"))
                elif "tnc2_hex" in i:
                    out.append(bytes.fromhex(i["tnc2_hex"]))
                elif "info" in i or "info_hex" in i:
                    info = i["info"].encode("utf-8") if "info" in i else bytes.fromhex(i["info_hex"])
                    src = i.get("source", "N0CALL").encode()
                    dst = i.get("destination", "APZ001").encode()
                    out.append(src + b">" + dst + b":" + info)
    return out


def reservoir(path, k, rng):
    """k lines chosen evenly at random from a hex lines file, without holding it all."""
    chosen = []
    with gzip.open(path, "rt") as f:
        for n, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            if len(chosen) < k:
                chosen.append(line)
            else:
                j = rng.randrange(n + 1)
                if j < k:
                    chosen[j] = line
    return [bytes.fromhex(h) for h in chosen]


def split(line):
    colon = line.find(b":")
    return (line[: colon + 1], line[colon + 1 :]) if colon > 0 else (b"", line)


def mutate(line, seeds, rng):
    head, info = split(line)
    info = bytearray(info)
    for _ in range(rng.choice((1, 1, 1, 2, 2, 3))):
        op = rng.randrange(10)
        n = len(info)
        if op == 0 and n > 1:  # cut short
            del info[rng.randrange(1, n) :]
        elif op == 1 and n:  # change a byte to a significant one
            info[rng.randrange(n)] = rng.choice(SIGNIFICANT)
        elif op == 2:  # insert a significant byte
            info.insert(rng.randrange(n + 1), rng.choice(SIGNIFICANT))
        elif op == 3 and n:  # delete a byte
            del info[rng.randrange(n)]
        elif op == 4:  # splice in part of another packet's information field
            other = split(rng.choice(seeds))[1]
            if other:
                a = rng.randrange(len(other))
                b = min(len(other), a + rng.randrange(1, 20))
                at = rng.randrange(n + 1)
                info[at:at] = other[a:b]
        elif op == 5 and n:  # push a number to a limit
            runs = list(DIGITS.finditer(bytes(info)))
            if runs:
                m = rng.choice(runs)
                info[m.start() : m.end()] = rng.choice(BOUNDARIES)
        elif op == 6 and n:  # change the data type
            info[0] = rng.choice(DTIS)
        elif op == 7 and n:  # flip a letter's case
            i = rng.randrange(n)
            if 65 <= info[i] <= 90 or 97 <= info[i] <= 122:
                info[i] ^= 0x20
        elif op == 8 and n > 2:  # repeat a span
            a = rng.randrange(n)
            b = min(n, a + rng.randrange(1, 10))
            info[b:b] = info[a:b]
        elif op == 9 and n > 2:  # swap two bytes
            i, j = rng.randrange(n), rng.randrange(n)
            info[i], info[j] = info[j], info[i]
    return head + bytes(info)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lines", help="a capture's lines file (hex TNC2, gzip), or - for the cases alone")
    ap.add_argument("out", help="where to write the mutated lines (hex TNC2, gzip)")
    ap.add_argument("--seeds", type=int, default=50000, help="capture lines to take as seeds (default 50000)")
    ap.add_argument("--count", type=int, default=1000000, help="mutated lines to write (default 1000000)")
    ap.add_argument("--seed", type=int, default=1, help="random seed (default 1)")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    seeds = seeds_from_cases()
    if args.lines != "-":
        seeds += reservoir(args.lines, args.seeds, rng)
    seen = set()
    written = 0
    with gzip.open(args.out, "wt", compresslevel=1) as out:
        while written < args.count:
            line = mutate(rng.choice(seeds), seeds, rng)
            if line in seen or b"\n" in line:
                continue
            seen.add(line)
            out.write(line.hex().upper() + "\n")
            written += 1
    print(f"{args.out}: {written:,} mutated lines from {len(seeds):,} seeds")


if __name__ == "__main__":
    main()
