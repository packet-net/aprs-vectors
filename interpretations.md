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

Both belong to a position: APRS12c ch. 13 puts base-91 telemetry in "the comment field of any of the three position packet formats", and a DAO refines a position. A positionless weather report has neither, so text in its comment that looks like either stays there.

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

**Decision:** a mismatch is an error in both modes, not a tolerance: the sentence is corrupt, and a real one (`$GPRMC,...,4609.2815,N8.9077,W,...`) had lost characters from its longitude. The encoder refuses to write a sentence whose checksum is wrong. A sentence with no checksum is fine; `has_checksum` says which. The checksum is the `*hh` that ends the sentence, even when a comment follows it ([below](#what--text-is-an-nmea-sentence)).

## A directed query's target is one callsign

- APRS12c §15: a directed query is `?APRSx` with, for some types, the callsign it asks about, which "does not need filler spaces as it is at the end of the data". Its APRSH example, though, notes "the trailing spaces in the callsign following APRSH, padding the callsign to 9 characters", and the notes on APRS 1.2 say "APRSH: callsigns must be padded to 9 characters."

**Decision:** the target is one callsign, as an APRS-IS address is: 1-9 letters, digits or `-`. Spaces after it are padding, and one space between the query type and the target is a separator: a type the spec does not define has no fixed length, so its target needs one. Any other text after the query type (longer than 9 characters, holding a space, or any other character) is not a target, so the message is a plain text message with an `invalid-query` info, not a query. A bot's help text that begins `?APRSM for the last 10...` is the case that found this. An encoder writes a defined type's target straight after the type, an APRSH target padded to 9 characters, and any other type's target after one space (`?FOO N0QBF`).

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

**Decision:** the cs speed is converted from knots to mph for `wind_speed_mph` (1852 / 1609.344 mph per knot, exactly), so the field means the same in every report; it is the one value the neutral form converts. A direction of 0 stays 0. cs bytes that carry no wind (blank, or holding a GGA altitude or a range) mean the wind is unknown, not missing, so they add no `incomplete-weather`: otherwise a compressed report with unknown wind could never be written without a defect. Gust and temperature are still required. Wind sent some other way after a compressed position ([above](#wind-after-a-compressed-weather-position)) gets the default compression type, but only when it is known.

## Re-encoding into compressed bytes rounds

- A LoRa weather station sends a compressed position with blank cs bytes, then `103/000` as a wind extension (KD8ZLZ-13, 103 packets in the capture). On re-encoding, the wind goes back where APRS12c puts it, in the cs bytes, which carry direction in 4 degree steps.
- A range from an `RNG` later in the comment of such a position goes back into the cs bytes too, which APRS12c ch. 9 gives as 2 x 1.08^s miles.
- Some values have no place in the cs bytes at all: a range under 2 miles, a course and speed together with a range, or a compression type with neither wind nor course to carry.
- A GGA altitude in the cs bytes is 1.002^cs feet, so it cannot be 0 feet or below and is rarely exact; a `/A=` altitude wins over it.

**Decision:** a value the cs bytes carry in steps (a wind direction or speed, a range) is rounded to the nearest step, as a compressed course or speed given by an application is (103 degrees is written as 104). This is the only change of value an encoder may make, so such a report does not re-encode `identical` or `equivalent`, and its case says nothing about re-encoding; an implementation may round or refuse. A value the cs bytes cannot hold at all is refused, not moved to the nearest value they can hold. An altitude is different, because a `/A=` keeps it exact: the cs bytes carry the nearest altitude they can (1 foot for 0 feet or below) and a `/A=` carries the altitude itself, so the report re-encodes `equivalent`.

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

## Mic-E Rev 0 binary telemetry

- APRS12c ch. 10 describes an obsolete form of Mic-E telemetry: the byte 0x1D, then five binary values, straight after the symbol. It predates the device type codes, and nothing in the captured traffic uses it.
- Kenwood radios pad Mic-E status text with 0xFF bytes, which a decoder removes before reading the status text (UAP 5.10, and [below](#mic-e-0xff-padding-is-in-the-status-text)).

**Decision:** once any 0xFF padding is removed, 0x1D followed by at least five bytes at the start of the status text is `legacy_telemetry`, the five byte values, with an `obsolete-format` info as for the other obsolete formats. Anything after them is status text as usual. An encoder writes it back as received, like the other obsolete formats it decodes. A value of 255 is refused, because it would be removed as padding on the way back in.

## A packet is read in order

- APRS12c does not say which defect a decoder reports when a packet has several. A strict decoder rejects a packet by the first one it meets, so the order of the checks decides what it says.

**Decision:** a packet is read from the start, and each part is judged when it is reached: a defect later in the packet never changes the diagnosis of one before it. So a Mic-E destination is checked before the information field, and the nine fixed bytes before the status text and its 0xFF padding ([below](#mic-e-0xff-padding-is-in-the-status-text)); an NMEA sentence's address and fields before its checksum; a latitude's or longitude's digits and range before its hemisphere letter; a positioned weather report's wind where the `DDD/SSS` extension belongs, before the width of any field; and a garbled object timestamp on the position straight after it, not on anything later in the report. Bytes also belong to the element that reaches them first: a PHG straight after a Mic-E type code is lifted before an altitude is looked for later in the text, so `0PH}` inside `PHG3330PH}` is not an altitude. Structural checks (an addressee, braces, fields, a `!DAO!`) come before the encoding of the text that is left, which is only known once they are lifted out.

## Mic-E 0xFF padding is in the status text

- UAP 5.10: "Sometimes, apparently at random, the Kenwood TM-D710 will insert a bunch of 0xff characters on the packet." Every example there has the 0xFF run in the status text, before the radio's `=` suffix.
- APRS12c ch. 10: "The first 9 bytes of the Information field contain the APRS Data Type Identifier, longitude, speed, course and symbol data." None of the ranges it gives for those bytes includes 0xFF.

**Decision:** 0xFF padding is removed from the status text only, once the destination and the nine fixed bytes have decoded (`kenwood-ff-padding`, tolerated). An 0xFF among the fixed bytes is out of range like any other byte: removing it and shifting the bytes after it into its place would build a plausible position out of a corrupted one. A report that fails before its status text has no padding warning, so the tolerated warning never becomes the reason a strict decoder gives for rejecting it.

## Longitude blanks follow the latitude

- APRS12c ch. 6: "The level of ambiguity specified in the latitude will automatically apply to the longitude as well", and spaces in the longitude are allowed but not needed ("it is permissible but not necessary to include any" of them). A note in the same chapter adds that "Ambiguity was defined in the LATITUDE field only".
- FAP ignores the longitude digits the latitude's level covers, and rejects a space in any other.

**Decision:** the latitude alone sets the level. In the longitude, each digit place that level blanks is ignored, and may hold a digit or a space in any mix. Every other place must be a digit: a space there is a digit missing from the precision the latitude states, so the report is `invalid-longitude` rather than a guess.

## A late data extension is the first well-formed one

- UAP 5.15: a PHG "should appear at the very beginning of the comment", though "Some applications might recognize it anywhere".
- The vectors accept a PHG, RNG or DFS later in the comment (`data-extension-in-comment`, tolerated) when none came straight after the symbol.

**Decision:** that later extension is the first well-formed `PHG`, else the first well-formed `RNG`, else the first well-formed `DFS`. A malformed one such as `PHG12` is comment text, not an extension, so it does not stop the search for one that is. The other lifted elements already work this way: `/A=` is the first one that parses, and `!DAO!` the last.

## `!DAO!` datum digits

- APRS12c ch. 5, the `!DAO!` extension: "the DATUM can be one of ten locally defined options. These are indicated by the digits 0 through 9." The precision comes from a letter's case: "Capital letters indicate human readable decimal digits for A and O, and lower case indicates base 91 encoding for A and O." Spaces for A and O "imply NO ADDED precision".

**Decision:** a digit datum is read only with spaces for A and O, and gives precision `none`. With anything else there the five bytes are comment text, since a digit has no case to say how to read them. A `!DAO!` is five bytes as sent, so taking another element out of the comment (base-91 telemetry, a Mic-E altitude) never joins one.

## Signpost overlays are printable ASCII

- APRS12c ch. 11: signposts (the `\m` symbol) "display as a yellow box" with an overlay of 1-3 characters, given in braces in the comment.

**Decision:** an overlay character is printable ASCII, as every APRS overlay is. Braces around anything else, such as `{5`, 0xFF, `5}`, are comment text, where bytes that are not UTF-8 get `non-utf8-text` as usual.

## Which weather field a letter is

- APRS12c ch. 12 defines `s` twice: "s = sustained one-minute wind speed (in mph)" and "s = snowfall (in inches) in the last 24 hours". `L` and `l` are both luminosity, `l` for 1000 watts per square metre and above. A report "must include at least the MDHM date/timestamp, wind direction, wind speed, gust and temperature, but the remaining parameters may be in a different order".
- The vectors read the fields as one contiguous run (README, Weather).

**Decision:** which field a letter is depends on what has been read. `c` is the wind direction until the wind is known, wherever it comes, but only with a value after it: a bare `c` is not a field. When the wind comes as fields, `s` is the wind speed until the speed is known, wherever it comes, and snowfall after that. `L` and `l` are one field, so a second luminosity ends the run rather than overwriting the first. Extra fields are kept as a list, so a repeated extra letter overwrites nothing and does not end the run; only a defined field already read does. An extra field's value is the whole run of digits, dots and `-` after its letter, and it must end in a digit, so `V62.` is not a field. Snowfall keeps its width of three characters, digits with at most one decimal point, and only a run of dots (unknown) may be shorter: a garbled `s00/` where the wind extension belongs would otherwise become a snowfall of 0 inches, and a digit after `s1.5` could as well be a stray character as a fourth figure, so it is left as text.

## What `$` text is an NMEA sentence

- APRS12c ch. 5: "APRS recognizes raw ASCII data strings conforming to the NMEA 0183 Version 2.0 specification". It gives examples but no format of its own.
- NMEA 0183: a sentence is `$`, an address field, then comma-separated fields in printable ASCII with `$` and `*` reserved, and an optional `*hh` checksum. The address field is upper-case letters and digits: a talker and a sentence formatter (`GPRMC`), a query, or `P` and a manufacturer's code (`PGRMZ`, `PMGNWPL`).
- Real `$` packets that are not sentences: `$W6SCR-6  :BITS.11111111,Colby Data` and `$3tXJkPA`. TinyTrack and FreeTrak send a comment after the checksum (`$GPRMC,...,*0C/Home Station by TinyTrack`): 349 of 2,156 real sentences in one capture, each checksum matching.
- APRS12c ch. 5: "any APRS packet can contain a plain text comment (such as a beacon message) in the Information field, immediately following the APRS Data or APRS Data Extension."

**Decision:** after `$`, text that is not an NMEA 0183 sentence is `invalid-nmea`, an error in both modes. The address field is five upper-case letters or digits, or `P` and three or more of them, and at least one field follows it. A sentence ends at its first `*` followed by two hex digits: the checksum is verified, and any text after it is the report's `comment`, kept as sent. A `*` not followed by two hex digits is a reserved character in a field, so `invalid-nmea`. The structure is checked before the checksum. Three departures from NMEA 0183 are deliberate: lower-case checksum digits are accepted (DJ3HZ-5 sends them); the length is not checked, when decoding or encoding (NMEA allows 82 characters with the `$` and line ending, APRS12c says 25-209, and a sentence without a fix is shorter than 25); and the comment after the checksum.

## Reading the fields of an NMEA sentence

- NMEA 0183 gives a latitude as `llll.ll` and a longitude as `yyyyy.yy`, with a fixed number of degree digits; a time as `hhmmss.ss`; RMC's and GLL's status as `A` (valid) or `V`; and GGA's quality as one digit, 0 for no fix. A proprietary sentence's fields are whatever its manufacturer defines.
- DJ3HZ-5 drops leading zeros from its degrees (`1001.850` for 10 degrees 1.85 minutes). gpsd reads coordinates as loosely: the two digits before the point are minutes, and the rest degrees.

**Decision:** each field is read on its own: one that is missing or does not parse is left out and the rest are still read, however few fields the sentence has. A coordinate's degrees are whatever digits come before the two minute digits, but there must be at least one, the minutes must be below 60 and the value within 90 or 180 degrees, and a position needs both coordinates. The time is exactly `hhmmss`, with valid hours, minutes and seconds and an optional fraction that is kept as sent. `fix` comes from an `A` or `V` status, or a GGA quality of one digit. Only a five-character address that does not start `P` has a sentence formatter, in its last three characters, so a proprietary sentence such as `$PGRMC` is not read, even though its address ends in `RMC`.

## Station capabilities: items, tokens and values

- APRS12c ch. 15: "Each capability is a TOKEN or a TOKEN=VALUE pair. More than one capability may be on a line, with each capability separated by a comma." It says nothing about spaces, control characters or an empty token.

**Decision:** items are split at commas, and each at its first `=`. Spaces around an item, a token or a value are padding, so `MSG_CNT = 43` is `MSG_CNT` and `43`. Only U+0020 is a space: which other characters count as whitespace differs between languages, and a CR trimmed from the edge of an item would pass where one in its middle does not. The report is free text (`free-text-capabilities`) when a token is empty (`=43`) or holds a space or a control character (below U+0020, or U+007F), or a value holds a control character; a space inside a value is text, and U+00A0 is neither a space nor a control character. An encoder refuses anything that would not read back the same.

## A brace in telemetry metadata

- APRS12c ch. 14: message text "may contain any printable ASCII or UTF-8 characters except { which indicates start of Message Identifier". Ch. 13 sends telemetry metadata as messages, and says nothing about a `{` inside its lists.

**Decision:** a `{` in a `PARM.`, `UNIT.` or `BITS.` list that does not start a message ID is a text defect, as in any message: it stays where it is, with `brace-in-message-text`, and the message is still telemetry metadata, since its prefix and list are intact. A directed query does become a plain message on any `{`, because a query never has a message ID; metadata may have one. An encoder refuses to write a `{` into names, units or a project title.

## Reply-acks are for messages

- APRS12c ch. 14: bulletins and announcements "are not acknowledged". The reply-ack format exists for "including an ACK within an outgoing message".
- The data form gives `reply_ack` only to messages, acks and rejects.

**Decision:** bulletins, NWS bulletins and telemetry metadata take a message ID but not the reply-ack form. `{MM}` or `{MM}AA` on them is not an ID: it is `brace-in-message-text`, and the text is kept, so nothing is lost.

## Query types are upper-case letters

- APRS12c ch. 15: "Each query contains a Query Type (in upper-case)." UAP 1.4: "Query types must be in all upper case." Every type the spec lists is letters, apart from `PING?`, and a directed query's target follows its type with no separator (`?APRSHN0QBF`).

**Decision:** a query type is upper-case letters (or `PING?`). Digits have no case, and digits in a type the spec does not define would swallow the start of a target. So `?IGAT7?` is `invalid-general-query`, and a message `?APRS000` is plain text.

## Numbers in telemetry

- APRS12c ch. 13: telemetry values are often "much longer variable width values including decimal points, optionally preceded by a minus sign". The `EQNS.` format gives no number syntax at all.

**Decision:** a telemetry value is an optional `-`, then digits with an optional decimal point, with at least one digit: no `+`, no spaces, and no NUL or other byte after it. An `EQNS.` coefficient is the same, and may also have spaces (U+0020 only) around it and an exponent (`e` or `E`, an optional sign, digits). A coefficient is a floating-point number: `10E60` is 1e61, and `0eN` is 0 however large N is. One that is not a finite number (`1e400`) is not a coefficient, so the `EQNS.` is a plain message with an `invalid-telemetry-metadata` info.

## A general query footprint is a real place

- APRS12c ch. 15: "the latitude and longitude parameters are in floating point degrees", positive values with a leading space, and "The radius of the footprint is in miles, expressed as a fixed 4-digit number in whole miles." It gives no range.

**Decision:** a latitude beyond 90 degrees or a longitude beyond 180 is `invalid-general-query`, as a radius that is not exactly 4 digits is, and an encoder refuses it. There is no such place for the query to be about, and dropping the footprint instead would turn a regional query into one to every station.

## Third-party header addresses

- APRS12c ch. 17: "The source address in the encapsulated third-party packet is a character string and does not need to adhere to the AX.25 address restrictions. It can contain 1 to 9 printable ASCII characters, other than" `>`, "which is the field terminator". The destination is kept, and the path gains a network identifier and the gateway's callsign.

**Decision:** the inner source is 1-9 printable ASCII characters (0x20-0x7E) other than `>` and `:`; a `:` would end the TNC2 header. The inner destination and path follow the APRS-IS address rule, 1-9 letters, digits or `-`. Anything else is `invalid-third-party`. A defect the inner header may tolerate (several used markers, an empty path entry) is decoded leniently, with its warning on the inner packet, while a strict decoder rejects the packet as `invalid-third-party`. An encoder refuses such a packet: the inner packet's diagnostics are part of its data, so no clean form reproduces it.

## An Agrelo bearing is 0 to 360

- APRS12c Appendix 1 gives the Agrelo format as `%`, a 3-digit bearing, `/` and a 1-digit quality, 6 bytes in all. It gives the bearing no range.

**Decision:** the report is exactly those 6 bytes, and the bearing is 000 to 360, since it is a direction. Anything else is `invalid-agrelo-df`, an error: the report holds nothing but the bearing and quality, so there is nothing left once the bearing goes. An encoder refuses a bearing over 360.

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
