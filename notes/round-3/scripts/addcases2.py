import json, sys
sys.path.insert(0,'/tmp/r3/scripts')
from addcases import add, ax25
TWO = ["which-refusal-a-record-with-two-faults-gets"]
WIND = ["a-wind-direction-is-judged-in-whole-degrees"]
SRC = "differential fuzzing 2026-11-14"
CW = {"type": "position", "latitude": 49.5, "longitude": -72.75, "symbol": "/_", "compressed": True,
      "compression": {"fix": "current", "source": "other", "origin": "software"}}
def enc(id_, desc, data, expect, interp=TWO, auth="interpretation", src=SRC):
    c = {"id": "encode/" + id_, "description": desc, "source": src, "authority": auth}
    if auth == "interpretation": c["interpretations"] = interp
    c["input"] = {"encode": data}
    c["expect"] = expect if isinstance(expect, dict) else {"refused": True, "refusal": expect}
    return c
P = {"type": "position", "latitude": 49.05833333333333, "longitude": -72.02916666666667, "symbol": "/-"}
AMB = ["ambiguity-cuts-a-raw-position"]
cases = [
 enc("ambiguous-latitude-just-under-90-degrees", "A latitude of 89.9999167 degrees with two levels of ambiguity is in the box 89 59, cut and not rounded first, so it is written there (centre 89 59.5) rather than refused as a box centred past the pole.",
     dict(P, latitude=89.9999167, longitude=10.0, ambiguity=2), {"info": "!8959.  N/01000.  E-"}, AMB),
 enc("ambiguous-longitude-just-under-180-degrees", "A longitude of 179.9999167 degrees with two levels of ambiguity is in the box 179 59, cut and not rounded first.",
     dict(P, latitude=10.0, longitude=179.9999167, ambiguity=2), {"info": "!1000.  N/17959.  E-"}, AMB),
 enc("ambiguous-south-west-corner", "A position a rounding step from both the south pole and 180 west, with one level of ambiguity, is cut into the boxes below the edges.",
     dict(P, latitude=-89.9999167, longitude=-179.9999167, ambiguity=1), {"info": "!8959.9 S/17959.9 W-"}, AMB),
 enc("mic-e-ambiguous-position-just-under-the-edges", "A Mic-E position a rounding step from 90 and 180 degrees, with two levels of ambiguity, is cut into the boxes below the edges, as an uncompressed one is.",
     {"type": "mic-e", "mic_e_message": "en-route", "latitude": 89.9999167, "longitude": 179.9999167, "ambiguity": 2, "symbol": "/>"},
     {"info": "`kWNl \x1c>/", "destination": "XY5YZL"}, AMB),
 enc("compressed-wind-direction-minus-0-4-is-north", "A compressed wind direction of -0.4 degrees is 0 in whole degrees, in range, and rounds to the 4-degree step 0.",
     dict(CW, weather={"wind_direction_degrees": -0.4, "wind_speed_mph": 0, "wind_gust_mph": 5, "temperature_f": 77}), {"info": "!/5L!!<*e8_!!Cg005t077"}, WIND),
 enc("uncompressed-wind-direction-360-5-is-out-of-range", "An uncompressed wind direction of 360.5 degrees rounds to 361, out of range, as it is in cs bytes.",
     {"type": "position", "latitude": 49.5, "longitude": -72.75, "symbol": "/_", "weather": {"wind_direction_degrees": 360.5, "wind_speed_mph": 4, "wind_gust_mph": 5, "temperature_f": 77}}, "value-out-of-range", WIND),
 enc("phg-digit-10-beside-a-course", "A PHG power digit of 10 (value-out-of-range) given beside a course and speed, which want the same data extension (extension-conflict): the PHG's place exists, so its digits are checked first, and the refusal is value-out-of-range.",
     dict(P, course_degrees=88, speed_knots=36, phg={"power": 10, "height": 1, "gain": 3, "directivity": 2}), "value-out-of-range"),
 enc("query-type-and-radius-both-wrong", "A general query whose type is not upper-case letters (invalid-code) and whose radius is past 9999 miles (value-out-of-range): the refusal is value-out-of-range, which the order puts first.",
     {"type": "query", "query_type": "X Y", "footprint": {"latitude": 34.02, "longitude": -117.15, "radius_miles": 10000}}, "value-out-of-range"),
 enc("query-without-a-type-and-radius-too-big", "A general query with no type (missing-field) and a radius past 9999 miles (value-out-of-range): value-out-of-range.",
     {"type": "query", "footprint": {"latitude": 34.02, "longitude": -117.15, "radius_miles": 10000}}, "value-out-of-range"),
 enc("sixteen-telemetry-coefficients", "EQNS. carries at most 15 coefficients; 16 is a list longer than its field: too-long.",
     {"type": "telemetry-coefficients", "addressee": "N0CALL", "coefficients": [1] * 16}, "too-long", auth="spec", src="APRS12c ch. 13 (" + SRC + ")"),
 enc("maidenhead-beacon-comment-and-locator-both-wrong", "A Maidenhead beacon with a line break in its comment (invalid-character) and a locator of 5 characters (malformed): invalid-character, which the order puts first.",
     {"type": "maidenhead-beacon", "locator": "IO91S", "comment": "a\rb"}, "invalid-character"),
 enc("lower-case-status-locator", "A status locator in lower case reads back in upper case, so it is not the fixed form a locator is: malformed.",
     {"type": "status", "locator": "io91sx", "symbol": "/-", "text": "Hello"}, "malformed", auth="spec", src="APRS12c ch. 16 (" + SRC + ")"),
 enc("lower-case-status-locator-without-a-symbol", "A lower-case status locator (malformed) with no symbol (missing-field): malformed, which the order puts first.",
     {"type": "status", "locator": "io91sx", "text": "Hello"}, "malformed"),
 enc("dao-digit-datum-with-added-precision", "A !DAO! datum digit is read only with no added precision, so a digit datum with base-91 digits is a datum outside the set its precision takes: invalid-code.",
     dict(P, dao={"datum": "1", "precision": "base91"}), "invalid-code", ["dao-datum-digits"]),
 enc("dao-digit-datum-with-added-precision-on-an-ambiguous-position", "A digit datum with base-91 digits (invalid-code) on an ambiguous position (field-not-allowed): the !DAO! has a place in the comment, so its own checks run first, and the refusal is invalid-code.",
     dict(P, ambiguity=2, dao={"datum": "1", "precision": "base91"}), "invalid-code", ["dao-datum-digits"] + TWO),
 enc("nmea-comment-without-a-checksum", "An NMEA comment follows the sentence's checksum, which ends the sentence; given with a sentence that has none, it would read back as part of the sentence. An NMEA problem of any kind is invalid-nmea.",
     {"type": "nmea", "sentence": "GPRMC,063909,A,3349.4302,N,11700.3721,W,43.022,89.3,291099,13.6,E", "comment": "hello", "latitude": 33.823836666666665, "longitude": -117.00620166666667, "fix": "valid", "course_degrees": 89.3, "speed_knots": 43.022, "time": "06:39:09"},
     "invalid-nmea", ["nmea-data-is-its-sentence"]),
 enc("query-target-and-type-both-wrong", "A directed query whose target is not one callsign (invalid-addressee) and whose type is in lower case (invalid-code): invalid-addressee.",
     {"type": "directed-query", "addressee": "N0CALL", "query_type": "aprs", "target": "A B"}, "invalid-addressee"),
 enc("beam-power-code-and-locator-both-wrong", "A beam power code of 0 (invalid-code) and a locator of 5 characters (malformed): invalid-code.",
     {"type": "status", "locator": "IO91S", "symbol": "/-", "beam": {"heading_code": "B", "power_code": "0"}, "text": "Hello"}, "invalid-code"),
]
add('encode.json', cases)
AXI = ["an-ax25-address-is-letters-and-digits"]
def axc(name, desc, frame, expect, strict):
    return {"id": "envelope/" + name, "description": desc, "source": "AX.25 2.2 section 3.12", "authority": "interpretation",
            "interpretations": AXI, "input": {"ax25_hex": frame}, "expect": expect, "strict": strict}
add('envelope.json', [
 axc("ax25-all-space-source", "An AX.25 source call of six spaces has no characters: invalid-address, as an empty TNC2 source is unusable.",
     ax25("APZ001", "      ", [], b">x"), {"header_error": ["error:invalid-address"]}, "same"),
 axc("ax25-all-space-destination", "An AX.25 destination of six spaces is an empty destination, tolerated as in TNC2 (empty-destination).",
     ax25("      ", "N0CALL", [], b">x"), {"header": {"source": "N0CALL", "destination": ""}, "data": {"type": "status", "text": "x"}, "diagnostics": ["warning:empty-destination"]},
     {"rejected_by": "empty-destination", "header": True}),
 axc("ax25-all-space-digipeater", "An AX.25 digipeater of six spaces is an empty path entry, tolerated as in TNC2 (empty-path-entry) and left out of the path.",
     ax25("APZ001", "N0CALL", ["      ", "WIDE1"], b">x"), {"header": {"source": "N0CALL", "destination": "APZ001", "path": ["WIDE1"]}, "data": {"type": "status", "text": "x"}, "diagnostics": ["warning:empty-path-entry"]},
     {"rejected_by": "empty-path-entry", "header": True}),
])
print('ok')
