# Round 5 six-way run: triage of the join ruling

Runs: /tmp/r4run/s10101 and /tmp/r4run/s10202, libraries and vectors on `round-5` (vectors 8ce4dac). Libraries: #1 aprs-cs, #2 aprs-rs, #3 aprs-py, #4 aprs-ts, #5 aprs-c, #6 aprs-go. "Line n" below is the number compare.py prints, the dump's 0-based `n` (so `zcat set.hex.gz | sed -n "$((n+1))p"` gives the input). Every verdict is by the rule text (README "Rules the cases rely on", interpretations.md) and the existing cases, not by count. Probes of my own were run on all six with the built dump tools (inputs and outputs under /tmp/r5-triage/in and /tmp/r5-triage/out).

Summary: aprs-cs, aprs-rs and aprs-ts are right everywhere. aprs-go has one decoder bug (it reads a frequency field across a lifted `!DAO!`, telemetry or late extension) and sits on the losing side of one rule gap (a field whose space stands before a `/A=`); every go written and strict difference follows from its decode. aprs-c has one encoder bug with two faces (it judges whether free text after a frequency would read as a field without looking at what it wrote in between) and is on the losing side of one gap. aprs-py is on the losing side of one gap (a delimiter, then a lifted element, then a frequency). The writers' four reported choices: all six chose the same in each; one is decided by the text, three are gaps (wording proposed).

## 1. Buckets

Counts are s10101 / s10202. "Majority" is #1+#2+#3+#4 plus whichever of #5, #6 is not alone.

| Set | Count | Split | Example input (line) | Deciding rule | Verdict |
|---|---|---|---|---|---|
| comments | 341 / 353 | position lenient.data: 1-5 \| 6 | s10101 307 `!4903.50N/07201.75W>146.52 MHz !W12!C107/A=-00016 R25m` | Comments: "nothing is read across the place it came from"; interpretations [Lifting an element never joins](interpretations.md#lifting-an-element-never-joins-the-text-either-side-of-it): "A `!DAO!` or base-91 telemetry between a frequency and its fields does cut them off" | Majority right in about two thirds (go reads a field across a lifted `!DAO!`, telemetry, or late PHG/RNG/DFS: bug go-1). The other third (about 146 / 166 lines, e.g. s10101 4013 `146.52 MHz /A=-00016Toff`) is gap G1; recommended: majority |
| comments | 315 / 321 | position strict.data: 1-5 \| 6 | same lines | same | Same as above (strict reads the frequency the same way) |
| comments | 319 / 324 | position written: 1-5 \| 6 | same lines | Encoding: written bytes follow the data | Follows from go's decode; no separate go encoder fault (every go written or strict difference is on a line whose lenient data differs) |
| comments | 181 / 183, 171 / 171, 158 / 162 | object lenient, strict, written: 1-5 \| 6 | s10101 1514 `;SIGN ...m445.950MHz !W12!C107 +500x` | as above | as above (go-1 and G1) |
| comments | 73 / 64 | position written: 1-4,6 \| 5 | s10101 1297 `!...>146.520MHz T100 +/A=000100500` (data: tone 100, alt 100, comment `+500`) | Encoding: "When a space after a voice frequency would make the comment read as one of its fields, the comment is written straight after it"; "A delimiter ... is written before a comment only where the comment would not read back as itself without one"; case `position/tone-split-by-an-altitude-is-text` (canonical `146.520MHz/A=000100T100 x`) | c writes `T100/A=000100 /+500`, the others `T100/A=000100+500`. Gap G3 (the text does not say it for a frequency with fields); recommended: majority (bug c-1, conditional) |
| comments | 111 / 132 | object written: 1-4,6 \| 5 | s10101 3894 `;SIGN ...m445.950MHz!W12! -060{55}` (data: freq, signpost 55, comment `-060`) | interpretations [Where a voice frequency goes](interpretations.md#where-a-voice-frequency-goes): "the free text (after a space when a frequency or its fields come before it)"; Comments: braces are lifted and cut; case `object/signpost-frequency-and-altitude` (canonical `146.520MHz{55}/A=000100 Hello`); Encoding delimiter sentence | c wrong: after braces it writes `{55}-060` (no space) or `T103{AB} /R20k` (a needless `/`). Bug c-2. Lines with fields and a `/A=` here are c-1 |
| comments | 23 / 21, 22 / 29 | object, position written: 1-4 \| 5 \| 6 | s10101 1988 `!...>|!!!!|146.52 MHz t077 /A=-00016+500` | as for G1 and c-1 | Majority right: go differs by its decode (G1), c by c-1 |
| fuzz | 1 / 2, 1 / 1 | position written and reencode: 1-4,6 \| 5 | s10101 41977 `!...>146.520MHz T100/A=000100-181 x` | as c-1 | c-1 (c says `equivalent` where the bytes re-encode `identical`) |
| fuzz | 1 / 4, 1 / 4 | mic-e lenient.data and reencode: 1,2,4,5,6 \| 3 | s10202 130533 `` `/Xg\x7f:O>O>/"5o}438.900MHz T077 -760 Kamil `` (status text `>/"5o}438.900MHz...`) | Comments: "a voice frequency at the start, after at most one space or `/`"; "the comment's leading space or `/` ... judged on the text left"; IMPLEMENT.md item 2 "The frequency is still read at the start of the text left" | Gap G2 (the delimiter before a frequency is not in the list of things judged on the text left); recommended: majority. py does not read the frequency |
| data | 4 / 5 | object, item, position info: 1-4,6 \| 5 | s10101 34350 item, freq 147.345, signpost `5`, comment `C107` | as c-2 | c wrong (c-2): `{5}C107` for `{5} C107`, `T103{AB} /R20k` for `T103{AB} R20k` |

Not differences but checked: aprs-ts's comments dump differs from the others only below 1e-9 (compare.py agrees: no ts bucket).

## 2. Fix lists

### aprs-go

1. **A frequency field is read across a lifted element that stands between its space and its value.** Cause: `frequencyAt` in comment.go, the `field` closure: it checks `t.cut[start+at]&^cutAltitude != 0` (a lift before the space) and `t.whole(start+at+1, start+at+5)`, but `whole(from, to)` only looks at `cut[from+1 .. to-1]`, so a lift recorded at `start+at+1` (between the space and the first value byte) is never seen. A `!DAO!`, telemetry, braces or a late PHG/RNG/DFS lifted there joins the space to the value. Fix: test `t.whole(start+at, start+at+5)` (the space and four bytes as one run), keeping the existing allowance for a lifted `/A=` before the space. This one change also gives the recommended answer to gap G1 below. Rule: Comments, "nothing is read across the place it came from"; interpretations, "A `!DAO!` or base-91 telemetry between a frequency and its fields does cut them off". Inputs:
   - comments s10101 line 307 `!4903.50N/07201.75W>146.52 MHz !W12!C107/A=-00016 R25m`: frequency 146.52 (ten_khz_resolution), no tone or range, altitude -16, dao W thousandths, comment `C107 R25m`; re-encodes `equivalent` as `!4903.50N/07201.75W>146.52 MHz/A=-00016C107 R25m!W12!`.
   - comments s10101 line 705 `!4903.50N/07201.75W>/A=-00016146.52 MHz |!:&0'p|C107 Toff`: frequency 146.52 (ten_khz_resolution) with no tone, telemetry seq 25 analog [470, 625], altitude -16, comment `C107 Toff`; written `!4903.50N/07201.75W>146.52 MHz/A=-00016C107 Toff|!:&0'p|`.
   - comments s10202 line 454 `!4903.50N/07201.75W>445.950MHz |!!!!|R25m/A=000100`: frequency 445.95 with no range, telemetry seq 0 analog [0], altitude 100, comment `R25m`; written `!4903.50N/07201.75W>445.950MHz/A=000100R25m|!!!!|`.
2. **(Gap G1, recommended answer.)** A field whose space stands before a `/A=` and whose value comes straight after it is read as a field. Same place in `frequencyAt`; fixed by item 1. Inputs:
   - comments s10101 line 4013 `!4903.50N/07201.75W>146.52 MHz /A=-00016Toff`: no tone, comment `Toff`, altitude -16; written `!4903.50N/07201.75W>146.52 MHz/A=-00016Toff`.
   - comments s10101 line 3682 `!4903.50N/07201.75W>146.520MHz /A=-00016-060 R25m`: frequency 146.52 alone, comment `-060 R25m`; written `!4903.50N/07201.75W>146.520MHz/A=-00016-060 R25m`.
   - comments s10202 line 185 `!4903.50N/07201.75W>146.520MHz /A=000100t077 R25mhello`: frequency 146.52 alone, comment `t077 R25mhello`; written `!4903.50N/07201.75W>146.520MHz/A=000100t077 R25mhello`.

### aprs-c

1. **(Gap G3, recommended answer.) Free text that would read as a later field, after a frequency with fields and a `/A=`, gets ` /` where nothing is needed.** Cause: `put_comment_part` in src/encode.c, the `if (n > 0 && !slash && starts_freq_field(c, n) > last)` branch: with `last` > 0 it writes a space and sets `slash`, without knowing that the caller (`encode` positioned path, around line 1441) has already written a `/A=` after the fields. Bytes straight after a lifted `/A=` with no space cannot be a field, so the comment reads back as itself written straight on. Fix: pass in whether a `/A=` was the last thing written after the frequency (and nothing else); if so, write the comment straight on, with neither space nor `/`. Rule: Encoding, "When a space after a voice frequency would make the comment read as one of its fields, the comment is written straight after it" and "A delimiter ... is written before a comment only where the comment would not read back as itself without one"; the case `position/tone-split-by-an-altitude-is-text` already has this form without fields. Inputs:
   - fuzz s10101 line 41977 `!4903.50N/07201.75W>146.520MHz T100/A=000100-181 x`: re-encodes `identical` (c gives `equivalent`, writing `...T100/A=000100 /-181 x`).
   - comments s10101 line 1297 `!4903.50N/07201.75W>146.520MHz T100 +/A=000100500`: data tone 100, altitude 100, comment `+500`; written `!4903.50N/07201.75W>146.520MHz T100/A=000100+500`.
   - fuzz s10202 line 5508 `=4701.42N/12254.21W>240/059/146.820MHz/A=-00016 T103  -060 73!`: data tone 103, altitude -16, comment `-060 73!`; written `=4701.42N/12254.21W>240/059/146.820MHz T103/A=-00016-060 73!`.
2. **Free text after a frequency and braces is judged as if it followed the frequency directly.** Cause: the same branch in `put_comment_part` ignores the braces the caller wrote (signpost at line ~1416, corridor at ~1430). Braces are lifted elements that cut the frequency off from what follows, so after them a space never makes the comment a field. Two symptoms: with no fields, c writes the text straight after the braces (`{55}-060`) where the rule wants the space; with fields, it writes ` /` where a space alone reads back. Fix: when braces were written after the frequency, take the ordinary path (one space, then the comment, with a `/` only for a comment that itself starts with a space or `/`). Rule: interpretations, "Where a voice frequency goes": "the free text (after a space when a frequency or its fields come before it)"; the Encoding delimiter sentence; case `object/signpost-frequency-and-altitude` (canonical `146.520MHz{55}/A=000100 Hello`). Inputs:
   - data s10101 line 34350 (item `147.345+`, PHG 4480, frequency 147.345, signpost `5`, comment `C107`): info `)147.345+!5133.39N\11220.22WmPHG4480/147.345MHz{5} C107`.
   - data s10202 line 19845 (object `A`, frequency 432.5 tone T103, signpost `AB`, comment `R20k (Reteaua RoLink) http://www.439100.ro`, compressed): info as aprs-cs writes it, `...432.500MHz T103{AB} R20k (Reteaua RoLink)...` (no `/`).
   - comments s10101 line 3894 `;SIGN     *092345z4903.50N\07201.75Wm445.950MHz!W12! -060{55}`: written `;SIGN     *092345z4903.50N\07201.75Wm445.950MHz{55} -060!W12!`.

### aprs-py

1. **(Gap G2, recommended answer.) A frequency after the comment's one delimiter and a lifted element is not read.** Cause: `_frequency` in src/pdn_aprs/_comment.py takes the first non-empty fragment and looks for the delimiter and the frequency inside that one fragment (`text = texts[first]; start = 1 if text[:1] in (" ", "/") else 0`). When that fragment is only the delimiter (` ` or `/`) and the frequency starts the next non-empty fragment, it gives up. Fix: if the first non-empty fragment is exactly one space or `/`, look for the frequency at offset 0 of the next non-empty fragment (and drop the delimiter with it via `dropped_to`). The frequency itself must still stand whole in one fragment. Rule: Comments, "a voice frequency at the start, after at most one space or `/`" with "the comment's leading space or `/` ... judged on the text left"; IMPLEMENT.md item 2. Inputs:
   - fuzz s10202 line 130533 `` SQ7KRJ-9>UQST53:`/Xg\x7f:O>O>/"5o}438.900MHz T077 -760 Kamil ``: frequency 438.9, tone T077, offset -7600, comment `Kamil`, altitude 587.270341 (warning `mic-e-altitude-not-first`); re-encodes `equivalent`.
   - fuzz s10101 line 190948 `` BG2VZP-13>SX5WU1,...:`1ADl H#//"4u}144.640MHz Dalian Jiaofang 11.46V |"w!)$5,!-W| ``: frequency 144.64, comment `Dalian Jiaofang 11.46V `; re-encodes `equivalent`.
   - own probe `!4903.50N/07201.75W>/|!!!!|146.520MHz T100 x`: frequency 146.52 tone 100, telemetry seq 0 analog [0], comment `x`; canonical `!4903.50N/07201.75W>146.520MHz T100 x|!!!!|`.

### aprs-cs, aprs-rs, aprs-ts

Nothing to fix from these runs.

## 3. Rule gaps

### G1. A frequency field whose space stands before a `/A=` (go differs)

Shape: `146.520MHz /A=000100T100 x`, `146.520MHz T100 /A=000100-060 x`. The text gives two answers. For: the README says the `/A=` "between it and its fields ... does not cut them off", and interpretations says the frequency "is read ... as it is without the `/A=`", which, applied to the fields too, gives `146.520MHz T100 x`, a tone. Against: the README says each field needs "a space before", interpretations says a voice frequency's fields are each "contiguous as sent" and quotes ch. 18 "Optional Added fields (with leading space)", which makes the space part of the field, and "one inside a field ... splits it, and the bytes either side are text". IMPLEMENT.md item 2 (what the writers were asked to build) says "with its leading space after it".

What each does: cs, rs, py, ts, c read no field (comment `T100 x`); go reads the tone. All six agree that `146.520MHz /A=000100 T100 x` (a space each side) has no tone: two bytes stand between the frequency and the field.

Recommendation: no field (the majority). A field is a space and its value as one run (ch. 18 says "with leading space"); the spec's exception is about an altitude standing anywhere in the comment, not about re-pairing a field with a space left on the other side of it; interpretations itself calls the exception "a mild stretch; it goes no further". A search of October and November APRS-IS captures (/home/tf/aprs-corpus) found the `/A=` after a frequency only as `MHz/A=dddddd T103` (APRSdroid, about 12,000 packets) and never with the space before the `/A=`, so the choice costs no live packet.

Wording, README Comments, after "does not cut them off": "A field is its space and value together as sent, so a `/A=` may stand before a field's space but not between the space and the value (`146.520MHz /A=000100T100` has no tone)."

### G2. Where the start is, for a voice frequency (py differs)

Two questions. (a) May a lifted element stand before the frequency? The README exception says a `/A=` "before a voice frequency ... does not cut them off", which implies other elements before it do; but the cases `corpus/0493` (`/A=000524|#.!?|433.775Mhz`) and `object/signpost-frequency-and-altitude` (`/A=000100{55}146.520MHz`), IMPLEMENT.md item 2 ("read at the start of the text left once the elements before it are lifted") and all six libraries read it. (b) May the one delimiter stand before a lifted element, with the frequency after it (`/|!!!!|146.520MHz`, Mic-E `/"4e}146.520MHz` after a later altitude)? The README lists three things judged on the text left (a locator's space, the space after a frequency's fields, the comment's leading space or `/`), and the delimiter before a frequency is not named.

What each does: (a) all six read the frequency. (b) cs, rs, ts, c, go read it; py does not.

Recommendation: read it in both. The delimiter before a frequency is the free text's leading delimiter of ch. 18 ("any free text field that begins with either of these two delimiters ... can be ignored"), the same byte the README already judges on the text left; it recognises nothing and only places the frequency. Since the cases already put the start on the text left for (a), judging the delimiter as sent would be the one place a start is judged otherwise.

Wording, README Comments, replacing "and a voice frequency at the start, after at most one space or `/`": "and a voice frequency at the start of the text left, after at most one space or `/` (judged, like the comment's leading delimiter, on the text left)"; and in the exception sentence say "between a voice frequency and its fields, or between two of its fields" (dropping "before a voice frequency", which the start rule already covers).

### G3. Free text that would read as a later field, after fields and a `/A=` (c differs)

Shape: data with frequency and tone, altitude, comment `-060 x`. Options: straight after the `/A=` (`146.520MHz T100/A=000100-060 x`, reads back, and is the received form so `identical`) or a space and `/` (`...T100/A=000100 /-060 x`). The README's "written straight after it" sentence is written for a comment straight after a frequency with no fields; interpretations' "(after a space when a frequency or its fields come before it)" and "takes a `/` after its space where without it it would not read back as itself" read literally give c's form; the README's "A delimiter ... is written before a comment only where the comment would not read back as itself without one" gives the majority's. So the text gives two answers.

What each does: cs, rs, py, ts, go write it straight on; c writes ` /`. Without fields all six already write it straight on (`146.520MHz/A=000100T100 x`, the canonical of `position/tone-split-by-an-altitude-is-text`).

Recommendation: straight on. It is the form the case already pins without fields, the bytes a station like APRSdroid sends, and the shortest that reads back; the space before free text exists to separate it from a field, which the lifted `/A=` already does.

Wording, README Encoding, extending the sentence: "When a space after a voice frequency, or after its fields and a `/A=` written after them, would make the comment read as one of its fields, the comment is written straight after (`445.950MHz-500 T110`, `146.520MHz T100/A=000100-060 x`)."

### W1. The comment's leading delimiter with a lifted element after it (writers' choice 1)

Decided. README Comments: "the comment's leading space or `/` are judged on the text left". `!4903.50N/07201.75W> |!!!!|x` and `/!W12!x` give the comment `x` in all six; ` /A=000100x` gives `x` and altitude 100. No wording needed; a case pins it (section 4).

### W2. A PHGR whose rate byte and `/` are split off by a lift (writers' choice 2)

Two readings. A PHG is seven bytes that stand whole, and a following byte never stops it being one (`PHG23605x` is a PHG and text), so `PHG23605!W12!/x` is the PHG 2360 and the text `5/x`. But if the PHGR (`PHGphgdr/`, ch. 7) is one element, a lift inside it "splits it, and the bytes either side are text" (interpretations), and nothing is a PHG.

What each does: all six read the PHG 2360 and the comment `5/x` (re-encoded `PHG2360/5/x!W12!`); with a `/A=` between (`PHG2360/A=0001005/x`) the same, `identical`.

Recommendation: keep the six's reading. The rate and its `/` are an optional suffix, not part of the PHG's own bytes, and the PHG stands whole. Wording, README Comments, after "PHG and DFS height codes ...": "A PHG's rate byte and `/` (PHGR) count only where they follow its seven bytes as sent; split off by a lifted element, the PHG is read and they are text."

### W3. A weather software type and unit with a lift before or after (writers' choice 3)

Two readings. README Weather: telemetry and a `!DAO!` "are lifted out first ... What is left is the software type and unit if it is a letter then a 2-4 character unit ..., and nothing else", which gives `software x, unit RSW` for `t058!W12!xRSW`. But the run-on clause in the same bullet says text after a lifted element "is comment text on its own", which read generally makes `xRSW` weather-comment text.

What each does: all six: `t058!W12!xRSW`, `t058|!!!!|xRSW`, `t058xRSW!W12!` and `t2147483647!W12!xRSW` give the software type and unit; `t058xR!W12!SW` (split), `t058xRSW!W12! hi` and `t058 !W12!xRSW` give `weather-comment` text.

Recommendation: keep the six's reading: the software type and unit is one element judged whole on what is left, so a lift beside it changes nothing and a lift inside it makes it text. Wording, in the run-on clause: "and text after it is not joined to the run's digits" in place of "and text after it is comment text on its own"; and after "and nothing else": "(judged on the text left; a software type and unit split by a lifted element is text)".

### W4. Two `/A=` altitudes (writers' choice 4)

The text does not say which `/A=` is the altitude when there are two: README "a `/A=` altitude anywhere", interpretations "A `/A=` altitude wins over a Mic-E or compressed one" (about a different pair). And interpretations' "A `/` that begins `/A=` is an altitude, not a delimiter" conflicts with dropping the leading `/` of a second, unlifted one.

What each does: all six lift the first `/A=` that stands whole and keep later ones as text: `/A=000100/A=000200` gives altitude 100 and comment `A=000200` (the `/` dropped as the comment's leading delimiter); `x/A=0001!W12!00 /A=000200 y` gives altitude 200 and comment `x/A=000100  y`; `/A=000100 /A=000200` gives comment `/A=000200`. Each re-encodes `equivalent` (the later one reads back as text behind the first).

Options: first whole one (the six; Ham::APRS::FAP's comment parser takes the first match too, FAP.pm line 1192), last one, or refuse the report as ambiguous. Recommendation: the first that stands whole; later ones are comment text, and the leading-delimiter rule treats their `/` like any other (ch. 18 says a free text field beginning with `/` may be ignored, and only a lifted `/A=` is an altitude). Wording, README Comments: "a `/A=` altitude anywhere (the first that stands whole as sent; a later one is comment text)"; interpretations, Delimiters: "A `/` that begins the `/A=` lifted as the altitude is not a delimiter."

## 4. Cases to add

Values taken from aprs-cs's dump and checked by hand (positions from the bytes, DAO thousandths added to the minutes, Mic-E latitude 33 25.64 N from `S32UVT`, longitude 112 07.74 W, speed 20, course 251, `"4e}` = 78 m = 255.9055 ft). Who fails each today: go fails the first three and both G1 cases; c fails both object cases, the second G1 case (canonical), the G3 case and the encode case; py fails both G2 cases; the W1 to W4 cases and `position/spaces-either-side-of-an-altitude-after-a-frequency` pass in all six. Files: position cases to cases/position.json, object to object-item.json, Mic-E to mic-e.json, weather to weather.json, encode to encode.json. The `interpretations` lists name the existing section; cases for a gap should also name the new wording's anchor once it is written.

```json
{
 "id": "position/tone-after-a-space-and-a-dao-is-text",
 "description": "A !DAO! between a frequency's space and its tone cuts them off: a field's space and value stand together as sent, and only a /A= may stand before the space, so T100 is comment text.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": "!4903.50N/07201.75W>146.520MHz !W12!T100 x"
 },
 "expect": {
  "data": {
   "type": "position",
   "latitude": 49.05835,
   "longitude": -72.0292,
   "symbol": "/>",
   "dao": {
    "datum": "W",
    "precision": "thousandths"
   },
   "frequency": {
    "mhz": 146.52
   },
   "comment": "T100 x"
  }
 },
 "strict": "same",
 "reencode": "equivalent",
 "canonical_info": "!4903.50N/07201.75W>146.520MHzT100 x!W12!"
}
```

```json
{
 "id": "position/tone-after-a-space-and-telemetry-is-text",
 "description": "Base-91 telemetry between a frequency's space and its tone cuts them off, so T100 is comment text.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": "!4903.50N/07201.75W>146.520MHz |!!!!|T100 x"
 },
 "expect": {
  "data": {
   "type": "position",
   "latitude": 49.05833333333333,
   "longitude": -72.02916666666667,
   "symbol": "/>",
   "telemetry": {
    "sequence": 0,
    "analog": [
     0
    ]
   },
   "frequency": {
    "mhz": 146.52
   },
   "comment": "T100 x"
  }
 },
 "strict": "same",
 "reencode": "equivalent",
 "canonical_info": "!4903.50N/07201.75W>146.520MHzT100 x|!!!!|"
}
```

```json
{
 "id": "position/offset-after-a-space-and-a-dao-is-text",
 "description": "A !DAO! between an offset's space and its value cuts the offset off the tone before it, so -060 is comment text, written back after a space and a /.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": "!4903.50N/07201.75W>146.520MHz T100 !W12!-060 x"
 },
 "expect": {
  "data": {
   "type": "position",
   "latitude": 49.05835,
   "longitude": -72.0292,
   "symbol": "/>",
   "dao": {
    "datum": "W",
    "precision": "thousandths"
   },
   "frequency": {
    "mhz": 146.52,
    "tone": "tone",
    "tone_value": 100
   },
   "comment": "-060 x"
  }
 },
 "strict": "same",
 "reencode": "equivalent",
 "canonical_info": "!4903.50N/07201.75W>146.520MHz T100 /-060 x!W12!"
}
```

```json
{
 "id": "object/text-after-a-frequency-and-a-signpost-takes-its-space",
 "description": "Braces cut a frequency off from what follows, so text after them that looks like an offset is written after a space, as free text after a frequency is: re-encodes identical.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": ";SIGN     *092345z4903.50N\\07201.75Wm146.520MHz{55} -060"
 },
 "expect": {
  "data": {
   "type": "object",
   "name": "SIGN",
   "timestamp": "092345z",
   "latitude": 49.05833333333333,
   "longitude": -72.02916666666667,
   "symbol": "\\m",
   "frequency": {
    "mhz": 146.52
   },
   "signpost": "55",
   "comment": "-060"
  }
 },
 "strict": "same",
 "reencode": "identical"
}
```

```json
{
 "id": "object/text-after-a-tone-and-a-signpost-takes-no-slash",
 "description": "Text that looks like a range after a frequency's tone and braces needs no /: the braces already cut it off from the frequency, so a delimiter is not needed and is not written.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": ";SIGN     *092345z4903.50N\\07201.75Wm146.520MHz T100{55} R25m x"
 },
 "expect": {
  "data": {
   "type": "object",
   "name": "SIGN",
   "timestamp": "092345z",
   "latitude": 49.05833333333333,
   "longitude": -72.02916666666667,
   "symbol": "\\m",
   "frequency": {
    "mhz": 146.52,
    "tone": "tone",
    "tone_value": 100
   },
   "signpost": "55",
   "comment": "R25m x"
  }
 },
 "strict": "same",
 "reencode": "identical"
}
```

```json
{
 "id": "position/tone-after-an-altitude-with-its-space-before-the-altitude-is-text",
 "description": "A field's space and value stand together as sent: with the space before the /A= and T100 straight after it, the /A= stands inside the field ( T100) and splits it, so T100 is comment text.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": "!4903.50N/07201.75W>146.520MHz /A=000100T100 x"
 },
 "expect": {
  "data": {
   "type": "position",
   "latitude": 49.05833333333333,
   "longitude": -72.02916666666667,
   "symbol": "/>",
   "altitude_feet": 100,
   "frequency": {
    "mhz": 146.52
   },
   "comment": "T100 x"
  }
 },
 "strict": "same",
 "reencode": "equivalent",
 "canonical_info": "!4903.50N/07201.75W>146.520MHz/A=000100T100 x"
}
```

```json
{
 "id": "position/offset-after-an-altitude-with-its-space-before-the-altitude-is-text",
 "description": "The tone is complete at the space; the offset's value follows a /A= whose space came before it, so -060 is comment text, written back straight after the /A=.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": "!4903.50N/07201.75W>146.520MHz T100 /A=000100-060 x"
 },
 "expect": {
  "data": {
   "type": "position",
   "latitude": 49.05833333333333,
   "longitude": -72.02916666666667,
   "symbol": "/>",
   "altitude_feet": 100,
   "frequency": {
    "mhz": 146.52,
    "tone": "tone",
    "tone_value": 100
   },
   "comment": "-060 x"
  }
 },
 "strict": "same",
 "reencode": "equivalent",
 "canonical_info": "!4903.50N/07201.75W>146.520MHz T100/A=000100-060 x"
}
```

```json
{
 "id": "position/spaces-either-side-of-an-altitude-after-a-frequency",
 "description": "A space before and after a /A= put two bytes between the frequency and the tone, so the tone does not follow the frequency and is comment text.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": "!4903.50N/07201.75W>146.520MHz /A=000100 T100 x"
 },
 "expect": {
  "data": {
   "type": "position",
   "latitude": 49.05833333333333,
   "longitude": -72.02916666666667,
   "symbol": "/>",
   "altitude_feet": 100,
   "frequency": {
    "mhz": 146.52
   },
   "comment": "T100 x"
  }
 },
 "strict": "same",
 "reencode": "equivalent",
 "canonical_info": "!4903.50N/07201.75W>146.520MHz/A=000100T100 x"
}
```

```json
{
 "id": "position/frequency-after-a-slash-and-telemetry",
 "description": "The comment's one leading / and the start of the text are judged on the text left, so a frequency after a / and lifted telemetry is at the start.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": "!4903.50N/07201.75W>/|!!!!|146.520MHz T100 x"
 },
 "expect": {
  "data": {
   "type": "position",
   "latitude": 49.05833333333333,
   "longitude": -72.02916666666667,
   "symbol": "/>",
   "telemetry": {
    "sequence": 0,
    "analog": [
     0
    ]
   },
   "frequency": {
    "mhz": 146.52,
    "tone": "tone",
    "tone_value": 100
   },
   "comment": "x"
  }
 },
 "strict": "same",
 "reencode": "equivalent",
 "canonical_info": "!4903.50N/07201.75W>146.520MHz T100 x|!!!!|"
}
```

```json
{
 "id": "mic-e/frequency-after-a-slash-and-a-later-altitude",
 "description": "Status text /\"4e}146.520MHz: once the later altitude is lifted, the frequency is at the start of the text left after one /, as in a position comment; strict leaves the altitude in the text, so the frequency is not at the start.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": "`(_fn\"Oj/`/\"4e}146.520MHz T100 x",
  "destination": "S32UVT"
 },
 "expect": {
  "data": {
   "type": "mic-e",
   "mic_e_message": "returning",
   "type_code": "`",
   "latitude": 33.42733333333334,
   "longitude": -112.129,
   "symbol": "/j",
   "course_degrees": 251,
   "speed_knots": 20,
   "altitude_feet": 255.9055118110236,
   "frequency": {
    "mhz": 146.52,
    "tone": "tone",
    "tone_value": 100
   },
   "comment": "x"
  },
  "diagnostics": [
   "warning:mic-e-altitude-not-first"
  ]
 },
 "strict": {
  "data": {
   "type": "mic-e",
   "mic_e_message": "returning",
   "type_code": "`",
   "latitude": 33.42733333333334,
   "longitude": -112.129,
   "symbol": "/j",
   "course_degrees": 251,
   "speed_knots": 20,
   "comment": "\"4e}146.520MHz T100 x"
  }
 },
 "reencode": "equivalent",
 "canonical_info": "`(_fn\"Oj/`\"4e}146.520MHz T100 x"
}
```

```json
{
 "id": "position/text-reading-as-an-offset-after-a-tone-and-an-altitude",
 "description": "Text that would read as an offset, after a tone and a /A=, is written straight after the /A=: it reads back as itself with no delimiter, so none is written and the report re-encodes identical.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": "!4903.50N/07201.75W>146.520MHz T100/A=000100-060 x"
 },
 "expect": {
  "data": {
   "type": "position",
   "latitude": 49.05833333333333,
   "longitude": -72.02916666666667,
   "symbol": "/>",
   "altitude_feet": 100,
   "frequency": {
    "mhz": 146.52,
    "tone": "tone",
    "tone_value": 100
   },
   "comment": "-060 x"
  }
 },
 "strict": "same",
 "reencode": "identical"
}
```

```json
{
 "id": "position/leading-space-before-telemetry",
 "description": "The comment's leading space is judged on the text left, so a space, telemetry and x give the comment x.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": "!4903.50N/07201.75W> |!!!!|x"
 },
 "expect": {
  "data": {
   "type": "position",
   "latitude": 49.05833333333333,
   "longitude": -72.02916666666667,
   "symbol": "/>",
   "telemetry": {
    "sequence": 0,
    "analog": [
     0
    ]
   },
   "comment": "x"
  }
 },
 "strict": "same",
 "reencode": "equivalent",
 "canonical_info": "!4903.50N/07201.75W>x|!!!!|"
}
```

```json
{
 "id": "position/phg-rate-split-by-a-dao-is-text",
 "description": "PHG2360 stands whole and is a PHG; its rate byte and / are split by a !DAO!, so they are not a PHGR and are comment text, written back after a / so they are not read as one.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": "!4903.50N/07201.75W#PHG23605!W12!/x"
 },
 "expect": {
  "data": {
   "type": "position",
   "latitude": 49.05835,
   "longitude": -72.0292,
   "symbol": "/#",
   "phg": {
    "power": 2,
    "height": 3,
    "gain": 6,
    "directivity": 0
   },
   "dao": {
    "datum": "W",
    "precision": "thousandths"
   },
   "comment": "5/x"
  }
 },
 "strict": "same",
 "reencode": "equivalent",
 "canonical_info": "!4903.50N/07201.75W#PHG2360/5/x!W12!"
}
```

```json
{
 "id": "position/phg-rate-after-an-altitude-is-text",
 "description": "A /A= between a PHG and a rate byte and / splits the PHGR: the PHG is read and 5/x is comment text.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": "!4903.50N/07201.75W#PHG2360/A=0001005/x"
 },
 "expect": {
  "data": {
   "type": "position",
   "latitude": 49.05833333333333,
   "longitude": -72.02916666666667,
   "symbol": "/#",
   "altitude_feet": 100,
   "phg": {
    "power": 2,
    "height": 3,
    "gain": 6,
    "directivity": 0
   },
   "comment": "5/x"
  }
 },
 "strict": "same",
 "reencode": "identical"
}
```

```json
{
 "id": "weather/software-and-unit-after-a-dao",
 "description": "The software type and unit are judged on what is left once the !DAO! is lifted: xRSW stands whole, so it is the software type and unit.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": "!4903.50N/07201.75W_090/005g010t058!W12!xRSW"
 },
 "expect": {
  "data": {
   "type": "position",
   "latitude": 49.05835,
   "longitude": -72.0292,
   "symbol": "/_",
   "dao": {
    "datum": "W",
    "precision": "thousandths"
   },
   "weather": {
    "wind_direction_degrees": 90,
    "wind_speed_mph": 5,
    "wind_gust_mph": 10,
    "temperature_f": 58,
    "software": "x",
    "unit": "RSW"
   }
  }
 },
 "strict": "same",
 "reencode": "equivalent",
 "canonical_info": "!4903.50N/07201.75W_090/005g010t058xRSW!W12!"
}
```

```json
{
 "id": "position/second-altitude-is-text",
 "description": "Only the first /A= that stands whole is the altitude; a second is comment text, and its / is dropped as the comment's leading delimiter.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": "!4903.50N/07201.75W>/A=000100/A=000200"
 },
 "expect": {
  "data": {
   "type": "position",
   "latitude": 49.05833333333333,
   "longitude": -72.02916666666667,
   "symbol": "/>",
   "altitude_feet": 100,
   "comment": "A=000200"
  }
 },
 "strict": "same",
 "reencode": "equivalent",
 "canonical_info": "!4903.50N/07201.75W>/A=000100A=000200"
}
```

```json
{
 "id": "position/whole-altitude-after-one-split-by-a-dao",
 "description": "A /A= split by a !DAO! is not one, so the first whole /A= later in the text is the altitude and the split one is comment text, written after the altitude.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": "!4903.50N/07201.75W>x/A=0001!W12!00 /A=000200 y"
 },
 "expect": {
  "data": {
   "type": "position",
   "latitude": 49.05835,
   "longitude": -72.0292,
   "symbol": "/>",
   "altitude_feet": 200,
   "dao": {
    "datum": "W",
    "precision": "thousandths"
   },
   "comment": "x/A=000100  y"
  }
 },
 "strict": "same",
 "reencode": "equivalent",
 "canonical_info": "!4903.50N/07201.75W>/A=000200x/A=000100  y!W12!"
}
```

```json
{
 "id": "position/second-altitude-after-a-space-is-text",
 "description": "A second /A= after a space is comment text; the space is the dropped delimiter, so the comment starts with / and is written back after a /.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage)",
 "authority": "interpretation",
 "interpretations": [
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "info": "!4903.50N/07201.75W>/A=000100 /A=000200"
 },
 "expect": {
  "data": {
   "type": "position",
   "latitude": 49.05833333333333,
   "longitude": -72.02916666666667,
   "symbol": "/>",
   "altitude_feet": 100,
   "comment": "/A=000200"
  }
 },
 "strict": "same",
 "reencode": "equivalent",
 "canonical_info": "!4903.50N/07201.75W>/A=000100//A=000200"
}
```

```json
{
 "id": "encode/text-after-a-frequency-and-a-signpost-takes-its-space",
 "description": "Free text after a frequency and braces is written after a space even when it looks like a tone: the braces cut it off from the frequency.",
 "source": "differential fuzzing 2026-11-15 (round 5 triage, data seed 10101 line 34350)",
 "authority": "interpretation",
 "interpretations": [
  "where-a-voice-frequency-goes",
  "lifting-an-element-never-joins-the-text-either-side-of-it"
 ],
 "input": {
  "encode": {
   "type": "item",
   "name": "147.345+",
   "latitude": 51.5565,
   "longitude": -112.337,
   "symbol": "\\m",
   "phg": {
    "power": 4,
    "height": 4,
    "gain": 8,
    "directivity": 0
   },
   "frequency": {
    "mhz": 147.345
   },
   "comment": "C107",
   "signpost": "5"
  }
 },
 "expect": {
  "info": ")147.345+!5133.39N\\11220.22WmPHG4480/147.345MHz{5} C107"
 }
}
```

