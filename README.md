# APRS conformance vectors

Language-neutral test cases for APRS decoders and encoders: what a packet means, what is wrong with it, and what a strict and a lenient decoder should each make of it. Any implementation in any language can run them, and every implementation below consumes them the same way: as a git submodule, pinned to a commit, run by its own test suite on every build.

The cases come from three places, and each says which:

| Authority | Meaning | An implementation should |
|---|---|---|
| `spec` | The expected values follow from the text of APRS12c or *Understanding APRS Packets* (UAP), usually a worked example printed there. | match them |
| `interpretation` | The spec is ambiguous, contradicts itself or is wrong here; the expected values follow a decision recorded in [`interpretations.md`](interpretations.md), linked from the case. | match them or document why not |
| `observed` | A real packet from the APRS-IS feed; the expected values are what an implementation made of it when the case was recorded (Packet.Aprs, for every case so far), kept as a regression record. | treat a difference as a question, not a failure |

About 250 cases cover every example packet printed in APRS12c and UAP, the encoder, and every defect a lenient decoder may tolerate; another 1,395 are real packets of every distinct shape seen on APRS-IS, and 40 more pin the rules on which two implementations disagreed over a whole capture.

**Licence:** AGPL-3.0-or-later ([`LICENSE`](LICENSE)).

## Implementations

| Implementation | Language | Repository | Package |
|---|---|---|---|
| Packet.Aprs | C# (.NET) | [packet-net/packet.net](https://github.com/packet-net/packet.net) | [NuGet `Packet.Aprs`](https://www.nuget.org/packages/Packet.Aprs) |
| pdn-aprs | Rust (`no_std` + `alloc`) | [packet-net/aprs-rs](https://github.com/packet-net/aprs-rs) | [crates.io `pdn-aprs`](https://crates.io/crates/pdn-aprs) |
| pdn-aprs | Python (3.10+) | [packet-net/aprs-py](https://github.com/packet-net/aprs-py) | [PyPI `pdn-aprs`](https://pypi.org/project/pdn-aprs/) |
| pdn-aprs | TypeScript (Node 20+, browsers) | [packet-net/aprs-ts](https://github.com/packet-net/aprs-ts) | [npm `@packet-net/pdn-aprs`](https://www.npmjs.com/package/@packet-net/pdn-aprs) |

This repository's CI also runs each implementation against the vectors in every change, so a pull request shows which implementations already pass a new case. A failure there does not break an implementation, which only sees new cases when it moves its pin.

To use the vectors, add this repository as a git submodule and point your test runner at `cases/` and `codes.json`:

```sh
git submodule add https://github.com/packet-net/aprs-vectors vectors
```

The submodule pins a commit, so new cases reach an implementation only when it moves the pin on, and its own CI shows whether it still passes. Dependabot's `gitsubmodule` ecosystem can open that pull request.

## Files

| File | What |
|---|---|
| `cases/*.json` | The cases, one file per area (`position`, `mic-e`, `message`, ...). Each file is `{"cases": [ ... ]}`. `deviations.json` holds the tolerated defects; `corpus.json` the real packets; `differential.json` the real packets on which two implementations disagreed, one for each rule that settled it. |
| `codes.json` | Every diagnostic code a case can name, with its meaning and whether a lenient decoder may tolerate it. |
| `schema.json` | JSON Schema (2020-12) for the case files. |
| `interpretations.md` | The decisions taken where the spec is ambiguous, contradicts itself or is wrong. |
| `tools/check.py` | Checks the files are well formed and consistent; CI runs it on every change. |
| `tools/compare.py` | Compares two implementations' decodings of the same capture and buckets every disagreement (see [Comparing two implementations](#comparing-two-implementations)). |

## A case

```json
{
  "id": "position/lowercase-hemisphere",
  "description": "Lower-case hemisphere letters: a strict decoder rejects them, a lenient one reads them as upper case.",
  "source": "UAP 5.9",
  "authority": "spec",
  "input": { "tnc2": "N1EOE>APN391,N1NCI-3*,WIDE2-1:!4216.95n/07243.20w#phg6230/ Easthampton MA" },
  "expect": {
    "data": { "type": "position", "latitude": 42.2825, "longitude": -72.72, "symbol": "/#", "comment": "phg6230/ Easthampton MA" },
    "diagnostics": [ "warning:lowercase-hemisphere", "warning:lowercase-hemisphere" ]
  },
  "strict": { "rejected_by": "lowercase-hemisphere" },
  "reencode": "equivalent",
  "canonical_info": "!4216.95N/07243.20W#phg6230/ Easthampton MA"
}
```

| Key | Required | Meaning |
|---|---|---|
| `id` | yes | Unique, `area/short-name`. Stable: other suites may refer to it. |
| `description` | yes | One sentence saying why the case exists. |
| `source` | yes | Where the packet comes from: a spec section, a UAP section, or `APRS-IS <date>` for the live feed. |
| `authority` | yes | `spec`, `interpretation` or `observed` (above). |
| `interpretations` | no | Headings in [`interpretations.md`](interpretations.md) (as GitHub anchors) that the expected values depend on. |
| `input` | yes | What to decode, or with `encode`, what to encode (below). |
| `expect` | yes | The lenient decoder's result, or an encode case's result. |
| `strict` | no | The strict decoder's result: `"same"` (the default), `{"rejected_by": code}` (add `"header": true` when the header is what fails), or a full `{"data", "diagnostics"}` when strict reads the packet differently without rejecting it. |
| `reencode` | no | Encoding the lenient decoder's data again: `"identical"` gives the input's information field byte for byte (for Mic-E, the destination too), `"equivalent"` gives bytes that decode to the same data, `"refused"` means the encoder must decline (for example message text over 67 characters, which receivers accept and senders may not write). |
| `canonical_info` | no | With `equivalent`: the bytes Packet.Aprs writes. Another encoder may choose differently and still conform. |

### Input

One of:

- `"tnc2"`: a TNC2 / APRS-IS text line. `"tnc2_hex"` when the line is not valid UTF-8.
- `"ax25_hex"`: an AX.25 UI frame in KISS form (no flags, no FCS), as hex.
- `"info"` (or `"info_hex"`): just the information field. The header is `N0CALL>APZ001` unless the case gives `"source"`, `"destination"` or `"path"` alongside it.
- `"encode"`: data in the form below, for an encode case. `"source"` and `"destination"` default as above.

### Expect

For a decode case:

| Key | Meaning |
|---|---|
| `data` | The decoded data (form below). |
| `diagnostics` | Every diagnostic, as `"severity:code"`. Compare as a multiset (order does not matter, repeats do). A decoder that does not report `info` diagnostics can ignore those. Absent means none. |
| `header` | The header, when the case is about it: `source`, `destination`, `path`, `q_construct`. |
| `header_error` | Instead of `data`: the header is unusable and nothing is decoded; the diagnostics that say why. |
| `device` | The sending device from the [aprs-deviceid](https://github.com/aprsorg/aprs-deviceid) database: `vendor`, `model`. Depends on the database version. |

For an encode case, `expect` is `{"info": "..."}` (the information field to write) or `{"refused": true}`. A Mic-E encode case also gives `"destination"`, the address the encoder computes, since Mic-E carries half its position there.

## The data form

The rules, which make absence meaningful: a field that is not listed must not be produced.

- Names are snake_case. Quantities keep the units APRS sends, with the unit in the name (`speed_knots`, `altitude_feet`, `temperature_f`); nothing is converted, except the wind speed in a compressed weather position's cs bytes, which is knots on air and goes in `wind_speed_mph` ([interpretation](interpretations.md#wind-in-a-compressed-weather-position)).
- Null values, empty strings and empty lists are left out. The one exception is `reply_ack`, where an empty string says the sender supports reply-acks.
- Booleans are named for the less usual state and written only when true (`compressed`, `messaging`, `killed`, `old_data`).
- Enumerations are kebab-case strings (`off-duty`, `peet-bros-hash`).
- Timestamps are written as on air: `092345z`, `092345/`, `234517h`, or `10090556` (month, day, hour, minute).
- Digital telemetry bits are written as on air: eight `0`/`1` characters, channel B1 first.
- Values another field already determines are not written: a symbol's description, PHG in watts, a bulletin's kind, a Mic-E radio's messaging capability.
- Byte-valued text (user-defined data) is a string of code points U+0000-U+00FF, one per byte.

### Comparing

- Strings, booleans and integers compare exactly.
- Other numbers compare within 1e-9, relative to the larger magnitude (or absolute below 1). Implementations reach the same degrees by different arithmetic.
- An implementation that does not produce some field should skip it, and knows it has not been tested on it.
- An implementation with no lenient mode can run `strict` alone.

### Checking a case

- `strict: {"rejected_by": code}` means the decoder still returns a packet, with `data` `{"type": "unrecognized", "reason": "malformed"}` and `error:code` among its diagnostics. With `"header": true`, the header is rejected instead, and `error:code` is among the header's diagnostics. Other diagnostics may be there too.
- `reencode: "identical"` compares against the input's information field without any trailing CR or LF, which is a tolerated defect rather than part of the data.
- `reencode: "equivalent"` means the bytes written decode, leniently, to the same data with no warnings or errors. `canonical_info` is only what Packet.Aprs writes.
- A tolerance check (turning off only the one tolerance a case used) applies to cases whose lenient diagnostics name exactly one tolerable code; it must give the `strict` result.

### Rules the cases rely on

These follow from the cases, but an implementation meets them before it meets the case, so they are spelled out here.

- **Addresses and path.** On APRS-IS an address is 1-9 letters, digits or `-`. Anything else in a TNC2 header is `invalid-address`; a missing `>` or `:`, or an empty source, is `invalid-header`. A path entry is used when it is marked `*` or comes before one that is, and the neutral form writes `*` on every used entry. An entry of `qA` and one more letter, in either case, is a q-construct, and the entry after it is its station.
- **Data type identifiers.** `&`, `+` and `.` are reserved: `unrecognized` with reason `reserved-data-type` and an `info:reserved-data-type`. Any other first byte that is not a data type identifier is `not-aprs`. An empty information field is `empty`, with no diagnostic.
- **Device.** `device` is recorded only in Mic-E cases. A case without it says nothing about device identification, so do not check that it is absent.
- **Text that is not UTF-8** is read as Latin-1, the whole field, with one `non-utf8-text` warning for the field.
- **Numbers as sent.** Telemetry values and equation coefficients are compared as numbers, but `identical` re-encoding needs the text as sent (`073`, `190.0`, `.53`), so keep it.
- **The order of checks.** When a packet has several defects, a strict decoder rejects it by the first one it meets; the cases expect structural checks (addressee, braces, fields) before the text's encoding.
- **Weather.** A report with the weather station symbol (`_`, either table) is weather even with no fields. The fields are one contiguous run, which ends at the first thing that is not a field, at a field letter seen before, and at `c` once the wind is known. A value is digits (only `t` may start with `-`), a run of dots (read up to the field's width), or exactly the field's width of spaces. After the fields, base-91 telemetry and a `!DAO!` are lifted out first; what is left is the software type and unit if it is a letter then a 2-4 character unit of letters, digits, `-` or `_` (not all digits), and nothing else, and otherwise `weather-comment` text, from which an altitude or a data extension is not lifted. A positionless report's comment keeps its leading space or `/`. A letter the spec does not define followed by two or more digits, dots or `-`, ending in a digit, is an `extra` field. A field shorter than its fixed width, or one longer (`h7`, `t45`, `h100`, `b...`), is `non-standard-weather-field-width`; so is a fixed-width value that runs on into one more digit, which is read at the longer width. One that runs on by two or more digits is read at its own width, and the fields end there.
- **Complete weather.** `incomplete-weather` is given once for each missing part. A positionless report gets one if any of `c`, `s`, `g` and `t` is missing. A position, object or item report gets one if the wind is missing (no `DDD/SSS` extension and no `c` and `s` fields) and another if `g` or `t` is missing. A value sent as unknown, dots or spaces, counts as present. After a compressed position the cs bytes are the wind, and cs bytes that carry none mean it is unknown, so it is never missing ([interpretation](interpretations.md#wind-in-a-compressed-weather-position)); wind sent after a compressed position follows [another](interpretations.md#wind-after-a-compressed-weather-position).
- **Comments.** Structured elements are lifted out of a comment in this order, so that one is not taken for another: base-91 telemetry, only looked for between the last two `|`, and a `!DAO!`, the last one outside it; a `/A=` altitude anywhere, which wins over a compressed or Mic-E one; signpost or corridor braces, the first `{...}` holding 1-3 characters; a data extension later in the text, only when none came straight after the symbol (the first `PHG`, else the first `RNG`, else the first `DFS`), where a course/speed, or a compressed course/speed or altitude, does not count as one but PHG, RNG, DFS and a compressed range do; and a voice frequency at the start, after at most one space or `/`. `MHz` may be in any case. A frequency's tone, offset and range fields each need a space before and a space or the end after, a range is `R`, two digits, then `m` or `k`, and one space after the frequency is dropped. Last, one leading space or `/` is dropped from what is left. PHG and DFS height codes run from `0` on through the ASCII table to `~`, as the spec's height doubling allows.
- **Telemetry.** A report's sequence is `MIC` or letters and digits up to a comma ([interpretation](interpretations.md#telemetry-sequence-numbers-are-not-3-characters)). Each value ends at a comma or the end of the field; an empty one is `null`, and one left by a trailing comma still counts. The eight bits are only read after all five values; fewer values, or no bits, is `invalid-telemetry`, tolerated, and anything after that is the comment. In `EQNS.`, trailing commas and spaces are the list stopping ("the list may stop at any field", APRS12c ch. 13), and a coefficient may have spaces around it and an exponent. Metadata sent as a numbered message keeps its `message_id`, and its structure (the `PARM.` or other prefix, and the list) is checked before its text's encoding. An empty `PARM.` list is one empty name.
- **Messages and queries.** A second `:` straight after the first is not an unpadded addressee but an empty one: `invalid-message`. Text starting `?` and an upper-case type the spec does not define (`?WX`) is still a directed query, which the recipient ignores; a known type in lower case, a message ID, or a target that is not one callsign makes it a plain message with an `invalid-query` info.
- **Timestamps that are not there.** A `/` or `@` report whose timestamp is not 6 digits then `z`, `/` or `h` is read with the position straight after the DTI if that decodes, else after seven bytes (`malformed-timestamp`, tolerated). An object's seven timestamp bytes that look like one (six digits, or ending `z`, `/` or `h`) but are not, with a whole position report after them, are `malformed-timestamp`; otherwise the object has `object-without-timestamp` and its position starts straight after the name. Whether a whole position report follows is judged under the options in force, so such an object can decode differently lenient and strict. An object report shorter than 11 bytes is `truncated`. An item's `!` or `_` is looked for from the fourth byte on, so a name has at least three characters.
- **Positions.** A zero latitude or longitude keeps its hemisphere letter so that it re-encodes `identical`, though the neutral form writes 0 either way. Text, then a `!` and a position (the TNC beacon form), is only taken as a position report when what follows the `!` decodes as one. An empty position is `truncated`.
- **Mic-E.** Every 0xFF byte is removed from the information field first. The destination's latitude is checked before the information field, and a latitude of exactly 90 degrees is valid. Information bytes outside the ranges APRS12c gives, or fewer than 9 of them, are `invalid-mic-e-information`. `mic-e-missing-device-type` applies only when there is status text. A device suffix is matched only after the type codes `` ` `` or `'` (two characters) or `>` or `]` (one). An altitude that is not at the start is the first run of three base-91 characters and `}`. For `identical` re-encoding the encoder uses the printable forms APRS12c ch. 10 allows (longitude minutes under 10 + 60, speed tens + 80 below 200 knots, course hundreds + 4), and with ambiguity writes the centre it reports into the longitude digits a decoder ignores.
- **Capabilities.** The text's encoding is checked before free text. A token with a space or a control character in it makes the report free text (`free-text-capabilities`); an encoder accepts any other token without `,` or `=`.
- **Raw data.** Raw weather station data is printable ASCII, or `invalid-weather`.
- **Encoding.** Base-91 telemetry in a weather report, which has no comment, is refused. A third-party packet re-encodes with its inner packet's information field as received. When a space after a voice frequency would make the comment read as one of its fields, the comment is written straight after it (`445.950MHz-500 T110`).
- **NMEA.** A checksum is `*hh` at the very end; a `*` elsewhere, and whatever follows it, is part of the sentence. `invalid-nmea` is a sentence that is not printable ASCII. `sentence` is written without the `$`; `time` is `HH:MM:SS` with any fraction of a second kept, less trailing zeros. A position is `ddmm.mm`, `dddmm.mm` as a number, so the hundreds are degrees whatever the number of digits. A field that does not parse (a position before the receiver has a fix, say) is left out; the sentence is still decoded.

### Enumerations

| Field | Values |
|---|---|
| `compression.fix` | `old`, `current` |
| `compression.source` | `other`, `gll`, `gga`, `rmc` |
| `compression.origin` | `compressed`, `tnc-beacon-text`, `software`, `reserved3`, `kpc3`, `pico`, `other-tracker`, `digipeater-conversion` |
| `area.shape` | `open-circle`, `line-down-right`, `open-ellipse`, `open-triangle`, `open-box`, `filled-circle`, `line-down-left`, `filled-ellipse`, `filled-triangle`, `filled-box` (codes 0-9) |
| `area.color` | `black`, `blue`, `green`, `cyan`, `red`, `violet`, `yellow`, `gray` (codes `/0`-`/7`), then the same with `-low` (codes `/8`, `/9`, `10`-`15`) |
| `storm.type` | `tropical-storm`, `hurricane`, `tropical-depression` |
| `mic_e_message` | `off-duty`, `en-route`, `in-service`, `returning`, `committed`, `special`, `priority`, `custom0`-`custom6`, `emergency`, `unknown` |
| `dao.precision` | `none`, `thousandths`, `base91` |
| `frequency.tone` | `off`, `tone`, `ctcss`, `dcs`, `tone-burst` (`1750`, with no `tone_value`) |
| `raw-weather` `format` | `peet-bros-hash`, `peet-bros-star`, `ultimeter-packet`, `ultimeter-logging` |
| `unrecognized` `reason` | `empty`, `not-aprs`, `reserved-data-type`, `malformed` |

### Fields by type

Every decoded `data` has `type`. Positions, Mic-E reports, objects and items share the positioned fields.

| Type | Fields |
|---|---|
| `position` | `timestamp`, `messaging`, positioned fields |
| `mic-e` | `mic_e_message`, `old_data` (`'` rather than `` ` ``), `type_code`, `device_suffix`, `locator`, `legacy_telemetry`, `destination_ssid`, positioned fields |
| `object` | `name`, `killed`, `timestamp`, positioned fields |
| `item` | `name`, `killed`, positioned fields |
| `message` | `addressee`, `text`, `message_id`, `reply_ack` |
| `ack` / `reject` | `addressee`, `acked_id` / `rejected_id`, `reply_ack` |
| `bulletin`, `nws-bulletin` | `addressee`, `text`, `message_id` |
| `telemetry-names` / `-units` / `-coefficients` | `addressee`, `names` / `units` / `coefficients`, `message_id` |
| `telemetry-bits` | `addressee`, `bits`, `project`, `message_id` |
| `directed-query` | `addressee`, `query_type`, `target` |
| `status` | `timestamp`, `locator`, `symbol`, `beam` (`heading_code`, `power_code`), `text` |
| `telemetry` | `sequence` (as sent), `analog` (numbers, `null` for an empty channel), `bits`, `comment` |
| `weather` | `timestamp`, `weather`, `comment` |
| `raw-weather` | `format`, `data` |
| `nmea` | `sentence`, `has_checksum`, `latitude`, `longitude`, `fix` (`valid`/`invalid`), `course_degrees`, `speed_knots`, `altitude_m`, `time`, `waypoint` |
| `maidenhead-beacon` | `locator`, `comment` |
| `query` | `query_type`, `footprint` (`latitude`, `longitude`, `radius_miles`) |
| `capabilities` | `capabilities`: `[token]` or `[token, value]` pairs, in order |
| `third-party` | `packet`: the inner packet's `source`, `destination`, `path`, `data`, `diagnostics` |
| `user-defined` | `user_id`, `packet_type`, `data` |
| `test` | `data` |
| `agrelo-df` | `bearing_degrees`, `quality` |
| `unrecognized` | `reason`: `empty`, `not-aprs`, `reserved-data-type` or `malformed` |

Positioned fields:

| Field | Meaning |
|---|---|
| `latitude`, `longitude` | Degrees, north and east positive, with any `!DAO!` precision applied. An ambiguous position gives the centre of its box ([interpretation](interpretations.md#position-ambiguity-which-point-is-reported)). |
| `ambiguity` | 1-4 digits blanked; absent for none. |
| `symbol` | Table (or overlay) character and code, e.g. `/>`. |
| `compressed`, `compression` | Compressed format, and its type byte: `fix` (`old`/`current`), `source` (`other`/`gll`/`gga`/`rmc`), `origin`. |
| `course_degrees`, `speed_knots`, `altitude_feet` | As sent. |
| `phg` | Codes as sent: `power`, `height`, `gain`, `directivity`, and `beacons_per_hour` for PHGR. |
| `range_miles`, `dfs`, `area`, `df_bearing`, `storm` | The other data extensions, codes as sent. |
| `dao` | `datum` and `precision` (`none`/`thousandths`/`base91`). |
| `telemetry` | Base-91 comment telemetry: `sequence`, `analog`, `digital`. |
| `frequency` | APRS 1.2 voice frequency: `mhz`, `tone`, `tone_value`, `offset_khz`, `range`, `range_km`, `narrow`, `ten_khz_resolution`. |
| `weather` | `wind_direction_degrees`, `wind_speed_mph`, `wind_gust_mph`, `temperature_f`, `rain_1h_in`, `rain_24h_in`, `rain_midnight_in`, `rain_raw`, `humidity_percent`, `pressure_mbar`, `luminosity_w_m2`, `snow_24h_in`, `software`, `unit`, `extra` (`letter`, `value`). |
| `signpost`, `comment` | Signpost text, and the free text left once everything above is lifted out. |

## Adding a case

Send a pull request here. Write the `id`, `description`, `source`, `authority` and `input` by hand; the expected values can be drafted by any implementation and then checked. For `spec` and `interpretation` cases, check every value against the document the case cites: an implementation's output is a draft, not the authority. Encode cases are written by hand in full. `python3 tools/check.py` must pass, and the case should fail in an implementation whose behaviour it describes is broken.

A new diagnostic code goes in `codes.json` in the same pull request. A new interpretation goes in `interpretations.md`, and the cases that depend on it link to its heading.

### Drafting with Packet.Aprs

packet.net has this repository as a submodule at `spec/aprs`, and its corpus tool writes into it. From a packet.net checkout:

```sh
git submodule update --init spec/aprs
dotnet run --project tools/Packet.Aprs.Corpus -- vectors fill spec/aprs/cases/position.json
```

`fill` completes every decode case that has no `expect` yet (`expect`, `strict`, `reencode`) and leaves the others alone. Commit inside `spec/aprs`, push a branch of this repository, and open the pull request here; once it merges, packet.net moves its pin on.

Real packets come from the APRS-IS capture that packet.net's `aprs-corpus collect` writes:

```sh
dotnet run --project tools/Packet.Aprs.Corpus -c Release -- curate ~/aprs-corpus samples.txt
dotnet run --project tools/Packet.Aprs.Corpus -c Release -- vectors from-samples samples.txt spec/aprs/cases/corpus.json
```

`curate` picks one or two packets of every distinct shape; `from-samples` adds the ones not already in the file after the existing cases, which keep their ids. When Packet.Aprs changes on purpose, `vectors refresh <files>` works out every observed case again, so the change can be reviewed as a diff.

## Comparing two implementations

The cases say what a decoder should make of a packet of every shape they cover. To find what they do not cover, run two implementations over a whole capture and compare them packet by packet. Each writes one JSON object per packet, in order, with its lenient and strict results in the neutral form and how the lenient data re-encodes (`identical`, `equivalent`, `refused`, `fails`, or `none` when there is nothing to re-encode: a header error, or unrecognized data):

```sh
# packet.net: extract the capture once, as one hex-encoded TNC2 line per line, and decode it
dotnet run --project tools/Packet.Aprs.Corpus -c Release -- diff lines ~/aprs-corpus lines.hex.gz
dotnet run --project tools/Packet.Aprs.Corpus -c Release -- diff dump lines.hex.gz cs.jsonl.gz
# aprs-rs, aprs-py and aprs-ts: decode the same lines
cargo run --release --example diff_dump -- lines.hex.gz rs.jsonl.gz
python3 tools/diff_dump.py lines.hex.gz py.jsonl.gz
npm ci && npm run build && node scripts/diff-dump.mjs lines.hex.gz ts.jsonl.gz
# here: bucket the disagreements
python3 tools/compare.py cs.jsonl.gz rs.jsonl.gz --names C# Rust --lines lines.hex.gz --json summary.json
```

`compare.py` needs only Python's standard library. It groups disagreements by which fields and diagnostics differ, with a count and example packets for each, and exits 1 if there are any. When one side re-encodes byte for byte and the other only equivalently, both round-trip and the encoders merely write different bytes; that is reported as an encoder choice, not a disagreement. A new implementation needs only the dump: read the lines file, decode each line, and write the same JSON. Each rule a disagreement settles becomes a case in `differential.json`.
