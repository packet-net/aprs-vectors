#!/usr/bin/env python3
"""Makes Mic-E status texts of every awkward shape, for differential comparison.

Random mutation almost never puts a locator, a later altitude, base-91 telemetry, a !DAO!, a PHG
or RNG and a few spaces together in the orders that test where each is read, so this writes them
on purpose: one Mic-E report per line (the same nine fixed bytes and destination each time), its
status text a type code or none, then a mix of a locator, elements, text and runs of spaces in any
order, sometimes with an altitude dropped inside another element, sometimes with a device suffix.
The output is one hex-encoded TNC2 line per line, as tools/mutate.py writes, for the dump tools and
compare.py (README, Comparing implementations).

    python3 tools/mice_shapes.py mice.hex.gz --count 20000 --seed 1

Standard library only. The same arguments always give the same output.
"""

import argparse
import gzip
import random

HEADER = b'N0CALL>S32UVT:`(_fn"Oj/'  # 33.4273N 112.129W, course 251, speed 20, symbol /j
TYPE_CODES = [b"", b"`", b"'", b">", b"]", b" "]
SUFFIXES = [b"", b"", b"", b"=", b"_1", b"_%", b"^"]
LOCATORS = [b"IO91/G", b"IO91SX/G", b"Io91/G", b"io91sx/G", b"IO91/g", b"IO91SX"]
ALTITUDES = [b'"4e}', b"abc}", b'"4T}']
ELEMENTS = [
    b"|!:&0'p|",  # base-91 telemetry, two values
    b"|!:&0hl!Y[='p|",  # five values and the bits
    b"!W12!",  # !DAO!, human-readable
    b"!w3U!",  # !DAO!, base-91
    b"PHG3330",
    b"PHG5132",
    b"RNG0001",
    b"/A=000123",
    b"x",
    b"hello",
    b"=",
    b"/",
    b"}",
    b"!W1",  # the halves of elements
    b"2!",
    b"PH",
    b"G3330",
]
SPACES = [b" ", b"  ", b"   "]


def shape(rng):
    parts = [rng.choice(LOCATORS)] if rng.random() < 0.9 else []
    for _ in range(rng.randrange(1, 6)):
        r = rng.random()
        if r < 0.25:
            parts.append(rng.choice(ALTITUDES))
        elif r < 0.45:
            parts.append(rng.choice(SPACES))
        else:
            parts.append(rng.choice(ELEMENTS))
    if rng.random() < 0.7:
        # the locator first, as a sender puts it; otherwise wherever the shuffle leaves it
        head, rest = parts[:1], parts[1:]
        rng.shuffle(rest)
        parts = head + rest
    else:
        rng.shuffle(parts)
    if rng.random() < 0.3:
        # an altitude inside another element (a locator included), splitting its bytes
        long = [i for i, p in enumerate(parts) if len(p) > 1]
        if long:
            i = rng.choice(long)
            at = rng.randrange(1, len(parts[i]))
            parts[i] = parts[i][:at] + rng.choice(ALTITUDES) + parts[i][at:]
    return rng.choice(TYPE_CODES) + b"".join(parts) + rng.choice(SUFFIXES)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", help="where to write the lines (hex TNC2, gzip)")
    ap.add_argument("--count", type=int, default=20000, help="distinct lines to write (default 20000)")
    ap.add_argument("--seed", type=int, default=1, help="random seed (default 1)")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    seen = set()
    tries = 0
    with gzip.open(args.out, "wt", compresslevel=1) as out:
        while len(seen) < args.count and tries < args.count * 50:
            tries += 1
            line = HEADER + shape(rng)
            if line in seen:
                continue
            seen.add(line)
            out.write(line.hex().upper() + "\n")
    print(f"{args.out}: {len(seen):,} Mic-E status-text shapes")


if __name__ == "__main__":
    main()
