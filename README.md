# APRS conformance vectors

Language-neutral test cases for APRS decoders and encoders: what a packet means, what is wrong with it, and what a strict and a lenient decoder should each make of it. Any implementation in any language can run them, and every implementation below consumes them the same way: as a git submodule, pinned to a commit, run by its own test suite on every build.

The cases come from three places, and each says which:

| Authority | Meaning | An implementation should |
|---|---|---|
| `spec` | The expected values follow from the text of APRS12c or *Understanding APRS Packets* (UAP), usually a worked example printed there. | match them |
| `interpretation` | The spec is ambiguous, contradicts itself or is wrong here; the expected values follow a decision recorded in [`interpretations.md`](interpretations.md), linked from the case. | match them or document why not |
| `observed` | A real packet from the APRS-IS feed; the expected values are what an implementation made of it when the case was recorded (Packet.Aprs, for every case so far), kept as a regression record. | treat a difference as a question, not a failure |

About 250 cases cover every example packet printed in APRS12c and UAP, the encoder, and every defect a lenient decoder may tolerate; another 1,395 are real packets of every distinct shape seen on APRS-IS.

**Licence:** AGPL-3.0-or-later ([`LICENSE`](LICENSE)).

## Implementations

| Implementation | Language | Repository | Package |
|---|---|---|---|
| Packet.Aprs | C# (.NET) | [packet-net/packet.net](https://github.com/packet-net/packet.net) | [NuGet `Packet.Aprs`](https://www.nuget.org/packages/Packet.Aprs) |
| packet-aprs | Rust (`no_std` + `alloc`) | [packet-net/aprs-rs](https://github.com/packet-net/aprs-rs) | [crates.io `packet-aprs`](https://crates.io/crates/packet-aprs) |

This repository's CI also runs each implementation against the vectors in every change, so a pull request shows which implementations already pass a new case. A failure there does not break an implementation, which only sees new cases when it moves its pin.

To use the vectors, add this repository as a git submodule and point your test runner at `cases/` and `codes.json`:

```sh
git submodule add https://github.com/packet-net/aprs-vectors vectors
```

The submodule pins a commit, so new cases reach an implementation only when it moves the pin on, and its own CI shows whether it still passes. Dependabot's `gitsubmodule` ecosystem can open that pull request.

## Files

| File | What |
|---|---|
| `cases/*.json` | The cases, one file per area (`position`, `mic-e`, `message`, ...). Each file is `{"cases": [ ... ]}`. `deviations.json` holds the tolerated defects; `corpus.json` the real packets. |
| `codes.json` | Every diagnostic code a case can name, with its meaning and whether a lenient decoder may tolerate it. |
| `schema.json` | JSON Schema (2020-12) for the case files. |
| `interpretations.md` | The decisions taken where the spec is ambiguous, contradicts itself or is wrong. |
| `tools/check.py` | Checks the files are well formed and consistent; CI runs it on every change. |

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

- Names are snake_case. Quantities keep the units APRS sends, with the unit in the name (`speed_knots`, `altitude_feet`, `temperature_f`); nothing is converted.
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

- **Addresses.** On APRS-IS an address is 1-9 letters, digits or `-`. Anything else in a TNC2 header is `invalid-address`; a missing `>` or `:`, or an empty source, is `invalid-header`.
- **Text that is not UTF-8** is read as Latin-1, the whole field, with one `non-utf8-text` warning for the field.
- **Numbers as sent.** Telemetry values and equation coefficients are compared as numbers, but `identical` re-encoding needs the text as sent (`073`, `190.0`, `.53`), so keep it.
- **The order of checks.** When a packet has several defects, a strict decoder rejects it by the first one it meets; the cases expect structural checks (addressee, braces, fields) before the text's encoding.
- **Weather.** A report with the weather station symbol (`_`, either table) is weather even with no fields. After the fields, 3-5 letters and digits and nothing else are the software type and unit; anything else is `weather-comment` text, from which telemetry and a `!DAO!` are still lifted, but not an altitude or a data extension. A letter the spec does not define followed by three or more digits is an `extra` field. A field one or more characters off its fixed width (`h7`, `t45`, `h100`, `b...`) is `non-standard-weather-field-width`.
- **Comments.** Base-91 telemetry is only looked for between the last two `|`; a `/A=` altitude anywhere wins over a compressed or Mic-E one. After a voice frequency the text starts past any spaces and one `/`; its tone, offset and range fields each need a space before and a space or the end after.
- **NMEA.** `sentence` is written without the `$`; `time` is `HH:MM:SS` with any fraction of a second kept, less trailing zeros.

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
| `frequency.tone` | `off`, `tone`, `ctcss`, `dcs` |
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
| `telemetry-names` / `-units` / `-coefficients` | `addressee`, `names` / `units` / `coefficients` |
| `telemetry-bits` | `addressee`, `bits`, `project` |
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
