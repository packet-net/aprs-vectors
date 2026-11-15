#!/usr/bin/env python3
"""Makes Mic-E status texts and comments of every awkward shape, for differential comparison.

Random mutation almost never puts a locator, a later altitude, base-91 telemetry, a !DAO!, a PHG
or RNG and a few spaces together in the orders that test where each is read, so this writes them
on purpose: one Mic-E report per line (the same nine fixed bytes and destination each time), its
status text a type code or none, then a mix of a locator, elements, text and runs of spaces in any
order, sometimes with an altitude dropped inside another element, sometimes with a device suffix,
and sometimes with a `/A=` whose last digits and a `}` after them read as a later Mic-E altitude.
The output is one hex-encoded TNC2 line per line, as tools/mutate.py writes, for the dump tools and
compare.py (README, Comparing implementations).

    python3 tools/mice_shapes.py mice.hex.gz --count 20000 --seed 1
    python3 tools/mice_shapes.py comments.hex.gz --comments --count 20000 --seed 1

With --comments it writes position, object, weather and Mic-E reports instead, their comments mixing a
voice frequency and its fields, a `/A=` altitude, PHG, RNG, DFS, signpost braces, base-91 telemetry,
a !DAO!, weather fields and text, with an element dropped inside another (a frequency's digits or
field included) and a `/A=`, telemetry or !DAO! before a frequency, between it and its fields, or
between two of them, so the rule that lifting never joins the text either side is reached; in Mic-E
status text a later Mic-E altitude is among the lifted elements, beside or overlapping a `/A=`.

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
    b"/A=000100}",  # a /A= overlapping a later Mic-E altitude (100})
    b"/A=-00016}",
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


POSITION = b"N0CALL>APZ001:!4903.50N/07201.75W>"
OBJECT = b"N0CALL>APZ001:;SIGN     *092345z4903.50N\\07201.75Wm"
WEATHER = b"N0CALL>APZ001:!4903.50N/07201.75W_220/004g005"
FREQUENCIES = [b"146.520MHz", b"445.950MHz", b"146.52 MHz"]
FIELDS = [b" T100", b" t077", b" C107", b" -060", b" +500", b" R25m", b" Toff"]
LIFTED = [b"/A=000100", b"/A=-00016", b"|!!!!|", b"|!:&0'p|", b"!W12!", b"!w3U!"]
# in Mic-E status text a later Mic-E altitude is lifted too, beside a /A= or overlapping one
MICE_LIFTED = LIFTED + [b'"4e}', b"abc}", b"/A=000100}", b"/A=-00016}"]
COMMENT_ELEMENTS = [b"PHG2360", b"RNG0050", b"DFS2360", b"{55}", b"/A=000123", b"x", b"hello", b" ", b"  "]
WEATHER_FIELDS = [b"t077", b"r000", b"p010", b"P020", b"h50", b"b10132", b"L123", b"s001", b"Xyz", b"X yz"]


def split_inside(rng, part, lifted=LIFTED):
    """``part`` with a lifted element dropped somewhere inside it."""
    if len(part) < 2:
        return part
    at = rng.randrange(1, len(part))
    return part[:at] + rng.choice(lifted) + part[at:]


def comment_shape(rng):
    kind = rng.choice(("position", "position", "object", "weather", "mic-e"))
    lifted = MICE_LIFTED if kind == "mic-e" else LIFTED
    parts = []
    if kind == "weather":
        parts += [rng.choice(WEATHER_FIELDS) for _ in range(rng.randrange(1, 4))]
    elif rng.random() < 0.7:
        # a frequency with fields, something lifted before it, between it and a field, or between fields
        freq = [rng.choice(FREQUENCIES)] + [rng.choice(FIELDS) for _ in range(rng.randrange(0, 3))]
        if rng.random() < 0.6:
            freq.insert(rng.randrange(0, len(freq) + 1), rng.choice(lifted))
        parts += freq
    for _ in range(rng.randrange(0, 4)):
        parts.append(rng.choice(COMMENT_ELEMENTS + lifted))
    if rng.random() < 0.5 and parts:
        i = rng.randrange(len(parts))
        parts[i] = split_inside(rng, parts[i], lifted)
    if kind == "mic-e":
        return HEADER + rng.choice(TYPE_CODES) + b"".join(parts)
    head = {"position": POSITION, "object": OBJECT, "weather": WEATHER}[kind]
    return head + b"".join(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", help="where to write the lines (hex TNC2, gzip)")
    ap.add_argument("--count", type=int, default=20000, help="distinct lines to write (default 20000)")
    ap.add_argument("--seed", type=int, default=1, help="random seed (default 1)")
    ap.add_argument("--comments", action="store_true", help="position, object and weather comments instead of Mic-E status text")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    seen = set()
    tries = 0
    with gzip.open(args.out, "wt", compresslevel=1) as out:
        while len(seen) < args.count and tries < args.count * 50:
            tries += 1
            line = comment_shape(rng) if args.comments else HEADER + shape(rng)
            if line in seen:
                continue
            seen.add(line)
            out.write(line.hex().upper() + "\n")
    print(f"{args.out}: {len(seen):,} {'comment' if args.comments else 'Mic-E status-text'} shapes")


if __name__ == "__main__":
    main()
