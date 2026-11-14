import json, sys
R = '/home/tf/src/aprs-vectors-r3/cases/'
def ax25(dest, src, digis, info, used=()):
    def addr(call, ssid, last, h=False):
        call = call.ljust(6)
        b = bytes((ord(c) << 1) & 0xFF for c in call)
        return b + bytes([0x60 | (ssid << 1) | (0x80 if h else 0) | (1 if last else 0)])
    out = addr(dest, 0, False) + addr(src, 0, not digis)
    for i, d in enumerate(digis):
        out += addr(d, 0, i == len(digis) - 1, i in used)
    return (out + b'\x03\xf0' + info).hex().upper()

import sys as _s; _s.path.insert(0, '/tmp/r3/scripts')
from fmt import fmt_case
def add(fname, cases):
    p = R + fname
    text = open(p, encoding='utf-8').read()
    doc = json.loads(text)
    ids = {c['id'] for c in doc['cases']}
    for c in cases:
        assert c['id'] not in ids, c['id']
    tail = '\n  ]\n}\n'
    assert text.endswith(tail), fname
    text = text[:-len(tail)] + ',\n' + ',\n'.join(fmt_case(c) for c in cases) + tail
    json.loads(text)
    open(p, 'w', encoding='utf-8').write(text)

TWO = ["which-refusal-a-record-with-two-faults-gets"]
WIND = ["a-wind-direction-is-judged-in-whole-degrees"]
CW = {"type": "position", "latitude": 49.5, "longitude": -72.75, "symbol": "/_", "compressed": True,
      "compression": {"fix": "current", "source": "other", "origin": "software"}}
def cw(**w):
    d = dict(CW); d["weather"] = dict(w); return d
enc = [
 {"id": "encode/mic-e-course-0-and-an-altitude-past-every-form",
  "description": "A Mic-E course of 0 (value-has-no-form) and an altitude no form holds, past /A= and not whole metres (value-out-of-range): the refusal names value-out-of-range, which the Refusal reasons order puts first.",
  "source": "differential fuzzing 2026-11-13", "authority": "interpretation", "interpretations": TWO,
  "input": {"encode": {"type": "mic-e", "mic_e_message": "en-route", "latitude": 42.179, "longitude": -71.1985, "symbol": "/>", "course_degrees": 0, "speed_knots": 9, "altitude_feet": 1500000.7}},
  "expect": {"refused": True, "refusal": "value-out-of-range"}},
 {"id": "encode/compressed-wind-speed-past-the-cs-steps-without-a-direction",
  "description": "A compressed weather report with a wind speed of -0.3 mph, nearest a cs step below the byte (value-out-of-range), and no wind direction (missing-field): the refusal names value-out-of-range, which the Refusal reasons order puts first.",
  "source": "differential fuzzing 2026-11-13", "authority": "interpretation", "interpretations": TWO,
  "input": {"encode": cw(wind_speed_mph=-0.3, wind_gust_mph=5, temperature_f=77)},
  "expect": {"refused": True, "refusal": "value-out-of-range"}},
 {"id": "encode/weather-altitude-past-999999-feet-has-no-place",
  "description": "An uncompressed weather report has no comment for an /A= altitude, so an altitude of 999999.5 feet is field-not-allowed, and its range is not checked.",
  "source": "differential fuzzing 2026-11-13", "authority": "interpretation", "interpretations": TWO,
  "input": {"encode": {"type": "position", "latitude": 49.05833333333333, "longitude": -72.02916666666667, "symbol": "/_", "weather": {"wind_direction_degrees": 220, "wind_speed_mph": 4, "wind_gust_mph": 5, "temperature_f": 77}, "altitude_feet": 999999.5}},
  "expect": {"refused": True, "refusal": "field-not-allowed"}},
 {"id": "encode/compressed-wind-direction-360-4-is-north",
  "description": "A compressed wind direction of 360.4 degrees is 360 in whole degrees, in range, and then rounds to the 4-degree step 360, north, written as c = 0.",
  "source": "differential fuzzing 2026-11-13", "authority": "interpretation", "interpretations": WIND,
  "input": {"encode": cw(wind_direction_degrees=360.4, wind_speed_mph=0, wind_gust_mph=5, temperature_f=77)},
  "expect": {"info": "!/5L!!<*e8_!!Cg005t077"}},
 {"id": "encode/compressed-wind-direction-360-5-is-out-of-range",
  "description": "A compressed wind direction of 360.5 degrees is 361 in whole degrees, out of range as it is uncompressed, though the 4-degree step nearest it is 360.",
  "source": "differential fuzzing 2026-11-13", "authority": "interpretation", "interpretations": WIND,
  "input": {"encode": cw(wind_direction_degrees=360.5, wind_speed_mph=0, wind_gust_mph=5, temperature_f=77)},
  "expect": {"refused": True, "refusal": "value-out-of-range"}},
 {"id": "encode/compressed-wind-direction-minus-0-5-is-out-of-range",
  "description": "A compressed wind direction of -0.5 degrees is -1 in whole degrees, out of range as it is uncompressed, though the 4-degree step nearest it is 0.",
  "source": "differential fuzzing 2026-11-13", "authority": "interpretation", "interpretations": WIND,
  "input": {"encode": cw(wind_direction_degrees=-0.5, wind_speed_mph=0, wind_gust_mph=5, temperature_f=77)},
  "expect": {"refused": True, "refusal": "value-out-of-range"}},
 {"id": "encode/compressed-wind-direction-out-of-range-and-a-range",
  "description": "A compressed wind direction of 360.5 degrees (value-out-of-range) and a range that also wants the cs bytes (extension-conflict): the refusal names value-out-of-range, which the Refusal reasons order puts first.",
  "source": "differential fuzzing 2026-11-13", "authority": "interpretation", "interpretations": WIND + TWO,
  "input": {"encode": dict(cw(wind_direction_degrees=360.5, wind_speed_mph=0, wind_gust_mph=5, temperature_f=77), range_miles=2)},
  "expect": {"refused": True, "refusal": "value-out-of-range"}},
 {"id": "encode/third-party-path-entry-before-a-used-one-not-marked",
  "description": "A third-party header whose path entry comes before a used one but is not marked used reads back with both used (a path entry before a used one is used too), so the header cannot be written as given: invalid-third-party-header.",
  "source": "differential fuzzing 2026-11-13", "authority": "spec", 
  "input": {"encode": {"type": "third-party", "packet": {"source": "N0CALL", "destination": "APZ001", "path": ["TCPIP", "G4ABC*"], "data": {"type": "message", "addressee": "N0CALL", "text": "Hello"}}}},
  "expect": {"refused": True, "refusal": "invalid-third-party-header"}},
 {"id": "encode/telemetry-report-with-six-analog-values",
  "description": "A telemetry report carries five analog values; a sixth makes the list longer than its field allows: too-long, as codes.json gives it (more than 5 analog values).",
  "source": "APRS12c ch. 13 (differential fuzzing 2026-11-13)", "authority": "spec",
  "input": {"encode": {"type": "telemetry", "sequence": "001", "analog": [1, 2, 3, 4, 5, 6], "bits": "00000000"}},
  "expect": {"refused": True, "refusal": "too-long"}},
 {"id": "encode/base91-telemetry-with-six-analog-values",
  "description": "Base-91 comment telemetry carries 1-5 analog values; six is a list longer than its field allows: too-long.",
  "source": "APRS12c ch. 13 (differential fuzzing 2026-11-13)", "authority": "spec",
  "input": {"encode": {"type": "position", "latitude": 49.05833333333333, "longitude": -72.02916666666667, "symbol": "/-", "telemetry": {"sequence": 1, "analog": [1, 2, 3, 4, 5, 6]}}},
  "expect": {"refused": True, "refusal": "too-long"}},
 {"id": "encode/base91-telemetry-with-no-analog-values",
  "description": "Base-91 comment telemetry carries 1-5 analog values; none is too few telemetry values: malformed, as codes.json gives it.",
  "source": "APRS12c ch. 13 (differential fuzzing 2026-11-13)", "authority": "spec",
  "input": {"encode": {"type": "position", "latitude": 49.05833333333333, "longitude": -72.02916666666667, "symbol": "/-", "telemetry": {"sequence": 1, "analog": []}}},
  "expect": {"refused": True, "refusal": "malformed"}},
 {"id": "encode/nmea-sentence-without-its-fields",
  "description": "NMEA data that gives the sentence but not the fields it holds reads back with them, so it is data that disagrees with its sentence: invalid-nmea. A field not listed must not be produced.",
  "source": "differential fuzzing 2026-11-13", "authority": "spec",
  "input": {"encode": {"type": "nmea", "sentence": "GPRMC,063909,A,3349.4302,N,11700.3721,W,43.022,89.3,291099,13.6,E*52", "has_checksum": True}},
  "expect": {"refused": True, "refusal": "invalid-nmea"}},
 {"id": "encode/locator-status-with-an-invalid-symbol-table",
  "description": "A grid locator status whose symbol table is x is invalid-symbol, not a missing symbol.",
  "source": "differential fuzzing 2026-11-13", "authority": "spec",
  "input": {"encode": {"type": "status", "locator": "IO91SX", "symbol": "x-", "text": "Hello"}},
  "expect": {"refused": True, "refusal": "invalid-symbol"}},
 {"id": "encode/beam-heading-code-in-lower-case",
  "description": "A beam heading code is 0-9 or A-Z; a is outside the set: invalid-code, not text that reads as a field.",
  "source": "APRS12c ch. 16 (differential fuzzing 2026-11-13)", "authority": "spec",
  "input": {"encode": {"type": "status", "locator": "IO91SX", "symbol": "/-", "beam": {"heading_code": "a", "power_code": "7"}, "text": "Hello"}},
  "expect": {"refused": True, "refusal": "invalid-code"}},
]
if __name__ == "__main__": add("encode.json", enc)

pos = [
 {"id": "position/dao-without-digits-on-an-ambiguous-position",
  "description": "A !DAO! with no added digits (!W  !) on an ambiguous position still reads with dao-with-ambiguity, as the Encoding rule says it does whatever its precision.",
  "source": "differential fuzzing 2026-11-13", "authority": "interpretation", "interpretations": ["dao-on-an-ambiguous-position"],
  "input": {"info": "!4903.5 N/07201.7 W-!W  !"},
  "expect": {"data": {"type": "position", "latitude": 49.05916666666667, "longitude": -72.02916666666667, "ambiguity": 1, "symbol": "/-", "dao": {"datum": "W", "precision": "none"}},
             "diagnostics": ["warning:dao-with-ambiguity"]},
  "strict": {"rejected_by": "dao-with-ambiguity"}, "reencode": "refused", "reencode_refusal": "field-not-allowed"},
]
if __name__ == '__main__': add('position.json', pos)

wx = [
 {"id": "weather/dao-on-ambiguity-is-met-before-the-weather-comment",
  "description": "A weather report with comment text and then a !DAO! on an ambiguous position: the !DAO! is lifted out before the text left is judged, so a strict decoder rejects it by dao-with-ambiguity, not weather-comment.",
  "source": "differential fuzzing 2026-11-13", "authority": "interpretation", "interpretations": ["a-packet-is-read-in-order"],
  "input": {"info": "!49  .  N/072  .  W_090/010g015t077 hello!W12!"},
  "expect": {"data": {"type": "position", "latitude": 49.5, "longitude": -72.5, "ambiguity": 4, "symbol": "/_", "dao": {"datum": "W", "precision": "thousandths"},
                      "weather": {"wind_direction_degrees": 90, "wind_speed_mph": 10, "wind_gust_mph": 15, "temperature_f": 77}, "comment": "hello"},
             "diagnostics": ["warning:dao-with-ambiguity", "warning:weather-comment"]},
  "strict": {"rejected_by": "dao-with-ambiguity"}, "reencode": "refused", "reencode_refusal": "field-not-allowed"},
]
if __name__ == '__main__': add('weather-telemetry.json', wx)

TP = ["third-party-packets-nest-at-most-four-deep"]
def nest(n, inner=">hi"):
    return "N0CALL>APZ001:" + "}A>B:" * n + inner
def nested_data(levels, innermost):
    d = innermost
    for _ in range(levels):
        d = {"type": "third-party", "packet": dict(d)}
    return d
def packet(data=None, diagnostics=None):
    p = {"source": "A", "destination": "B", "data": data}
    if diagnostics: p["diagnostics"] = diagnostics
    return p
# Build expected: outer data is third-party whose packet is P1; P_k data is third-party(P_{k+1}) ...
def chain(levels, last_packet):
    p = last_packet
    for _ in range(levels - 1):
        p = packet({"type": "third-party", "packet": p})
    return {"type": "third-party", "packet": p}
four = chain(4, packet({"type": "status", "text": "hi"}))
over = chain(4, packet({"type": "unrecognized", "reason": "malformed"}, ["error:invalid-third-party"]))
third = [
 {"id": "third-party/nested-four-deep",
  "description": "Third-party packets nested four deep, the most a decoder reads: every level is decoded.",
  "source": "APRS12c ch. 17", "authority": "interpretation", "interpretations": TP,
  "input": {"tnc2": nest(4)}, "expect": {"header": {"source": "N0CALL", "destination": "APZ001"}, "data": four},
  "strict": "same", "reencode": "identical"},
 {"id": "third-party/nested-five-deep",
  "description": "A fifth third-party level is not read: the packet holding it is invalid-third-party, an error, and its information field stays as received.",
  "source": "APRS12c ch. 17", "authority": "interpretation", "interpretations": TP,
  "input": {"tnc2": nest(5)}, "expect": {"header": {"source": "N0CALL", "destination": "APZ001"}, "data": over},
  "strict": "same", "reencode": "identical"},
 {"id": "third-party/nested-2000-deep",
  "description": "2000 nested third-party headers decode as five do, with no recursion or memory beyond the fifth level.",
  "source": "differential fuzzing 2026-11-13", "authority": "interpretation", "interpretations": TP,
  "input": {"tnc2": nest(2000)}, "expect": {"header": {"source": "N0CALL", "destination": "APZ001"}, "data": over},
  "strict": "same", "reencode": "identical"},
]
if __name__ == '__main__': add('status-other.json', third)

AXI = ["an-ax25-address-is-letters-and-digits"]
def axcase(name, desc, frame):
    return {"id": "envelope/" + name, "description": desc, "source": "AX.25 2.2 section 3.12", "authority": "interpretation",
            "interpretations": AXI, "input": {"ax25_hex": frame}, "expect": {"header_error": ["error:invalid-address"]}, "strict": "same"}
ax = [
 axcase("ax25-comma-in-the-source", "An AX.25 source call holding a comma, which would end it in TNC2 text: invalid-address, and the header is unusable.", ax25("APZ001", "N0,CAL", [], b">x")),
 axcase("ax25-greater-than-in-the-destination", "An AX.25 destination holding >, which would end it in TNC2 text: invalid-address.", ax25("AP>Z01", "N0CALL", [], b">x")),
 axcase("ax25-colon-in-a-digipeater", "An AX.25 digipeater call holding :, which would end the TNC2 header early: invalid-address.", ax25("APZ001", "N0CALL", ["WI:DE1"], b">x")),
 axcase("ax25-asterisk-in-a-digipeater", "An AX.25 digipeater call holding *, which TNC2 text reads as the used marker: invalid-address.", ax25("APZ001", "N0CALL", ["AC*X"], b">x")),
 axcase("ax25-hyphen-in-the-source", "An AX.25 source call holding -, which TNC2 text reads as the start of the SSID: invalid-address.", ax25("APZ001", "N0-CAL", [], b">x")),
 axcase("ax25-space-inside-the-source", "An AX.25 source call with a space before its last character: spaces only pad a call at the end, so invalid-address.", ax25("APZ001", "N0 CAL", [], b">x")),
 axcase("ax25-control-character-in-the-source", "An AX.25 source call holding a control character: invalid-address.", ax25("APZ001", "N0\x01CAL", [], b">x")),
]
if __name__ == '__main__': add('envelope.json', ax)
print('added')
