#!/usr/bin/env python3
"""Makes data and builder recipes whose text, written naively, reads back as something else.

  python3 tools/readback_shapes.py data.jsonl.gz [--count 100000] [--seed 1]
  python3 tools/readback_shapes.py recipes.jsonl.gz --recipes [--count 100000] [--seed 1]

For the encode and build modes of the dump tools (README, "Comparing implementations"): every
encoder must read back what it wrote (README, Read-back), and these records are the shapes where
that read-back decides the result. The output starts with a fixed catalogue, the same for every
seed:

- element-shaped text (a timestamp, a locator, a `!DAO!`, base-91 telemetry, a `/A=`, PHG, RNG,
  DFS, a course/speed, a frequency and its fields, braces, weather fields, message, ack, query and
  telemetry metadata forms, a data type identifier, delimiters) and the same text with its first or
  last character cut off (partial element text), alone, at the start and at the end of every text
  field of every report type: comments, status, message, bulletin and NWS text, telemetry names,
  units and project titles, a query's target, capability tokens and values, a weather report's
  software type and unit, raw weather, test and user-defined data, NMEA comments, object and item
  names, a third-party packet's inner text;
- that text in a positioned comment beside each element a positioned report can carry (altitude,
  course/speed, PHG, RNG, DFS, frequency, telemetry, `!DAO!`, area, signpost, compression);
- every user-defined user ID and packet type (printable ASCII), every Agrelo bearing and quality,
  and bearings either side of a half;
- ack and reject IDs, message IDs and reply-acks, bulletin groups and addressees of element text,
  a third-party inner source and destination, and recipe sources and destinations;
- Mic-E altitudes held by both forms, by a `/A=` only, and by neither, beside comments holding a
  `/A=`, telemetry, a `!DAO!` and a locator, with and without a type code; telemetry coefficients
  and general-query footprints of awkward numbers;
- non-integers in fields held only in whole units or as codes (PHG and DFS digits, comment telemetry,
  area offsets, a DF bearing, storm fields), values between steps ("exact": false), and faults
  planted in third-party inner data one and two levels deep;
- separators (`,` `>` `:` `*`, a space, a NUL) in a third-party inner source, destination and path
  entry one and two levels deep and in a recipe's station, and extreme finite integers (32- and
  64-bit limits, 2^53) in every integer field;
- weather extra fields of every printable letter with values that read as other fields, as too
  short a run, or as a software type and unit;
- with --recipes, header paths of every shape a station may give, entries used before, after and
  out of order with unused ones (an entry not marked used before one that is), and the element text
  in every text argument of every builder report.

Then --count random records (default 0) from --seed: element texts joined two or three at a time.
Every data record has "exact": true (every value is one its format holds) except the Agrelo bearings
between whole degrees, which are rounded; a record whose bytes
read back changed, or whose built line's header does, is one compare.py reports on its own. Standard
library only.
"""

import argparse
import gzip
import json
import random

# Text shaped like an element, or like a form a decoder recognises at the start or end of a field.
ELEMENTS = [
    # message forms
    "ack1", "ackAB", "rej12", "ack1}AB", "rejAB}12", "{1", "{12345", "{AB}CD", "{1}", "}AB", "x{1", "a{12}34", "{", "}",
    "PARM.A,B", "UNIT.V,A", "EQNS.0,1,0", "BITS.11111111,proj", "PARM.", "BITS.",
    "?APRSP", "?APRS?", "?PING?", "?WX?", "?IGATE?", "?APRSD", "?APRSS ", "?", ":N0CALL   :hi", ":BLN1     :x", "N0CALL   :x",
    # timestamps
    "092345z", "092345/", "123456h", "10092345", "311259z",
    # locators
    "IO91", "IO91SX", "IO91sx", "IO91SX/G", "IO91SX/G>", "AA00",
    # Mic-E
    "!!!}", "\"3r}", "aaa}", "`", "'", "_\"", "_)", "_ ", "^", "=", ">", "]", "]=", "_#", "|3", "\"",
    # beam heading
    "^B7", "^A1", "^B0",
    # DAO, telemetry
    "!W12!", "!w\"#!", "!S  !", "|!!!!|", "|##$$%%|", "|!!|", "||",
    # weather
    "c000s000g000t077", "r001p002P003h50b10132", "h50", "h5", "b10132", "L123", "l123", "#123", "s012", "s.50", "_090/005",
    "090/005g010t072", "t077", "g005", "c090", "p000", "P000", "r000", "eRSW", "wRSW", "xDvs", "X01", "XO1", "dU2k",
    # data extensions and comment elements
    "PHG5132", "PHG5132/", "PHG51324/", "RNG0050", "DFS2360", "BRG123/NRQ456", "123/456/789/123", "123/045", "/123/045",
    ".../...", "000/000", "/A=000100", "/A=-00010", "/A=999999", "146.520MHz", " 146.520MHz", "T100", " T100", "+060",
    " +060", "C100", " C100", "D023", " D023", "Toff", " R25m", "1290MHz", "146.520MHz T100 +060", "{55}", "{5}", "{AB}",
    # other reports
    "T#001,1,2,3,4,5,00000000", "T#MIC", "T#", "$GPGGA,", "$GPRMC,1,2", "!4903.50N/07201.75W-", "@", ";", ")", "<IGATE",
    "}N0CALL>APRS:test", "_10092345", "*", "#", "%", "%123/4", "[IO91SX]", "/5L!!<*e7>7P[",
    # bars: telemetry is the last pair of bars around a valid block (R27)
    "|144.190|", "| a |", "||", "|!a!'!#|", "|!!!!| a |b c|", "|!!!!|x|!\"!#|", "|x y|!!!!|",
    # delimiters
    "\\", "/", "//", " ", "  ", "x ", " x", "/x", "x/", " /", "/ ",
]


def partials(texts):
    """Each text with its first or its last character cut off (the text beside an element)."""
    out = []
    for t in texts:
        for p in (t[1:], t[:-1]):
            if p.strip() and p not in texts and p not in out:
                out.append(p)
    return out


TEXTS = ELEMENTS + partials(ELEMENTS)


def placed(t):
    """The text alone, at the start of a field and at the end of one."""
    return [t, t + "x", "x" + t]


POSITION = {"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "/>"}
TELEMETRY = {"sequence": 1, "analog": [1, 2]}
BESIDE = {
    "none": {},
    "altitude": {"altitude_feet": 100},
    "course-speed": {"course_degrees": 88, "speed_knots": 36},
    "phg": {"phg": {"power": 5, "height": 1, "gain": 3, "directivity": 2}},
    "rng": {"range_miles": 50},
    "dfs": {"dfs": {"strength": 2, "height": 3, "gain": 6, "directivity": 0}},
    "frequency": {"frequency": {"mhz": 146.52}},
    "frequency-fields": {"frequency": {"mhz": 146.52, "tone": "tone", "tone_value": 100, "offset_khz": 600}},
    "telemetry": {"telemetry": TELEMETRY},
    "dao": {"dao": {"datum": "W", "precision": "base91"}},
    "dao-thousandths": {"dao": {"datum": "W", "precision": "thousandths"}},
    "area": {"symbol": "\\l", "area": {"shape": "filled-ellipse", "color": "cyan", "lat_offset": 10, "lon_offset": 10}},
    "signpost": {"symbol": "\\m", "signpost": "55"},
    "altitude-telemetry": {"altitude_feet": 100, "telemetry": TELEMETRY},
    "telemetry-dao": {"telemetry": TELEMETRY, "dao": {"datum": "W", "precision": "base91"}},
    "compressed": {"compressed": True, "compression": {"fix": "current", "source": "rmc", "origin": "software"}},
    "compressed-altitude": {"compressed": True, "compression": {"fix": "current", "source": "rmc", "origin": "software"},
                            "altitude_feet": 1000},
}
STORM = {"type": "hurricane", "sustained_wind_knots": 150, "gust_knots": 200, "central_pressure_mbar": 980,
         "hurricane_radius_nm": 90, "tropical_storm_radius_nm": 30}


def text_slots():
    """(name, function of a text giving data) for every text field of every report type."""
    def pos(**k):
        d = dict(POSITION)
        d.update(k)
        return d

    def wx(w, **k):
        d = {"type": "weather", "timestamp": "10092345", "weather": w}
        d.update(k)
        return d

    def tp(data, path=("TCPIP*",)):
        return {"type": "third-party", "packet": {"source": "N0CALL", "destination": "APRS", "path": list(path), "data": data}}

    slots = []
    for name, extra in BESIDE.items():
        slots.append((f"position comment beside {name}", lambda t, e=extra: pos(**e, comment=t)))
    slots += [
        ("position with a timestamp", lambda t: pos(timestamp="092345z", comment=t)),
        ("object comment", lambda t: pos(type="object", name="OBJ", timestamp="092345z", comment=t)),
        ("item comment", lambda t: pos(type="item", name="ITEM", comment=t)),
        ("object name", lambda t: pos(type="object", name=t[:9], timestamp="092345z")),
        ("item name", lambda t: pos(type="item", name=t[:9])),
        ("storm comment", lambda t: pos(symbol="/@", storm=STORM, comment=t)),
        ("df comment", lambda t: pos(symbol="/\\", course_degrees=88, speed_knots=36,
                                     df_bearing={"bearing_degrees": 270, "number": 7, "range": 2, "quality": 9}, comment=t)),
        ("mic-e comment", lambda t: {"type": "mic-e", "mic_e_message": "en-route", "type_code": "`", "latitude": 51.5,
                                     "longitude": -0.5, "symbol": "/>", "speed_knots": 10, "comment": t}),
        ("mic-e comment without a type code", lambda t: {"type": "mic-e", "mic_e_message": "en-route", "latitude": 51.5,
                                                         "longitude": -0.5, "symbol": "/>", "speed_knots": 10, "comment": t}),
        ("message text", lambda t: {"type": "message", "addressee": "N0CALL", "text": t}),
        ("message text with an id", lambda t: {"type": "message", "addressee": "N0CALL", "text": t, "message_id": "12"}),
        ("bulletin text", lambda t: {"type": "bulletin", "addressee": "BLN1", "text": t}),
        ("nws text", lambda t: {"type": "nws-bulletin", "addressee": "NWS-WARN", "text": t}),
        ("telemetry name first", lambda t: {"type": "telemetry-names", "addressee": "N0CALL", "names": [t, "B"]}),
        ("telemetry name last", lambda t: {"type": "telemetry-names", "addressee": "N0CALL", "names": ["A", t]}),
        ("telemetry unit", lambda t: {"type": "telemetry-units", "addressee": "N0CALL", "units": ["V", t]}),
        ("telemetry project", lambda t: {"type": "telemetry-bits", "addressee": "N0CALL", "bits": "11111111", "project": t}),
        ("query target", lambda t: {"type": "directed-query", "addressee": "N0CALL", "query_type": "APRSP", "target": t}),
        ("status text", lambda t: {"type": "status", "text": t}),
        ("status text after a timestamp", lambda t: {"type": "status", "timestamp": "092345z", "text": t}),
        ("status text after a locator", lambda t: {"type": "status", "locator": "IO91SX", "symbol": "/G", "text": t}),
        ("status text after a short locator", lambda t: {"type": "status", "locator": "IO91", "symbol": "/G", "text": t}),
        ("status text before a beam", lambda t: {"type": "status", "locator": "IO91SX", "symbol": "/G",
                                                 "beam": {"heading_code": "3", "power_code": "7"}, "text": t}),
        ("telemetry comment", lambda t: {"type": "telemetry", "sequence": "001", "analog": [1, 2, 3, 4, 5], "bits": "00000000", "comment": t}),
        ("telemetry comment after MIC", lambda t: {"type": "telemetry", "sequence": "MIC", "analog": [1, 2, 3, 4, 5], "bits": "00000000", "comment": t}),
        ("positionless weather software and unit", lambda t: wx({"temperature_f": 70, "software": t[:1], "unit": t[1:5]})),
        ("weather position software and unit", lambda t: pos(symbol="/_", weather={"temperature_f": 70, "software": t[:1], "unit": t[1:5]})),
        ("weather object software and unit", lambda t: pos(type="object", name="WX", timestamp="092345z", symbol="/_",
                                                          weather={"humidity_percent": 50, "software": t[:1], "unit": t[1:5]})),
        ("maidenhead comment", lambda t: {"type": "maidenhead-beacon", "locator": "IO91SX", "comment": t}),
        ("short maidenhead comment", lambda t: {"type": "maidenhead-beacon", "locator": "IO91", "comment": t}),
        ("nmea comment", lambda t: {"type": "nmea", "sentence": "GPGLL,4916.45,N,12311.12,W,225444,A*31", "has_checksum": True, "comment": t}),
        ("capability value", lambda t: {"type": "capabilities", "capabilities": [["IGATE", t]]}),
        ("capability token", lambda t: {"type": "capabilities", "capabilities": [[t]]}),
        ("second capability token", lambda t: {"type": "capabilities", "capabilities": [["A", "1"], [t, "x"]]}),
        ("third-party status text", lambda t: tp({"type": "status", "text": t})),
        ("third-party message text", lambda t: tp({"type": "message", "addressee": "N0CALL", "text": t}, ())),
        ("third-party comment", lambda t: tp(pos(comment=t))),
        ("user-defined data", lambda t: {"type": "user-defined", "user_id": "A", "packet_type": "x", "data": t}),
        ("ack id", lambda t: {"type": "ack", "addressee": "N0CALL", "acked_id": t[:5]}),
        ("reject id", lambda t: {"type": "reject", "addressee": "N0CALL", "rejected_id": t[:5]}),
        ("message id", lambda t: {"type": "message", "addressee": "N0CALL", "text": "hi", "message_id": t[:5]}),
        ("reply-ack", lambda t: {"type": "message", "addressee": "N0CALL", "text": "hi", "message_id": "1", "reply_ack": t[:5]}),
        ("bulletin group", lambda t: {"type": "bulletin", "addressee": ("BLN1" + t)[:9], "text": "hi"}),
        ("addressee", lambda t: {"type": "message", "addressee": t[:9], "text": "hi"}),
        ("third-party inner source", lambda t: {"type": "third-party", "packet": {"source": t[:9], "destination": "APRS", "data": {"type": "status", "text": "hi"}}}),
        ("third-party inner destination", lambda t: {"type": "third-party", "packet": {"source": "N0CALL", "destination": t[:9], "data": {"type": "status", "text": "hi"}}}),
        ("mic-e comment beside an altitude", lambda t: {"type": "mic-e", "mic_e_message": "en-route", "type_code": "`", "latitude": 51.5,
                                                        "longitude": -0.5, "symbol": "/>", "speed_knots": 0, "altitude_feet": 0, "comment": t}),
        ("mic-e comment beside telemetry and a dao", lambda t: {"type": "mic-e", "mic_e_message": "en-route", "type_code": "`", "latitude": 51.5,
                                                                "longitude": -0.5, "symbol": "/>", "speed_knots": 0, "telemetry": TELEMETRY,
                                                                "dao": {"datum": "W", "precision": "base91"}, "comment": t}),
        ("mic-e comment after a locator", lambda t: {"type": "mic-e", "mic_e_message": "en-route", "type_code": "`", "latitude": 51.5,
                                                     "longitude": -0.5, "symbol": "/>", "speed_knots": 0, "locator": "IO91SX", "comment": t}),
        ("test data", lambda t: {"type": "test", "data": t}),
    ]
    for fmt in ("ultimeter-packet", "ultimeter-logging", "peet-bros-hash", "peet-bros-star"):
        slots.append((f"raw weather {fmt}", lambda t, f=fmt: {"type": "raw-weather", "format": f, "data": t}))
    return slots


# Weather extra fields: values that read as a field, a run too short or not ending in a digit, a software type and unit.
EXTRA_VALUES = ["123", "50", "A00", "077", "1", "12.", "012", "01", "-1", "..1", "Dvs", "RSW", "0092345", "10132"]


def weather_extras():
    for code in range(0x20, 0x7F):
        for value in EXTRA_VALUES:
            extra = [{"letter": chr(code), "value": value}]
            yield {"type": "weather", "timestamp": "10092345", "weather": {"pressure_mbar": 1013.2, "extra": extra}}
            yield dict(POSITION, symbol="/_", weather={"pressure_mbar": 1013.2, "extra": extra})


def user_defined():
    for u in range(0x20, 0x7F):
        for p in range(0x20, 0x7F):
            yield {"type": "user-defined", "user_id": chr(u), "packet_type": chr(p), "data": "{1"}


def agrelo():
    for b in range(0, 361):
        for q in range(10):
            yield {"type": "agrelo-df", "bearing_degrees": b, "quality": q}
    for b in (0.4, 0.5, 12.49, 12.5, 359.49, 359.5, 360.4, 360.5, -0.4, -0.5):
        yield {"type": "agrelo-df", "bearing_degrees": b, "quality": 5}


# Path entries a station may give, used (`*`) or not: every order of used and unused, out of order included.
PATH_ENTRIES = ["WIDE1-1", "N0CALL-1", "WIDE2-1", "TCPIP", "qAR", "N0CALL-15", "A", "ABCDEFGHI", "N0CALL-0", "RELAY"]


def paths():
    out = [[]]
    for n in (1, 2, 3):
        for start in range(len(PATH_ENTRIES)):
            calls = [PATH_ENTRIES[(start + i) % len(PATH_ENTRIES)] for i in range(n)]
            for marks in range(1 << n):
                out.append([c + ("*" if marks >> i & 1 else "") for i, c in enumerate(calls)])
    return out


# Values: Mic-E altitudes (both forms, only a /A=, neither), telemetry coefficients and footprints.
MIC_E_ALTITUDES = [0, 1000, 1250, 100.5, -50000, 231932 / 0.3048, 1e6]
COEFFICIENTS = [[0, 1e-7, -2.5], [1e20, -0.0, 0.5], [12345678901, 1, 0], [1e-300, 1e300, 3]]
FOOTPRINTS = [(1e-7, -117.15, 200), (0, 0, 5), (-0.0, 0.5, 9999), (90, 180, 0), (-90, -180, 1), (34.02, -117.15, 200.5), (51.123456789, -0.987654321, 25)]
# Fields held only in whole units or as codes, given a non-integer (README Read-back: value-out-of-range).
NON_INTEGERS = [
    {"phg": {"power": 4.4, "height": 1, "gain": 3, "directivity": 2}}, {"phg": {"power": 4, "height": 2.5, "gain": 3, "directivity": 2}},
    {"dfs": {"strength": 1.2, "height": 3, "gain": 6, "directivity": 0}}, {"telemetry": {"sequence": 1.4, "analog": [1, 2]}},
    {"telemetry": {"sequence": 1, "analog": [1.5, 2]}},
    {"symbol": "\\l", "area": {"shape": "filled-ellipse", "color": "cyan", "lat_offset": 10.5, "lon_offset": 10}},
    {"symbol": "/\\", "course_degrees": 88, "speed_knots": 36, "df_bearing": {"bearing_degrees": 270.5, "number": 7, "range": 2, "quality": 9}},
    {"symbol": "/@", "storm": dict(STORM, sustained_wind_knots=150.5)},
]
# Values between the steps a form holds: written rounded, so not exact.
INEXACT = [
    {"latitude": 51.123456789, "longitude": -0.987654321}, {"course_degrees": 88.5, "speed_knots": 10.25}, {"altitude_feet": 100.4},
    {"range_miles": 49.6}, {"frequency": {"mhz": 146.5205}}, {"compressed": True, "course_degrees": 101, "speed_knots": 12.3},
    {"dao": {"datum": "W", "precision": "base91"}, "latitude": 51.1234567},
]
# Faults planted in third-party inner data at depth 1 and 2: every rule check applies there too.
INNER_FAULTS = [{"course_degrees": 400, "speed_knots": 5}, {"phg": {"power": 10, "height": 1, "gain": 3, "directivity": 2}},
                {"symbol": "x"}, {"comment": "a\x07b"}, {"ambiguity": 2, "dao": {"datum": "W", "precision": "base91"}}] + NON_INTEGERS


def nested(data, depth):
    for _ in range(depth):
        data = {"type": "third-party", "packet": {"source": "N0CALL", "destination": "APRS", "data": data}}
    return data


# Separators a header must not hold where an address goes (README, Addresses and path).
SEPARATED = ["A,B", "A>B", "A:B", "A*B", "A B", "A,", ",B", "*", ">", ":", "A\x00B"]
# Extreme finite integers: type limits of the libraries' own number types.
EXTREMES = [-2147483648, 2147483647, 4294967295, -9223372036854775808, 9223372036854775807, 2 ** 53, -(2 ** 53)]


def extremes():
    for v in EXTREMES:
        yield dict(POSITION, frequency={"mhz": 146.52, "offset_khz": v})
        yield dict(POSITION, frequency={"mhz": 146.52, "tone": "ctcss", "tone_value": v})
        yield dict(POSITION, telemetry={"sequence": v, "analog": [1]})
        yield dict(POSITION, telemetry={"sequence": 1, "analog": [v]})
        yield dict(POSITION, range_miles=v)
        yield dict(POSITION, altitude_feet=v)
        yield dict(POSITION, course_degrees=v, speed_knots=v)
        yield dict(POSITION, phg={"power": v, "height": 1, "gain": 3, "directivity": 2})
        yield {"type": "agrelo-df", "bearing_degrees": v, "quality": 5}
        yield {"type": "agrelo-df", "bearing_degrees": 90, "quality": v}
        yield {"type": "telemetry", "sequence": "001", "analog": [v, 0, 0, 0, 0], "bits": "00000000"}
        yield {"type": "query", "query_type": "APRS", "footprint": {"latitude": 0, "longitude": 0, "radius_miles": v}}
        yield {"type": "weather", "timestamp": "10092345", "weather": {"temperature_f": v, "rain_raw": v}}


def separated():
    for sep in SEPARATED:
        for depth in (1, 2):
            for field in ("source", "destination"):
                d = nested({"type": "status", "text": "hi"}, depth)
                inner = d
                while inner["packet"]["data"]["type"] == "third-party":
                    inner = inner["packet"]["data"]
                inner["packet"][field] = sep
                yield d
            d = nested({"type": "status", "text": "hi"}, depth)
            d["packet"]["path"] = [sep, "WIDE2-1"]
            yield d


def data_catalogue():
    """(data, exact) pairs."""
    for d in extremes():
        yield d, True
    for d in separated():
        yield d, True
    for _, make in text_slots():
        for t in TEXTS:
            for text in placed(t):
                yield make(text), True
    for alt in MIC_E_ALTITUDES:
        for comment in (None, "x", "/A=001234 x", "x /A=001234", "/x", " x"):
            for code in ("`", None):
                d = {"type": "mic-e", "mic_e_message": "en-route", "latitude": 51.5, "longitude": -0.5, "symbol": "/>", "speed_knots": 0, "altitude_feet": alt}
                if code:
                    d["type_code"] = code
                if comment:
                    d["comment"] = comment
                yield d, float(alt).is_integer()
    for cs in COEFFICIENTS:
        yield {"type": "telemetry-coefficients", "addressee": "N0CALL", "coefficients": cs}, True
    for lat, lon, radius in FOOTPRINTS:
        yield {"type": "query", "query_type": "APRS", "footprint": {"latitude": lat, "longitude": lon, "radius_miles": radius}}, float(radius).is_integer()
    for extra in NON_INTEGERS:
        yield dict(POSITION, **extra), True
    for extra in INEXACT:
        yield dict(POSITION, **extra), False
    for depth in (1, 2):
        for extra in INNER_FAULTS:
            yield nested(dict(POSITION, **extra), depth), True
    for d in weather_extras():
        yield d, True
    for d in user_defined():
        yield d, True
    for d in agrelo():
        # an Agrelo bearing between whole degrees is rounded (README Encoding), so it is not exact
        yield d, float(d["bearing_degrees"]).is_integer()
    for path in paths():
        yield {"type": "third-party", "packet": {"source": "N0CALL", "destination": "APRS", "path": path,
                                                 "data": {"type": "status", "text": "hi"}}}, True
    # empty where the data form leaves an empty value out (Read-back: empty and absent are one value)
    yield {"type": "message", "addressee": "N0CALL", "text": "hi", "message_id": ""}, True
    yield {"type": "message", "addressee": "N0CALL", "text": "hi", "message_id": "1", "reply_ack": ""}, True
    yield {"type": "directed-query", "addressee": "N0CALL", "query_type": "APRSP", "target": ""}, True
    yield {"type": "ack", "addressee": "N0CALL", "acked_id": ""}, True
    yield dict(POSITION, messaging=False, compressed=False), True
    for fmt in ("ultimeter-packet", "ultimeter-logging", "peet-bros-hash", "peet-bros-star"):
        yield {"type": "raw-weather", "format": fmt, "data": ""}, True


STATION = {"source": "N0CALL"}


def recipe_slots():
    def positioned(report, **k):
        args = {"latitude": 51.5, "longitude": -0.5, "symbol": "/>"}
        if report == "object":
            args.update(name="OBJ", timestamp={"utc": "2026-09-27T09:23:45Z", "format": "dhm"})
        if report == "item":
            args.update(name="ITEM")
        if report == "mic-e":
            args.update(mic_e_message="en-route")
        args.update(k)
        return args

    slots = []
    for report in ("position", "object", "item", "mic-e"):
        slots.append((report, lambda t, r=report: positioned(r, comment=t)))
        slots.append((report, lambda t, r=report: positioned(r, comment=t, altitude_feet=100)))
        slots.append((report, lambda t, r=report: positioned(r, comment=t, frequency={"mhz": 146.52, "tone": "tone", "tone_value": 100})))
        slots.append((report, lambda t, r=report: positioned(r, comment=t, compressed=True)))
        slots.append((report, lambda t, r=report: positioned(r, comment=t, dao=True)))
    slots += [
        ("message", lambda t: {"addressee": "N0CALL", "text": t}),
        ("bulletin", lambda t: {"id": "1", "text": t}),
        ("status", lambda t: {"text": t}),
        ("status", lambda t: {"text": t, "locator": "IO91SX", "symbol": "/G"}),
        ("telemetry", lambda t: {"sequence": 1, "analog": [1, 2, 3, 4, 5], "comment": t}),
        ("telemetry-names", lambda t: {"names": ["A", t]}),
        ("telemetry-units", lambda t: {"units": [t]}),
        ("telemetry-bits", lambda t: {"bits": "11111111", "project": t}),
    ]
    return slots


def recipe_catalogue():
    for path in paths():
        station = {"source": "N0CALL", "path": path} if path else dict(STATION)
        yield {"station": station, "report": "status", "args": {"text": "hi"}}
        yield {"station": station, "report": "position", "args": {"latitude": 51.5, "longitude": -0.5, "symbol": "/>"}}
        yield {"station": station, "report": "mic-e", "args": {"latitude": 51.5, "longitude": -0.5, "symbol": "/>"}}
    for report, make in recipe_slots():
        for t in TEXTS:
            for text in placed(t):
                yield {"station": STATION, "report": report, "args": make(text)}
    for t in TEXTS:
        for text in placed(t):
            yield {"station": {"source": "N0CALL", "destination": text[:9]}, "report": "status", "args": {"text": "hi"}}
            yield {"station": {"source": text[:9]}, "report": "status", "args": {"text": "hi"}}
    for sep in SEPARATED:
        yield {"station": {"source": sep}, "report": "status", "args": {"text": "hi"}}
        yield {"station": {"source": "N0CALL", "destination": sep}, "report": "status", "args": {"text": "hi"}}
        yield {"station": {"source": "N0CALL", "path": [sep, "WIDE2-1"]}, "report": "status", "args": {"text": "hi"}}
    for alt in ("altitude_feet", "altitude_m"):
        for value in (0, 1000, 304.8, 100.5, -50000):
            for comment in (None, "/A=001234 x", "x /A=001234"):
                args = {"latitude": 51.5, "longitude": -0.5, "symbol": "/>", "mic_e_message": "en-route", alt: value}
                if comment:
                    args["comment"] = comment
                yield {"station": STATION, "report": "mic-e", "args": args}
    for value in ("", "1", "ABCDEF"):
        yield {"station": STATION, "report": "message", "args": {"addressee": "N0CALL", "text": "hi", "message_id": value}}
        yield {"station": STATION, "report": "ack", "args": {"addressee": "N0CALL", "message_id": value}}


def random_text(rng):
    sep = rng.choice(["", "", " ", "/"])
    return sep.join(rng.choice(TEXTS) for _ in range(rng.choice([2, 2, 3])))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out")
    ap.add_argument("--recipes", action="store_true", help="builder recipes (for build mode) instead of neutral data")
    ap.add_argument("--count", type=int, default=0, help="random records after the catalogue")
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    n = 0
    with gzip.open(args.out, "wt", encoding="utf-8") as f:
        def put(record):
            nonlocal n
            f.write(json.dumps({"n": n, **record}, ensure_ascii=False, separators=(",", ":")) + "\n")
            n += 1

        if args.recipes:
            for r in recipe_catalogue():
                put(r)
            slots = recipe_slots()
            for _ in range(args.count):
                report, make = rng.choice(slots)
                path = rng.choice(paths())
                station = {"source": "N0CALL", "path": path} if path else dict(STATION)
                put({"station": station, "report": report, "args": make(random_text(rng))})
        else:
            for d, exact in data_catalogue():
                put({"data": d, "exact": exact})
            slots = text_slots()
            for _ in range(args.count):
                _, make = rng.choice(slots)
                put({"data": make(random_text(rng)), "exact": True})
    print(f"{n:,} {'recipes' if args.recipes else 'data records'} in {args.out}")


if __name__ == "__main__":
    main()
