import json, gzip, sys, itertools
P = ["|", "|!", "|!!", "|!!!", "|!!!!", "|!!!!|", "!", "!W", "!W1", "!W12", "!w", "!w\"", "!w\"#", "W12!", "2!", "#!", "!|", "|!", "}", "{", "{1", "{12", "1}", "12}", "/A", "/A=", "/A=0", "/A=00001", "A=000100", "=000100", "0", "00", "000", "0000", "/", "MHz", ".520MHz", "520MHz", "T1", "T10", "+0", "+06", "R2", "R25", "R25m", "m", " ", "  ", "/ ", " /", "PHG", "PHG5", "PHG513", "HG5132", "RNG", "RNG005", "DFS", "DFS236", "5132", "0050", "/1", "/12", "/123", "123", "12/", "1/", "x", "Hi", "Hi ", " Hi", "!!", "!!!", "|||", "}}", "{{", "~", "^", "\"", "'", "`", "_", ".", "...", "/...", "...", "t", "g", "h", "b", "#", "L", "l", "c", "s", "r", "p", "P", "e", "w", "d", "x", "X"]
base = {"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "/>"}
els = {
  "none": {}, "alt": {"altitude_feet": 100}, "cs": {"course_degrees": 88, "speed_knots": 36},
  "phg": {"phg": {"power": 5, "height": 1, "gain": 3, "directivity": 2}}, "rng": {"range_miles": 50},
  "dfs": {"dfs": {"strength": 2, "height": 3, "gain": 6, "directivity": 0}},
  "freq": {"frequency": {"mhz": 146.52}}, "freqt": {"frequency": {"mhz": 146.52, "tone": "tone", "tone_value": 100, "offset_khz": 600}},
  "tel": {"telemetry": {"sequence": 1, "analog": [1, 2]}}, "dao": {"dao": {"datum": "W", "precision": "base91"}},
  "daot": {"dao": {"datum": "W", "precision": "thousandths"}},
  "area": {"symbol": "\\l", "area": {"shape": "filled-ellipse", "color": "cyan", "lat_offset": 10, "lon_offset": 10}},
  "sign": {"symbol": "\\m", "signpost": "55"},
  "alt+tel": {"altitude_feet": 100, "telemetry": {"sequence": 1, "analog": [1, 2]}},
  "tel+dao": {"telemetry": {"sequence": 1, "analog": [1, 2]}, "dao": {"datum": "W", "precision": "base91"}},
  "cs+alt": {"course_degrees": 88, "speed_knots": 36, "altitude_feet": 100},
  "comp": {"compressed": True, "compression": {"fix": "current", "source": "rmc", "origin": "software"}},
  "comp+alt": {"compressed": True, "compression": {"fix": "current", "source": "rmc", "origin": "software"}, "altitude_feet": 1000},
}
recs = []
for name, e in els.items():
    for a in P:
        for b in [""] + P:
            for kind in ("position", "object", "item"):
                d = dict(base); d.update(e); d["comment"] = a + b; d["type"] = kind
                if kind == "object": d["name"] = "OBJ"; d["timestamp"] = "092345z"
                if kind == "item": d["name"] = "ITEM"
                if not d["comment"]: continue
                recs.append(d)
with gzip.open(sys.argv[1], "wt") as f:
    for n, d in enumerate(recs):
        f.write(json.dumps({"n": n, "data": d, "exact": True}) + "\n")
print(len(recs))
