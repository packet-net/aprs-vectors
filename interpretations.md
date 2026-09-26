# APRS spec interpretations

Where APRS12c is ambiguous, contradicts itself, or disagrees with the reference implementations, the decision these vectors take is recorded here with its reasoning. A case whose expected values depend on one lists its heading in `interpretations`. direwolf means `decode_aprs` from [wb2osz/direwolf](https://github.com/wb2osz/direwolf). FAP means [Ham::APRS::FAP](https://github.com/hessu/perl-aprs-fap), the parser behind aprs.fi.

## Weather wind speed unit in the DIR/SPD extension

- APRS12c §7 (Wind Direction and Wind Speed): the DIR/SPD extension speed "is expressed in knots".
- APRS12c §12 (Complete Weather Reports): the DIR/SPD extension "replace[s] the cccc and ssss fields" of the positionless report, whose `s` is "sustained one-minute wind speed (in mph)".
- direwolf reads it as knots. FAP (aprs.fi) reads it as mph. Weather software that feeds CWOP sends mph.

**Decision:** in a weather report the DIR/SPD speed is mph (`wind_speed_mph`). §12 is the more specific rule for weather reports, and it matches what senders actually transmit. In a non-weather report, DIR/SPD is course/speed and the speed is knots.

## Position ambiguity: which point is reported

- APRS12c §6 (Position Ambiguity) says ambiguity "is not a truncation and it is not a box", and should be drawn as a circle centred on the position.
- direwolf treats the blanked digits as zeros, so it reports the corner of the range. FAP reports the centre of the range: +0.05', +0.5', 5', or +0.5° for ambiguity 1 to 4.

**Decision:** report the centre (FAP), and give the level as `ambiguity`. Encoding blanks the same digits again, so the round trip is exact.

## Compressed coordinates: round, not truncate

APRS12c §9 computes `190463 x (180 - 72.75) = 20427156` for the worked example, dropping the `.75`, which gives `<*e7`. An encoder rounds to the nearest step, as direwolf's `latlong.c` does, which gives `<*e8`, the point nearer the true position. Decoding is unaffected, and any decoded compressed position re-encodes to the same characters.

## Delimiters at the start of free text

APRS12c §18: "any free text field that begins with either of these two delimiters [space or `/`] ... can be ignored and the beginning of the text field begins after them." After the structured elements are lifted out of a position, object, item or Mic-E comment, **one** leading space or `/` is dropped. This covers `PHG7440/DigiPeater` and `r/RV46 PRIJEDOR` (FAP does the same) and Mic-E `' KJ6TMS` (direwolf and FAP both give `KJ6TMS`). A `/` that begins `/A=` is an altitude, not a delimiter. The encoder writes a `/` before a comment that itself starts with a space or `/`, or that would otherwise read as a data extension, so every comment round-trips.

## Compressed course 0 is north

The compressed course byte gives 0 to 356 degrees in 4-degree steps and has no "unknown" value (APRS12c §9). Course is reported 1-360 with 360 as north, so a compressed `c` of `!` (0) decodes as 360, as FAP does. A compressed course/speed can't be built without a course; an unknown course has no compressed form.

## Base-91 telemetry and `!DAO!`

The spec orders them comment, telemetry, DAO (APRS12c §13). Base-91 telemetry can contain a run that happens to look like a DAO (`|!m2n!Q[P|`), so the telemetry block is located first and the DAO is only looked for outside it.

## `!DAO!` on a compressed position

Compressed positions already resolve to about 0.3 m. A `!DAO!` on one is kept (its datum is information) but its extra digits are not applied.

## Mic-E type codes

APRS 1.2 reassigned `` ` `` and `'` after the symbol to "messaging capable" and "not messaging capable" device type codes. They were originally Mic-E telemetry flags, and the telemetry is now obsolete. They are decoded as type codes. A single leading space is the original Mic-E type code. The device suffix is matched against the device identification database, as direwolf does, so an unknown suffix stays in the comment rather than being guessed at.

## Grid locator status reports

`>JN55VD Powered by...` is a bare 6-character locator followed by text: plain status text, not the grid format. The grid format requires a symbol straight after the locator. A 4-character reading (`JN55` with symbol `VD`) is only tried when the first 6 characters are not themselves a locator.

## Object names may start with spaces

- APRS12c §11: the name "may consist of any printable ASCII characters, including embedded spaces. Trailing spaces are used to make the field 9 characters wide."

**Decision:** leading spaces are part of the name (`;   OR4F  *...` is the object `   OR4F`), and the encoder writes them. Only a trailing space is refused, since it would be read back as padding.

## Raw NMEA with a checksum that doesn't match

- APRS12c defers the sentence format to NMEA 0183, whose `*hh` checksum exists to detect corruption. FAP rejects a mismatch (`nmea_inv_cksum`).

**Decision:** a mismatch is an error in both modes, not a tolerance: the sentence is corrupt, and a real one (`$GPRMC,...,4609.2815,N8.9077,W,...`) had lost characters from its longitude. The encoder refuses to write a sentence whose checksum is wrong. A sentence with no checksum is fine; `has_checksum` says which.

## A directed query's target is one callsign

- APRS12c §15: a directed query is `?APRSx` with, for some types, the callsign it asks about.

**Decision:** text after the query type that is longer than 9 characters or contains spaces is not a target, so the message is a plain text message (with an `Info` diagnostic), not a query. A bot's help text that begins `?APRSM for the last 10...` is the case that found this.

## A telemetry project title is 23 characters

- APRS12c ch. 13 gives the bit-sense message's project title as 0-23 in its "Bytes" row, written when APRS text was ASCII; for status text it counts characters.
- A real title such as `Traisnerhütte Telemetry` is 23 characters, 23 bytes in the Latin-1 it was sent in and 24 in UTF-8.

**Decision:** the limit is 23 characters, whatever the encoding. An encoder refuses a longer title; a decoder accepts one.

## Wind after a compressed weather position

- APRS12c ch. 12: a compressed weather position carries the wind in its cs bytes, and the weather fields start at `g`. There is no `DDD/SSS` extension in the compressed format.
- UAP 5.33: LoRa trackers send one anyway. `_H*C156/001` has cs bytes that read 156 degrees at 1.15 mph and an extension saying 156/001, the same reading at full precision. `_.$H.../...` (a tracker with a weather sensor) has cs bytes that read 52 degrees at 0.3 mph and an extension saying the wind is unknown.
- Other LoRa trackers leave the cs bytes blank (a space where the course would be) and send positionless-style wind fields instead: `_ !Gc041s000g000t092...`.

**Decision:** the extension is the wind. It replaces what the cs bytes gave, and when it says unknown, the wind is unknown (`wind-extension-after-compressed`, tolerated). When the cs bytes carry no wind, `c` and `s` fields are read as the wind, as they are in an uncompressed report that sends them instead of the extension (`wind-fields-instead-of-extension`, tolerated). After cs wind, a `c` ends the fields like any other letter out of place. Either way, wind that was not in the cs bytes gets the default compression type, so that re-encoding has somewhere to put it.

## Wind in a compressed weather position

- APRS12c ch. 9 and 12: in a compressed report with the weather station symbol, the cs bytes carry the wind as they would a course and speed: direction c x 4 degrees, speed 1.08^s - 1 knots. Every other wind value in a weather report is in mph.
- The compressed format has no way to say the wind is unknown, which `.../...` says in an uncompressed report.

**Decision:** the cs speed is converted from knots to mph for `wind_speed_mph`, so the field means the same in every report; it is the one value the neutral form converts. A direction of 0 stays 0. cs bytes that carry no wind (blank, or holding a GGA altitude or a range) mean the wind is unknown, not missing, so they add no `incomplete-weather`: otherwise a compressed report with unknown wind could never be written without a defect. Gust and temperature are still required. Wind sent some other way after a compressed position ([above](#wind-after-a-compressed-weather-position)) gets the default compression type, but only when it is known.

## `!DAO!` base-91 digits

- The `!DAO!` extension (APRS12c, from aprs.org's datum note): in the base-91 form each of the two characters carries 0-90, and the note says to multiply by 1.1 to get the two extra digits of minutes, 0-99.

**Decision:** a base-91 value v adds v/91 of a hundredth of a minute to the position. That is the same as multiplying by 1.1 to within a tenth of a ten-thousandth of a minute (about 2 cm), and it spreads the 91 values evenly over the hundredth. An encoder writes the nearest ninety-first.

## Telemetry sequence numbers are not 3 characters

- APRS12c ch. 13: the sequence number "is a 3-character value, typically a 3-digit number, or the three letters MIC". The same section says the 3-digit width of the analog values "is often ignored".
- On APRS-IS, 13,000 of 6.9 million packets count past 999 (`T#51752,...`) or use more letters.

**Decision:** the sequence is `MIC` (with or without a comma after it) or letters and digits of any length up to the first comma, with no diagnostic. Anything else there (no comma, or other characters) is not a telemetry report: `invalid-telemetry`, an error.

## NWS bulletins are addressed NWS- or NWS_

- APRS12c ch. 14: National Weather Service bulletins are addressed `NWS-` followed by the severity (`NWS-WARN`, `NWS-ADVIS`).
- aprs-is.net/wx: the compressed form of the same bulletins is addressed `NWS_`.

**Decision:** an addressee starting `NWS-` or `NWS_` is an NWS bulletin; one that merely starts `NWS` (`NWSBOT`) is an ordinary message. An encoder refuses an NWS bulletin addressed any other way.

## A capabilities report lists at least one capability

- APRS12c ch. 15: a station capabilities report is `<` then a comma-separated list of `TOKEN` or `TOKEN=VALUE` items.

**Decision:** empty items are skipped, and a report with no items left (`<`, or `< , ,`) is malformed: `invalid-capabilities`, an error. An encoder refuses a report with no capabilities.

## Where these decisions and Ham::APRS::FAP differ

Found by comparing Packet.Aprs with FAP on the same 33,000 APRS-IS packets (see [packet.net's validation notes](https://github.com/packet-net/packet.net/blob/main/docs/aprs-validation.md#5-against-hamaprsfap)):

| Case | FAP | These vectors | Why |
|---|---|---|---|
| `/3517.73N/...` (a `/` report with no timestamp) | skips 7 characters and decodes garbage (61.97N) | decodes the position that follows the DTI | a timestamp starts with 6 digits, so a position straight after the DTI is unambiguous |
| `...wHP1000` or a comment containing `ESP32` after weather data | reads `P100` / `P32` as rain since midnight | stops weather fields at the first non-field | weather fields are a contiguous run (APRS12c §12) |
| compressed weather wind in cs | not decoded | decoded as wind direction and speed | APRS12c §12 compressed weather format |
| `!DAO!` in a weather report | not applied | applied | the DAO belongs to the position, not the comment |
| `rejAR}` | rejected ID `AR}` | rejected ID `AR`, reply-ack `""` | reply-ack format (APRS12c §14) |
| PHGR with rate `0` (`PHG01000/`) | accepted | plain PHG; `0/` stays in the comment | the rate is 1-9 then A-Z |
| Mic-E comment | keeps device prefix and suffix | lifts them into `type_code` / `device_suffix` | APRS12c §10 says applications should remove them |
| voice frequency | stays in the comment | lifted into `frequency` | APRS12c §18 |

## Errata in APRS12c's own examples

These examples in the spec cannot be what was meant; the cases use the corrected form.

- **§21 Overlays with Symbols**: `=BL!!<*e7>7P[` is 12 characters after the DTI; a compressed position is 13. The latitude `5L!!` has lost its `5`: `=B5L!!<*e7>7P[`.
- **§12 Complete Weather Report, compressed, no timestamp**: `=/5L!!<*e7>_7P[g005...` has a stray `>` before the `_` symbol code. As printed it decodes as a car (`/>`) with course 248 and a comment. The timestamped example beside it (`@092345z/5L!!<*e7_7P[g005...`) is right.
- **§11 Area Objects**: `;FLIGHTPTH*4903.50N\07201.75W l 610/310{100}` has no timestamp, though the same chapter says an object always has one. The spaces around `l` are typesetting, not data (a raw text extraction of the PDF gives `Wl610/310`). The `object-without-timestamp` tolerance exists partly for this.
- **§12 Complete Weather Report with Object**: `;BRENDA   *4903.50N/07201.75W_220/004g005t077...` likewise has no timestamp.
- **§8 examples** use `…` to mean "more fields here", not literal characters.
