import sys, json, gzip, random, itertools
sys.path.insert(0, "/tmp/r5-readback")
import importlib.util
spec = importlib.util.spec_from_file_location("ga", "/tmp/r5-readback/gen_adv.py")
src = open("/tmp/r5-readback/gen_adv.py").read().replace("\nmain()\n", "\n")
ns = {}; exec(compile(src, "gen_adv", "exec"), ns)
EL = ns["EL"]
rng = random.Random(5)
def texts():
    out = set(EL)
    for e in EL:
        out.add("Hi " + e); out.add(e + " Hi"); out.add("Hi" + e); out.add(e + "Hi")
    for _ in range(3000):
        out.add(rng.choice(EL) + rng.choice(["", " ", "/"]) + rng.choice(EL))
    return sorted(out)
T = texts()
recs = []
def add(d): recs.append(d)
for t in T:
    for f in ["ultimeter-packet", "ultimeter-logging", "peet-bros-hash", "peet-bros-star"]:
        add({"type": "raw-weather", "format": f, "data": t})
    for loc in ["IO91", "IO91SX"]:
        add({"type": "maidenhead-beacon", "locator": loc, "comment": t})
    add({"type": "test", "data": t})
    add({"type": "capabilities", "capabilities": [["IGATE", t]]})
    add({"type": "capabilities", "capabilities": [[t]]})
    add({"type": "capabilities", "capabilities": [["A", "1"], [t, "x"]]})
    add({"type": "user-defined", "user_id": "A", "packet_type": "x", "data": t})
    add({"type": "status", "text": t})
    add({"type": "status", "timestamp": "092345z", "text": t})
    add({"type": "status", "locator": "IO91SX", "symbol": "/>", "text": t})
    add({"type": "status", "locator": "IO91", "symbol": "/>", "text": t})
    add({"type": "status", "locator": "IO91SX", "symbol": "/>", "beam": {"heading_code": "3", "power_code": "7"}, "text": t})
    add({"type": "telemetry", "sequence": "001", "analog": [1, 2, 3, 4, 5], "bits": "00000000", "comment": t})
    add({"type": "telemetry", "sequence": "001", "analog": [1, 2, 3, 4, 5], "comment": t})
    add({"type": "telemetry", "sequence": "MIC", "analog": [1, 2, 3, 4, 5], "bits": "00000000", "comment": t})
    add({"type": "telemetry", "sequence": "001", "analog": [1, None, None, None, None], "comment": t})
    add({"type": "telemetry", "sequence": "001", "analog": [1, 2, 3, 4, 5.5], "bits": "11110000", "comment": t})
    for ad in ["N0CALL", "N0CALL-15", "BLN1", "BLNA", "NWS-WARN", "ABCDEFGHI", "A"]:
        add({"type": "message", "addressee": ad, "text": t})
        add({"type": "message", "addressee": ad, "text": t, "message_id": "12"})
        add({"type": "message", "addressee": ad, "text": t, "message_id": "AB", "reply_ack": "CD"})
        add({"type": "message", "addressee": ad, "text": t, "message_id": "AB", "reply_ack": ""})
    add({"type": "bulletin", "addressee": "BLN1", "text": t})
    add({"type": "bulletin", "addressee": "BLN1WX", "text": t, "message_id": "1"})
    add({"type": "bulletin", "addressee": "BLNA", "text": t})
    add({"type": "nws-bulletin", "addressee": "NWS-WARN", "text": t})
    add({"type": "nws-bulletin", "addressee": "NWS_ADVIS", "text": t, "message_id": "AB"})
    add({"type": "telemetry-names", "addressee": "N0CALL", "names": [t]})
    add({"type": "telemetry-names", "addressee": "N0CALL", "names": ["a", t, "b"]})
    add({"type": "telemetry-units", "addressee": "N0CALL", "units": [t, "V"]})
    add({"type": "telemetry-bits", "addressee": "N0CALL", "bits": "11111111", "project": t})
    add({"type": "telemetry-names", "addressee": "N0CALL", "names": ["A"], "message_id": "1"})
    add({"type": "weather", "timestamp": "10092345", "weather": {"temperature_f": 70, "software": "w", "unit": t[:4]}})
    add({"type": "weather", "timestamp": "10092345", "weather": {"humidity_percent": 50, "software": t[:1], "unit": t[1:5]}})
    add({"type": "weather", "timestamp": "10092345", "weather": {"pressure_mbar": 1013.2, "extra": [{"letter": t[:1] or "X", "value": t[1:]}]}})
    for nm in ["OBJ", "IO91SX", "A B", "ABCDEFGHI"]:
        add({"type": "object", "name": nm, "timestamp": "092345z", "latitude": 51.5, "longitude": -0.5, "symbol": "/>", "comment": t})
    add({"type": "item", "name": "ITEM", "latitude": 51.5, "longitude": -0.5, "symbol": "/>", "comment": t})
    add({"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "/>", "storm": {"type": "hurricane", "sustained_wind_knots": 150, "gust_knots": 200, "central_pressure_mbar": 980, "hurricane_radius_nm": 90, "tropical_storm_radius_nm": 30, "whole_gale_radius_nm": 40}, "comment": t})
    add({"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "/>", "storm": {"type": "hurricane", "sustained_wind_knots": 150, "gust_knots": 200, "central_pressure_mbar": 980, "hurricane_radius_nm": 90, "tropical_storm_radius_nm": 30}, "comment": t})
    add({"type": "object", "name": "AREA", "timestamp": "092345z", "latitude": 51.5, "longitude": -0.5, "symbol": "\\l", "area": {"shape": "filled-ellipse", "color": "cyan", "lat_offset": 10, "lon_offset": 10}, "comment": t})
    add({"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "/\\", "course_degrees": 88, "speed_knots": 36, "df_bearing": {"bearing_degrees": 270, "number": 7, "range": 2, "quality": 9}, "comment": t})
    add({"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "\\m", "signpost": "55", "comment": t})
    add({"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "/>", "altitude_feet": 100, "comment": t})
    add({"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "/>", "frequency": {"mhz": 146.52, "tone": "tone", "tone_value": 100, "offset_khz": 600}, "comment": t})
    add({"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "/>", "dfs": {"strength": 2, "height": 3, "gain": 6, "directivity": 0}, "comment": t})
    add({"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "/>", "telemetry": {"sequence": 1, "analog": [1, 2]}, "comment": t})
    add({"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "/>", "dao": {"datum": "W", "precision": "base91"}, "comment": t})
    add({"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "/>", "timestamp": "092345z", "comment": t})
    add({"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "/>", "compressed": True, "compression": {"fix": "current", "source": "rmc", "origin": "software"}, "altitude_feet": 1000, "comment": t})
    add({"type": "third-party", "packet": {"source": "N0CALL", "destination": "APRS", "path": ["TCPIP*"], "data": {"type": "status", "text": t}}})
    add({"type": "third-party", "packet": {"source": "N0CALL", "destination": "APRS", "data": {"type": "message", "addressee": "N0CALL", "text": t}}})
for u in range(32, 127):
    for p in range(32, 127):
        add({"type": "user-defined", "user_id": chr(u), "packet_type": chr(p), "data": "{1"})
        add({"type": "user-defined", "user_id": chr(u), "packet_type": chr(p), "data": "x"})
for b in range(0, 361):
    for q in range(10):
        add({"type": "agrelo-df", "bearing_degrees": b, "quality": q})
for qt in ["APRS", "IGATE", "WX", "APRSP", "X", "PING"]:
    for fp in [None, {"latitude": 0, "longitude": 0, "radius_miles": 0}, {"latitude": -0.5, "longitude": 179.99, "radius_miles": 9999}]:
        d = {"type": "query", "query_type": qt}
        if fp: d["footprint"] = fp
        add(d)
for tok in ["IGATE", "A", "MSG_CNT", "x"]:
    for val in [None, "", "=", "a=b", "1,", " "]:
        add({"type": "capabilities", "capabilities": [[tok] if val is None else [tok, val]]})
with gzip.open(sys.argv[1], "wt") as f:
    for n, d in enumerate(recs):
        f.write(json.dumps({"n": n, "data": d, "exact": True}, ensure_ascii=False) + "\n")
print(len(recs))
