import json, gzip, sys
A = ["N0CALL ", " N0CALL", "N0 CALL", "n0call", "", " ", "         ", "ABCDEFGHI", "A:B", "A}B", "A{B", "BLN1 ", "BLN1", "BLNA", "NWS-X", "NWS_X", "NWS", "BLN", "BLN12345", "PARM", "ack1", "?", ":", "N0CALL-15", "A" * 10, "é"]
N = ["OBJ", " OBJ", "  OBJ", "O J", "OBJ*", "OBJ_", "ABCDEFGHI", "A", "A!B", "A_B", "123456789", "OBJ ", "!", "_", "*", " ", "IO91SX", "é", "OB:J", "  ", "AB*CDEFGH"]
recs = []
for a in A:
    recs.append({"type": "message", "addressee": a, "text": "hi"})
    recs.append({"type": "message", "addressee": a, "text": "hi", "message_id": "1"})
    recs.append({"type": "ack", "addressee": a, "acked_id": "1"})
    recs.append({"type": "reject", "addressee": a, "rejected_id": "1"})
    recs.append({"type": "bulletin", "addressee": a, "text": "hi"})
    recs.append({"type": "nws-bulletin", "addressee": a, "text": "hi"})
    recs.append({"type": "telemetry-names", "addressee": a, "names": ["A"]})
    recs.append({"type": "directed-query", "addressee": a, "query_type": "APRSP"})
    recs.append({"type": "directed-query", "addressee": "N0CALL", "query_type": "APRSP", "target": a})
for t in ["APRSD", "APRSH", "APRSO", "APRSP", "APRSS", "APRST", "PING", "WX", "FOO", "PING?", "aprsp", "APRS?", "A B", "", "APRSP ", " APRSP"]:
    recs.append({"type": "directed-query", "addressee": "N0CALL", "query_type": t})
    recs.append({"type": "directed-query", "addressee": "N0CALL", "query_type": t, "target": "N1CALL"})
for n in N:
    for ts in ["092345z", "092345/", "092345h"]:
        recs.append({"type": "object", "name": n, "timestamp": ts, "latitude": 51.5, "longitude": -0.5, "symbol": "/>"})
        recs.append({"type": "object", "name": n, "timestamp": ts, "latitude": 51.5, "longitude": -0.5, "symbol": "/>", "compressed": True})
    recs.append({"type": "item", "name": n, "latitude": 51.5, "longitude": -0.5, "symbol": "/>"})
    recs.append({"type": "item", "name": n, "latitude": 51.5, "longitude": -0.5, "symbol": "/>", "killed": True})
    recs.append({"type": "item", "name": n, "latitude": 51.5, "longitude": -0.5, "symbol": "/>", "compressed": True})
for ids in ["1", "12345", "123456", "a", "A b", "}", "{", "", "1}", "AB}C"]:
    recs.append({"type": "ack", "addressee": "N0CALL", "acked_id": ids})
    recs.append({"type": "message", "addressee": "N0CALL", "text": "hi", "message_id": ids})
    recs.append({"type": "message", "addressee": "N0CALL", "text": "hi", "message_id": "1", "reply_ack": ids})
    recs.append({"type": "ack", "addressee": "N0CALL", "acked_id": "1", "reply_ack": ids})
    recs.append({"type": "telemetry-names", "addressee": "N0CALL", "names": ["A"], "message_id": ids})
with gzip.open(sys.argv[1], "wt") as f:
    for i, d in enumerate(recs): f.write(json.dumps({"n": i, "data": d, "exact": True}, ensure_ascii=False) + "\n")
print(len(recs))
