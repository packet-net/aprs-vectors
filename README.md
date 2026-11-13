# APRS conformance vectors

Language-neutral test cases for APRS decoders and encoders: what a packet means, what is wrong with it, and what a strict and a lenient decoder should each make of it. Any implementation in any language can run them, and every implementation below consumes them the same way: as a git submodule, pinned to a commit, run by its own test suite on every build.

The cases come from three places, and each says which:

| Authority | Meaning | An implementation should |
|---|---|---|
| `spec` | The expected values follow from the text of APRS12c or *Understanding APRS Packets* (UAP), usually a worked example printed there. | match them |
| `interpretation` | The spec is ambiguous, contradicts itself or is wrong here; the expected values follow a decision recorded in [`interpretations.md`](interpretations.md), linked from the case. | match them or document why not |
| `observed` | A real packet from the APRS-IS feed; the expected values are what an implementation made of it when the case was recorded (Packet.Aprs, for every case so far), kept as a regression record. | treat a difference as a question, not a failure |

About 250 cases cover every example packet printed in APRS12c and UAP, the encoder, and every defect a lenient decoder may tolerate; another 1,395 are real packets of every distinct shape seen on APRS-IS; 40 more pin the rules on which two implementations disagreed over a whole capture, and 120 more the rules that differential fuzzing of all five implementations settled. `precedence.json`, made by `tools/precedence.py`, pins what a record with two faults gives: the refusal an encoder names, and the defect a strict decoder rejects a packet by.

**Licence:** AGPL-3.0-or-later ([`LICENSE`](LICENSE)).

## Implementations

| Implementation | Language | Repository | Package |
|---|---|---|---|
| Packet.Aprs | C# (.NET) | [packet-net/aprs-cs](https://github.com/packet-net/aprs-cs) | [NuGet `Packet.Aprs`](https://www.nuget.org/packages/Packet.Aprs) |
| pdn-aprs | Rust (`no_std` + `alloc`) | [packet-net/aprs-rs](https://github.com/packet-net/aprs-rs) | [crates.io `pdn-aprs`](https://crates.io/crates/pdn-aprs) |
| pdn-aprs | Python (3.10+) | [packet-net/aprs-py](https://github.com/packet-net/aprs-py) | [PyPI `pdn-aprs`](https://pypi.org/project/pdn-aprs/) |
| pdn-aprs | TypeScript (Node 20+, browsers) | [packet-net/aprs-ts](https://github.com/packet-net/aprs-ts) | [npm `@packet-net/pdn-aprs`](https://www.npmjs.com/package/@packet-net/pdn-aprs) |
| pdn_aprs | C (C99, no allocation) | [packet-net/aprs-c](https://github.com/packet-net/aprs-c) | [GitHub releases](https://github.com/packet-net/aprs-c/releases): `pdn_aprs.h` + `pdn_aprs.c` |
| aprs | Go (1.24+, standard library only) | [packet-net/aprs-go](https://github.com/packet-net/aprs-go) | [pkg.go.dev `github.com/packet-net/aprs-go`](https://pkg.go.dev/github.com/packet-net/aprs-go) |

This repository's CI also runs each implementation against the vectors in every change, so a pull request shows which implementations already pass a new case. A failure there does not break an implementation, which only sees new cases when it moves its pin.

To use the vectors, add this repository as a git submodule and point your test runner at `cases/` and `codes.json`:

```sh
git submodule add https://github.com/packet-net/aprs-vectors vectors
```

The submodule pins a commit, so new cases reach an implementation only when it moves the pin on, and its own CI shows whether it still passes. Dependabot's `gitsubmodule` ecosystem can open that pull request.

**Versions.** The vectors are released as tagged versions (a zip of the files is attached to each [release](https://github.com/packet-net/aprs-vectors/releases)). The six implementations above share the vectors' major and minor version: an implementation at 1.0.x passes the vectors at 1.0. A new round of rulings is a minor version for the vectors and all six together; a fix in one implementation is that implementation's own patch version; a change that breaks a public API is a new major version.

## Files

| File | What |
|---|---|
| `cases/*.json` | The cases, one file per area (`position`, `mic-e`, `message`, ...). Each file is `{"cases": [ ... ]}`. `deviations.json` holds the tolerated defects; `corpus.json` the real packets; `differential.json` the real packets on which two implementations disagreed, one for each rule that settled it; `precedence.json` the generated two-fault cases (edit `tools/precedence.py`, not the file). |
| `codes.json` | Every diagnostic code a case can name, with its meaning and whether a lenient decoder may tolerate it. |
| `schema.json` | JSON Schema (2020-12) for the case files. |
| `interpretations.md` | The decisions taken where the spec is ambiguous, contradicts itself or is wrong. |
| `tools/check.py` | Checks the files are well formed and consistent; CI runs it on every change. |
| `tools/precedence.py` | Makes `cases/precedence.json`: a case for every pair of refusal codes one record can hold, and for pairs of tolerated decoding defects, from a catalogue of single faults (`--check` says whether the file is up to date). |
| `tools/mutate.py` | Makes mutated packets from a capture and the cases' inputs, for differential fuzzing (see [Comparing implementations](#comparing-implementations)). |
| `tools/generate.py` | Makes data in the neutral form, and builder recipes, for comparing encoders and builders. |
| `tools/compare.py` | Compares any number of implementations' dumps of the same input and buckets every difference. |

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
| `reencode` | no | Encoding the lenient decoder's data again: `"identical"` gives the input's information field byte for byte (for Mic-E, the destination too); `"equivalent"` gives `canonical_info`, bytes that decode to the same data; `"rounded"` gives `canonical_info`, where a value the format holds only in steps is rounded to the nearest ([interpretation](interpretations.md#re-encoding-into-compressed-bytes-rounds)); `"refused"` means the encoder must decline (for example message text over 67 characters, which receivers accept and senders may not write). |
| `canonical_info` | with `equivalent` or `rounded` | The information field an encoder writes, byte for byte, as the Encoding rule below gives it. Where the spec allows several forms, the rule names one, so every encoder writes the same bytes. |

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

For an encode case, `expect` is `{"info": "..."}` (the information field to write) or `{"refused": true, "refusal": "<id>"}`, where `refusal` is the reason, an id from the `refusals` list in `codes.json` (a separate list from the diagnostic codes; `refusal` goes only with `refused`). A decode case with `"reencode": "refused"` names its reason in a top-level `"reencode_refusal"`. A Mic-E encode case also gives `"destination"`, the address the encoder computes, since Mic-E carries half its position there.

## The data form

The rules, which make absence meaningful: a field that is not listed must not be produced.

- Names are snake_case. Quantities keep the units APRS sends, with the unit in the name (`speed_knots`, `altitude_feet`, `temperature_f`); nothing is converted, except the wind speed in a compressed weather position's cs bytes, which is knots on air and goes in `wind_speed_mph` ([interpretation](interpretations.md#wind-in-a-compressed-weather-position)).
- Null values, empty strings and empty lists are left out. The exceptions are `reply_ack`, where an empty string says the sender supports reply-acks, and a header's `source` and `destination`, which are always written, even when empty.
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
- `reencode: "equivalent"` means the bytes written are `canonical_info`, byte for byte, and decode, leniently, to the same data with no warnings or errors.
- `reencode: "rounded"` means the bytes written are `canonical_info`, byte for byte; they decode cleanly, to the data with one value rounded, so the data is not compared.
- A tolerance check (turning off only the one tolerance a case used) applies to cases whose lenient diagnostics name exactly one tolerable code; it must give the `strict` result.

### Rules the cases rely on

These follow from the cases, but an implementation meets them before it meets the case, so they are spelled out here.

- **Addresses and path.** On APRS-IS an address is 1-9 letters, digits or `-`. Anything else in a TNC2 header, whether the source, the destination or a path entry, is `invalid-address`; a missing `>` or `:`, or an empty source, is `invalid-header`. A path entry is used when it is marked `*` or comes before one that is, and the neutral form writes `*` on every used entry. An entry of `qA` and one more letter, in either case, is a q-construct, and the entry after it is its station; this is read only in the outer header, so a third-party header's path is kept as sent and its packet has no `q_construct`. In a third-party header the source may be 1-9 printable ASCII characters (0x20-0x7E) other than `>` and `:` (APRS12c ch. 17), while the destination and path follow the rule above; anything else there is `invalid-third-party` ([interpretation](interpretations.md#third-party-header-addresses)). A defect the inner header may tolerate (several used markers, say) is decoded leniently, with its warning on the inner packet, and a strict decoder rejects the packet as `invalid-third-party`. Third-party packets nest at most four deep: a fifth `}` is not read, and the packet whose information field it starts is `unrecognized` (`malformed`) with `error:invalid-third-party`, as one with an unusable third-party header is ([interpretation](interpretations.md#third-party-packets-nest-at-most-four-deep)). In an AX.25 frame each address is upper-case letters and digits, padded with spaces at the end (AX.25 2.2 section 3.12); a lower-case letter is tolerated (`invalid-ax25-address-characters`), and any other character, a space before the last character included, is `invalid-address`, so the header is unusable and no TNC2 line is written from it; a call of spaces only is empty, so a source is `invalid-address`, a destination `empty-destination` and a digipeater `empty-path-entry`, as they are in TNC2 ([interpretation](interpretations.md#an-ax25-address-is-letters-and-digits)).
- **Data type identifiers.** `&`, `+` and `.` are reserved: `unrecognized` with reason `reserved-data-type` and an `info:reserved-data-type`. 0x1C and 0x1D are Mic-E (Rev 0 beta units, APRS12c ch. 10) with an `obsolete-format` info, given for the data type identifier before anything else is checked, whatever follows it; 0x1D, like `'`, is `old_data`. Any other first byte that is not a data type identifier is `not-aprs`. An empty information field is `empty`, with no diagnostic.
- **Device.** `device` is recorded only in Mic-E cases. A case without it says nothing about device identification, so do not check that it is absent.
- **Text that is not UTF-8** is read as Latin-1: the whole text (a comment, a message or status text, a telemetry list), with one `non-utf8-text` warning for it. Bytes outside the text, such as a garbled timestamp that was skipped, do not count.
- **Numbers as sent.** Telemetry values, equation coefficients and a general query's footprint numbers are compared as numbers, but `identical` re-encoding needs the text as sent (`073`, `190.0`, `.53`, `34.0`, and whether a positive footprint number had a leading space), so keep it ([interpretation](interpretations.md#numbers-in-telemetry)).
- **The order of checks.** When a packet has several defects, a strict decoder rejects it by the first one it meets, and it meets them in reading order: a defect later in the packet never changes the diagnosis of one before it ([interpretation](interpretations.md#a-packet-is-read-in-order)). Structural checks (addressee, braces, fields, a `!DAO!`) come before the text's encoding. A trailing CR or LF (`trailing-line-break`) is met when the information field is taken, after the header and before anything in the field. Elements lifted out of a comment are met before the text left over is judged, so in a weather report a `!DAO!` on an ambiguous position (`dao-with-ambiguity`) is met before `weather-comment`, wherever the text is. In a position, object or item weather report, the wind is decided where the `DDD/SSS` extension belongs, before any field: missing wind (`incomplete-weather`) and wind sent as `c` and `s` fields (`wind-fields-instead-of-extension`) are both met there, before any field's width.
- **Weather.** A report with the weather station symbol (`_`, either table) is weather even with no fields. The fields are one contiguous run, which ends at the first thing that is not a field, at a defined field already read, and at `c` once the wind is known ([interpretation](interpretations.md#which-weather-field-a-letter-is)). Before that, `c` is the wind direction wherever it comes, but only with a value after it. A positionless report's wind always comes as fields; a position, object or item report's comes as fields only once a `c` has been read, so an `s` before any `c` there is snowfall. When the wind comes as fields, `s` is the wind speed until the speed is known, wherever it comes, and snowfall after that. `L` and `l` are one field, luminosity. Extra fields are kept as a list, so a repeated extra letter does not end the run. A value is digits (only `t` may start with `-`), a run of dots (read up to the field's width, so `s.....` is an unknown snowfall and two dots of text), or exactly the field's width of spaces. Snowfall's three characters may include one decimal point (APRS12c: "A decimal point is allowed for non-integer values"), so `s.50` is 0.5 inches; a value that holds a digit is a number, not a run of dots. A wind direction over 360, in the extension or a `c` field, is `out-of-range-value` (tolerated) and is dropped. After the fields of a position, object or item report, base-91 telemetry and a `!DAO!` are lifted out first; a positionless report keeps them in its comment. What is left is the software type and unit if it is a letter then a 2-4 character unit of letters, digits, `-` or `_` (not all digits), and nothing else, and otherwise `weather-comment` text, from which an altitude or a data extension is not lifted. A positionless report's comment keeps its leading space or `/`. A letter the spec does not define followed by a run of two or more digits, dots or `-` (the whole run, up to the first other character) that ends in a digit is an `extra` field. A field shorter than its fixed width, or one longer (`h7`, `t45`, `h100`, `b...`), is `non-standard-weather-field-width`; so is a fixed-width value that runs on into one more digit, which is read at the longer width. One that runs on by two or more digits is read at its own width, and the fields end there. Snowfall keeps its width of three characters, and only a run of dots may be shorter, when no digit follows it (`s..6` is not a field) ([interpretation](interpretations.md#which-weather-field-a-letter-is)), so `s00/` is not a field and in `s.050` the last `0` is text.
- **Complete weather.** `incomplete-weather` is given once for each missing part. A positionless report gets one if any of `c`, `s`, `g` and `t` is missing. A position, object or item report gets one if the wind is missing or incomplete (no `DDD/SSS` extension, and not both `c` and `s` fields) and another if `g` or `t` is missing. A value sent as unknown, dots or spaces, counts as present. Humidity `h00` is 100 percent; a humidity over 100 is `out-of-range-value` (tolerated) and is dropped. After a compressed position the cs bytes are the wind, and cs bytes that carry none mean it is unknown, so it is never missing ([interpretation](interpretations.md#wind-in-a-compressed-weather-position)); wind sent after a compressed position follows [another](interpretations.md#wind-after-a-compressed-weather-position).
- **Comments.** Structured elements are lifted out of a comment in this order, so that one is not taken for another: base-91 telemetry, only looked for between the last two `|`, and a `!DAO!`, the last one outside it; a `/A=` altitude anywhere, which wins over a compressed or Mic-E one; signpost or corridor braces, the first well-formed ones wherever they are: `{`, 1-3 characters that are not braces, and `}`, the characters being printable ASCII for a signpost, which needs the `\m` symbol and not an overlaid `m`, or digits for a corridor (so `{5Wm{55}` has the signpost `55` and `{{5}` has `5`; braces that do not qualify are comment text and do not stop the search, as with a data extension); a data extension later in the text, only when none came straight after the symbol (the first well-formed `PHG`, else the first well-formed `RNG`, else the first well-formed `DFS`; a malformed one such as `PHG12` is comment text and does not stop the search, [interpretation](interpretations.md#a-late-data-extension-is-the-first-well-formed-one)), where a course/speed, an area, a DF bearing, storm data, or a compressed course/speed or altitude, does not count as one but PHG, RNG, DFS and a compressed range do ([interpretation](interpretations.md#an-area-df-bearing-or-storm-is-not-the-data-extension)); and a voice frequency at the start, after at most one space or `/`. A `!DAO!` is five bytes as sent, so taking another element out never joins one, and a digit datum is only read with spaces for A and O ([interpretation](interpretations.md#dao-datum-digits)). Braces around anything but printable ASCII are not a signpost ([interpretation](interpretations.md#signpost-overlays-are-printable-ascii)). `MHz` may be in any case, but a microwave band letter (`A96.000MHz` for 1296 MHz) is upper case. A frequency's tone, offset and range fields each need a space before and a space or the end after, and come in that order: one out of order, and everything after it, stays in the comment; a range is `R`, two digits, then `m` or `k`, and one space after the frequency is dropped. Last, one leading space or `/` is dropped from what is left. PHG and DFS height codes run from `0` on through the ASCII table to `~`, as the spec's height doubling allows.
- **Telemetry.** A report's sequence is `MIC` or letters and digits up to a comma ([interpretation](interpretations.md#telemetry-sequence-numbers-are-not-3-characters)). Each value ends at a comma or the end of the field; an empty one is `null`, and one left by a trailing comma still counts. A value is an optional `-`, then digits with an optional decimal point (at least one digit): no `+`, no spaces, nothing else, or the report is `invalid-telemetry`, an error ([interpretation](interpretations.md#numbers-in-telemetry)). The eight bits are only read after all five values; fewer values, or no bits, is `invalid-telemetry`, tolerated, and anything after that is the comment. An `EQNS.` with no coefficients at all (`EQNS.,,,`) is a plain message with an `invalid-telemetry-metadata` info. In `EQNS.`, trailing commas and spaces are the list stopping ("the list may stop at any field", APRS12c ch. 13), and a coefficient is a number as above that may also have spaces (U+0020 only) around it and an exponent (`e` or `E`, an optional sign, digits). A coefficient must be a finite number (`0eN` is 0), or the `EQNS.` is a plain message with an `invalid-telemetry-metadata` info. A `{` in a `PARM.`, `UNIT.` or `BITS.` list that does not start a message ID stays in the list (`brace-in-message-text`); it does not make the message a plain one ([interpretation](interpretations.md#a-brace-in-telemetry-metadata)). Metadata sent as a numbered message keeps its `message_id`, and its structure (the `PARM.` or other prefix, and the list) is checked before its text's encoding. An empty `PARM.` list is one empty name.
- **Messages and queries.** When the tenth byte is `:`, the addressee is the nine bytes before it, whatever they hold (a `:` or space among them is `invalid-addressee-characters`). Only when it is not is a `:` looked for earlier: straight after the first, it is not an unpadded addressee but an empty one, `invalid-message`; later, it ends an addressee before its ninth character, which is `unpadded-addressee` (tolerated) and is then checked like any other: empty, or with a byte that is not printable ASCII, it is `invalid-message`; with a space or `:` in it, `invalid-addressee-characters`. An addressee is a bulletin when it is `BLN` then a digit or an upper-case letter; `BLN` followed by anything else is an ordinary message. The message ID starts at the last `{` followed by 1-5 letters or digits (and optionally `}` and a reply-ack); any other `{` is `brace-in-message-text`, and the ID is still read. Bulletins, NWS bulletins and telemetry metadata take a message ID but not the reply-ack form: `{MM}` or `{MM}AA` on them is `brace-in-message-text`, and the text is kept ([interpretation](interpretations.md#reply-acks-are-for-messages)). An ack or rej is `ack` or `rej`, an ID of 1-5 letters or digits, optionally `}` and a reply-ack, and optionally a message ID (`message-id-on-ack`, tolerated); anything else after the ID makes the text a plain message. Only a message can be a directed query, since APRS12c addresses one to "the station being queried": bulletin and NWS bulletin text that starts `?` is just text. In the same way only a message can be telemetry metadata, which APRS12c addresses to "the callsign of the station transmitting the telemetry data": bulletin and NWS bulletin text starting `PARM.`, `UNIT.`, `EQNS.` or `BITS.` is just text. A query type is upper-case letters, apart from the spec's own `PING?` ([interpretation](interpretations.md#query-types-are-upper-case-letters)). Text starting `?` and a type of upper-case letters the spec does not define (`?WX`) is still a directed query, which the recipient ignores; a known type in lower case, a message ID or any other `{`, or a target that is not one callsign (1-9 letters, digits or `-`) makes it a plain message with an `invalid-query` info. One space between the type and the target is a separator, and spaces after the target are padding ([interpretation](interpretations.md#a-directed-querys-target-is-one-callsign)). A general query's footprint is a latitude and longitude in decimal degrees, each a number as a telemetry value is (an optional `-`, then digits with an optional decimal point and at least one digit, so `-.1715`), with one leading space allowed only before a value that is not negative (APRS12c: "Note the leading space in the latitude, as its value is positive"; 0 takes it too, [interpretation](interpretations.md#a-footprint-coordinate-of-0-takes-the-space)), and a radius of exactly 4 digits; anything else, a latitude beyond 90 or a longitude beyond 180, or a query type that is not upper-case letters (`?IGAT7?`), is `invalid-general-query` ([interpretation](interpretations.md#a-general-query-footprint-is-a-real-place)).
- **Timestamps that are not there.** A `/` or `@` report whose timestamp is not 6 digits then `z`, `/` or `h` is read with the position straight after the DTI if that position decodes, else after seven bytes (`malformed-timestamp`, tolerated). When neither decodes, the report is `malformed-timestamp`, an error. An object's seven timestamp bytes that look like one (six digits, or ending `z`, `/` or `h`) but are not, with a position after them, are `malformed-timestamp`; otherwise the object has `object-without-timestamp` and its position starts straight after the name. Whether a position follows is judged on the position itself (latitude, symbol table, longitude and symbol code, or the 13 bytes of a compressed position), not on anything after it, and under the options in force, so such an object can decode differently lenient and strict. An object report shorter than 11 bytes is `truncated`. An item's `!` or `_` is looked for from the fourth byte on, so a name has at least three characters.
- **Positions.** A zero latitude or longitude keeps its hemisphere letter so that it re-encodes `identical`, though the neutral form writes 0 either way. A latitude's or longitude's digits, and its range, are checked before its hemisphere letter. The latitude alone sets the ambiguity, and one whose reported centre is past 90 degrees (`90  .  N`, centred on 90 degrees 30 minutes) is `invalid-latitude`, met before the longitude, as a longitude whose centre is past 180 degrees is `invalid-longitude`: in the longitude, each digit place that level blanks is ignored and may hold a digit or a space, in any mix, and a space in any other place is `invalid-longitude` ([interpretation](interpretations.md#longitude-blanks-follow-the-latitude)). Text, then a `!` and a position (the TNC beacon form), is only taken as a position report when the `!` is within the first 40 characters (offset 39 at most) and what follows it decodes as one. An empty position is `truncated`. A DF report's bearing (`/BRG/NRQ` after the course and speed) is degrees, so one over 360 is `out-of-range-value` (tolerated) and the whole `/BRG/NRQ` is dropped, as an out-of-range course is.
- **Mic-E.** The destination is checked first, its latitude before anything in the information field (a latitude of exactly 90 degrees is valid, but one whose ambiguity puts its centre past 90 degrees, such as `90LLLL`, is `invalid-mic-e-destination`). Then come the nine fixed bytes of the information field, as sent: an 0xFF among them is out of range like any other byte. Information bytes outside the ranges APRS12c gives, or fewer than 9 of them, are `invalid-mic-e-information`; after them the course is checked (over 360 is `out-of-range-value`, tolerated), then the symbol. Only then is every 0xFF byte in the status text removed (`kenwood-ff-padding`, tolerated), so a report that fails earlier has no padding warning ([interpretation](interpretations.md#mic-e-0xff-padding-is-in-the-status-text)). `mic-e-missing-device-type` applies only when there is status text. A device suffix is matched only after the type codes `` ` `` or `'` (two characters) or `>` or `]` (one). A PHG or RNG is straight after the type code only where it is so in the status text as sent: one that comes there only once a later altitude is lifted is a late one (`data-extension-in-comment`). A PHG straight after the type code, or straight after a locator and its space, is lifted before an altitude is looked for later in the text, so its bytes are never read as one (`0PH}` in `PHG3330PH}`). An altitude that is not at the start is the first run of three base-91 characters and `}`. A locator read at the start is taken before a later altitude is looked for, and its bytes are never part of one (`` `IO91/G}`` has no altitude). A locator is read only at the start of the status text (after any type code) or straight after a Mic-E altitude; anywhere else, after a PHG or RNG say, `IO91SX/G` is text. A later Mic-E altitude is looked for before base-91 telemetry and a `!DAO!` are lifted, so bytes either side of a `!DAO!` never join into one, and a `!DAO!` that shares a byte with the altitude found is not one. A strict decoder, which does not take a later altitude (`mic-e-altitude-not-first`), reads it as text and lifts the `!DAO!` as usual; it rejects the report with `mic-e-altitude-not-first` only when the status text has a later altitude, the defect it declines, and the text left once base-91 telemetry and the `!DAO!` are both lifted holds an altitude across a place one was taken from, which a lenient reader would then take (`...;X|!wII|!wII!}3` leaves `";X}`). With no later altitude in the status text there is nothing to decline, and a strict decoder reads it as a lenient one does, even where lifting telemetry leaves a run that looks like one (`"=K3RW|)>%v|J}` leaves `RWJ}`, which is comment text). Base-91 telemetry and a `!DAO!` are lifted out of the status text before the locator is read, so a locator followed straight by either has no missing space ([interpretation](interpretations.md#where-a-mic-e-locator-is-read)). For `identical` re-encoding the encoder uses the printable forms APRS12c ch. 10 allows (longitude minutes under 10 + 60, speed tens + 80 below 190 knots, and `/` for 190-199 knots, where + 80 would be DEL; course hundreds + 4), and with ambiguity writes the centre it reports into the longitude digits a decoder ignores. Where ch. 10 gives only DEL (longitude degrees 9 and 99, a course ending 99), it is written.
- **Capabilities.** The text's encoding is checked before free text. Items are split at commas, and each item at its first `=` into a token and a value. Spaces (U+0020, and no other character) around an item, a token or a value are padding and are dropped; an item left empty is skipped. The report is free text (`free-text-capabilities`) when a token is empty or holds a space or a control character (below U+0020, or U+007F), or a value holds a control character; a space inside a value is text ([interpretation](interpretations.md#station-capabilities-items-tokens-and-values)). An encoder refuses a token that is empty or holds a space, a control character, `,` or `=`, and a value that holds a control character or `,`, or starts or ends with a space.
- **Status.** `^`, a heading code (`0`-`9`, `A`-`Z`) and an ERP code (`1`-`9`, `:` to `@`, `A`-`K`) at the very end of the text is a beam heading; the text before it is kept as sent, spaces included. `^B0` is text, since `0` is not an ERP code.
- **Agrelo DF.** A report is exactly `%`, three bearing digits from 000 to 360, `/` and one quality digit; anything else is `invalid-agrelo-df` ([interpretation](interpretations.md#an-agrelo-bearing-is-0-to-360)).
- **Raw data.** Raw weather station data is printable ASCII, or `invalid-weather`.
- **Encoding.** An encoder never writes bytes that read back as different data: it writes an equivalent form or refuses, and a refusal carries a reason code, an id from the `refusals` list in `codes.json` (`invalid-address`, `ax25-cannot-carry`, `too-long`, `value-out-of-range` and so on) that names the rule which declined the data; `does-not-read-back` is the fallback for a library's own read-back check when no rule names the cause, and no case expects it; only rounding a value to the steps its field holds may change it. A number between those steps (a course or speed, `/A=` feet, a Mic-E speed or course, latitude and longitude minutes, DAO digits, a weather value, RNG miles, a footprint radius, a voice frequency, and a value carried in cs bytes, [interpretation](interpretations.md#re-encoding-into-compressed-bytes-rounds)) is rounded to the nearest step, halves away from zero, and refused only when the rounded value is outside the field; every other check applies to the rounded value, so 99.7 percent humidity is `h00`, a humidity of 0.4, which rounds to 0, is refused, and a course of -0.3 rounds to 0 ([interpretation](interpretations.md#values-between-steps-are-rounded)). A wind direction, like a course, is in range or not in whole degrees (0 to 360), whatever form it is written in, and one in range is then rounded once to its field's step: 360.4 and -0.4 degrees in cs bytes are north, and 360.5 and -0.5 are `value-out-of-range` in every form ([interpretation](interpretations.md#a-wind-direction-is-judged-in-whole-degrees)). An ambiguous position, given to an encoder or a builder, is cut to the box that holds it, never rounded first, so a value within a rounding step of 90 or 180 degrees is written in the box below the edge (89.9999167 degrees with two levels is `8959.  N`), not refused as a box centred past it ([interpretation](interpretations.md#ambiguity-cuts-a-raw-position)). A course of 0 is written only where it reads back as 0: uncompressed it is `000`, which APRS12c ch. 7 gives as unknown and a decoder reports as 0, while in Mic-E (where ch. 10's 0 reads back as no course) and in a compressed report (where a c of 0 reads back as 360) it is refused. A half is judged on the value in binary floating point, where a value within 1e-6 of a step's half, measured in steps, is the half: a latitude of 0.9764166666666666 degrees is 58.584999999999996 minutes and is written `0058.59N`, and a pressure of 986.9499999999999 mbar is `b09870`. A value derived from another (minutes from degrees, knots from km/h) is computed from the value given and rounded once. Where the only clean form needs a separating space (a Mic-E comment that would join a later PHG's digits into an altitude), the encoder writes the space: it refuses only data no clean form holds. Base-91 telemetry in a weather report, which has no comment, is refused. A third-party packet re-encodes with its inner packet's information field as received, even when it is empty; one whose inner header has a tolerated defect is refused, since the defect is part of its data, but one whose inner packet reads back with only `info` diagnostics is written. When a space after a voice frequency would make the comment read as one of its fields, the comment is written straight after it (`445.950MHz-500 T110`). Mic-E status text that would start with a type code character or 0x1D is written after a `/`; after Rev 0 telemetry, a comment starting with 0x1D is text and is written straight on. A delimiter (`/`, or a space) is written before a comment only where the comment would not read back as itself without one ([interpretation](interpretations.md#delimiters-at-the-start-of-free-text)). An altitude the GGA cs bytes cannot hold exactly, including one under 1 foot, is written as the nearest cs value (`!!` for 1 foot or less) and a `/A=` that wins; in a compressed weather report, which has no comment, the nearest cs value alone, so the report re-encodes `rounded`. A `{` in message, bulletin or NWS bulletin text, telemetry names or units, or a project title is refused: it would read back as `brace-in-message-text`. NWS bulletin text has no length limit; the 67-character limit is for messages and other bulletins, and counts characters (Unicode code points: APRS12c ch. 14 allows "printable ASCII or UTF-8 characters"), not bytes or UTF-16 units. A directed query's target is written straight after a type the spec defines, an APRSH target padded to 9 characters, and after one space for any other type (`?FOO N0QBF`). A snowfall is written in its three characters: it is rounded to hundredths if that leaves it under 1, else to tenths if that leaves it under 10, else to a whole number, and then written as a whole number in three digits when it is one (`002`; 0.995 as `001`, 9.96 as `010`), a number under 1 as `.` and two digits (0.5 as `.50`, 0.32 as `.32`), and any other as a digit, `.` and a digit (2.5 as `2.5`); one that rounds past 999 is refused. User-defined data is written back as it came, its user ID and packet type included, whatever the bytes. A general query footprint out of range, and an Agrelo bearing over 360, are refused. A position, object or item report's comment is written in one order: the voice frequency with its fields, the signpost or corridor braces, the `/A=` altitude, the free text, base-91 telemetry and the `!DAO!`; a frequency straight after a seven-byte data extension, or after a DF bearing (`/BRG/NRQ`) or storm data, which extend the course and speed, follows a `/`, as it does after a PHG or RNG in Mic-E status text, and after a PHGR, which ends in `/`, it follows straight on ([interpretation](interpretations.md#where-a-voice-frequency-goes)). A `!DAO!` on a compressed position carries the digits of the position reported ([interpretation](interpretations.md#dao-on-a-compressed-position)). A compressed speed byte may be `{` (90): APRS12c ch. 9 limits only the course byte to `!`-`z`, so such a speed is written back. A compressed report whose cs bytes carry a value (a course and speed, a range or wind) and whose data has no compression type gets the default one (`C`: current fix, other source, software), as a late `RNG` or late wind moved into the cs bytes does ([interpretation](interpretations.md#re-encoding-into-compressed-bytes-rounds)). DF or storm data with no course and speed is written after `.../...`, the form APRS12c ch. 7 gives that reads back as unknown (a course of `000` is a fixed DF station). Only one data extension follows the symbol, so a course/speed, an area, a DF bearing or storm data together with a PHG, RNG or DFS is refused: the second could only go later in the comment, where it reads back with `data-extension-in-comment`; Mic-E status text, which carries a PHG or RNG with no course/speed extension, is not affected. For the same reason comment text holding a well-formed PHG, RNG or DFS after an area, a DF bearing or storm data (`l710/310RNG12 RNG0050`) is refused. A compressed course with no speed, or a speed with no course, is refused: the cs bytes hold both, and writing one adds a value the data does not have. A `!DAO!` on an ambiguous position is refused, whatever its precision (`!W  !` too): it reads back with `dao-with-ambiguity`, which a decoder gives for every precision ([interpretation](interpretations.md#dao-on-an-ambiguous-position)). A humidity of 0 (after rounding) is refused, since `h00` is 100 percent. `T#MIC` with an empty first channel is refused: no form reads back with that channel empty. NMEA data whose fields disagree with its sentence, by more than the 1e-9 the cases compare within, is refused: written, it reads back with the sentence's values. Where a number arrives as data rather than as the text sent (the text wins when there is one), a telemetry value that is a whole number from 0 to 999 is three digits (`005`, `000`, 190.0 as `190`), as a sequence given as a number is; any other number (another telemetry value, an `EQNS.` coefficient, a footprint's latitude and longitude) is the shortest decimal that reads back as the same number, with no exponent and no `+`, a `0` before a leading point and no trailing `.0` (`0.53`, `-94`, 1e61 as `1` and 61 zeros); and a footprint's latitude and longitude each have one leading space unless negative, 0 included (`?APRS? 0,-117.15,0200`), with a radius of four digits in whole miles ([interpretation](interpretations.md#numbers-given-without-their-text)). A Mic-E locator followed by base-91 telemetry or a `!DAO!`, with no comment, is written with them straight after it (`` `IO91/G|!:&0'p| ``), and comment text that looks like a locator after a Mic-E PHG or RNG is written straight on (`]PHG3330IO91SX/G`), since a locator is only read at the start. There is no size limit: `refused` means this rule declines the data, never that an encoder's buffer is too small.
- **Refusal reasons.** Where data has several faults, the refusal names the first code that applies in this order: `not-encodable`; `invalid-address`, `ax25-cannot-carry`, `tnc2-cannot-carry`, `invalid-third-party-header`; `invalid-addressee`, `invalid-name`, `invalid-timestamp`, `not-a-number`, `value-out-of-range`, `value-has-no-form`, `invalid-code`, `invalid-symbol`, `invalid-character`, `too-long`, `padding-space`, `malformed`, `invalid-message-id`, `invalid-nmea`; `extension-conflict`, `field-not-allowed`, `symbol-mismatch`, `missing-field`, `value-given-twice`; `text-reads-as-field`; `does-not-read-back`. The header is written first, a field wrong on its own is wrong whatever else is given, what the frame cannot hold comes before the symbol and companions, and the safety net is last ([interpretation](interpretations.md#which-refusal-a-record-with-two-faults-gets)); `precedence.json` has a case for each pair of codes that one record can hold and its fault catalogue covers, and `tools/precedence-excluded.txt` lists the other pairs, each with the reason no record holds both (by a hand-made table of where each code can apply, which `check.py` holds the catalogue to). Some codes have no case, each for one reason: `not-a-number` (JSON cannot carry NaN or infinity), `invalid-address`, `ax25-cannot-carry` and `tnc2-cannot-carry` (they need a packet header, which an encode case does not give), `value-given-twice` (it needs builder input in two units), `not-encodable` (undecoded data: no neutral form of it is held by all six libraries) and `does-not-read-back` (the fallback). Fixed-form text (a locator, a bit sense, telemetry bits, a telemetry sequence of letters and digits or `MIC`, a capability token) is `malformed` whatever is wrong with it; free text is `too-long`, `invalid-character` or `padding-space`, and a capability value is free text. A telemetry project title over 23 characters is `too-long`. A telemetry report with no bits at all is `missing-field`; bits given that are not eight `0` or `1` characters are `malformed`. More analog values than a telemetry report (5) or base-91 telemetry (1-5) holds is `too-long`; fewer is `malformed`. NMEA data is its sentence: a field it leaves out is taken from the sentence and the sentence is written, while a field given that disagrees with the sentence is `invalid-nmea`, and so is a comment given with a sentence that has no checksum, since only a checksum ends a sentence ([interpretation](interpretations.md#nmea-data-is-its-sentence)). More than 15 `EQNS.` coefficients is `too-long`. A locator not in the fixed form (a status locator in lower case, which reads back in upper case, or one of 5 characters) is `malformed`. A `!DAO!` digit datum with added precision is `invalid-code`: a digit datum is read only with spaces for A and O. A third-party path entry before a used one that is not marked used reads back used, so it is `invalid-third-party-header`, as a bad inner address is. NaN or an infinity is `not-a-number` at every check that also catches it. A directed query's target is an addressee: a wrong length or character is `invalid-addressee`. A message whose addressee would make it read back as a bulletin or NWS bulletin (`BLN...`, `NWS-...`) is `invalid-addressee`. A Mic-E device suffix the device database does not know for the type code, a single space (a type code) included, is `invalid-code`, since the suffix is not free text. A builder given an altitude in feet and in metres refuses with `value-given-twice`. `_` with no weather data is `symbol-mismatch` whatever else the data holds, since a report is a weather report only when it carries weather (not in Mic-E, which cannot carry weather: a Mic-E `_` symbol is no fault, and such a report is refused only for its other faults); a course (with its speed) on the area symbol `\l` with no area is `symbol-mismatch` too, as `ddd/sss` would read back as an area, but a speed alone is written `.../sss`, which reads back cleanly as a speed on `\l`, so it is written; storm data without the hurricane symbol is `symbol-mismatch` too. A DF bearing and storm data together are `extension-conflict`: both extend the one course/speed. Uncompressed weather with course/speed, PHG, RNG, DFS, an area, a DF bearing or storm data is `extension-conflict`, as the wind holds the data extension. In a compressed report, course/speed and a range live in the cs bytes and never count toward one data extension: a 7-byte extension is `field-not-allowed` (it has no data extension), course/speed with a range is `extension-conflict`, and a compressed weather report's course/speed or range is `extension-conflict`. A compressed GGA altitude on a weather report is legitimate and never causes `extension-conflict` by itself: such a report refused only for comment-borne data (telemetry and so on) is `field-not-allowed`, and `extension-conflict` applies when something else also wants the cs bytes (a range, course or speed beside the GGA altitude). An altitude on a compressed weather report whose compression type is not GGA is `field-not-allowed` (its `/A=` needs the comment a weather report lacks). A field the report has no place for is `field-not-allowed` and that field's own checks (range, characters, length) do not run: a comment on a weather report is `field-not-allowed` even when it holds a line break, and a non-GGA altitude on a compressed weather report is `field-not-allowed` even past 999999 feet; a field whose place exists but is wanted twice (a range in cs bytes that hold the wind or a GGA altitude, a PHG beside a course and speed) or contradicts another (a `!DAO!` on an ambiguous position) still gets its own checks first, so a PHG digit of 10 beside a course is `value-out-of-range` and a digit datum with added precision on an ambiguous position is `invalid-code`. The bulletin rule for an addressee covers only a bulletin form (`BLN` then 0-9 or A-Z, or `NWS-`/`NWS_`); any other addressee starting `BLN` (`BLNe`, `BLN-`) is a station, and its message is judged on its text, so `?WX` to it is `text-reads-as-field`. A Mic-E altitude with no type code whose only form is the Mic-E altitude bytes (whole metres, beyond the 6 digits of a `/A=`), and whose first byte is a type code character (`` ` ``, `'`, `>`, `]` or a space), would read back with a type code: it has no form, `value-has-no-form`, not `text-reads-as-field` (no comment changed) and not `does-not-read-back`. When a read-back finds a change, free text that reads back changed is `text-reads-as-field` (a weather report's software type, unit and extra fields are free text) and anything else is `does-not-read-back`, never `field-not-allowed`; the ambiguity-box check runs only for a form that writes ambiguity (uncompressed and Mic-E), since on a compressed report ambiguity is already `field-not-allowed`; a read-back that catches a fault a named rule covers (an NMEA field that disagrees, `T#MIC` with an empty first channel, an ambiguous position centred past a pole or 180 degrees, a `!DAO!` on an ambiguous position, an unknown device suffix) reports that rule's code.
- **NMEA.** After `$` (unless the field starts `$ULTW`, which is raw weather), the text must be an NMEA 0183 sentence, or it is `invalid-nmea`, an error in both modes ([interpretation](interpretations.md#what--text-is-an-nmea-sentence)). A sentence is printable ASCII (0x20-0x7E, so not DEL). Its address field, up to the first `,`, is five upper-case letters or digits, or `P` and three or more of them (a proprietary sentence), and at least one field follows it. The fields contain no `$`, and no `*` except the one that starts a checksum. A checksum is `*` and two hex digits, in either case; the sentence ends there, the checksum must match, and any text after it is the `comment`, kept as sent. A `*` not followed by two hex digits is a reserved character in a field, so `invalid-nmea`. The sentence's structure is checked before its checksum, so a malformed sentence with a wrong checksum is `invalid-nmea`. Its length is not checked, and an encoder sets no limit either. Only GGA, GLL, RMC, VTG and WPL are read, by field position, and only from a five-character address that does not start `P`; any other sentence is kept as text ([interpretation](interpretations.md#reading-the-fields-of-an-nmea-sentence)). `sentence` is written without the `$`, up to and including any checksum. A field that is missing or does not parse (a position before the receiver has a fix, say) is left out, and the sentence is still decoded, however few fields it has. A position needs both coordinates: each is digits with an optional `.` and fraction, with at least three digits before the `.`, of which the last two are minutes (below 60) and the rest degrees, however many digits they have; at most 90 or 180 degrees; hemisphere `N` or `S`, `E` or `W`. `time` is `hhmmss` (hours 00-23, minutes and seconds 00-59) with an optional `.` and fraction, written `HH:MM:SS` with the fraction as sent, less trailing zeros. `fix` is RMC's or GLL's status, `A` valid and `V` invalid, or GGA's quality indicator, one digit, `0` invalid and any other valid. Speed, course and altitude are an optional `-` then digits with an optional `.` and fraction.

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
| `nmea` | `sentence`, `has_checksum`, `latitude`, `longitude`, `fix` (`valid`/`invalid`), `course_degrees`, `speed_knots`, `altitude_m`, `time`, `waypoint`, `comment` (the text after the checksum, as sent) |
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
| `range_miles`, `dfs`, `area`, `df_bearing`, `storm` | The other data extensions, codes as sent. Storm data's fields are digits, as APRS12c ch. 12 gives them (`/TS/150^200/0980>090&030%040`): unlike a weather value, a field holding a space is not one, so `> 90` makes the whole of it comment text. |
| `dao` | `datum` and `precision` (`none`/`thousandths`/`base91`). |
| `telemetry` | Base-91 comment telemetry: `sequence`, `analog`, `digital` (the eight binary channels, 0-255; bits 9-13 of the value are reserved and ignored). |
| `frequency` | APRS 1.2 voice frequency: `mhz`, `tone`, `tone_value`, `offset_khz`, `range`, `range_km`, `narrow`, `ten_khz_resolution`. |
| `weather` | `wind_direction_degrees`, `wind_speed_mph`, `wind_gust_mph`, `temperature_f`, `rain_1h_in`, `rain_24h_in`, `rain_midnight_in`, `rain_raw`, `humidity_percent`, `pressure_mbar`, `luminosity_w_m2`, `snow_24h_in`, `software`, `unit`, `extra` (`letter`, `value`). |
| `signpost`, `comment` | Signpost text, and the free text left once everything above is lifted out. |

## Adding a case

Send a pull request here. Write the `id`, `description`, `source`, `authority` and `input` by hand; the expected values can be drafted by any implementation and then checked. For `spec` and `interpretation` cases, check every value against the document the case cites: an implementation's output is a draft, not the authority. Encode cases are written by hand in full. `python3 tools/check.py` must pass, and the case should fail in an implementation whose behaviour it describes is broken.

A new diagnostic code goes in `codes.json` in the same pull request. A new interpretation goes in `interpretations.md`, and the cases that depend on it link to its heading.

### Drafting with Packet.Aprs

aprs-cs has this repository as a submodule at `spec/aprs`, and its corpus tool writes into it. From an aprs-cs checkout:

```sh
git submodule update --init spec/aprs
dotnet run --project tools/Packet.Aprs.Corpus -- vectors fill spec/aprs/cases/position.json
```

`fill` completes every decode case that has no `expect` yet (`expect`, `strict`, `reencode`) and leaves the others alone. Commit inside `spec/aprs`, push a branch of this repository, and open the pull request here; once it merges, aprs-cs moves its pin on.

Real packets come from the APRS-IS capture that aprs-cs's `aprs-corpus collect` writes:

```sh
dotnet run --project tools/Packet.Aprs.Corpus -c Release -- curate ~/aprs-corpus samples.txt
dotnet run --project tools/Packet.Aprs.Corpus -c Release -- vectors from-samples samples.txt spec/aprs/cases/corpus.json
```

`curate` picks one or two packets of every distinct shape; `from-samples` adds the ones not already in the file after the existing cases, which keep their ids. When Packet.Aprs changes on purpose, `vectors refresh <files>` works out every observed case again, so the change can be reviewed as a diff.

## Comparing implementations

The cases say what to make of every shape of packet they cover. To find what they do not cover, run the implementations side by side over many inputs and compare what each makes of every one. Each implementation has a dump tool with three modes, and `tools/compare.py` compares any number of dumps of the same input:

| Mode | Input | Each output record |
|---|---|---|
| decode | packets, one hex-encoded TNC2 line per line: a capture, or fuzzed packets from `tools/mutate.py` | the lenient and strict results, the bytes the lenient data re-encodes to, and the API view |
| encode | data in the neutral form, one object per line, from `tools/generate.py` | the bytes written, or a refusal, and what they decode to |
| build | builder recipes, one per line, from `tools/generate.py --recipes` | the TNC2 line built, or a refusal, and what it decodes to |

Every file is gzip-compressed JSON lines, and the output keeps the input's order.

```sh
# aprs-cs: extract a capture once, as one hex-encoded TNC2 line per line
dotnet run --project tools/Packet.Aprs.Corpus -c Release -- diff lines ~/aprs-corpus lines.hex.gz
# here: fuzzed packets, neutral data and builder recipes
python3 tools/mutate.py lines.hex.gz fuzz.hex.gz --seeds 50000 --count 2000000 --seed 1
python3 tools/generate.py data.jsonl.gz --count 1000000 --seed 1
python3 tools/generate.py recipes.jsonl.gz --recipes --count 1000000 --seed 1
python3 tools/generate.py faults.jsonl.gz --faults --count 1000000 --seed 1            # two or three faults a line, values at their bounds
python3 tools/generate.py faults-recipes.jsonl.gz --recipes --faults --count 1000000 --seed 1
# each implementation: decode (the default), --encode or --build
dotnet run --project tools/Packet.Aprs.Corpus -c Release -- diff dump lines.hex.gz cs.jsonl.gz    # or diff encode / diff build
cargo run --release --example diff_dump -- lines.hex.gz rs.jsonl.gz                               # aprs-rs
python3 tools/diff_dump.py lines.hex.gz py.jsonl.gz                                              # aprs-py
npm ci && npm run build && node scripts/diff-dump.mjs lines.hex.gz ts.jsonl.gz                   # aprs-ts
zcat lines.hex.gz | build/pdn_aprs_diffdump | gzip > c.jsonl.gz                                  # aprs-c
go run ./cmd/aprs-diffdump lines.hex.gz go.jsonl.gz                                             # aprs-go
# here: compare them
python3 tools/compare.py cs.jsonl.gz rs.jsonl.gz py.jsonl.gz ts.jsonl.gz c.jsonl.gz go.jsonl.gz --input lines.hex.gz --json summary.json
```

`compare.py` needs only Python's standard library. It groups the inputs on which the implementations differ by what differs and by which implementations side together, with a count and examples for each, and exits 1 if there are any. A new implementation needs only the dump tool. Each rule a disagreement over real packets settles becomes a case in `differential.json`; one found by fuzzing, generated data or recipes becomes a case in the file for its area, with the source `differential fuzzing` and the date.

### Decode records

```json
{"n": 0, "lenient": R, "strict": R, "reencode": "equivalent", "written": "21343231362e...", "api": A}
```

- `lenient` and `strict` are `{"header", "data", "diagnostics"}` in the neutral form, or `{"header_error": [...]}` when the header is unusable.
- `reencode` says how the lenient data encodes again: `identical`, `equivalent`, `refused`, `fails` (it wrote bytes that do not decode, leniently and cleanly, to the same data), or `none` when there is nothing to re-encode (a header error, or unrecognized data). To judge it, decode the bytes written under a well-formed header (for Mic-E, the destination the encoder computed), so that a defect in the original header is not counted against the encoder.
- `written` is the information field the encoder wrote, as hex, whenever it wrote one; `written_destination` is the destination it computed for Mic-E. The implementations should write the same bytes, byte for byte: see the Encoding rule.
- `reencode_refusal`, when `reencode` is `refused`, is the reason code (an id from `refusals` in `codes.json`). It is optional: a 1.0.0 dump does not write it, and `compare.py` compares it only among the dumps that do.
- `api` is the API view of the lenient packet (below), when there is one.

### The API view

What a library's own API offers beyond the neutral form, read through the public API a program would call, not through the code that writes the neutral form (which the cases already test). An implementation writes only the keys its API offers, and `compare.py` compares each key among the implementations that write it.

| Key | What |
|---|---|
| `source`, `destination` | The header addresses, from the packet's accessors. |
| `path` | The path, each entry as text with a `*` when it is used. |
| `q_construct` | `{"construct": "qAR", "station": "N0CALL"}` from the q-construct accessor, or `null` for none. |
| `third_party` | `true` for a packet carried inside a third-party packet, from the accessor that says so. |
| `has_errors`, `has_warnings` | The packet's own accessors for its diagnostics. |
| `tnc2` | The packet written back as a TNC2 line by the library, as hex: its header and the information field as received. |
| `ax25` | The packet as an AX.25 UI frame (hex, without flags or FCS), or `"refused"` when the library will not write one (an address AX.25 cannot carry as sent: an SSID written with a leading zero or as `-0`, `WB4APR-00` or `N0ZO-0`, which a frame would give back as `WB4APR` or `N0ZO`; a call of more than six characters or with lower-case letters, such as the APRS-IS q-construct `qAC` or `T2ROMANIA`; an SSID over 15 or not a number; more than eight path entries). |
| `ax25_refusal` | When `ax25` is `"refused"`, the reason code (`ax25-cannot-carry` or `invalid-address`). |
| `device` | The device the library identifies from the destination or the Mic-E bytes: `vendor`, `model` and `class` as the aprs-deviceid database gives them (each left out when it gives none), or `null`. Every packet's view gives it, an inner packet's and an unrecognised packet's too, since it comes from the destination, not the data. The lookup is case-sensitive, as the database lists tocalls in upper case and a destination is a callsign (`APNl02` matches nothing), and its wildcard `n` is a digit. |
| `symbol` | `{"description": "Car"}`: the library's description of the symbol in the data, when there is one. |
| `phg` | For data with a PHG, what the library derives from its codes: `watts`, `height_feet`, `gain_db`, `directivity_degrees` (`null` for omnidirectional). |
| `inner` | The same view of a third-party packet's inner packet. |

### Encode records

`tools/generate.py` writes one object per line: `{"n": 0, "data": D, "exact": true}`. `D` is data in the neutral form, recombined from the cases' own data with new values, text chosen to be awkward, and fields dropped. With `"exact": true`, every value is one its format holds exactly, so the bytes written must decode to `D` itself; with `false`, some value lies between the steps its format holds and is rounded as the Encoding rule says. With `--faults`, a line instead gets up to three faults on purpose, each on its own field, where its report type has any (two or three where it has that many; user-defined, test and raw weather data have none, about 3 percent of data lines): a value at its bound or half a step either side, a field the report has no place for, a companion left out, a fault inside a third-party packet, and for recipes a value given in two units. They are named in `"faults"`, with `"exact": false`; a value at its bound may be in range, so such a line can still be written. Uniform data rarely has two faults in one record, which is where the Refusal reasons order decides the code. `--nonfinite` adds NaN and infinities, written as the non-standard JSON tokens `NaN` and `Infinity`, for dump tools that read them. Each implementation converts `D` to its own data, encodes it, and writes:

```json
{"n": 0, "result": "written", "info": "21343231362e...", "destination": "APZ001", "again": {"data": D2, "diagnostics": [...]}}
```

- `result` is `written`, `refused` (the Encoding rule declines the data), or `unsupported` with a `reason` (the implementation's own data cannot hold something in `D`, which `compare.py` skips).
- `refusal`, when `result` is `refused`, is the reason code, an id from `refusals` in `codes.json`, beside the library's own `reason` text. It is optional: a 1.0.0 dump does not write it, and `compare.py` compares it only among the dumps that do.
- `info` is the information field written, as hex; `destination` is the Mic-E destination the encoder computed, and `APZ001` for everything else.
- `again` is `info` decoded leniently under `N0CALL>` and that destination, in the neutral form.

### Build records

`tools/generate.py --recipes` writes one builder recipe per line: what to build, with every input given (the time included, so the result does not depend on the clock):

```json
{"n": 0, "station": {"source": "N0CALL", "destination": "APZ001", "path": ["WIDE1-1"]}, "report": "position",
 "args": {"latitude": 51.50735, "longitude": -0.12776, "symbol": "/>", "speed_kmh": 42.5, "comment": "hello"}}
```

| `report` | `args` |
|---|---|
| `position` | `latitude`, `longitude` in degrees, `messaging`, `timestamp`, and the positioned options |
| `object` | `name`, `latitude`, `longitude`, `timestamp`, `killed`, and the positioned options |
| `item` | `name`, `latitude`, `longitude`, `killed`, and the positioned options |
| `mic-e` | `latitude`, `longitude`, `mic_e_message`, `messaging`, and the positioned options |
| `weather` | `timestamp`, the weather values, and `latitude`, `longitude` and `symbol` for a report with a position (without them, a positionless report) |
| `message` | `addressee`, `text`, `message_id`, `reply_ack` |
| `ack`, `reject` | `addressee`, `message_id` |
| `bulletin` | `id` (one character), `group`, `text` |
| `status` | `text`, `timestamp`, `locator` with `symbol`, `beam` (`heading_code`, `power_code`) |
| `telemetry` | `sequence` (a number), `analog` (five numbers, `null` for an empty channel), `bits` (eight `0` or `1`), `comment` |
| `telemetry-names`, `telemetry-units` | `names` or `units` (text), `addressee` (the station itself when absent) |
| `telemetry-coefficients` | `coefficients` (numbers), `addressee` |
| `telemetry-bits` | `bits`, `project`, `addressee` |

- The positioned options: `symbol` (`"/>"`), `course_degrees`, `speed_knots` or `speed_kmh`, `altitude_feet` or `altitude_m`, `comment`, `phg` (codes as in the data form), `range_miles`, `frequency` (`mhz`, and optionally `tone` (`tone`, `ctcss` or `dcs`) with `tone_value`, and `offset_khz`), `compressed`, `ambiguity` (1-4), `dao` (`true`: add a `!DAO!`, datum `W`, base-91), `telemetry` (`sequence`, `analog`, `digital`).
- The weather values: `wind_direction_degrees`, `wind_speed_mph`, `wind_gust_mph`, `temperature_f` or `temperature_c`, `rain_1h_in`, `rain_24h_in`, `rain_midnight_in` (or `rain_1h_mm` and so on), `humidity_percent`, `pressure_mbar`, `luminosity_w_m2`, `snow_24h_in`.
- `timestamp` is `{"utc": "2026-09-27T09:23:45Z", "format": "dhm"}`, the format being `dhm` (day, hours, minutes, zulu), `hms` or `mdhm` (a positionless weather report's).
- Values are as a program would have them: a latitude from a GPS receiver, a speed in km/h. What a builder makes of them is settled like any other disagreement; the rules so far are below and in the Encoding rule, which a builder's output meets like any encoder's.

Builder rules:

- **Course 0 is unknown.** A builder's course of 0 is the spec's 0, an unknown course (APRS12c ch. 7 and ch. 10), and north is 360: an uncompressed report writes `000`, Mic-E writes 0, and a compressed report refuses it, since the cs bytes have no unknown course. A course that rounds to 0 whole degrees (0.3) is unknown too: whether a course is unknown, and whether it is in range (1-360), is decided in whole degrees, the unit APRS gives a course in, and a known course in range is then rounded once to its field's step, so a compressed course of 1.2 degrees is north (c = 0), not unknown ([interpretation](interpretations.md#a-builders-course-of-0-is-unknown)). The same holds for an encoder given neutral data.
- **Units.** km/h is converted to knots (1 knot is 1.852 km/h), metres to feet (1 foot is 0.3048 m), Celsius to Fahrenheit, millimetres to inches (25.4 to the inch), and the result rounded once as the Encoding rule says. A Mic-E altitude given in metres goes in the Mic-E altitude bytes, whose unit is the metre (APRS12c ch. 10), rounded to the metre; one given in feet goes in a `/A=`.
- **Ambiguity.** On a raw position the reported box is the one that holds the position: its digits are cut, not rounded, then blanked (49 degrees 03.596 minutes with one level is the box 03.5x, centre 03.55), and a value within 1e-6 of the box edge above it, in the box's units, is on that edge (80.49 degrees is 29.40 minutes, box 29.4x), and the centre goes in the Mic-E longitude digits a decoder ignores ([interpretation](interpretations.md#ambiguity-cuts-a-raw-position)).
- **DAO.** On a raw position with a `!DAO!`, the position is taken in DAO steps (thousandths of a minute, or ninety-firsts of a hundredth), rounded once, and split into the main digits and the DAO digits ([interpretation](interpretations.md#dao-base-91-digits)).
- **Timestamps** from a UTC time are cut to the field's resolution, not rounded (09:23:59 is `0923` in `dhm`): a clock shows a minute until the next one begins.
- **Telemetry.** A sequence from a program is 0-999, written in three digits (APRS12c ch. 13 `sss`); a larger one is refused, not wrapped. Values follow the Encoding rule's numbers given without their text.
- **Mic-E messaging.** The type code is how a Mic-E report says whether the station can message (`` ` `` it can, `'` it cannot): a builder writes `` ` `` when the program says the station can message and `'` when it does not, unless the program gives a device type ([interpretation](interpretations.md#mic-e-messaging-from-a-builder)).
- **Out of range is refused, never clamped:** an object name over 9 characters, an item name outside 3-9, a message ID that is empty or over 5 characters (APRS12c ch. 14: 1-5 letters or digits), a telemetry sequence over 999.

Each implementation calls its builder as a program would (the fluent builder, the station methods, whatever its API offers) and writes:

```json
{"n": 0, "result": "built", "tnc2": "4e3043414c4c3e...", "again": {"header": H, "data": D, "diagnostics": [...]}}
```

`result` is `built`, `refused` (the builder or encoder declined), or `unsupported` with a `reason` (the builder has no way to say something in the recipe); `tnc2` is the line built, as hex; `again` is that line decoded leniently. A `refused` record gains `refusal`, the reason code, as an encode record does.
