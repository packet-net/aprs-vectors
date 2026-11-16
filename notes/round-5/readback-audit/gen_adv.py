"""Adversarial encode data and build recipes: element-like text in every text field."""
import sys, random, json, gzip, copy
sys.path.insert(0, "/home/tf/src/aprs-r4/aprs-vectors/tools")
import generate as g

EL = [
 # message forms
 "ack1", "ackAB", "rej12", "ack1}AB", "rejAB}12", "ack", "rej", "{1", "{12345", "{AB}CD", "{1}", "}AB", "x{1", "a{12}34", "{", "{{", "}{",
 "PARM.A,B", "UNIT.V,A", "EQNS.0,1,0", "BITS.11111111,proj", "PARM.", "BITS.",
 "?APRSP", "?APRS?", "?PING?", "?WX?", "?IGATE?", "?APRSD", "?", "?APRSS ",
 ":N0CALL   :hi", ":BLN1     :x", "N0CALL   :x",
 # timestamps
 "092345z", "092345/", "123456h", "10092345", "092345z/", "311259z",
 # locators
 "IO91", "IO91SX", "IO91sx", "JO01aa", "IO91SX/G", "IO91SX/G>", "AA00",
 # mic-e
 "!!!}", "\"3r}", "aaa}", "abc}", "`", "'", "_\"", "_)", "_ ", " X", "^", "=", ">", "]", "]=", "_#", "_$", "_%", "_(", "|3", "\"",
 # dao, telemetry
 "!W12!", "!w\"#!", "!S  !", "|!!!!|", "|##$$%%|", "|!!|", "||",
 # weather
 "c000s000g000t077", "r001p002P003h50b10132", "h50", "b10132", "L123", "l123", "#123", "s012", "_090/005", "090/005g010t072",
 "t077", "g005", "c090", "p000", "P000", "r000", "eRSW", "wRSW", "xDvs", "XO1", "F123", "V138", "Z999", "f12", "dU2k", "wU2K",
 # extensions
 "PHG5132", "PHG5132/", "PHG51324/", "RNG0050", "DFS2360", "BRG123/NRQ456", "123/456/789/123", "123/045", "/123/045", ".../...", "000/000",
 "/A=000100", "/A=-00010", "/A=999999",
 "146.520MHz", "146.52MHz", " 146.520MHz", "T100", " T100", "+060", " +060", "C100", " C100", "D023", " D023", "Toff", " Toff", "R25m", " R25m", "1290MHz", "146.520MHz T100 +060",
 "T#001,1,2,3,4,5,00000000", "T#MIC", "T#",
 "$GPGGA,", "$GPRMC,1,2", "!4903.50N/07201.75W-", "@", ";", ")", "<IGATE", "}N0CALL>APRS:test", "{{x", "_10092345", "*", "#", "%",
 "/5L!!<*e7>7P[", "{55}", "{5}", "{AB}", "\\", "/", "//", " ", "  ", "x ", " x", "/x", "x/",
 "]Ax", " /", "/ ",
]
WORDS = ["Hello", "73", "Test 123", "abc", "Net"]

def adv_text(rng, *a, **k):
    n = rng.choice([1, 1, 2, 2, 3])
    parts = []
    for _ in range(n):
        if rng.random() < 0.8:
            parts.append(rng.choice(EL))
        else:
            parts.append(rng.choice(WORDS))
    sep = rng.choice(["", "", " ", "/"])
    return sep.join(parts)

def text(rng, pool, key, awkward=0.35):
    return adv_text(rng)

g.text = text

class DG(g.DataGen):
    WEIGHTS = dict(g.DataGen.WEIGHTS)
    WEIGHTS.update({"mic-e": 4, "position": 10, "message": 10, "ack": 4, "reject": 3, "bulletin": 6, "nws-bulletin": 4,
                    "telemetry": 8, "telemetry-names": 4, "telemetry-units": 4, "telemetry-bits": 4, "status": 10,
                    "capabilities": 4, "nmea": 4, "maidenhead-beacon": 4, "third-party": 6, "user-defined": 4, "test": 4,
                    "weather": 10, "raw-weather": 2})

    def _wx(self, positioned=False, compressed=False):
        w = super()._wx(positioned, compressed)
        r = self.rng
        if r.random() < 0.6:
            w["software"] = r.choice(["w", "e", "x", "d", "#", "h", "b", "1", "t", "g", "c", "s", "P", "p", "r", "L", "l", "_", " ", "/"])
            w["unit"] = r.choice(["RSW", "U2k", "Dvs", "h50", "b1013", "t07", "g00", "50", "1", "12", "1234", "c000", "AB", "s00", "L12", "}", "|!", "/A=", " a"])
        return w

    def _weather_positionless(self, d):
        super()._weather_positionless(d)
        if self.rng.random() < 0.6:
            d["comment"] = adv_text(self.rng)
    _weather = _weather_positionless

    def _test(self, d):
        d["data"] = adv_text(self.rng)

    def _user_defined(self, d):
        r = self.rng
        d["user_id"] = r.choice(["{", "}", "A", "Q", "!", "'", "x"])
        d["packet_type"] = r.choice(["{", "}", "A", "x", "1", "!"])
        d["data"] = adv_text(r)

    def _nmea(self, d):
        r = self.rng
        if r.random() < 0.5 and d.get("has_checksum"):
            d["comment"] = adv_text(r)

    def _maidenhead_beacon(self, d):
        d["comment"] = adv_text(self.rng)

    def _capabilities(self, d):
        r = self.rng
        caps = []
        for _ in range(r.randint(1, 4)):
            tok = r.choice(["IGATE", "MSG_CNT", "A", "?", "{1", "ack1", ":x", "PHG5132", "T#", "x"])
            val = r.choice(["1", "43", "{1", "ack1", "?APRS?", "|!!!!|", "/A=000100", "T100", "146.520MHz", "a b"])
            caps.append([tok] if r.random() < 0.3 else [tok, val])
        d["capabilities"] = caps

    def _status(self, d):
        super()._status(d)
        if self.rng.random() < 0.7:
            d["text"] = adv_text(self.rng)

    def _telemetry(self, d):
        super()._telemetry(d)
        if self.rng.random() < 0.7:
            d["comment"] = adv_text(self.rng)

    def _positioned(self, d, mic_e=False):
        super()._positioned(d, mic_e)
        if self.rng.random() < 0.85:
            d["comment"] = adv_text(self.rng)


def main():
    out, count, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    recipes = len(sys.argv) > 4 and sys.argv[4] == "--recipes"
    rng = random.Random(seed)
    pool = g.Pool()
    gen = g.RecipeGen(rng, pool) if recipes else DG(rng, pool, 0.0)
    with gzip.open(out, "wt", encoding="utf-8") as f:
        for n in range(count):
            if recipes:
                rec = {"n": n, **gen.recipe()}
            else:
                data, exact = gen.data()
                rec = {"n": n, "data": data, "exact": exact}
            f.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")

main()
