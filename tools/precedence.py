#!/usr/bin/env python3
"""Makes the refusal-precedence cases: for every pair of refusal codes that can occur together in
one encode record, a case with exactly those two faults, whose expected refusal is the one the
README's "Refusal reasons" order (R1) puts first.

  python3 tools/precedence.py                 # rewrites cases/precedence.json, prints the pair table
  python3 tools/precedence.py --check         # exits 1 if cases/precedence.json is not what it would write
  python3 tools/precedence.py --singles F     # writes each single fault as one neutral data object per line

Each fault is a small change to a clean record of one report type, and names the fields it
touches. A pair is made on a report type that has both faults on different fields, so that
neither fault's field is one the other takes away (the README: a field the report has no place
for is not range-checked, so two faults on one field are not two faults). A pair that no report
type can hold is listed with the reason.

The same arguments always give the same file. Standard library only.
"""

from __future__ import annotations

import argparse
import copy
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "cases", "precedence.json")
EXCLUDED = os.path.join(HERE, "precedence-excluded.txt")

# The README's "Refusal reasons" order (R1): the refusal names the first code that applies.
ORDER = [
    "not-encodable",
    "invalid-address", "ax25-cannot-carry", "tnc2-cannot-carry", "invalid-third-party-header",
    "invalid-addressee", "invalid-name", "invalid-timestamp", "not-a-number", "value-out-of-range", "value-has-no-form",
    "invalid-code", "invalid-symbol", "invalid-character", "too-long", "padding-space", "malformed", "invalid-message-id",
    "invalid-nmea",
    "extension-conflict", "field-not-allowed", "symbol-mismatch", "missing-field", "value-given-twice",
    "text-reads-as-field",
    "does-not-read-back",
]

# Codes no encode case can carry, each for one reason (the README's "Refusal reasons").
NO_CASE = {
    "not-encodable": "undecoded data has no other field to hold a second fault, and no neutral form of it is held by all six libraries",
    "invalid-address": "needs a packet header, which an encode case does not give",
    "ax25-cannot-carry": "needs a packet header, which an encode case does not give",
    "tnc2-cannot-carry": "needs a packet header, which an encode case does not give",
    "not-a-number": "JSON cannot carry NaN or infinity (generate.py --faults gives it to the dump tools)",
    "value-given-twice": "needs builder input in two units, and a case has no builder recipe (generate.py --recipes --faults gives it to the dump tools)",
    "does-not-read-back": "the fallback, which no case may expect",
}

LAT, LON = 49.05833333333333, -72.02916666666667  # 4903.50N 07201.75W
WIND = {"wind_direction_degrees": 220, "wind_speed_mph": 4, "wind_gust_mph": 5, "temperature_f": 77}

BASES = {
    "position": {"type": "position", "latitude": LAT, "longitude": LON, "symbol": "/-"},
    "compressed": {"type": "position", "latitude": 49.5, "longitude": -72.75, "symbol": "/>", "compressed": True},
    "object": {"type": "object", "name": "LEADER", "timestamp": "092345z", "latitude": LAT, "longitude": LON, "symbol": "/-"},
    "item": {"type": "item", "name": "ITEM1", "latitude": LAT, "longitude": LON, "symbol": "/-"},
    "mic-e": {"type": "mic-e", "mic_e_message": "en-route", "latitude": 42.179, "longitude": -71.1985, "symbol": "/>",
              "course_degrees": 215, "speed_knots": 9},
    "weather-position": {"type": "position", "latitude": LAT, "longitude": LON, "symbol": "/_", "weather": dict(WIND)},
    "weather-compressed": {"type": "position", "latitude": 49.5, "longitude": -72.75, "symbol": "/_", "compressed": True,
                           "compression": {"fix": "current", "source": "other", "origin": "software"},
                           "weather": {"wind_direction_degrees": 88, "wind_speed_mph": 0, "wind_gust_mph": 5, "temperature_f": 77}},
    "weather": {"type": "weather", "timestamp": "10090556", "weather": dict(WIND)},
    "weather-object": {"type": "object", "name": "LEADER", "timestamp": "092345z", "latitude": LAT, "longitude": LON, "symbol": "/_",
                       "weather": dict(WIND)},
    "message": {"type": "message", "addressee": "N0CALL", "text": "Hello"},
    "ack": {"type": "ack", "addressee": "N0CALL", "acked_id": "1"},
    "bulletin": {"type": "bulletin", "addressee": "BLN1", "text": "Hello"},
    "directed-query": {"type": "directed-query", "addressee": "N0CALL", "query_type": "APRSD"},
    "telemetry-names": {"type": "telemetry-names", "addressee": "N0CALL", "names": ["Vin", "Temp"]},
    "telemetry": {"type": "telemetry", "sequence": "001", "analog": [1, 2, 3, 4, 5], "bits": "00000000"},
    "telemetry-bits": {"type": "telemetry-bits", "addressee": "N0CALL", "bits": "11111111", "project": "Balloon"},
    "status": {"type": "status", "text": "Hello"},
    "locator-status": {"type": "status", "locator": "IO91SX", "symbol": "/-", "text": "Hello"},
    "capabilities": {"type": "capabilities", "capabilities": [["IGATE"], ["MSG_CNT", "43"]]},
    "query": {"type": "query", "query_type": "APRS", "footprint": {"latitude": 34.02, "longitude": -117.15, "radius_miles": 200}},
    "nmea": {"type": "nmea", "sentence": "GPRMC,063909,A,3349.4302,N,11700.3721,W,43.022,89.3,291099,13.6,E*52", "has_checksum": True,
             "latitude": 33.823836666666665, "longitude": -117.00620166666667, "fix": "valid", "course_degrees": 89.3,
             "speed_knots": 43.022, "time": "06:39:09"},
}


def tp(inner: str) -> dict:
    return {"type": "third-party", "packet": {"source": "N0CALL", "destination": "APZ001", "path": ["TCPIP*", "G4ABC*"],
                                              "data": copy.deepcopy(BASES[inner])}}


DELETE = object()
PHG = {"power": 5, "height": 1, "gain": 3, "directivity": 2}
AREA = {"shape": "filled-ellipse", "color": "cyan", "lat_offset": 10, "lon_offset": 10}

# (code, base, label, {path: value}); a path is dotted, and a value of DELETE removes the field.
POSITIONED = ("position", "object", "item")
FAULTS: list[tuple[str, str, str, dict]] = []


def fault(code: str, bases, label: str, patch: dict) -> None:
    for b in ([bases] if isinstance(bases, str) else bases):
        FAULTS.append((code, b, label, patch))


# Positioned reports, uncompressed.
fault("invalid-timestamp", ("position", "object"), "a day of 32", {"timestamp": "322345z"})
fault("value-out-of-range", POSITIONED + ("weather-position",), "a latitude past 90", {"latitude": 91.0})
fault("value-out-of-range", POSITIONED, "an /A= altitude past 999999 feet", {"altitude_feet": 1000000})
fault("value-out-of-range", POSITIONED, "PHG power digit 10", {"phg": {"power": 10, "height": 1, "gain": 3, "directivity": 2}})
fault("invalid-symbol", POSITIONED + ("mic-e", "compressed"), "symbol table x", {"symbol": "x-"})
fault("invalid-character", POSITIONED + ("mic-e",), "a CR in the comment", {"comment": "a\rb"})
fault("too-long", POSITIONED, "six base-91 telemetry values",
      {"telemetry": {"sequence": 1, "analog": [1, 2, 3, 4, 5, 6]}})
fault("extension-conflict", POSITIONED, "course/speed and PHG", {"course_degrees": 88, "speed_knots": 36, "phg": PHG})
fault("field-not-allowed", POSITIONED, "a !DAO! on an ambiguous position",
      {"ambiguity": 2, "dao": {"datum": "W", "precision": "none"}})
fault("symbol-mismatch", POSITIONED, "an area without the area symbol", {"area": AREA})
fault("malformed", POSITIONED, "base-91 telemetry with no analog values", {"telemetry": {"sequence": 1, "analog": []}})
fault("text-reads-as-field", POSITIONED + ("mic-e",), "comment text that reads as an altitude", {"comment": "/A=001234"})
fault("invalid-code", POSITIONED, "a !DAO! datum of !", {"dao": {"datum": "!", "precision": "none"}})
# Objects and items.
fault("invalid-name", "object", "a name of 10 characters", {"name": "0123456789"})
fault("invalid-name", "item", "a name of 2 characters", {"name": "AB"})
fault("padding-space", "object", "a name ending in a space", {"name": "OR4F "})
fault("missing-field", "object", "no timestamp", {"timestamp": DELETE})
# Compressed positions.
fault("value-out-of-range", "compressed", "a range under the first cs step",
      {"range_miles": 1, "compression": {"fix": "current", "source": "other", "origin": "software"}})
fault("value-has-no-form", "compressed", "a course of 0",
      {"course_degrees": 0, "speed_knots": 0, "compression": {"fix": "current", "source": "other", "origin": "software"}})
fault("field-not-allowed", "compressed", "PHG on a compressed position", {"phg": PHG})
fault("field-not-allowed", "compressed", "ambiguity on a compressed position", {"ambiguity": 2})
fault("missing-field", "compressed", "a course with no speed",
      {"course_degrees": 88, "compression": {"fix": "current", "source": "rmc", "origin": "software"}})
fault("text-reads-as-field", "compressed", "comment text that reads as an altitude", {"comment": "/A=001234"})
fault("invalid-character", "compressed", "a CR in the comment", {"comment": "a\rb"})
fault("invalid-timestamp", "compressed", "a day of 32", {"timestamp": "322345z"})
fault("too-long", "compressed", "six base-91 telemetry values", {"telemetry": {"sequence": 1, "analog": [1, 2, 3, 4, 5, 6]}})
fault("malformed", "compressed", "base-91 telemetry with no analog values", {"telemetry": {"sequence": 1, "analog": []}})
fault("invalid-code", "compressed", "a !DAO! datum of !", {"dao": {"datum": "!", "precision": "none"}})
# Mic-E.
fault("value-has-no-form", "mic-e", "a course of 0", {"course_degrees": 0})
fault("value-out-of-range", "mic-e", "a speed of 800 knots", {"speed_knots": 800})
fault("invalid-code", "mic-e", "a message of unknown", {"mic_e_message": "unknown"})
fault("invalid-code", "mic-e", "a type code of x", {"type_code": "x"})
fault("malformed", "mic-e", "four legacy telemetry values", {"legacy_telemetry": [65, 66, 67, 68]})
fault("field-not-allowed", "mic-e", "weather in Mic-E", {"weather": dict(WIND)})
# Weather with a position.
fault("value-out-of-range", ("weather-position", "weather", "weather-compressed"), "a gust of 1000 mph", {"weather.wind_gust_mph": 1000})
fault("value-has-no-form", ("weather-position", "weather", "weather-compressed"), "a humidity of 0", {"weather.humidity_percent": 0})
fault("invalid-timestamp", "weather-position", "a day of 32", {"timestamp": "322345z"})
fault("invalid-symbol", "weather-position", "symbol table x", {"symbol": "x_"})
fault("extension-conflict", "weather-position", "wind and PHG", {"phg": PHG})
fault("symbol-mismatch", "weather-position", "weather on a symbol that is not the weather station", {"symbol": "/-"})
fault("field-not-allowed", ("weather-position", "weather", "weather-compressed"), "a comment", {"comment": "hello"})
fault("extension-conflict", "weather-compressed", "wind and a range in the cs bytes", {"range_miles": 2})
fault("field-not-allowed", "weather-compressed", "PHG on a compressed report", {"phg": PHG})
fault("missing-field", "weather-compressed", "a wind speed with no direction", {"weather.wind_direction_degrees": DELETE})
# An object weather report.
fault("value-has-no-form", "weather-object", "a humidity of 0", {"weather.humidity_percent": 0})
fault("value-out-of-range", "weather-object", "a gust of 1000 mph", {"weather.wind_gust_mph": 1000})
fault("invalid-name", "weather-object", "a name of 10 characters", {"name": "0123456789"})
fault("padding-space", "weather-object", "a name ending in a space", {"name": "OR4F "})
fault("invalid-timestamp", "weather-object", "a day of 32", {"timestamp": "322345z"})
fault("missing-field", "weather-object", "no timestamp", {"timestamp": DELETE})
fault("extension-conflict", "weather-object", "wind and PHG", {"phg": PHG})
fault("field-not-allowed", "weather-object", "a comment", {"comment": "hello"})
fault("invalid-symbol", "weather-object", "symbol table x", {"symbol": "x_"})
# Positionless weather.
fault("invalid-timestamp", "weather", "a month of 13", {"timestamp": "13090556"})
# Messages.
fault("invalid-addressee", ("message", "telemetry-bits"), "an addressee of 11 characters", {"addressee": "TOOLONGCALL"})
fault("invalid-character", "message", "a { in the text", {"text": "a{b"})
fault("too-long", "message", "68 characters of text", {"text": "x" * 68})
fault("invalid-message-id", "message", "a message ID of 6 characters", {"message_id": "123456"})
fault("text-reads-as-field", "message", "text that reads as a directed query", {"text": "?WX"})
fault("missing-field", "message", "a reply-ack with no message ID", {"reply_ack": "AB"})
fault("invalid-addressee", ("ack", "bulletin", "directed-query", "telemetry-names"), "an addressee of 11 characters", {"addressee": "TOOLONGCALL"})
fault("invalid-message-id", "ack", "an acked ID of 6 characters", {"acked_id": "123456"})
fault("field-not-allowed", "ack", "a message ID on an ack", {"message_id": "2"})
fault("invalid-message-id", "bulletin", "a message ID of 6 characters", {"message_id": "123456"})
fault("invalid-character", "bulletin", "a { in the text", {"text": "a{b"})
fault("too-long", "bulletin", "68 characters of text", {"text": "x" * 68})
fault("invalid-code", "directed-query", "a query type in lower case", {"query_type": "aprsd"})
fault("invalid-character", "telemetry-names", "a { in a name", {"names": ["V{in", "Temp"]})
fault("too-long", "telemetry-names", "14 names", {"names": [f"C{i}" for i in range(1, 15)]})
# Telemetry.
fault("malformed", "telemetry", "four analog values", {"analog": [1, 2, 3, 4]})
fault("too-long", "telemetry", "six analog values", {"analog": [1, 2, 3, 4, 5, 6]})
fault("value-has-no-form", "telemetry", "T#MIC with an empty first channel", {"sequence": "MIC", "analog": [None, 33, 1, 2, 3]})
fault("missing-field", "telemetry", "no bits", {"bits": DELETE})
fault("invalid-character", "telemetry", "a CR in the comment", {"comment": "a\rb"})
fault("malformed", "telemetry-bits", "bits of 7 characters", {"bits": "1111111"})
fault("invalid-message-id", "telemetry-bits", "a message ID of 6 characters", {"message_id": "123456"})
fault("too-long", "telemetry-bits", "a project title of 24 characters", {"project": "abcdefghijklmnopqrstuvwx"})
fault("invalid-character", "telemetry-bits", "a { in the project title", {"project": "a{b"})
# Status.
fault("invalid-timestamp", ("status",), "a timestamp in hours, minutes, seconds", {"timestamp": "010203h"})
fault("invalid-character", ("status", "locator-status"), "a CR in the text", {"text": "a\rb"})
fault("malformed", "locator-status", "a locator of 5 characters", {"locator": "IO91S"})
fault("invalid-code", "locator-status", "a beam heading code of a", {"beam": {"heading_code": "a", "power_code": "7"}})
fault("field-not-allowed", "locator-status", "a locator with a timestamp", {"timestamp": "092345z"})
fault("invalid-symbol", "locator-status", "symbol table x", {"symbol": "x-"})
# Capabilities.
fault("malformed", "capabilities", "a token with a space", {"capabilities": [["IG ATE"], ["MSG_CNT", "43"]]})
fault("padding-space", "capabilities", "a value starting with a space", {"capabilities": [["IGATE"], ["MSG_CNT", " 43"]]})
fault("invalid-character", "capabilities", "a control character in a value", {"capabilities": [["IGATE"], ["MSG_CNT", "4\x1c3"]]})
# General query.
fault("value-out-of-range", "query", "a footprint latitude of 100", {"footprint.latitude": 100.02})
fault("invalid-code", "query", "a query type in lower case", {"query_type": "aprs"})
# NMEA.
fault("invalid-nmea", "nmea", "a checksum that does not match", {"sentence": "GPRMC,063909,A,3349.4302,N,11700.3721,W,43.022,89.3,291099,13.6,E*53"})
fault("invalid-nmea", "nmea", "a course that disagrees with the sentence", {"course_degrees": 90})
fault("invalid-character", "nmea", "a CR in the comment", {"comment": "a\rb"})
# Third-party: every report above, inside one, keeps its faults, and gains one in the inner header.
# Not Mic-E: an inner Mic-E report's position is half in its destination, which the third-party
# header gives as APZ001, so the record would contradict itself.
for _name in [n for n in BASES if n != "mic-e"]:
    BASES["third-party-" + _name] = tp(_name)
for _code, _base, _label, _patch in [f for f in FAULTS if f[1] != "mic-e"]:
    fault(_code, "third-party-" + _base, _label + " in the inner packet", {"packet.data." + k: v for k, v in _patch.items()})
fault("invalid-third-party-header", [b for b in BASES if b.startswith("third-party-")],
      "an inner path entry, before a used one, not marked used", {"packet.path": ["TCPIP", "G4ABC*"]})


def touched(patch: dict) -> set[str]:
    return set(patch)


def disjoint(a: dict, b: dict) -> bool:
    """No path of one is the other's or inside it."""
    for x in a:
        for y in b:
            if x == y or x.startswith(y + ".") or y.startswith(x + "."):
                return False
    return True


def apply(data: dict, patch: dict) -> dict:
    d = copy.deepcopy(data)
    for path, value in patch.items():
        keys = path.split(".")
        node = d
        for k in keys[:-1]:
            node = node[k]
        if value is DELETE:
            node.pop(keys[-1], None)
        else:
            node[keys[-1]] = copy.deepcopy(value)
    return d


def pairs():
    """For every pair of codes, the first base (in BASES order) holding both on different fields."""
    base_order = list(BASES)
    made, impossible = [], []
    codes = [c for c in ORDER if c not in NO_CASE]
    for a, b in itertools.combinations(codes, 2):
        found = None
        for base in base_order:
            for fa in (f for f in FAULTS if f[0] == a and f[1] == base):
                for fb in (f for f in FAULTS if f[0] == b and f[1] == base):
                    if disjoint(fa[3], fb[3]):
                        found = (base, fa, fb)
                        break
                if found:
                    break
            if found:
                break
        if found:
            made.append((a, b) + found)
        else:
            impossible.append((a, b, reason(a, b)))
    return made, impossible


def bases_of(code: str) -> list[str]:
    """The report types a code is a fault of (a third-party packet holds any of them, so it is left out)."""
    return sorted({f[1] for f in FAULTS if f[0] == code and not f[1].startswith("third-party-")})


# Where each code can be a fault at all, from codes.json's meanings and the data form, read by hand
# (not from the catalogue above): a pair whose codes have no report in common cannot be held by one
# record. A third-party packet holds one inner report, so it adds no pair beyond its header's code.
WHERE = {
    "invalid-addressee": {"message", "ack", "bulletin", "nws-bulletin", "telemetry-metadata", "directed-query"},
    "invalid-message-id": {"message", "ack", "bulletin", "nws-bulletin", "telemetry-metadata"},
    "invalid-name": {"object", "item"},
    "invalid-timestamp": {"position", "object", "status", "weather"},
    "value-out-of-range": {"position", "object", "item", "mic-e", "weather", "query", "agrelo-df", "telemetry"},
    "value-has-no-form": {"position", "object", "item", "mic-e", "weather", "telemetry"},
    "invalid-code": {"position", "object", "item", "mic-e", "status", "query", "directed-query"},
    "invalid-symbol": {"position", "object", "item", "mic-e", "status"},
    "padding-space": {"object", "capabilities"},
    "too-long": {"position", "object", "item", "message", "bulletin", "telemetry-metadata", "telemetry"},
    "malformed": {"position", "object", "item", "mic-e", "status", "telemetry", "telemetry-metadata", "capabilities", "weather"},
    "invalid-nmea": {"nmea"},
    "extension-conflict": {"position", "object", "item"},
    "symbol-mismatch": {"position", "object", "item"},
    "field-not-allowed": {"position", "object", "item", "mic-e", "status", "weather", "ack"},
    "missing-field": {"position", "object", "item", "message", "telemetry", "capabilities", "weather"},
    "text-reads-as-field": {"position", "object", "item", "mic-e", "message", "status", "weather"},
}
ONE_FIELD = {
    ("invalid-name", "padding-space"): "a padding space is a fault of an object name, which holds the wrong-length fault too: one field",
    ("invalid-character", "text-reads-as-field"): "the free text that can read back as a field is a report's one comment or text field, where a character fault is too: one field",
}


def reason(a: str, b: str) -> str:
    """Why no record holds both, or that the catalogue has a gap (which --check refuses)."""
    if (a, b) in ONE_FIELD:
        return ONE_FIELD[(a, b)]
    if a in WHERE and b in WHERE and not WHERE[a] & WHERE[b]:
        return f"no report has both: {a} is a fault only of {', '.join(sorted(WHERE[a]))}; {b} only of {', '.join(sorted(WHERE[b]))}"
    return "GAP: the catalogue has no record holding both, though one may exist"


def case_for(a: str, b: str, base: str, fa, fb) -> dict:
    data = apply(apply(BASES[base], fa[3]), fb[3])
    return {
        "id": f"precedence/{a}-and-{b}",
        "description": f"Two faults, {fa[2]} ({a}) and {fb[2]} ({b}): the refusal names {a}, which the Refusal reasons order puts first.",
        "source": "README Refusal reasons (tools/precedence.py)",
        "authority": "interpretation",
        "interpretations": ["which-refusal-a-record-with-two-faults-gets"],
        "input": {"encode": data},
        "expect": {"refused": True, "refusal": a},
    }


# ------------------------------------------------------------------ strict decoding: which defect is met first
#
# Diagnostics compare as a multiset, so their order never matters to a lenient decoder; it matters
# to a strict one, which rejects a packet by the first defect it meets (README, "The order of
# checks"). A packet is built from parts, and each ingredient changes one part and adds one tolerated
# defect, with the rank at which a reader meets it: the header first, then the information field in
# reading order (a trailing CR or LF is met when the information field is taken, before anything in
# it), where the elements lifted from a comment (base-91 telemetry, then a `!DAO!`) are met
# before the text left over is judged (weather-comment), and the text's encoding after its structure.

TEMPLATES = {
    "position": {
        "parts": {"destination": "APZ001", "path": "", "timestamp": "092345z", "latitude": "4903.50N", "longitude": "07201.75W",
                  "symbol": ">", "extension": "", "wind_fields": "", "gust": "", "temperature": "", "comment": "Test", "dao": "", "tail": ""},
        "data": {"type": "position", "timestamp": "092345z", "latitude": LAT, "longitude": LON, "symbol": "/>", "comment": "Test"},
    },
    "weather": {
        "parts": {"destination": "APZ001", "path": "", "timestamp": "092345z", "latitude": "4903.50N", "longitude": "07201.75W",
                  "symbol": "_", "extension": "220/004", "wind_fields": "", "gust": "g005", "temperature": "t077", "comment": "", "dao": "",
                  "tail": ""},
        "data": {"type": "position", "timestamp": "092345z", "latitude": LAT, "longitude": LON, "symbol": "/_",
                 "weather": {"wind_direction_degrees": 220, "wind_speed_mph": 4, "wind_gust_mph": 5, "temperature_f": 77}},
    },
}

# (name, code, rank, templates, {part: value}, {data path: value}); a rank is when a reader meets it.
INGREDIENTS = [
    ("empty-destination", "empty-destination", 0, ("position", "weather"), {"destination": ""}, {}),
    ("two-used-markers", "multiple-used-markers", 1, ("position", "weather"), {"path": "WIDE1-1*,WIDE2-1*"}, {}),
    ("day-32", "invalid-timestamp", 2, ("position", "weather"), {"timestamp": "322345z"}, {"timestamp": "322345z"}),
    ("lower-case-n", "lowercase-hemisphere", 3, ("position", "weather"), {"latitude": "4903.50n"}, {}),
    ("lower-case-w", "lowercase-hemisphere", 4, ("position", "weather"), {"longitude": "07201.75w"}, {}),
    ("course-400", "out-of-range-value", 5, ("position",), {"extension": "400/010"}, {"speed_knots": 10}),
    ("wind-from-400", "out-of-range-value", 5, ("weather",), {"extension": "400/004"}, {"weather.wind_direction_degrees": DELETE}),
    ("wind-as-fields", "wind-fields-instead-of-extension", 5, ("weather",), {"extension": "", "wind_fields": "c220s004"}, {}),
    ("gust-in-two-digits", "non-standard-weather-field-width", 6, ("weather",), {"gust": "g05"}, {}),
    ("no-temperature", "incomplete-weather", 7, ("weather",), {"temperature": ""}, {"weather.temperature_f": DELETE}),
    ("dao-on-ambiguity", "dao-with-ambiguity", 8, ("position", "weather"), {"latitude": "4903.5 N", "longitude": "07201.7 W", "dao": "!W12!"},
     {"latitude": 49.05916666666667, "ambiguity": 1, "dao": {"datum": "W", "precision": "thousandths"}}),
    ("text-after-weather", "weather-comment", 9, ("weather",), {"comment": " hello"}, {"comment": "hello"}),
    ("latin-1-comment", "non-utf8-text", 10, ("position",), {"comment": "T\xe9st"}, {"comment": "T\xe9st"}),
    ("trailing-cr", "trailing-line-break", 1.5, ("position", "weather"), {"tail": "\r"}, {}),
]
HEADER_CODES = {"empty-destination", "multiple-used-markers"}


def build_packet(parts: dict) -> str:
    header = "N0CALL>" + parts["destination"] + ("," + parts["path"] if parts["path"] else "")
    info = "".join(parts[k] for k in ("timestamp", "latitude")) + "/" + "".join(
        parts[k] for k in ("longitude", "symbol", "extension", "wind_fields", "gust", "temperature", "comment", "dao", "tail"))
    return header + ":/" + info


def tnc2_input(line: str) -> dict:
    """A line of bytes 0-255 as a case input: text when it is ASCII, else hex (a tnc2 string is UTF-8)."""
    if line.isascii():
        return {"tnc2": line}
    return {"tnc2_hex": line.encode("latin-1").hex().upper()}


def merge_parts(parts: dict, change: dict) -> dict | None:
    """The parts with one ingredient's change; None when it changes a part another already changed."""
    changed = parts.get("_changed", ())
    if any(k in changed for k in change):
        return None
    return dict(parts, **change, _changed=changed + tuple(change))


def decode_cases() -> list[dict]:
    cases = []
    for tname, template in TEMPLATES.items():
        usable = [i for i in INGREDIENTS if tname in i[3]]
        for a, b in itertools.combinations(usable, 2):
            if a[1] == b[1]:
                continue
            parts = merge_parts(template["parts"], a[4])
            parts = parts and merge_parts(parts, b[4])
            if parts is None:
                continue
            data = apply(apply(template["data"], a[5]), b[5])
            first, second = sorted((a, b), key=lambda i: i[2])
            strict = {"rejected_by": first[1]}
            if first[1] in HEADER_CODES:
                strict["header"] = True
            cases.append({
                "id": f"strict-order/{tname}-{first[0]}-then-{second[0]}",
                "description": (f"Two tolerated defects, {first[1]} and then {second[1]}: a lenient decoder reports both, "
                                f"and a strict one rejects the packet by {first[1]}, which it meets first."),
                "source": "README The order of checks (tools/precedence.py)",
                "authority": "interpretation",
                "interpretations": ["a-packet-is-read-in-order"],
                "input": tnc2_input(build_packet(parts)),
                "expect": {"data": data, "diagnostics": sorted(["warning:" + a[1], "warning:" + b[1]])},
                "strict": strict,
            })
    return cases


def build() -> tuple[dict, list]:
    made, impossible = pairs()
    cases = [case_for(*m) for m in made] + decode_cases()
    return {"cases": cases}, impossible


def dump(document: dict) -> str:
    """The case files' layout: a case's keys one to a line, and its expect's keys one to a line."""
    j = lambda v: json.dumps(v, ensure_ascii=False)
    blocks = []
    for c in document["cases"]:
        lines = []
        for k, v in c.items():
            if k == "expect":
                lines.append(f'      "{k}": {{\n' + ",\n".join(f'        "{k2}": {j(v2)}' for k2, v2 in v.items()) + "\n      }")
            else:
                lines.append(f'      "{k}": {j(v)}')
        blocks.append("    {\n" + ",\n".join(lines) + "\n    }")
    return '{\n  "cases": [\n' + ",\n".join(blocks) + "\n  ]\n}\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if cases/precedence.json is out of date")
    ap.add_argument("--singles", metavar="FILE", help="write each single fault as a data object per line, and stop")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if args.singles:
        with open(args.singles, "w", encoding="utf-8") as f:
            for code, base, label, patch in FAULTS:
                f.write(json.dumps({"code": code, "base": base, "label": label, "data": apply(BASES[base], patch)}, ensure_ascii=False) + "\n")
            for name, data in BASES.items():
                f.write(json.dumps({"code": None, "base": name, "label": "clean", "data": data}, ensure_ascii=False) + "\n")
        return 0

    document, impossible = build()
    text = dump(document)
    codes = [c for c in ORDER if c not in NO_CASE]
    excluded = (f"# Pairs of refusal codes with no case in cases/precedence.json, and why (written by tools/precedence.py).\n"
                f"# {len(document['cases']) - len(decode_cases())} pair cases for {len(codes) * (len(codes) - 1) // 2} pairs of the "
                f"{len(codes)} codes an encode case can carry; {len(impossible)} pairs no record can hold:\n"
                + "".join(f"{a} + {b}: {why}\n" for a, b, why in impossible)
                + "# Codes no encode case can carry:\n"
                + "".join(f"{code}: {why}\n" for code, why in NO_CASE.items()))
    gaps = [p for p in impossible if p[2].startswith("GAP")]
    if args.check:
        for path, want in ((OUT, text), (EXCLUDED, excluded)):
            with open(path, encoding="utf-8") as f:
                if f.read() != want:
                    print(f"{os.path.relpath(path, os.path.join(HERE, '..'))} is out of date: run python3 tools/precedence.py", file=sys.stderr)
                    return 1
        if gaps:
            print(f"the fault catalogue has {len(gaps)} gaps: " + ", ".join(f"{a} + {b}" for a, b, _ in gaps), file=sys.stderr)
            return 1
        return 0
    for path, want in ((OUT, text), (EXCLUDED, excluded)):
        with open(path, "w", encoding="utf-8") as f:
            f.write(want)
    if not args.quiet:
        print(excluded, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
