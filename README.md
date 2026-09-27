# APRS conformance vectors

Language-neutral test cases for APRS decoders and encoders: what a packet means, what is wrong with it, and what a strict and a lenient decoder should each make of it. Any implementation in any language can run them, and every implementation below consumes them the same way: as a git submodule, pinned to a commit, run by its own test suite on every build.

The cases come from three places, and each says which:

| Authority | Meaning | An implementation should |
|---|---|---|
| `spec` | The expected values follow from the text of APRS12c or *Understanding APRS Packets* (UAP), usually a worked example printed there. | match them |
| `interpretation` | The spec is ambiguous, contradicts itself or is wrong here; the expected values follow a decision recorded in [`interpretations.md`](interpretations.md), linked from the case. | match them or document why not |
| `observed` | A real packet from the APRS-IS feed; the expected values are what an implementation made of it when the case was recorded (Packet.Aprs, for every case so far), kept as a regression record. | treat a difference as a question, not a failure |

About 250 cases cover every example packet printed in APRS12c and UAP, the encoder, and every defect a lenient decoder may tolerate; another 1,395 are real packets of every distinct shape seen on APRS-IS; 40 more pin the rules on which two implementations disagreed over a whole capture, and 120 more the rules that differential fuzzing of all five implementations settled.

**Licence:** AGPL-3.0-or-later ([`LICENSE`](LICENSE)).

## Implementations

| Implementation | Language | Repository | Package |
|---|---|---|---|
| Packet.Aprs | C# (.NET) | [packet-net/packet.net](https://github.com/packet-net/packet.net) | [NuGet `Packet.Aprs`](https://www.nuget.org/packages/Packet.Aprs) |
| pdn-aprs | Rust (`no_std` + `alloc`) | [packet-net/aprs-rs](https://github.com/packet-net/aprs-rs) | [crates.io `pdn-aprs`](https://crates.io/crates/pdn-aprs) |
| pdn-aprs | Python (3.10+) | [packet-net/aprs-py](https://github.com/packet-net/aprs-py) | [PyPI `pdn-aprs`](https://pypi.org/project/pdn-aprs/) |
| pdn-aprs | TypeScript (Node 20+, browsers) | [packet-net/aprs-ts](https://github.com/packet-net/aprs-ts) | [npm `@packet-net/pdn-aprs`](https://www.npmjs.com/package/@packet-net/pdn-aprs) |
| pdn_aprs | C (C99, no allocation) | [packet-net/aprs-c](https://github.com/packet-net/aprs-c) | [GitHub releases](https://github.com/packet-net/aprs-c/releases): `pdn_aprs.h` + `pdn_aprs.c` |

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
| `canonical_info` | no | With `equivalent`: the bytes the Encoding rule below leads to. Where that rule says what to write (a Mic-E status text starting with 0x1D goes after a `/`, say), an encoder writes those bytes; where it leaves a choice, another encoder may choose differently and still conform. |

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
- `reencode: "equivalent"` means the bytes written decode, leniently, to the same data with no warnings or errors. `canonical_info` is one clean form; where the Encoding rule leaves a choice, it is not the only one.
- A tolerance check (turning off only the one tolerance a case used) applies to cases whose lenient diagnostics name exactly one tolerable code; it must give the `strict` result.

### Rules the cases rely on

These follow from the cases, but an implementation meets them before it meets the case, so they are spelled out here.

- **Addresses and path.** On APRS-IS an address is 1-9 letters, digits or `-`. Anything else in a TNC2 header, whether the source, the destination or a path entry, is `invalid-address`; a missing `>` or `:`, or an empty source, is `invalid-header`. A path entry is used when it is marked `*` or comes before one that is, and the neutral form writes `*` on every used entry. An entry of `qA` and one more letter, in either case, is a q-construct, and the entry after it is its station; this is read only in the outer header, so a third-party header's path is kept as sent and its packet has no `q_construct`. In a third-party header the source may be 1-9 printable ASCII characters (0x20-0x7E) other than `>` and `:` (APRS12c ch. 17), while the destination and path follow the rule above; anything else there is `invalid-third-party` ([interpretation](interpretations.md#third-party-header-addresses)). A defect the inner header may tolerate (several used markers, say) is decoded leniently, with its warning on the inner packet, and a strict decoder rejects the packet as `invalid-third-party`.
- **Data type identifiers.** `&`, `+` and `.` are reserved: `unrecognized` with reason `reserved-data-type` and an `info:reserved-data-type`. 0x1C and 0x1D are Mic-E (Rev 0 beta units, APRS12c ch. 10) with an `obsolete-format` info, given for the data type identifier before anything else is checked, whatever follows it; 0x1D, like `'`, is `old_data`. Any other first byte that is not a data type identifier is `not-aprs`. An empty information field is `empty`, with no diagnostic.
- **Device.** `device` is recorded only in Mic-E cases. A case without it says nothing about device identification, so do not check that it is absent.
- **Text that is not UTF-8** is read as Latin-1: the whole text (a comment, a message or status text, a telemetry list), with one `non-utf8-text` warning for it. Bytes outside the text, such as a garbled timestamp that was skipped, do not count.
- **Numbers as sent.** Telemetry values and equation coefficients are compared as numbers, but `identical` re-encoding needs the text as sent (`073`, `190.0`, `.53`), so keep it.
- **The order of checks.** When a packet has several defects, a strict decoder rejects it by the first one it meets, and it meets them in reading order: a defect later in the packet never changes the diagnosis of one before it ([interpretation](interpretations.md#a-packet-is-read-in-order)). Structural checks (addressee, braces, fields, a `!DAO!`) come before the text's encoding. In a position, object or item weather report, the wind is decided where the `DDD/SSS` extension belongs, before any field: missing wind (`incomplete-weather`) and wind sent as `c` and `s` fields (`wind-fields-instead-of-extension`) are both met there, before any field's width.
- **Weather.** A report with the weather station symbol (`_`, either table) is weather even with no fields. The fields are one contiguous run, which ends at the first thing that is not a field, at a defined field already read, and at `c` once the wind is known ([interpretation](interpretations.md#which-weather-field-a-letter-is)). Before that, `c` is the wind direction wherever it comes, but only with a value after it. A positionless report's wind always comes as fields; a position, object or item report's comes as fields only once a `c` has been read, so an `s` before any `c` there is snowfall. When the wind comes as fields, `s` is the wind speed until the speed is known, wherever it comes, and snowfall after that. `L` and `l` are one field, luminosity. Extra fields are kept as a list, so a repeated extra letter does not end the run. A value is digits (only `t` may start with `-`), a run of dots (read up to the field's width, so `s.....` is an unknown snowfall and two dots of text), or exactly the field's width of spaces. Snowfall's three characters may include one decimal point (APRS12c: "A decimal point is allowed for non-integer values"), so `s.50` is 0.5 inches; a value that holds a digit is a number, not a run of dots. A wind direction over 360, in the extension or a `c` field, is `out-of-range-value` (tolerated) and is dropped. After the fields of a position, object or item report, base-91 telemetry and a `!DAO!` are lifted out first; a positionless report keeps them in its comment. What is left is the software type and unit if it is a letter then a 2-4 character unit of letters, digits, `-` or `_` (not all digits), and nothing else, and otherwise `weather-comment` text, from which an altitude or a data extension is not lifted. A positionless report's comment keeps its leading space or `/`. A letter the spec does not define followed by a run of two or more digits, dots or `-` (the whole run, up to the first other character) that ends in a digit is an `extra` field. A field shorter than its fixed width, or one longer (`h7`, `t45`, `h100`, `b...`), is `non-standard-weather-field-width`; so is a fixed-width value that runs on into one more digit, which is read at the longer width. One that runs on by two or more digits is read at its own width, and the fields end there. Snowfall keeps its width of three characters, and only a run of dots may be shorter, when no digit follows it (`s..6` is not a field) ([interpretation](interpretations.md#which-weather-field-a-letter-is)), so `s00/` is not a field and in `s.050` the last `0` is text.
- **Complete weather.** `incomplete-weather` is given once for each missing part. A positionless report gets one if any of `c`, `s`, `g` and `t` is missing. A position, object or item report gets one if the wind is missing or incomplete (no `DDD/SSS` extension, and not both `c` and `s` fields) and another if `g` or `t` is missing. A value sent as unknown, dots or spaces, counts as present. Humidity `h00` is 100 percent; a humidity over 100 is `out-of-range-value` (tolerated) and is dropped. After a compressed position the cs bytes are the wind, and cs bytes that carry none mean it is unknown, so it is never missing ([interpretation](interpretations.md#wind-in-a-compressed-weather-position)); wind sent after a compressed position follows [another](interpretations.md#wind-after-a-compressed-weather-position).
- **Comments.** Structured elements are lifted out of a comment in this order, so that one is not taken for another: base-91 telemetry, only looked for between the last two `|`, and a `!DAO!`, the last one outside it; a `/A=` altitude anywhere, which wins over a compressed or Mic-E one; signpost or corridor braces, the first `{` followed by 1-3 characters and a `}`, wherever it is (so `{5Wm{55}` has the signpost `55`), the characters being printable ASCII for a signpost, which needs the `\m` symbol and not an overlaid `m`, or digits for a corridor; a data extension later in the text, only when none came straight after the symbol (the first well-formed `PHG`, else the first well-formed `RNG`, else the first well-formed `DFS`; a malformed one such as `PHG12` is comment text and does not stop the search, [interpretation](interpretations.md#a-late-data-extension-is-the-first-well-formed-one)), where a course/speed, or a compressed course/speed or altitude, does not count as one but PHG, RNG, DFS and a compressed range do; and a voice frequency at the start, after at most one space or `/`. A `!DAO!` is five bytes as sent, so taking another element out never joins one, and a digit datum is only read with spaces for A and O ([interpretation](interpretations.md#dao-datum-digits)). Braces around anything but printable ASCII are not a signpost ([interpretation](interpretations.md#signpost-overlays-are-printable-ascii)). `MHz` may be in any case, but a microwave band letter (`A96.000MHz` for 1296 MHz) is upper case. A frequency's tone, offset and range fields each need a space before and a space or the end after, and come in that order: one out of order, and everything after it, stays in the comment; a range is `R`, two digits, then `m` or `k`, and one space after the frequency is dropped. Last, one leading space or `/` is dropped from what is left. PHG and DFS height codes run from `0` on through the ASCII table to `~`, as the spec's height doubling allows.
- **Telemetry.** A report's sequence is `MIC` or letters and digits up to a comma ([interpretation](interpretations.md#telemetry-sequence-numbers-are-not-3-characters)). Each value ends at a comma or the end of the field; an empty one is `null`, and one left by a trailing comma still counts. A value is an optional `-`, then digits with an optional decimal point (at least one digit): no `+`, no spaces, nothing else, or the report is `invalid-telemetry`, an error ([interpretation](interpretations.md#numbers-in-telemetry)). The eight bits are only read after all five values; fewer values, or no bits, is `invalid-telemetry`, tolerated, and anything after that is the comment. An `EQNS.` with no coefficients at all (`EQNS.,,,`) is a plain message with an `invalid-telemetry-metadata` info. In `EQNS.`, trailing commas and spaces are the list stopping ("the list may stop at any field", APRS12c ch. 13), and a coefficient is a number as above that may also have spaces (U+0020 only) around it and an exponent (`e` or `E`, an optional sign, digits). A coefficient must be a finite number (`0eN` is 0), or the `EQNS.` is a plain message with an `invalid-telemetry-metadata` info. A `{` in a `PARM.`, `UNIT.` or `BITS.` list that does not start a message ID stays in the list (`brace-in-message-text`); it does not make the message a plain one ([interpretation](interpretations.md#a-brace-in-telemetry-metadata)). Metadata sent as a numbered message keeps its `message_id`, and its structure (the `PARM.` or other prefix, and the list) is checked before its text's encoding. An empty `PARM.` list is one empty name.
- **Messages and queries.** When the tenth byte is `:`, the addressee is the nine bytes before it, whatever they hold (a `:` or space among them is `invalid-addressee-characters`). Only when it is not is a `:` looked for earlier: straight after the first, it is not an unpadded addressee but an empty one, `invalid-message`; later, it ends an addressee before its ninth character, which is `unpadded-addressee` (tolerated) and is then checked like any other: empty, or with a byte that is not printable ASCII, it is `invalid-message`; with a space or `:` in it, `invalid-addressee-characters`. An addressee is a bulletin when it is `BLN` then a digit or an upper-case letter; `BLN` followed by anything else is an ordinary message. The message ID starts at the last `{` followed by 1-5 letters or digits (and optionally `}` and a reply-ack); any other `{` is `brace-in-message-text`, and the ID is still read. Bulletins, NWS bulletins and telemetry metadata take a message ID but not the reply-ack form: `{MM}` or `{MM}AA` on them is `brace-in-message-text`, and the text is kept ([interpretation](interpretations.md#reply-acks-are-for-messages)). An ack or rej is `ack` or `rej`, an ID of 1-5 letters or digits, optionally `}` and a reply-ack, and optionally a message ID (`message-id-on-ack`, tolerated); anything else after the ID makes the text a plain message. Only a message can be a directed query, since APRS12c addresses one to "the station being queried": bulletin and NWS bulletin text that starts `?` is just text. In the same way only a message can be telemetry metadata, which APRS12c addresses to "the callsign of the station transmitting the telemetry data": bulletin and NWS bulletin text starting `PARM.`, `UNIT.`, `EQNS.` or `BITS.` is just text. A query type is upper-case letters, apart from the spec's own `PING?` ([interpretation](interpretations.md#query-types-are-upper-case-letters)). Text starting `?` and a type of upper-case letters the spec does not define (`?WX`) is still a directed query, which the recipient ignores; a known type in lower case, a message ID or any other `{`, or a target that is not one callsign (1-9 letters, digits or `-`) makes it a plain message with an `invalid-query` info. One space between the type and the target is a separator, and spaces after the target are padding ([interpretation](interpretations.md#a-directed-querys-target-is-one-callsign)). A general query's footprint is a latitude and longitude in decimal degrees (a positive value may have a leading space) and a radius of exactly 4 digits; anything else, a latitude beyond 90 or a longitude beyond 180, or a query type that is not upper-case letters (`?IGAT7?`), is `invalid-general-query` ([interpretation](interpretations.md#a-general-query-footprint-is-a-real-place)).
- **Timestamps that are not there.** A `/` or `@` report whose timestamp is not 6 digits then `z`, `/` or `h` is read with the position straight after the DTI if that position decodes, else after seven bytes (`malformed-timestamp`, tolerated). When neither decodes, the report is `malformed-timestamp`, an error. An object's seven timestamp bytes that look like one (six digits, or ending `z`, `/` or `h`) but are not, with a position after them, are `malformed-timestamp`; otherwise the object has `object-without-timestamp` and its position starts straight after the name. Whether a position follows is judged on the position itself (latitude, symbol table, longitude and symbol code, or the 13 bytes of a compressed position), not on anything after it, and under the options in force, so such an object can decode differently lenient and strict. An object report shorter than 11 bytes is `truncated`. An item's `!` or `_` is looked for from the fourth byte on, so a name has at least three characters.
- **Positions.** A zero latitude or longitude keeps its hemisphere letter so that it re-encodes `identical`, though the neutral form writes 0 either way. A latitude's or longitude's digits, and its range, are checked before its hemisphere letter. The latitude alone sets the ambiguity, and one whose reported centre is past 90 degrees (`90  .  N`, centred on 90 degrees 30 minutes) is `invalid-latitude`, met before the longitude, as a longitude whose centre is past 180 degrees is `invalid-longitude`: in the longitude, each digit place that level blanks is ignored and may hold a digit or a space, in any mix, and a space in any other place is `invalid-longitude` ([interpretation](interpretations.md#longitude-blanks-follow-the-latitude)). Text, then a `!` and a position (the TNC beacon form), is only taken as a position report when the `!` is within the first 40 characters (offset 39 at most) and what follows it decodes as one. An empty position is `truncated`. A DF report's bearing (`/BRG/NRQ` after the course and speed) is degrees, so one over 360 is `out-of-range-value` (tolerated) and the whole `/BRG/NRQ` is dropped, as an out-of-range course is.
- **Mic-E.** The destination is checked first, its latitude before anything in the information field (a latitude of exactly 90 degrees is valid, but one whose ambiguity puts its centre past 90 degrees, such as `90LLLL`, is `invalid-mic-e-destination`). Then come the nine fixed bytes of the information field, as sent: an 0xFF among them is out of range like any other byte. Information bytes outside the ranges APRS12c gives, or fewer than 9 of them, are `invalid-mic-e-information`; after them the course is checked (over 360 is `out-of-range-value`, tolerated), then the symbol. Only then is every 0xFF byte in the status text removed (`kenwood-ff-padding`, tolerated), so a report that fails earlier has no padding warning ([interpretation](interpretations.md#mic-e-0xff-padding-is-in-the-status-text)). `mic-e-missing-device-type` applies only when there is status text. A device suffix is matched only after the type codes `` ` `` or `'` (two characters) or `>` or `]` (one). A PHG straight after the type code is lifted before an altitude is looked for later in the text, so its bytes are never read as one (`0PH}` in `PHG3330PH}`). An altitude that is not at the start is the first run of three base-91 characters and `}`. For `identical` re-encoding the encoder uses the printable forms APRS12c ch. 10 allows (longitude minutes under 10 + 60, speed tens + 80 below 200 knots, course hundreds + 4), and with ambiguity writes the centre it reports into the longitude digits a decoder ignores.
- **Capabilities.** The text's encoding is checked before free text. Items are split at commas, and each item at its first `=` into a token and a value. Spaces (U+0020, and no other character) around an item, a token or a value are padding and are dropped; an item left empty is skipped. The report is free text (`free-text-capabilities`) when a token is empty or holds a space or a control character (below U+0020, or U+007F), or a value holds a control character; a space inside a value is text ([interpretation](interpretations.md#station-capabilities-items-tokens-and-values)). An encoder refuses a token that is empty or holds a space, a control character, `,` or `=`, and a value that holds a control character or `,`, or starts or ends with a space.
- **Status.** `^`, a heading code (`0`-`9`, `A`-`Z`) and an ERP code (`1`-`9`, `:` to `@`, `A`-`K`) at the very end of the text is a beam heading; the text before it is kept as sent, spaces included. `^B0` is text, since `0` is not an ERP code.
- **Agrelo DF.** A report is exactly `%`, three bearing digits from 000 to 360, `/` and one quality digit; anything else is `invalid-agrelo-df` ([interpretation](interpretations.md#an-agrelo-bearing-is-0-to-360)).
- **Raw data.** Raw weather station data is printable ASCII, or `invalid-weather`.
- **Encoding.** An encoder never writes bytes that read back as different data: it writes an equivalent form or refuses, and only the rounding [interpretations.md](interpretations.md#re-encoding-into-compressed-bytes-rounds) describes may change a value. Where the only clean form needs a separating space (a Mic-E comment that would join a later PHG's digits into an altitude), an encoder may write the space or refuse. Base-91 telemetry in a weather report, which has no comment, is refused. A third-party packet re-encodes with its inner packet's information field as received, even when it is empty; one whose inner header has a tolerated defect is refused, since the defect is part of its data. When a space after a voice frequency would make the comment read as one of its fields, the comment is written straight after it (`445.950MHz-500 T110`). Mic-E status text that would start with a type code character or 0x1D is written after a `/`. An altitude the GGA cs bytes cannot hold exactly, including one under 1 foot, is written as the nearest cs value (`!!` for 1 foot or less) and a `/A=` that wins. A `{` in message, bulletin or NWS bulletin text, telemetry names or units, or a project title is refused: it would read back as `brace-in-message-text`. NWS bulletin text has no length limit; the 67-character limit is for messages and other bulletins. A directed query's target is written straight after a type the spec defines, an APRSH target padded to 9 characters, and after one space for any other type (`?FOO N0QBF`). A snowfall is written exactly in its three characters, with a decimal point where it needs one (0.32 as `.32`), and refused when they cannot hold it. User-defined data is written back as it came, its user ID and packet type included, whatever the bytes. A general query footprint out of range, and an Agrelo bearing over 360, are refused.
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
| `range_miles`, `dfs`, `area`, `df_bearing`, `storm` | The other data extensions, codes as sent. |
| `dao` | `datum` and `precision` (`none`/`thousandths`/`base91`). |
| `telemetry` | Base-91 comment telemetry: `sequence`, `analog`, `digital` (the eight binary channels, 0-255; bits 9-13 of the value are reserved and ignored). |
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
# aprs-rs, aprs-py, aprs-ts and aprs-c: decode the same lines
cargo run --release --example diff_dump -- lines.hex.gz rs.jsonl.gz
python3 tools/diff_dump.py lines.hex.gz py.jsonl.gz
npm ci && npm run build && node scripts/diff-dump.mjs lines.hex.gz ts.jsonl.gz
cmake -S . -B build && cmake --build build --target pdn_aprs_diffdump && zcat lines.hex.gz | build/pdn_aprs_diffdump | gzip > c.jsonl.gz
# here: bucket the disagreements
python3 tools/compare.py cs.jsonl.gz rs.jsonl.gz --names C# Rust --lines lines.hex.gz --json summary.json
```

`compare.py` needs only Python's standard library. It groups disagreements by which fields and diagnostics differ, with a count and example packets for each, and exits 1 if there are any. When one side re-encodes byte for byte and the other only equivalently, both round-trip and the encoders merely write different bytes; that is reported as an encoder choice, not a disagreement. A new implementation needs only the dump: read the lines file, decode each line, and write the same JSON. To judge a re-encoding, decode the bytes written again under a well-formed header (for Mic-E, the destination the encoder computed), so that a defect in the original header is not counted against the encoder. Each rule a disagreement over real packets settles becomes a case in `differential.json`; a rule found by fuzzing, whose packets are made up, becomes a case in the file for its area, with the source `differential fuzzing` and the date.

Real traffic only exercises the packets people send. To reach the rest, `tools/mutate.py` makes mutated packets from a capture's lines file and the cases' own inputs: cut short, bytes changed to ones APRS gives meaning to, fields spliced in from other packets, numbers pushed to their limits, the data type changed. Dump them with each implementation and compare as above; the same arguments always give the same packets.

```sh
python3 tools/mutate.py lines.hex.gz fuzz.hex.gz --seeds 50000 --count 2000000 --seed 1
```
