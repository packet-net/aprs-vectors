import json, gzip, sys
recs = []
for s in ["1,2", "", "MIC1", "MI", " 1", "1 ", "#", "T#1", "1|", "MIC", "MIC,", "12345", "abc", "1.5", "-1", "+1", "0x1", "１", "ABCDEFGH"]:
    recs.append({"type": "telemetry", "sequence": s, "analog": [1, 2, 3, 4, 5], "bits": "00000000"})
    recs.append({"type": "telemetry", "sequence": s, "analog": [None, 2, 3, 4, 5]})
for b in ["0000000", "000000000", "0000000x", "", "1111111a", "00000000,"]:
    recs.append({"type": "telemetry", "sequence": "001", "analog": [1, 2, 3, 4, 5], "bits": b})
    recs.append({"type": "telemetry-bits", "addressee": "N0CALL", "bits": b, "project": "p"})
for a in [[1, 2, 3, 4], [1, 2, 3, 4, 5, 6], [], [None] * 5, [1e20, 0, 0, 0, 0], [-0.0, 0, 0, 0, 0], [0.1, 0, 0, 0, 0], [1e-7, 0, 0, 0, 0]]:
    recs.append({"type": "telemetry", "sequence": "001", "analog": a, "bits": "00000000"})
for sp in ["", "}", "{", "1234", "a}", "5}5", "{1", "1}", "  ", " 5", "5 ", "abc", "ab", "a"]:
    recs.append({"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "\\m", "signpost": sp})
    recs.append({"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "\\m", "signpost": sp, "comment": "x"})
    recs.append({"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "/>", "signpost": sp})
for sw in ["w", "e", "x", "d", "#", "h", "1", " ", "_", "/", "{", "}", "|", "!", ".", "t", "-", "\\"]:
    for un in ["", "R", "RS", "RSW", "RSWX", "RSWXY", "h50", "50", "1234", " ", "a b", ".", "..", "-1", "b1", "}", "{1}", "|!!|", "!W1!"]:
        w = {"temperature_f": 70, "software": sw, "unit": un}
        recs.append({"type": "weather", "timestamp": "10092345", "weather": w})
        recs.append({"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "/_", "weather": dict(w)})
        recs.append({"type": "position", "latitude": 51.5, "longitude": -0.5, "symbol": "/_", "weather": {"humidity_percent": 50, "software": sw, "unit": un}})
for f in ["ultimeter-packet", "ultimeter-logging", "peet-bros-hash", "peet-bros-star"]:
    for d in ["", " ", "x", "!", "!!", "#", "*", "$ULTW", "ULTW", "0000", "{1", "|!!|", "x ", " x", "é", "abc\x7f"]:
        recs.append({"type": "raw-weather", "format": f, "data": d})
for src in ["N0CALL", "N0CALL-0", "n0call", "A>B", "A:B", "A,B", "TCPIP", "A*", "-", "ABCDEFGHIJ", "N0CALL-R"]:
    for dst in ["APRS", "n0call", "A*", "A,B", "-"]:
        for path in [[], ["TCPIP*"], ["WIDE1-1", "N0CALL*"], ["A,B"], ["qAR"], ["A:B"]]:
            recs.append({"type": "third-party", "packet": {"source": src, "destination": dst, "path": path, "data": {"type": "status", "text": "hi"}}})
with gzip.open(sys.argv[1], "wt") as fo:
    for i, d in enumerate(recs): fo.write(json.dumps({"n": i, "data": d, "exact": True}, ensure_ascii=False) + "\n")
print(len(recs))
