#!/usr/bin/env python3
"""Makes data in the neutral form, or builder recipes, for comparing implementations' encoders and
builders (see the README, "Comparing implementations").

  python3 tools/generate.py data.jsonl.gz --count 1000000 --seed 1 [--inexact 0.05]
  python3 tools/generate.py recipes.jsonl.gz --recipes --count 1000000 --seed 1

Data: one {"n", "data", "exact"} object per line. The data is recombined from the cases' own
decoded data (so every shape is one a decoder produces): a report takes parts from other reports
of its kind, gets new numbers on the steps its format holds, awkward text, and fields dropped.
With "exact": false (a share of lines set by --inexact), one value lies between the steps its
format holds, so an encoder rounds it.

Recipes: one {"n", "station", "report", "args"} object per line, with values as a program would
have them (a position from a GPS receiver, a speed in km/h) and every input given, the time
included.

The same arguments always give the same lines. Standard library only.
"""

from __future__ import annotations

import argparse
import copy
import glob
import gzip
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(HERE, "..", "cases")

POSITIONED = ("position", "object", "item", "mic-e")

# Text chosen to be awkward: APRS syntax an encoder must not let a comment turn into, bytes that
# are not printable, text that is not ASCII, and lengths at and past the limits.
AWKWARD = [
    "", " ", "  ", "/", "//", " x", "/x", "x ", "x/", "{", "}", "{}", "{55}", "{5}", "{AB}", "{{5}", "|", "||", "|!!!!|", "|!!\"#|",
    "!", "!W12!", "!w8'!", "!S  !", "!1  !", "^", ":", "::", ",", "=", "*", "~", "`", "'", ">", "]", "\\", "#", "$", "%", "&", "@",
    "PHG5132", "PHG51324/", "phg5132", "RNG0050", "DFS2360", "T#", "/A=001234", "/A=-00012", "/A=12", "A=001234",
    "146.520MHz", "146.52 MHz", "146.520MHz T100 +060", " T100", " +060", " R25m", "C107", "444.900MHz",
    "090/013", ".../...", "_", "g005t077", "IO91SX", "IO91SX/G", "$GPRMC", "?APRS?", "?WX", "{12}AB", "}AB",
    "\x00", "\x01", "\x1c", "\x1d", "\x1f", "\x7f", "\r", "\n", "\t", "\xa0", "\xe9", "\xff", "été", "日本語",
    "ü", "€", "\U0001f4e1", "x" * 43, "x" * 67, "x" * 68, "x" * 200, "x" * 600,
]
WORDS = ["Hello", "LoRa iGate", "Digi", "de N0CALL", "73", "QTH", "Net", "WX", "Test 123", "abc", "Radio Club", "mobile"]


class Pool:
    """Every decoded data object in the cases, by type, and their parts."""

    def __init__(self) -> None:
        self.by_type: dict[str, list[dict]] = {}
        self.parts: dict[str, list] = {}
        for path in sorted(glob.glob(os.path.join(CASES, "*.json"))):
            with open(path, encoding="utf-8") as f:
                for case in json.load(f)["cases"]:
                    for d in self._data(case):
                        self.add(d)

    @staticmethod
    def _data(case: dict):
        """Decoded data only: an encode case's input holds values a program chose, not ones a
        format holds."""
        if "encode" in case.get("input", {}):
            return
        expect = case.get("expect", {})
        if "data" in expect:
            yield expect["data"]
        strict = case.get("strict")
        if isinstance(strict, dict) and "data" in strict:
            yield strict["data"]

    def add(self, d: dict) -> None:
        t = d.get("type")
        if not t or t == "unrecognized":
            return
        self.by_type.setdefault(t, []).append(d)
        if t == "third-party" and "data" in d.get("packet", {}):
            self.add(d["packet"]["data"])
        for k, v in d.items():
            if k != "type":
                self.parts.setdefault(f"{t}.{k}", []).append(v)
                if t in POSITIONED:
                    self.parts.setdefault(f"positioned.{k}", []).append(v)
        if isinstance(d.get("weather"), dict):
            for k, v in d["weather"].items():
                self.parts.setdefault(f"weather.{k}", []).append(v)

    def part(self, rng: random.Random, key: str, default=None):
        values = self.parts.get(key)
        return copy.deepcopy(rng.choice(values)) if values else default


def text(rng: random.Random, pool: Pool, key: str, awkward: float = 0.35) -> str:
    """A text value: one from the pool, a word, or an awkward one, sometimes joined."""
    choice = rng.random()
    if choice < awkward:
        base = rng.choice(AWKWARD)
    elif choice < awkward + 0.3:
        base = rng.choice(WORDS)
    else:
        base = pool.part(rng, key, "") or ""
        if not isinstance(base, str):
            base = ""
    if rng.random() < 0.2:
        base = base + rng.choice(AWKWARD) + rng.choice(WORDS)
    if rng.random() < 0.1:
        at = rng.randint(0, len(base))
        base = base[:at] + rng.choice(AWKWARD) + base[at:]
    return base


def tidy(d: dict) -> None:
    """The neutral form leaves empty text out (reply_ack apart), wherever it is."""
    for k in list(d):
        v = d[k]
        if v == "" and k != "reply_ack":
            del d[k]
        elif isinstance(v, dict):
            tidy(v)


# ------------------------------------------------------------------ numbers on their steps


def minutes_grid(rng: random.Random, max_degrees: int) -> tuple[int, float]:
    """Whole degrees and hundredths of a minute, never past max_degrees."""
    degrees = rng.randint(0, max_degrees)
    hundredths = 0 if degrees == max_degrees else rng.randint(0, 5999)
    return degrees, hundredths


def coordinate(rng: random.Random, max_degrees: int, ambiguity: int, dao: dict | None) -> float:
    """A latitude or longitude an uncompressed or Mic-E position holds exactly, positive."""
    degrees, hundredths = minutes_grid(rng, max_degrees)
    if ambiguity:
        if degrees == max_degrees:
            degrees -= 1
        # The centre of the box the blanked digits leave (interpretations.md).
        minutes = hundredths / 100
        step = [0.1, 1, 10, 60][ambiguity - 1]
        minutes = math.floor(minutes / step) * step + step / 2
        return degrees + minutes / 60
    minutes = hundredths / 100
    if dao and degrees < max_degrees:
        if dao.get("precision") == "thousandths":
            minutes += rng.randint(0, 9) / 1000
        elif dao.get("precision") == "base91":
            minutes += rng.randint(0, 90) / 91 / 100
    return degrees + minutes / 60


def signed(rng: random.Random, value: float) -> float:
    return -value if value and rng.random() < 0.5 else value


def compressed_latitude(rng: random.Random) -> float:
    return 90 - rng.randint(0, 380926 * 180) / 380926


def compressed_longitude(rng: random.Random) -> float:
    return -180 + rng.randint(0, 190463 * 360) / 190463


def cs_speed_knots(s: int) -> float:
    return 1.08**s - 1


KNOT_MPH = 1852 / 1609.344


# ------------------------------------------------------------------ data


class DataGen:
    def __init__(self, rng: random.Random, pool: Pool, inexact: float) -> None:
        self.rng = rng
        self.pool = pool
        self.inexact = inexact

    WEIGHTS = {
        "position": 22, "mic-e": 12, "object": 10, "item": 6, "weather": 5, "message": 6, "ack": 2, "reject": 1,
        "bulletin": 3, "nws-bulletin": 1, "telemetry": 4, "telemetry-names": 1, "telemetry-units": 1,
        "telemetry-coefficients": 2, "telemetry-bits": 1, "directed-query": 2, "query": 2, "status": 5,
        "capabilities": 2, "raw-weather": 1, "nmea": 2, "maidenhead-beacon": 1, "third-party": 3,
        "user-defined": 1, "test": 1, "agrelo-df": 1,
    }

    def data(self, depth: int = 0) -> tuple[dict, bool]:
        rng = self.rng
        types = [t for t in self.WEIGHTS if t in self.pool.by_type and (depth == 0 or t not in ("third-party", "mic-e"))]
        t = rng.choices(types, weights=[self.WEIGHTS[x] for x in types])[0]
        d = copy.deepcopy(rng.choice(self.pool.by_type[t]))
        exact = True
        make = getattr(self, "_" + t.replace("-", "_"), None)
        if make is not None:
            exact = make(d) is not False
        if exact and rng.random() < self.inexact:
            exact = not self._nudge(d)
        tidy(d)
        return d, exact

    # --- positioned reports

    def _position(self, d: dict) -> None:
        self._positioned(d)
        if self.rng.random() < 0.3:
            d.pop("timestamp", None) if self.rng.random() < 0.5 else d.__setitem__("timestamp", self._timestamp())
        if self.rng.random() < 0.2:
            d["messaging"] = True
        elif self.rng.random() < 0.2:
            d.pop("messaging", None)

    def _object(self, d: dict) -> None:
        self._positioned(d)
        if self.rng.random() < 0.3:
            d["name"] = self._name(1, 9)
        if self.rng.random() < 0.2:
            d["timestamp"] = self._timestamp()
        if self.rng.random() < 0.1:
            d["killed"] = True

    def _item(self, d: dict) -> None:
        self._positioned(d)
        if self.rng.random() < 0.3:
            d["name"] = self._name(3, 9)
        if self.rng.random() < 0.1:
            d["killed"] = True

    def _mic_e(self, d: dict) -> None:
        rng = self.rng
        self._positioned(d, mic_e=True)
        if rng.random() < 0.3:
            d["speed_knots"] = rng.choice([0, 1, 9, 10, 99, 100, 189, 190, 195, 199, 200, 799, rng.randint(0, 799)])
        if rng.random() < 0.3:
            c = rng.choice([None, 0, 1, 99, 199, 299, 360, rng.randint(0, 360)])
            if c is None:
                d.pop("course_degrees", None)
            else:
                d["course_degrees"] = c
        if rng.random() < 0.3:
            d["altitude_feet"] = rng.randint(-10000, 20000) / 0.3048
        if rng.random() < 0.2:
            d["mic_e_message"] = rng.choice(["off-duty", "en-route", "in-service", "returning", "committed", "special",
                                             "priority", "custom0", "custom3", "custom6", "emergency"])
        for key, choices in (("type_code", ["`", "'", ">", "]", " "]), ("device_suffix", ["_%", "=", "^", "_)", "|3"])):
            if rng.random() < 0.15:
                d.pop(key, None) if rng.random() < 0.4 else d.__setitem__(key, rng.choice(choices))
        if rng.random() < 0.1:
            d["old_data"] = True
        if rng.random() < 0.1:
            d["destination_ssid"] = rng.randint(1, 15)
        if rng.random() < 0.05:
            d["legacy_telemetry"] = [rng.randint(0, 255) for _ in range(rng.choice([2, 5]))]

    def _positioned(self, d: dict, mic_e: bool = False) -> None:
        rng, pool = self.rng, self.pool
        dao_before = json.dumps(d.get("dao"), sort_keys=True)
        # Take parts from other reports, mostly ones the report's symbol and format can carry.
        compressed_now = bool(d.get("compressed"))
        for key in ("phg", "frequency", "telemetry", "dao", "range_miles", "dfs", "area", "df_bearing", "storm", "signpost"):
            if rng.random() < 0.12:
                if rng.random() < 0.4:
                    d.pop(key, None)
                    continue
                value = pool.part(rng, f"positioned.{key}")
                if value is None:
                    continue
                odd = rng.random() < 0.05  # now and then, a part the report cannot carry
                extension = key in ("phg", "range_miles", "dfs", "area", "df_bearing", "storm")
                if not odd:
                    if mic_e and key in ("area", "df_bearing", "storm", "signpost", "dfs"):
                        continue
                    if compressed_now and key in ("phg", "dfs", "area", "df_bearing", "storm"):
                        continue
                    if "weather" in d and key not in ("dao", "telemetry"):
                        continue
                    if extension and any(k in d for k in ("phg", "range_miles", "dfs", "area", "df_bearing", "storm")):
                        continue
                    symbol = {"df_bearing": "/\\", "storm": "\\@", "signpost": "\\m", "area": "\\l"}.get(key)
                    if symbol:
                        d["symbol"] = symbol
                    if key == "range_miles":
                        value = 2 * 1.08 ** rng.randint(0, 90) if compressed_now else rng.randint(0, 9999)
                        if compressed_now:
                            for k in ("course_degrees", "speed_knots"):
                                d.pop(k, None)
                            d["compression"] = d.get("compression") or {"fix": "current", "source": "other", "origin": "software"}
                            if d["compression"].get("source") == "gga":
                                d["compression"]["source"] = "other"
                                d.pop("altitude_feet", None)
                d[key] = value
        if rng.random() < (0.03 if "weather" in d else 0.15):
            d["symbol"] = pool.part(rng, "positioned.symbol", "/>")
        if rng.random() < (0.03 if "weather" in d else 0.5):
            d["comment"] = text(rng, pool, "positioned.comment")
        compressed = bool(d.get("compressed"))
        toggled = False
        if not mic_e and rng.random() < 0.1:
            compressed, toggled = not compressed, True
            if compressed:
                d["compressed"] = True
                d.pop("ambiguity", None)
            else:
                d.pop("compressed", None)
                d.pop("compression", None)
        ambiguity_changed = False
        if not compressed and rng.random() < (0.01 if d.get("dao") else 0.06):
            ambiguity = rng.choice([0, 0, 1, 2, 3, 4])
            ambiguity_changed = ambiguity != d.get("ambiguity", 0)
            if ambiguity:
                d["ambiguity"] = ambiguity
            else:
                d.pop("ambiguity", None)
        # New numbers on the steps the format holds, and always when the format changed.
        dao_changed = json.dumps(d.get("dao"), sort_keys=True) != dao_before
        if toggled or dao_changed or ambiguity_changed or rng.random() < 0.6:
            if compressed:
                d["latitude"], d["longitude"] = compressed_latitude(rng), compressed_longitude(rng)
            else:
                ambiguity, dao = d.get("ambiguity", 0), d.get("dao")
                d["latitude"] = signed(rng, coordinate(rng, 90, ambiguity, dao))
                d["longitude"] = signed(rng, coordinate(rng, 180, ambiguity, dao))
        if compressed:
            self._cs(d, force=toggled)
        elif not mic_e:
            if toggled or (("course_degrees" in d or "speed_knots" in d) and rng.random() < 0.5):
                if "course_degrees" in d or "speed_knots" in d or rng.random() < 0.3:
                    d["course_degrees"] = rng.choice([1, 90, 360, rng.randint(1, 360)])
                    d["speed_knots"] = rng.choice([0, 1, 999, rng.randint(0, 999)])
            if "altitude_feet" in d and (toggled or rng.random() < 0.5):
                d["altitude_feet"] = rng.choice([0, -1, 999999, -99999, rng.randint(-99999, 999999)])
            if "range_miles" in d and (toggled or rng.random() < 0.5):
                d["range_miles"] = rng.randint(0, 9999)
        if "phg" in d and rng.random() < 0.3:
            d["phg"] = {"power": rng.randint(0, 9), "height": rng.randint(0, 9), "gain": rng.randint(0, 9),
                        "directivity": rng.randint(0, 8)}
            if rng.random() < 0.2:
                d["phg"]["beacons_per_hour"] = rng.randint(1, 35)
        if "telemetry" in d and rng.random() < 0.3:
            n = rng.randint(1, 5)
            d["telemetry"] = {"sequence": rng.randint(0, 8280), "analog": [rng.randint(0, 8280) for _ in range(n)]}
            if n == 5 and rng.random() < 0.5:
                d["telemetry"]["digital"] = rng.randint(0, 255)
        if isinstance(d.get("weather"), dict) and (toggled or rng.random() < 0.5):
            d["weather"] = self._wx(positioned=True, compressed=compressed)
            w = d["weather"]
            if compressed and ("wind_direction_degrees" in w or "wind_speed_mph" in w):
                d["compression"] = d.get("compression") or {"fix": "current", "source": "other", "origin": "software"}
                if d["compression"].get("source") == "gga":
                    d["compression"]["source"] = "other"
                for k in ("course_degrees", "speed_knots", "range_miles"):
                    d.pop(k, None)

    def _cs(self, d: dict, force: bool) -> None:
        """A compressed position's cs bytes: a course and speed, a range or a GGA altitude."""
        rng = self.rng
        if isinstance(d.get("weather"), dict) or (not force and rng.random() > 0.3):
            return
        for k in ("course_degrees", "speed_knots", "range_miles"):
            d.pop(k, None)
        if (d.get("compression") or {}).get("source") == "gga":
            d.pop("altitude_feet", None)
        kind = rng.choice(["course", "range", "altitude", "none"])
        compression = d.get("compression") or {"fix": "current", "source": "other", "origin": "software"}
        if kind == "course":
            c = rng.randint(0, 89)
            d["course_degrees"] = c * 4 if c else 360
            d["speed_knots"] = cs_speed_knots(rng.randint(0, 90))
            if compression.get("source") == "gga":
                compression["source"] = "other"
            d["compression"] = compression
        elif kind == "range":
            d["range_miles"] = 2 * 1.08 ** rng.randint(0, 90)
            if compression.get("source") == "gga":
                compression["source"] = "other"
            d["compression"] = compression
        elif kind == "altitude":
            compression["source"] = "gga"
            d["compression"] = compression
            d["altitude_feet"] = 1.002 ** rng.randint(0, 8280)
        else:
            d.pop("compression", None)
        if "altitude_feet" in d and kind != "altitude" and d["altitude_feet"] != int(d["altitude_feet"]):
            d["altitude_feet"] = rng.randint(-99999, 999999)

    # --- weather

    def _wx(self, positioned: bool = False, compressed: bool = False) -> dict:
        rng, pool = self.rng, self.pool
        w: dict = {}
        fields = {
            "wind_direction_degrees": lambda: rng.choice([0, 360, rng.randint(0, 360)]),
            "wind_speed_mph": lambda: rng.choice([0, 999, rng.randint(0, 999)]),
            "wind_gust_mph": lambda: rng.choice([0, 999, rng.randint(0, 999)]),
            "temperature_f": lambda: rng.choice([-99, -1, 0, 999, rng.randint(-99, 999)]),
            "rain_1h_in": lambda: rng.randint(0, 999) / 100,
            "rain_24h_in": lambda: rng.randint(0, 999) / 100,
            "rain_midnight_in": lambda: rng.randint(0, 999) / 100,
            "humidity_percent": lambda: rng.choice([1, 100, rng.randint(1, 100)]),
            "pressure_mbar": lambda: rng.randint(0, 99999) / 10,
            "luminosity_w_m2": lambda: rng.choice([0, 999, 1000, 1999, rng.randint(0, 1999)]),
            "snow_24h_in": lambda: rng.choice([rng.randint(0, 999), rng.randint(1, 99) / 10, rng.randint(1, 99) / 100]),
            "rain_raw": lambda: rng.randint(0, 999),
        }
        for key, make in fields.items():
            if rng.random() < 0.5:
                w[key] = make()
        if compressed and positioned:
            if "wind_direction_degrees" in w or "wind_speed_mph" in w:
                w["wind_direction_degrees"] = rng.randint(0, 89) * 4
                w["wind_speed_mph"] = cs_speed_knots(rng.randint(0, 90)) * KNOT_MPH
        if rng.random() < 0.15:
            w["software"] = pool.part(rng, "weather.software", "w")
            w["unit"] = pool.part(rng, "weather.unit", "RSW")
        if rng.random() < 0.1:
            w["extra"] = pool.part(rng, "weather.extra", [{"letter": "X", "value": "01"}])
        return w

    def _weather_positionless(self, d: dict) -> None:
        rng = self.rng
        if rng.random() < 0.6:
            d["weather"] = self._wx()
        if rng.random() < 0.3:
            d["timestamp"] = f"{rng.randint(1, 12):02d}{rng.randint(1, 31):02d}{rng.randint(0, 23):02d}{rng.randint(0, 59):02d}"
        if rng.random() < 0.3:
            c = text(rng, self.pool, "weather.comment")
            d.pop("comment", None) if not c else d.__setitem__("comment", c)

    _weather = _weather_positionless

    # --- messages

    def _addressee(self) -> str:
        rng = self.rng
        return rng.choice([self._call(), self._call(), "BLN1", "NWS-WARN", "a", "N0CALL-15", "ABCDEFGHI", "A B", "A:B", "\xe9"])

    def _message(self, d: dict) -> None:
        rng = self.rng
        if rng.random() < 0.3:
            d["addressee"] = self._addressee()
        if rng.random() < 0.5:
            d["text"] = text(rng, self.pool, "message.text")
        if rng.random() < 0.3:
            d.pop("message_id", None) if rng.random() < 0.3 else d.__setitem__("message_id", self._msgid())
        if rng.random() < 0.15:
            d.pop("reply_ack", None) if rng.random() < 0.4 else d.__setitem__("reply_ack", rng.choice(["", "AB", "1", "12345", self._msgid()]))
            if "reply_ack" in d and "message_id" not in d:
                d["message_id"] = self._msgid()

    def _msgid(self) -> str:
        rng = self.rng
        return rng.choice(["1", "001", "ABCDE", "a1", "12345", "123456", "AB}", "{", "x y", str(rng.randint(0, 99999))])

    def _ack(self, d: dict) -> None:
        rng = self.rng
        if rng.random() < 0.9:
            d.pop("message_id", None)
        if rng.random() < 0.3:
            d["addressee"] = self._addressee()
        key = "acked_id" if d["type"] == "ack" else "rejected_id"
        if rng.random() < 0.5:
            d[key] = self._msgid()
        if rng.random() < 0.2:
            d.pop("reply_ack", None) if rng.random() < 0.4 else d.__setitem__("reply_ack", rng.choice(["", "AB", "12345"]))

    _reject = _ack

    def _bulletin(self, d: dict) -> None:
        rng = self.rng
        if rng.random() < 0.3:
            ident = rng.choice("0123456789ABCZ")
            group = rng.choice(["", "WX", "GROUP", "12345"]) if ident.isdigit() or rng.random() < 0.05 else ""
            d["addressee"] = "BLN" + ident + group
        if rng.random() < 0.5:
            d["text"] = text(rng, self.pool, "bulletin.text")
        if rng.random() < 0.1:
            d["message_id"] = self._msgid()

    def _nws_bulletin(self, d: dict) -> None:
        if self.rng.random() < 0.5:
            d["text"] = text(self.rng, self.pool, "nws-bulletin.text")

    def _telemetry_names(self, d: dict) -> None:
        rng = self.rng
        key = "names" if d["type"] == "telemetry-names" else "units"
        if rng.random() < 0.6:
            d[key] = [text(rng, self.pool, "x", 0.2)[:12] for _ in range(rng.randint(0, 13))]
            if not d[key]:
                d[key] = [""]

    _telemetry_units = _telemetry_names

    def _telemetry_coefficients(self, d: dict) -> None:
        rng = self.rng
        if rng.random() < 0.6:
            d["coefficients"] = [rng.choice([0, 1, -1, 0.5, 5.2, -32, 1e-3, 1e61, rng.randint(-999, 999), rng.randint(-99999, 99999) / 1000])
                                 for _ in range(rng.choice([3, 6, 9, 12, 15, rng.randint(1, 15)]))]

    def _telemetry_bits(self, d: dict) -> None:
        rng = self.rng
        if rng.random() < 0.5:
            d["bits"] = "".join(rng.choice("01") for _ in range(8))
        if rng.random() < 0.5:
            p = text(rng, self.pool, "telemetry-bits.project")[:rng.choice([23, 24, 40])]
            d.pop("project", None) if not p else d.__setitem__("project", p)

    def _telemetry(self, d: dict) -> None:
        rng = self.rng
        if rng.random() < 0.5 or len(d.get("analog", [])) != 5:
            d["analog"] = [rng.choice([None, 0, 1, 255, 999, 1.5, -1, 0.25, rng.randint(0, 255), rng.randint(0, 99999) / 100]) for _ in range(5)]
        if "bits" not in d and rng.random() < 0.95:
            d["bits"] = "".join(rng.choice("01") for _ in range(8))
        if rng.random() < 0.3:
            d["sequence"] = rng.choice(["000", "1", "999", "MIC", "12345", "A1", str(rng.randint(0, 999)).zfill(3)])
        if rng.random() < 0.3:
            d["bits"] = "".join(rng.choice("01") for _ in range(8))
        if rng.random() < 0.3:
            c = text(rng, self.pool, "telemetry.comment")
            d.pop("comment", None) if not c else d.__setitem__("comment", c)

    def _directed_query(self, d: dict) -> None:
        rng = self.rng
        if rng.random() < 0.5:
            d["query_type"] = rng.choice(["APRSD", "APRSH", "APRSO", "APRSP", "APRSS", "APRST", "PING", "WX", "FOO"])
        if rng.random() < 0.5:
            d.pop("target", None) if rng.random() < 0.3 else d.__setitem__("target", self._call())

    def _query(self, d: dict) -> None:
        rng = self.rng
        if rng.random() < 0.4:
            d["query_type"] = rng.choice(["APRS", "IGATE", "WX"])
        if rng.random() < 0.5:
            if rng.random() < 0.3:
                d.pop("footprint", None)
            else:
                d["footprint"] = {"latitude": rng.choice([0, 34.02, -12.5, 90, rng.randint(-9000, 9000) / 100]),
                                  "longitude": rng.choice([0, -117.15, 179.9, rng.randint(-18000, 18000) / 100]),
                                  "radius_miles": rng.choice([0, 200, 9999, rng.randint(0, 9999)])}

    def _status(self, d: dict) -> None:
        rng = self.rng
        if rng.random() < 0.5:
            t = text(rng, self.pool, "status.text")
            d.pop("text", None) if not t else d.__setitem__("text", t)
        if rng.random() < 0.2:
            if "locator" in d or rng.random() < 0.5:
                d.pop("timestamp", None) if rng.random() < 0.5 else d.__setitem__("timestamp", f"{rng.randint(1, 31):02d}{rng.randint(0, 23):02d}{rng.randint(0, 59):02d}z")
        if rng.random() < 0.1:
            d["beam"] = {"heading_code": rng.choice("0123456789ABCZ"), "power_code": rng.choice("123456789:;<=>?@ABCK")}

    def _capabilities(self, d: dict) -> None:
        rng = self.rng
        if rng.random() < 0.5:
            caps = []
            for _ in range(rng.randint(1, 5)):
                token = rng.choice(["IGATE", "MSG_CNT", "LOC_CNT", "A", "TX"]) if rng.random() < 0.9 else rng.choice(["tok en", "x=y", "", "T,U"])
                value = rng.choice(["1", "43", "a b", "v1.2"]) if rng.random() < 0.9 else rng.choice([" v", "x,y", "", "\x01"])
                caps.append([token] if rng.random() < 0.4 else [token, value])
            d["capabilities"] = caps

    def _maidenhead_beacon(self, d: dict) -> None:
        if self.rng.random() < 0.5:
            c = text(self.rng, self.pool, "maidenhead-beacon.comment")
            d.pop("comment", None) if not c else d.__setitem__("comment", c)

    def _third_party(self, d: dict) -> bool:
        rng = self.rng
        packet = d["packet"]
        packet.pop("diagnostics", None)
        exact = True
        if rng.random() < 0.6:
            inner, exact = self.data(depth=1)
            packet["data"] = inner
        if rng.random() < 0.2:
            packet["source"] = self._call()
        if rng.random() < 0.2:
            packet["path"] = rng.choice([["TCPIP*"], ["WIDE1-1*", "WIDE2-1"], [], ["TCPIP*", "N0CALL-10*"]])
            if not packet["path"]:
                del packet["path"]
        return exact

    def _user_defined(self, d: dict) -> None:
        rng = self.rng
        if rng.random() < 0.5:
            d["data"] = "".join(chr(rng.randint(0, 255)) for _ in range(rng.randint(0, 20)))
            if not d["data"]:
                del d["data"]

    def _agrelo_df(self, d: dict) -> None:
        self.rng.random() < 0.7 and d.update(bearing_degrees=self.rng.randint(0, 360), quality=self.rng.randint(0, 9))

    # --- small things

    def _call(self) -> str:
        rng = self.rng
        base = rng.choice(["N0CALL", "G4ABC", "VK2XYZ", "M0LTE", "W1AW", "DL1ABC"])
        return base + (f"-{rng.randint(1, 15)}" if rng.random() < 0.4 else "")

    def _name(self, lo: int, hi: int) -> str:
        rng = self.rng
        name = rng.choice(["LEADER", "A", "ABC", "REPEATER1", " SPACE", "X Y Z", "147.345", "a*b", "!x!", "\xe9t\xe9",
                           "N0CALL-15", "_", "ABCDEFGHIJ"])
        return name if lo <= len(name) <= hi or rng.random() < 0.2 else name[:hi].ljust(lo, "X")

    def _timestamp(self) -> str:
        rng = self.rng
        kind = rng.choice("zzh/")
        if kind == "h":
            return f"{rng.randint(0, 23):02d}{rng.randint(0, 59):02d}{rng.randint(0, 59):02d}h"
        return f"{rng.randint(1, 31):02d}{rng.randint(0, 23):02d}{rng.randint(0, 59):02d}{kind}"

    # --- values between steps

    def _nudge(self, d: dict) -> bool:
        """Moves one value off the steps its format holds; True if one was moved."""
        rng = self.rng
        candidates = []
        for key in ("latitude", "longitude", "speed_knots", "course_degrees", "altitude_feet", "range_miles"):
            if isinstance(d.get(key), (int, float)) and not isinstance(d.get(key), bool):
                candidates.append((d, key))
        if isinstance(d.get("weather"), dict):
            for key, v in d["weather"].items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    candidates.append((d["weather"], key))
        if not candidates:
            return False
        obj, key = rng.choice(candidates)
        steps = {"latitude": 1 / 6000, "longitude": 1 / 6000, "rain_1h_in": 0.01, "rain_24h_in": 0.01, "rain_midnight_in": 0.01,
                 "pressure_mbar": 0.1, "snow_24h_in": 0.01}
        step = 1 / 380926 if d.get("compressed") and key in ("latitude", "longitude") else steps.get(key, 1)
        obj[key] = obj[key] + step * rng.choice([0.25, 0.4, 0.5, 0.6, 0.75, -0.3])
        return True


# ------------------------------------------------------------------ recipes


class RecipeGen:
    def __init__(self, rng: random.Random, pool: Pool) -> None:
        self.rng = rng
        self.pool = pool

    WEIGHTS = {
        "position": 24, "object": 8, "item": 5, "mic-e": 12, "weather": 8, "message": 8, "ack": 2, "reject": 1,
        "bulletin": 3, "status": 6, "telemetry": 5, "telemetry-names": 1, "telemetry-units": 1,
        "telemetry-coefficients": 1, "telemetry-bits": 1,
    }

    def recipe(self) -> dict:
        rng = self.rng
        report = rng.choices(list(self.WEIGHTS), weights=list(self.WEIGHTS.values()))[0]
        station = {"source": rng.choice(["N0CALL", "G4ABC-9", "M0LTE-7", "VK2XYZ-15", "W1AW"])}
        if rng.random() < 0.3:
            station["destination"] = rng.choice(["APZ001", "APRS", "APZXYZ"])
        if rng.random() < 0.5:
            station["path"] = rng.choice([["WIDE1-1"], ["WIDE1-1", "WIDE2-1"], ["WIDE2-2"]])
        args = getattr(self, "_" + report.replace("-", "_"))()
        return {"station": station, "report": report, "args": args}

    def _latlon(self, args: dict) -> None:
        rng = self.rng
        digits = rng.choice([2, 4, 5, 6, 7])
        args["latitude"] = round(rng.uniform(-89.99, 89.99), digits)
        args["longitude"] = round(rng.uniform(-179.99, 179.99), digits)
        if rng.random() < 0.05:
            args["latitude"] = rng.choice([0.0, 90.0, -90.0, 89.99999, 45.0])
            args["longitude"] = rng.choice([0.0, 180.0, -180.0, 179.99999, -0.00001])

    def _timestamp(self, fmt: str | None = None) -> dict:
        rng = self.rng
        day = rng.randint(1, 28)
        return {"utc": f"2026-{rng.randint(1, 12):02d}-{day:02d}T{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}:{rng.randint(0, 59):02d}Z",
                "format": fmt or rng.choice(["dhm", "hms"])}

    def _options(self, args: dict, *, mic_e: bool = False) -> None:
        rng = self.rng
        args["symbol"] = rng.choice(["/>", "/-", "/k", "\\>", "/_", "\\m", "/#", "S#", "3>", "/[", "/l"])
        if rng.random() < 0.4:
            args["course_degrees"] = rng.choice([0, 1, 359, 360, rng.randint(0, 360), round(rng.uniform(0, 360), 1)])
        if rng.random() < 0.4:
            if rng.random() < 0.5:
                args["speed_knots"] = rng.choice([0, 0.4, 12.5, 199.6, round(rng.uniform(0, 300), rng.choice([0, 1, 2]))])
            else:
                args["speed_kmh"] = rng.choice([0, 1, 100, round(rng.uniform(0, 400), rng.choice([0, 1, 2]))])
        if rng.random() < 0.3:
            if rng.random() < 0.5:
                args["altitude_feet"] = rng.choice([0, -12.5, 100.5, round(rng.uniform(-1000, 60000), 1)])
            else:
                args["altitude_m"] = rng.choice([0, 30.48, round(rng.uniform(-300, 20000), 1)])
        if rng.random() < 0.5:
            args["comment"] = text(rng, self.pool, "positioned.comment", 0.25)
        if rng.random() < 0.15 and not mic_e:
            args["phg"] = {"power": rng.randint(0, 9), "height": rng.randint(0, 9), "gain": rng.randint(0, 9), "directivity": rng.randint(0, 8)}
        if rng.random() < 0.1 and not mic_e:
            args["range_miles"] = rng.choice([0, 1.5, 10, 25.3, 9999])
        if rng.random() < 0.15:
            f = {"mhz": rng.choice([146.52, 145.5, 438.8, 144.39, round(rng.uniform(28, 999), 3)])}
            if rng.random() < 0.4:
                f["tone"] = rng.choice(["tone", "ctcss", "dcs"])
                f["tone_value"] = rng.choice([67, 100, 107, 123, 254])
            if rng.random() < 0.3:
                f["offset_khz"] = rng.choice([-600, 600, -7600, 5000, 0])
            args["frequency"] = f
        if rng.random() < 0.15 and not mic_e:
            args["compressed"] = True
        if rng.random() < 0.15:
            args["ambiguity"] = rng.randint(1, 4)
        if rng.random() < 0.1:
            args["dao"] = True
        if rng.random() < 0.1:
            n = rng.randint(1, 5)
            args["telemetry"] = {"sequence": rng.randint(0, 8280), "analog": [rng.randint(0, 8280) for _ in range(n)]}
            if n == 5 and rng.random() < 0.5:
                args["telemetry"]["digital"] = rng.randint(0, 255)

    def _position(self) -> dict:
        args: dict = {}
        self._latlon(args)
        self._options(args)
        if self.rng.random() < 0.3:
            args["messaging"] = True
        if self.rng.random() < 0.3:
            args["timestamp"] = self._timestamp()
        return args

    def _object(self) -> dict:
        args = {"name": self.rng.choice(["LEADER", "REPEATER1", "A", "ABC", "147.345", "NINECHARS", "TOOLONGNAME"])}
        self._latlon(args)
        self._options(args)
        args["timestamp"] = self._timestamp()
        if self.rng.random() < 0.1:
            args["killed"] = True
        return args

    def _item(self) -> dict:
        args = {"name": self.rng.choice(["LEADER", "ABC", "AB", "NINECHARS", "TOOLONGNAME", "X Y"])}
        self._latlon(args)
        self._options(args)
        if self.rng.random() < 0.1:
            args["killed"] = True
        return args

    def _mic_e(self) -> dict:
        args: dict = {}
        self._latlon(args)
        self._options(args, mic_e=True)
        args["mic_e_message"] = self.rng.choice(["off-duty", "en-route", "in-service", "returning", "committed", "special", "priority", "emergency"])
        if self.rng.random() < 0.5:
            args["messaging"] = True
        return args

    def _weather(self) -> dict:
        rng = self.rng
        args: dict = {}
        if rng.random() < 0.5:
            self._latlon(args)
            args["symbol"] = rng.choice(["/_", "\\_"])
            if rng.random() < 0.3:
                args["timestamp"] = self._timestamp()
        else:
            args["timestamp"] = self._timestamp("mdhm")
        values = {
            "wind_direction_degrees": lambda: rng.choice([0, 360, rng.randint(0, 360), round(rng.uniform(0, 360), 1)]),
            "wind_speed_mph": lambda: rng.choice([0, 2.5, round(rng.uniform(0, 120), 1)]),
            "wind_gust_mph": lambda: rng.choice([0, 3.5, round(rng.uniform(0, 150), 1)]),
            "rain_1h_in": lambda: rng.choice([0, 0.005, round(rng.uniform(0, 5), 3)]),
            "rain_24h_in": lambda: round(rng.uniform(0, 10), 3),
            "rain_midnight_in": lambda: round(rng.uniform(0, 10), 3),
            "humidity_percent": lambda: rng.choice([0, 1, 100, 100.4, round(rng.uniform(0, 100), 1)]),
            "pressure_mbar": lambda: rng.choice([1013.25, 999.95, round(rng.uniform(900, 1100), 2)]),
            "luminosity_w_m2": lambda: rng.choice([0, 999, 1000, 1999, round(rng.uniform(0, 1999), 1)]),
            "snow_24h_in": lambda: rng.choice([0, 0.5, 0.25, 2.5, 12.5, round(rng.uniform(0, 50), 2)]),
        }
        for key, make in values.items():
            if rng.random() < 0.5:
                args[key] = make()
        if rng.random() < 0.6:
            if rng.random() < 0.5:
                args["temperature_f"] = rng.choice([-40, 0, 32, 77.5, round(rng.uniform(-60, 130), 1)])
            else:
                args["temperature_c"] = rng.choice([-40, 0, 25, 21.3, round(rng.uniform(-50, 55), 1)])
        if rng.random() < 0.2:
            for key in ("rain_1h_in", "rain_24h_in", "rain_midnight_in"):
                if key in args:
                    args[key.replace("_in", "_mm")] = round(args.pop(key) * 25.4, 1)
        return args

    def _message(self) -> dict:
        rng = self.rng
        args = {"addressee": rng.choice(["N0CALL", "G4ABC-9", "VK2XYZ-15", "ABCDEFGHI", "TOOLONGCALL"]), "text": text(rng, self.pool, "message.text", 0.25)}
        if rng.random() < 0.5:
            args["message_id"] = rng.choice(["1", "001", "ABCDE", "123456", str(rng.randint(0, 99999))])
        if rng.random() < 0.1:
            args["reply_ack"] = rng.choice(["", "AB"])
        return args

    def _ack(self) -> dict:
        return {"addressee": self.rng.choice(["N0CALL", "G4ABC-9"]), "message_id": self.rng.choice(["1", "001", "ABCDE", "123456"])}

    _reject = _ack

    def _bulletin(self) -> dict:
        rng = self.rng
        args = {"id": rng.choice("0123456789ABCZ"), "text": text(rng, self.pool, "bulletin.text", 0.25)}
        if rng.random() < 0.3:
            args["group"] = rng.choice(["WX", "GROUP", "TOOLONG"])
        return args

    def _status(self) -> dict:
        rng = self.rng
        args: dict = {"text": text(rng, self.pool, "status.text", 0.25)}
        if rng.random() < 0.3:
            args["timestamp"] = self._timestamp("dhm")
        if rng.random() < 0.2:
            args["locator"] = rng.choice(["IO91", "IO91SX", "FN20XR", "io91sx"])
            args["symbol"] = rng.choice(["/-", "/>"])
        if rng.random() < 0.1:
            args["beam"] = {"heading_code": rng.choice("0123456789ABCZ"), "power_code": rng.choice("123456789ABCK")}
        return args

    def _telemetry(self) -> dict:
        rng = self.rng
        args = {"sequence": rng.choice([0, 1, 999, 1000, rng.randint(0, 999)]),
                "analog": [rng.choice([None, 0, 1, 255, 12.5, 999, rng.randint(0, 255), round(rng.uniform(0, 1000), 2)]) for _ in range(5)],
                "bits": "".join(rng.choice("01") for _ in range(8))}
        if rng.random() < 0.3:
            args["comment"] = text(rng, self.pool, "telemetry.comment", 0.25)
        return args

    def _telemetry_names(self) -> dict:
        rng = self.rng
        return {"names": [rng.choice(["Vin", "Temp", "Rx", "A5", "LongerName", "", "a,b"]) for _ in range(rng.randint(1, 13))]}

    def _telemetry_units(self) -> dict:
        rng = self.rng
        return {"units": [rng.choice(["V", "deg.F", "dBm", "", "%"]) for _ in range(rng.randint(1, 13))]}

    def _telemetry_coefficients(self) -> dict:
        rng = self.rng
        return {"coefficients": [rng.choice([0, 1, 0.5, -32, 5.2, 1e-4, round(rng.uniform(-100, 100), 3)]) for _ in range(15)]}

    def _telemetry_bits(self) -> dict:
        rng = self.rng
        args = {"bits": "".join(rng.choice("01") for _ in range(8))}
        if rng.random() < 0.7:
            args["project"] = rng.choice(["Balloon", "N0QBF's Big Balloon", "x" * 23, "x" * 24])
        return args


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out")
    ap.add_argument("--recipes", action="store_true", help="builder recipes instead of data")
    ap.add_argument("--count", type=int, default=1_000_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--inexact", type=float, default=0.05, help="share of data lines with a value between steps")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    pool = Pool()
    gen = RecipeGen(rng, pool) if args.recipes else DataGen(rng, pool, args.inexact)
    with gzip.open(args.out, "wt", encoding="utf-8", compresslevel=6) as out:
        for n in range(args.count):
            if args.recipes:
                record = {"n": n, **gen.recipe()}
            else:
                data, exact = gen.data()
                record = {"n": n, "data": data, "exact": exact}
            out.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            out.write("\n")
    kind = "recipes" if args.recipes else "data objects"
    print(f"{args.out}: {args.count:,} {kind}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
