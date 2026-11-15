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

APRS12c §18: "any free text field that begins with either of these two delimiters [space or `/`] ... can be ignored and the beginning of the text field begins after them." After the structured elements are lifted out of a position, object, item or Mic-E comment, **one** leading space or `/` is dropped. This covers `PHG7440/DigiPeater` and `r/RV46 PRIJEDOR` (FAP does the same) and Mic-E `' KJ6TMS` (direwolf and FAP both give `KJ6TMS`). A `/` that begins the `/A=` lifted as the altitude is not a delimiter; a later `/A=` is comment text ([below](#lifting-an-element-never-joins-the-text-either-side-of-it)), and its `/` is a delimiter like any other. The encoder writes a `/` before a comment that itself starts with a space or `/`, or that would otherwise read as a data extension, so every comment round-trips; and only then, so a comment that reads back as itself is written straight on.

## Where a voice frequency goes

- APRS12c ch. 18 adds a voice frequency "as a fixed formatted field in the first 10 bytes of the existing free-field position comment text", laid out for the 10-character displays of radios, which read it there. A `/A=` altitude "may appear anywhere in the comment" (APRS12c ch. 6). The signpost and corridor examples put their braces straight after the symbol or the area extension (`)I91 3N!4903.50N\07201.75Wm{55}`, `;FLIGHTPTH*4903.50N\07201.75W l 610/310{100}`, APRS12c ch. 11). Base-91 telemetry "MUST appear after the free-form comment text entered by the end-user, but before any DAO or Mic-E type codes", and "The DAO extension MAY appear after the Base91 Telemetry extension" (APRS12c ch. 13); ch. 5 lets a `!DAO!` appear "anywhere in the position comment field" and recommends "placing this option on the END of all other position comment text".
- After a data extension the spec lists `$CSE/SPD/FFF.FFFMHz`, `$PHGphgd/FFF.FFFMHz` and `$DFSshgd/FFF.FFFMHz` first, then the same with a space, then with no delimiter: "an optional delimiter is added to make the packet more readable". A PHGR is "an extra character followed by a mandatory / character" (APRS12c ch. 7), so it already ends in one.

**Decision:** a decoder reads all of these. An encoder writes one: after the data extension, the comment of a position, object or item report is the voice frequency with its fields, the signpost or corridor braces, the `/A=` altitude, the free text (after a space when a frequency or its fields come before it, braces or a `/A=` between them included, except where that space would make it read as one of the frequency's fields, [below](#lifting-an-element-never-joins-the-text-either-side-of-it)), base-91 telemetry and the `!DAO!`, in that order. A frequency straight after a seven-byte data extension (course and speed, PHG, RNG, DFS, area) follows a `/`, the form the spec lists first; after a PHGR, which ends in `/`, after a compressed position, or at the start, it follows straight on. Mic-E status text keeps its own order (the altitude first, as the radios send it), and a frequency after a PHG or RNG there follows a `/` too. Free text after a frequency still takes a `/` after its space where without it it would not read back as itself ([above](#delimiters-at-the-start-of-free-text)): in Mic-E status text a comment `X` written ` X` at the end would read back as the device suffix ` X`, so it is written ` /X`, after a frequency as after a locator.

## Compressed course 0 is north

The compressed course byte gives 0 to 356 degrees in 4-degree steps and has no "unknown" value (APRS12c §9). Course is reported 1-360 with 360 as north, so a compressed `c` of `!` (0) decodes as 360, as FAP does. A compressed course/speed can't be built without a course; an unknown course has no compressed form.

## Base-91 telemetry and `!DAO!`

APRS12c ch. 13 puts base-91 telemetry after the comment text and before any DAO, which "MAY appear after" it. Base-91 telemetry can contain a run that happens to look like a DAO (`|!m2n!Q[P|`), so the telemetry block is located first and the DAO is only looked for outside it.

Both belong to a position: APRS12c ch. 13 puts base-91 telemetry in "the comment field of any of the three position packet formats", and a DAO refines a position. A positionless weather report has neither, so text in its comment that looks like either stays there.

## `!DAO!` on a compressed position

Compressed positions already resolve to about 0.3 m. A `!DAO!` on one is kept (its datum is information) but its extra digits are not applied.

The data therefore does not carry the digits, and an encoder chooses them. As with the longitude digits a decoder ignores under ambiguity, they are written to agree with the position reported, so a reader that did apply them would land on it: the digits a DAO of that precision gives the position written uncompressed. Base-91, v = (the position in ninety-firsts of a hundredth of a minute, rounded to the nearest) mod 91; human-readable, d = (the position in thousandths of a minute, rounded to the nearest) mod 10.

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
- Some values have no place in the cs bytes at all: a range nearer a step below 2 miles than 2 miles itself (under 1.926 miles), a negative speed beyond the first step, a course and speed together with a range, or a compression type with neither wind nor course to carry.
- A GGA altitude in the cs bytes is 1.002^cs feet, so it cannot be 0 feet or below and is rarely exact; a `/A=` altitude wins over it.

**Decision:** a value the cs bytes carry in steps (a wind direction or speed, a range) is rounded to the nearest step, as a compressed course or speed given by an application is (103 degrees is written as 104). Rounding to a field's steps is the only change of value an encoder may make ([below](#values-between-steps-are-rounded) for every other field), so such a report re-encodes `rounded`: the encoder writes the case's `canonical_info` exactly, and the data read back differs by the rounding. The encoder rounds; it does not refuse. Halves round away from zero, and a direction that rounds to 360 degrees is north, which the cs bytes write as 0 (read back as 360 for a course, and as 0 for a wind direction, [above](#wind-in-a-compressed-weather-position)). A cs field's steps follow its formula (speed 1.08^s - 1 knots, range 2 x 1.08^s miles, altitude 1.002^cs feet) for every whole s, and the value is rounded to the nearest of them: when that s is outside the byte's range the value is refused, not moved to the nearest value the byte can hold. So a speed of -0.03 knots is nearest s = 0 and is written as 0, one of -0.3 is nearest s = -5 and is refused, a range of 1.95 miles is nearest s = 0 (2 miles) and is written, and one of 1.9 is nearest s = -1 and is refused. This is the same rule as for a field of whole units, where -0.3 knots rounds to 0 but -5 stays -5 and is refused. An altitude is different, because a `/A=` keeps it exact: the cs bytes carry the nearest altitude they can (1 foot for 0 feet or below) and a `/A=` carries the altitude itself, so the report re-encodes `equivalent`.

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

A strict decoder declines a later Mic-E altitude and reads it as text. Since lifting telemetry or a `!DAO!` never joins the text either side into an altitude ([below](#lifting-an-element-never-joins-the-text-either-side-of-it)), it never rejects a report by `mic-e-altitude-not-first`, and when a locator lacks its space that is the defect it rejects by (`mic-e/strict-missing-space-before-text-left-across-a-dao`).

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

**Decision:** a digit datum is read only with spaces for A and O, and gives precision `none`. An encoder refuses a digit datum with added precision as `invalid-code`: for that precision a digit is outside the datum's set. With anything else there the five bytes are comment text, since a digit has no case to say how to read them. A `!DAO!` is five bytes as sent, so taking another element out of the comment (base-91 telemetry, a Mic-E altitude) never joins one.

## Signpost overlays are printable ASCII

- APRS12c ch. 11: signposts (the `\m` symbol) "display as a yellow box" with an overlay of 1-3 characters, given in braces in the comment.

**Decision:** an overlay character is printable ASCII other than a brace, as every APRS overlay is printable and the braces delimit it. Braces around anything else, such as `{5`, 0xFF, `5}`, are comment text, where bytes that are not UTF-8 get `non-utf8-text` as usual, and they do not stop the search: the signpost is the first well-formed braces in the comment, as a late data extension is the first well-formed one.

## Which weather field a letter is

- APRS12c ch. 12 defines `s` twice: "s = sustained one-minute wind speed (in mph)" and "s = snowfall (in inches) in the last 24 hours". `L` and `l` are both luminosity, `l` for 1000 watts per square metre and above. A report "must include at least the MDHM date/timestamp, wind direction, wind speed, gust and temperature, but the remaining parameters may be in a different order".
- The vectors read the fields as one contiguous run (README, Weather).

**Decision:** which field a letter is depends on what has been read. `c` is the wind direction until the wind is known, wherever it comes, but only with a value after it: a bare `c` is not a field. When the wind comes as fields, `s` is the wind speed until the speed is known, wherever it comes, and snowfall after that. `L` and `l` are one field, so a second luminosity ends the run rather than overwriting the first. Extra fields are kept as a list, so a repeated extra letter overwrites nothing and does not end the run; only a defined field already read does. An extra field's value is the whole run of digits, dots and `-` after its letter, and it must end in a digit, so `V62.` is not a field. Snowfall keeps its width of three characters, digits with at most one decimal point, and only a run of dots (unknown) may be shorter: a garbled `s00/` where the wind extension belongs would otherwise become a snowfall of 0 inches, and a digit after `s1.5` could as well be a stray character as a fourth figure, so it is left as text.

## What `$` text is an NMEA sentence

- APRS12c ch. 5: "APRS recognizes raw ASCII data strings conforming to the NMEA 0183 Version 2.0 specification". It gives examples but no format of its own.
- NMEA 0183: a sentence is `$`, an address field, then comma-separated fields in printable ASCII with `$` and `*` reserved, and an optional `*hh` checksum. The address field is upper-case letters and digits: a talker and a sentence formatter (`GPRMC`), a query, or `P` and a manufacturer's code (`PGRMZ`, `PMGNWPL`).
- Real `$` packets that are not sentences: `$W6SCR-6  :BITS.11111111,Colby Data` and `$3tXJkPA`. TinyTrack and FreeTrak send a comment after the checksum (`$GPRMC,...,*0C/Home Station by TinyTrack`): 349 of 2,156 real sentences in one capture, each checksum matching.
- APRS12c ch. 5: "any APRS packet can contain a plain text comment (such as a beacon message) in the Information field, immediately following the APRS Data or APRS Data Extension."

**Decision:** after `$`, text that is not an NMEA 0183 sentence is `invalid-nmea`, an error in both modes. The address field is five upper-case letters or digits, or `P` and three or more of them, and at least one field follows it. A sentence ends at its first `*` followed by two hex digits: the checksum is verified, and any text after it is the report's `comment`, kept as sent. A `*` not followed by two hex digits is a reserved character in a field, so `invalid-nmea`. The structure is checked before the checksum. Three departures from NMEA 0183 are deliberate: lower-case checksum digits are accepted (DJ3HZ-5 sends them); the length is not checked, when decoding or encoding, beyond the information field's 256 bytes an encoder keeps to ([below](#an-information-field-is-at-most-256-bytes)) (NMEA allows 82 characters with the `$` and line ending, APRS12c says 25-209, and a sentence without a fix is shorter than 25); and the comment after the checksum.

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

**Decision:** a telemetry value is an optional `-`, then digits with an optional decimal point, with at least one digit: no `+`, no spaces, and no NUL or other byte after it. An `EQNS.` coefficient is the same, and may also have spaces (U+0020 only) around it and an exponent (`e` or `E`, an optional sign, digits). A coefficient is a floating-point number: `10E60` is 1e61, and `0eN` is 0 however large N is. One that is not a finite number (`1e400`) is not a coefficient, so the `EQNS.` is a plain message with an `invalid-telemetry-metadata` info. Each keeps its text as sent, so a report re-encodes byte for byte (`073`, `190.0`, `.53`, `0510`), and so does each number of a general query's footprint, which is read as a telemetry value is (`34.0`, `-.1715`, with or without a leading space before a positive value).

## A general query footprint is a real place

- APRS12c ch. 15: "the latitude and longitude parameters are in floating point degrees", positive values with a leading space, and "The radius of the footprint is in miles, expressed as a fixed 4-digit number in whole miles." It gives no range.

**Decision:** a latitude beyond 90 degrees or a longitude beyond 180 is `invalid-general-query`, as a radius that is not exactly 4 digits is, and an encoder refuses it. There is no such place for the query to be about, and dropping the footprint instead would turn a regional query into one to every station.

## Third-party header addresses

- APRS12c ch. 17: "The source address in the encapsulated third-party packet is a character string and does not need to adhere to the AX.25 address restrictions. It can contain 1 to 9 printable ASCII characters, other than" `>`, "which is the field terminator". The destination is kept, and the path gains a network identifier and the gateway's callsign.

**Decision:** the inner source is 1-9 printable ASCII characters (0x20-0x7E) other than `>` and `:`; a `:` would end the TNC2 header. The inner destination and path follow the APRS-IS address rule, 1-9 letters, digits or `-`. Anything else is `invalid-third-party`. A defect the inner header may tolerate (several used markers, an empty path entry) is decoded leniently, with its warning on the inner packet, while a strict decoder rejects the packet as `invalid-third-party`. An encoder refuses such a packet: the inner packet's diagnostics are part of its data, so no clean form reproduces it. It also refuses an inner path entry, before a used one, that is not marked used (`TCPIP,G4ABC*`): a path entry before a used one is used (the README's Addresses rule), so it reads back marked, and the header cannot be written as given (`invalid-third-party-header`).

## An Agrelo bearing is 0 to 360

- APRS12c Appendix 1 gives the Agrelo format as `%`, a 3-digit bearing, `/` and a 1-digit quality, 6 bytes in all. It gives the bearing no range.

**Decision:** the report is exactly those 6 bytes, and the bearing is 000 to 360, since it is a direction. Anything else is `invalid-agrelo-df`, an error: the report holds nothing but the bearing and quality, so there is nothing left once the bearing goes. An encoder refuses a bearing over 360.

## Values between steps are rounded

- APRS12c gives each field its resolution and width (hundredths of a minute in a position, ch. 6; whole degrees and knots in a course/speed, ch. 7; whole feet in `/A=`, ch. 6; whole miles in `RNG`, ch. 7; tenths of a millibar and hundredths of an inch in weather, ch. 12; a 4-digit radius in whole miles in a footprint, ch. 15) but no rule for a value that lies between its steps.
- A value given as data, whether by a program or by generated data, often does: a speed of 29.75 knots, a gust of 5.4 mph, a latitude whose minutes are 58.585.
- A neutral value is decimal text, and its nearest binary number often lies a few ulps either side of the half the text means: 986.95 is stored as 986.9499999999999 or 986.9500000000001 depending on how it was computed, and minutes derived from degrees almost never have an exact decimal.

**Decision:** a number between the steps its field holds is rounded to the nearest step, halves away from zero, and refused only when the rounded value is outside the field. Rounding comes first and every other check applies to the rounded value: a humidity of 99.7 is 100 and written `h00`, one of 0.4 rounds to 0 and is refused (APRS12c gives `h00` as 100 percent, so 0 has no form), a course of 360.4 is `360`, a course of -0.3 is 0 (written `000` uncompressed and refused in Mic-E, where 0 reads back as no course), a gust of 999.4 is `g999` and one of 999.5 is refused. This extends the cs rounding [above](#re-encoding-into-compressed-bytes-rounds) to every field: a course or speed, `/A=` feet, a Mic-E speed or course, latitude and longitude minutes, DAO digits, weather values, `RNG` miles, a footprint radius, a voice frequency and an Agrelo bearing (degrees, like a course: 12.5 is `013`, and 360.5 rounds to 361 and is refused). Rounding to the nearest is the only choice that keeps the written value nearest the one given, and one rule for every field leaves nothing to choose.

A half is decided on the value as computed in binary floating point, measured in steps: a value within 1e-6 of a step's half is the half, and goes away from zero. So a latitude of 0.9764166666666666 degrees, which is 58.584999999999996 minutes, is the half 58.585 and is written `0058.59N` (and the same longitude `00058.59W`), and a pressure of 986.9499999999999 mbar is 9869.5 tenths, written `b09870`. The tolerance makes the half the text means win in every language without decimal arithmetic. A value derived from another (minutes from degrees, knots from km/h) is computed from the value given and rounded once, never rounded twice.

Snowfall has three forms (the README's Encoding rule): it is rounded to hundredths if that leaves it under 1, else to tenths if that leaves it under 10, else to a whole number, and a result that is a whole number is written as one, in three digits. So 0.995 is 1.00 in hundredths, 1.0 in tenths, and written `001`; 9.96 is 10.0 in tenths and written `010`; one that rounds past 999 is refused.

## An area, DF bearing or storm is not the data extension

- The README's Comments rule looks for a PHG, RNG or DFS later in the comment only when no data extension came straight after the symbol, and a course/speed does not count as one: it describes the station's movement, not its radio.
- APRS12c ch. 7 lists the area object's `Tyy/Cxx` with the other seven-byte fields; ch. 7 puts a DF bearing (`/BRG/NRQ`) after a course/speed, and ch. 12 puts storm data after one too.

**Decision:** an area, a DF bearing or storm data does not count as the data extension either. Each describes the object or the bearing, not the station's radio, so a later PHG, RNG or DFS in the comment is found and read with `data-extension-in-comment`, as it is after a course/speed. An encoder therefore refuses comment text that holds one after an area, a DF bearing or storm data (`l710/310RNG12 RNG0050`): it has no clean form. It refuses a PHG, RNG or DFS given as data alongside any of them, or alongside a course/speed, for the same reason: only one extension goes after the symbol, and the second would read back with the warning.

## Numbers given without their text

- [Numbers in telemetry](#numbers-in-telemetry): a telemetry value, an `EQNS.` coefficient and a footprint number keep their text as sent, so a received packet re-encodes byte for byte. Data from a program, or generated data, has a number and no text.
- APRS12c ch. 13 gives the analog values as `aaa`, "expressed as 3-digit decimal numbers in the range 000-255", and writes them so (`T#005,199,000,255,073,123,01101001`), and the sequence as `sss`; its other examples (`T#151,45.7,2.3,190.0,91.0,-7.3,00001100`) and `EQNS.` (`0,5.2,0,0,.53,-32`) give no number format beyond themselves. Ch. 15 writes a footprint `?APRS? 34.02,-117.15,0200`: "North and east coordinates are positive values, indicated by a leading space", and the radius is "a fixed 4-digit number in whole miles".

**Decision:** where a number arrives without its text, a telemetry analog value that is a whole number from 0 to 999 is three digits (`005`, `000`, and 190.0 is `190`), as ch. 13's field and examples write it, and so is a sequence given as a number. Every other number (an analog value that is negative, over 999 or not whole, an `EQNS.` coefficient, a footprint latitude or longitude) is the shortest decimal that reads back as the same number, with no exponent and no `+`, a `0` before a leading decimal point (`0.53`), and no trailing `.0` (`-94.0` is `-94`); 1e61 is `1` followed by 61 zeros, and 1e-7 is `0.0000001`. This is the plain decimal form every language can write and every decoder reads; an exponent is only allowed in `EQNS.`, and not every decoder reads one. A footprint's latitude and longitude each get one leading space unless negative ([0 included](#a-footprint-coordinate-of-0-takes-the-space)), and its radius is four digits of whole miles: `?APRS? 51.5, 0.12,0005`.

## A footprint coordinate of 0 takes the space

- APRS12c ch. 15: "North and east coordinates are positive values, indicated by a leading space", and south and west are negative, with a minus sign. It does not say which a coordinate of 0 is.
- Elsewhere APRS writes the equator and the prime meridian as north and east (`0000.00N`, `00000.00E`).
- Without the space, a latitude of 0 is joined to the query type: `?WX?0,-117.15,0200`.

**Decision:** a coordinate of 0 takes the leading space, as north and east do: `?APRS? 0, 0,0200`. A decoder allows one leading space before any value that is not negative, 0 included, so that query reads back as itself, and an encoder writes it.

## Where a Mic-E locator is read

- APRS12c ch. 10's examples put a Maidenhead locator at the start of the status text, after any type code (`IO91SX/G Helloworld`, `>IO91SX/G`, `]IO91SX/G`), or straight after a Mic-E altitude.
- APRS12c ch. 13 puts base-91 telemetry after the comment text, a `!DAO!` "MAY appear after" it, and ch. 5 recommends a `!DAO!` at the end, though it may appear anywhere; the README's Comments rule lifts them out first, so that nothing else is read inside them.

**Decision:** a locator is read only at the start of the status text as sent, after any type code, or straight after a Mic-E altitude that is itself at the start as sent. Lifting an element never moves what follows it to a place it did not have as sent, as it never joins the text either side of it: `!W12!Io91/G` and `!w3U!abc}Io91/G` hold no locator. Text that looks like one anywhere else, such as after a PHG, RNG or DFS (`]PHG3330IO91SX/G`), is comment text and is written straight on, needing no delimiter. Base-91 telemetry and a `!DAO!` are lifted out of the status text before the locator is read, so a locator followed straight by either, with no comment (`` `IO91/G|!:&0'p| ``, `` `IO91SX/G!w!!! ``), has nothing after it and no `missing-space-after-locator`, and one followed by either and then a space and a comment (`` `IO91/G|!:&0'p| DG2MM ``) has its space, since once they are lifted the comment follows the locator's space; an encoder writes it so, with no space, as it writes a locator alone. A PHG, RNG or DFS straight after the locator and its space, or straight after the locator when the space is missing (a tolerated `missing-space-after-locator`, read as if the space were there, and written back with it), is lifted before a later Mic-E altitude is looked for, as one straight after the type code is, so in `` `IO91SX/G PHG1060}AB `` the `060}` is part of the PHG, not an altitude. A locator read at the start is likewise taken before a later altitude is looked for, and its bytes are never part of one: `` `IO91/G}!:&0'p| `` has no altitude, and `}!:&0'p|` is comment text.

The locator's space is judged once, on the decoder's own result, not on a trial removal of its own: on the status text after the locator with every element the decoder lifts from it under the options in force taken out (a later Mic-E altitude, base-91 telemetry and a `!DAO!`; a late PHG, RNG or `/A=` is comment content and counts as text), lifted exactly as for the data, in the same order and with the same refusals. A `!DAO!` that would exist only by joining the text either side of a lifted altitude is not one ([above](#dao-datum-digits)), so in `` `IO91/G!W1"4e}2! hi `` nothing more is lifted, the text after the locator starts `!W12!`, and `missing-space-after-locator` stands. A PHG, RNG or DFS straight after the locator is not lifted from the text but read where the separator belongs, so it needs the space before it, as above; and it is straight after the locator only where it is so as sent (once 0xFF padding is removed, [above](#mic-e-0xff-padding-is-in-the-status-text)), so one reached only once a `!DAO!`, telemetry or an altitude between them is lifted is late, as after the type code; one whose own bytes a lifted element splits is text ([below](#lifting-an-element-never-joins-the-text-either-side-of-it)). Judging the space never changes the text. When the locator has its space, that one space separates it and is not part of the comment, which then loses at most one further leading space or `/` by [Delimiters at the start of free text](#delimiters-at-the-start-of-free-text): `IO91/G /X` reads back as `X` (the form an encoder writes for `X`, [above](#where-a-voice-frequency-goes)), and in the same way `IO91/G  x`, with or without a lifted altitude or telemetry between the locator and the spaces, has the comment `x`. During round 5 aprs-cs and aprs-ts gave `x` there and the other four ` x`, and the libraries that judged the space on a trial removal of their own each went wrong in a different shape.

## A builder's course of 0 is unknown

- APRS12c ch. 7: a course is 001-360 "clockwise from due north", and "if the course and speed are unknown or not relevant, they can be set to 000/000 or .../..." or spaces. Ch. 10: a Mic-E course of "0 degrees represents an unknown or indefinite course, and 360 degrees represents due north".
- A program's heading often runs 0-359, with 0 as north.

**Decision:** a builder takes APRS courses, so a course of 0 is the spec's 0, unknown, and north is 360. An uncompressed report writes `000`, Mic-E writes 0, and a compressed report refuses it, since the cs bytes have no unknown course ([above](#compressed-course-0-is-north)). A course is rounded first, so 0.3 is 0 and unknown; 359.6 is 360, north. A program that holds north as 0 converts it to 360 itself: a builder cannot tell that 0 from unknown.

## Ambiguity cuts a raw position

- [Position ambiguity](#position-ambiguity-which-point-is-reported): a decoder reports the centre of the box an ambiguous position blanks, and an encoder given that centre blanks the same digits again.
- A builder is given a raw position, such as 49 degrees 03.596 minutes, and an ambiguity level.

**Decision:** the builder reports the box that holds the position: its digits are cut to the level, not rounded, then blanked. With one level, 03.596 is in the box 03.5x, centre 03.55. Rounding first would give 03.60, the box 03.6x, centre 03.65, which is further from the position than 03.55 is and does not hold it. The centre is what goes into the Mic-E longitude digits a decoder ignores. An encoder given a position with ambiguity cuts it the same way, as it does not round a value and then cut it again, so a value within a rounding step of 90 or 180 degrees (89.9999167 degrees, with two levels) is in the box below the edge (`8959.  N`) and is written, where rounding first would make a box centred past the edge and a refusal. The cut takes the same 1e-6 tolerance as a half ([above](#values-between-steps-are-rounded)), measured in the box's units: a value within 1e-6 of a box edge below it is on the edge, so 80.49 degrees, whose minutes compute as 29.399999999999636, is 29.40 and in the box 29.4x, as the text means.

## Mic-E messaging from a builder

- APRS 1.2's Mic-E type codes: after the symbol, `` ` `` marks a station that can message and `'` one that cannot ([above](#mic-e-type-codes)). The data form leaves a Mic-E radio's messaging capability out, since the type code already gives it.
- A builder's position options include `messaging`, which a Mic-E report has no other place for.

**Decision:** a builder writes `` ` `` when the program says the station can message and `'` when it does not, unless the program gives a device type, which says it instead.

## Which refusal a record with two faults gets

- APRS12c says what may be written, not what an encoder says when it declines. The vectors give each refusal a reason code (`codes.json`, `refusals`), and data can have several faults at once.

**Decision:** the refusal names the first code that applies in the README's "Refusal reasons" order: the header first, then a field wrong on its own, then what the frame cannot hold, then the symbol and companions, then text that reads back as a field, and the fallback last. A field the report has no place for is `field-not-allowed`, and its own checks (range, characters, length) do not run, so two faults in one field are one fault; faults in different fields are judged by the order alone. A field whose place exists but is wanted twice, or that contradicts another, keeps its own checks: a PHG digit of 10 beside a course and speed is `value-out-of-range`, not `extension-conflict`. One code wins whatever order a library checks in, so a program can act on it. `tools/precedence.py` makes a case for each pair of codes its catalogue of single faults can put in one record, each fault on its own field, and writes the other pairs to `tools/precedence-excluded.txt` with the reason: either both are faults of one field, or no report has both, by a table of the reports each code can apply to that is kept by hand, not drawn from the catalogue; `--check` fails when the table says a record could hold a pair the catalogue does not make.

## A wind direction is judged in whole degrees

- APRS12c gives a wind direction in whole degrees wherever it is written (`DDD/SSS`, `cDDD`, ch. 7 and 12), 0 to 360; in a compressed weather report the cs bytes hold it in 4-degree steps (ch. 9). The README's builder rule already decides a course's range in whole degrees and then rounds it once to its field's step.
- A value between steps is rounded to the nearest step and refused only when that is outside the field ([above](#values-between-steps-are-rounded)). Read alone, that would write 360.5 degrees as north in cs bytes (its nearest 4-degree step is 360) while refusing it uncompressed (361).

**Decision:** whether a wind direction is in range is decided in whole degrees, as a course's is, so the same value is in range or not whatever form it is written in: 360.4 is 360 and 360.5 is 361, refused as `value-out-of-range`; -0.4 is 0 and -0.5 is -1, refused. A direction in range is then rounded once, from the value given, to its field's step: 360.4 in cs bytes is north, c = 0. Unlike a course, a wind direction of 0 is a direction, not unknown. "The encoder rounds; it does not refuse" ([above](#re-encoding-into-compressed-bytes-rounds)) holds for a value in range. A wind speed stays judged by its form: unlike a direction it has no range of its own in APRS12c, only each field's (999 mph in three digits, the cs speed steps from 0 knots), so a speed past one form's limit can fit another.

## `!DAO!` on an ambiguous position

- APRS12c ch. 6: ambiguity deliberately hides digits of a position. The `!DAO!` extension adds a datum and, with letters for A and O, more digits; spaces for A and O "imply NO ADDED precision".
- The spec says nothing of the two together.

**Decision:** a `!DAO!` on an ambiguous position reads with `dao-with-ambiguity` (tolerated) whatever its precision, `!W  !` included, and an encoder refuses it (`field-not-allowed`). One rule for every precision keeps it simple to check; a station hiding its position has no use for a datum that refines it, and a decoder cannot tell a `!W  !` sent on purpose from one a tracker appends to every report.

## Third-party packets nest at most four deep

- APRS12c ch. 17: an IGate wraps a packet in a third-party header, and "the original Information field must not be changed", so a packet that is already a third-party packet can be wrapped again. A reader removes "everything up to and including the }" and processes what is left, which may hold another. The spec sets no limit.
- In two APRS-IS captures (2026-09-26 and 27, 18 million packets) 525 packets are third-party packets, every one of them one level deep; none holds another.
- With no limit, a line of `A>B:}` repeated a few thousand times makes a decoder recurse once per level, and one that copies each inner packet's text uses memory in the square of the line's length.

**Decision:** a decoder reads at most four levels of third-party header: a packet in a third-party packet in a third-party packet, and so on, four `}` in all. The real traffic needs one, the spec's rewrapping a second, and four leaves room for two more gateways in a row. A fifth `}` is not read: the packet whose information field it starts is decoded as one with an unusable third-party header is (`unrecognized`, `malformed`, with `error:invalid-third-party` among its own diagnostics), and the four levels above it are kept. It re-encodes as received, like any third-party packet whose inner packet holds an error. An encoder given data nested more than four deep refuses it as `invalid-third-party-header`: the fifth header would read back unusable, so it cannot be written as given. It counts the levels as it goes and stops at the fifth, so it never recurses further than a decoder does.

## An AX.25 address is letters and digits

- AX.25 2.2 section 3.12: "The call sign is made up of upper-case alpha and numeric ASCII characters only", padded with spaces. A frame can carry any 7-bit character there.
- A decoded packet is often written out as TNC2 text (an IGate passing what it hears on to APRS-IS), where `,`, `:`, `>`, `*` and `-` are structure: a call holding one would write a header that reads back as a different one (`APRS,q` as a destination makes a path entry), and an IGate would pass that on.
- The vectors already tolerate lower-case letters in an AX.25 address (`invalid-ax25-address-characters`), which TNC2 text carries without harm.

**Decision:** in an AX.25 address, after the shift, each character is an upper-case letter or a digit, then spaces to the end (or NULs, `nul-padded-address`). A lower-case letter is tolerated with `invalid-ax25-address-characters`. Anything else (punctuation, a space before the last character, a control character) makes the address unusable: the header is `invalid-address`, an error in both modes, and nothing is decoded, so a TNC2 line is never written from it. A call of spaces only is empty and is read as an empty TNC2 address is: an empty source is unusable (`invalid-address`), an empty destination is `empty-destination` and an empty digipeater is `empty-path-entry`, both tolerated.

## NMEA data is its sentence

- APRS12c ch. 5 carries raw NMEA 0183 sentences as they are; it defines no fields of its own. The data form gives a decoded sentence's position, time, fix, course and speed beside the sentence, read from it.
- A program that relays a sentence from a receiver has the sentence, not the fields, and the spec does not stop it sending one.

**Decision:** the sentence is the data, and the fields are what it determines (as the data form leaves out a symbol's description). An encoder given a sentence and no fields writes the sentence; a field given beside it must agree with it, or the data is refused as `invalid-nmea`, since written it would read back with the sentence's value. A comment goes after the checksum that ends a sentence, so a comment given with a sentence that has no checksum is `invalid-nmea` too: written, it would read back as part of the sentence. This is the one place where a field left out does not mean the field is absent.

## Absent text is empty text

- The data form leaves out empty strings, so data with no object or item name, addressee, query type or positioned symbol cannot say whether the text was empty or never given.

**Decision:** these four fields only are read as empty text when absent: an object or item with no name is `invalid-name`, a message or other addressed report with no addressee `invalid-addressee`, a query or directed query with no type `invalid-code` (an empty type is not upper-case letters), and a positioned report with no symbol `invalid-symbol`. Every other required field left out stays `missing-field`, as codes.json and the cases already give it: an object's timestamp, a telemetry report's bits, a capability, and a field needed only because another is there (a status symbol beside a locator, a message ID beside a reply-ack). A library whose own data cannot hold the record writes `unsupported` in its dump, and the record is not compared.

## A `/A=` altitude wins over a Mic-E or compressed one

- APRS12c ch. 6: "The altitude may appear anywhere in the comment", as `/A=` and six digits of feet. Ch. 10 gives Mic-E its own altitude, three base-91 characters and `}` in metres, and ch. 9 lets a compressed position's cs bytes hold one from a GGA sentence, in steps of 0.2 percent.
- A packet can hold two. direwolf reads the Mic-E or compressed altitude first and then sets the altitude again from a `/A=` in the comment; FAP's Mic-E reader does not look for `/A=` at all.
- In two APRS-IS captures the only Mic-E packets with both are corrupt ones (several packets run together).

**Decision:** when a report holds a `/A=` altitude as well as a Mic-E or compressed one, the `/A=` is the altitude, wherever it is in the text, as direwolf has it. It is the form every kind of report shares and the only one that is exact in feet, and one rule for every report is simpler to check than an order that depends on where each was found. The data form has one altitude, so the other is not reported; an encoder writes it where [a Mic-E altitude goes](#a-mic-e-altitude-goes-in-the-mic-e-altitude-bytes) says.

In Mic-E status text the `/A=` is also looked for first, before a later Mic-E altitude, so the two never take the same bytes: `x/A=000100}` has the altitude 100 feet and the comment `x}`, lenient and strict alike (`mic-e/altitude-before-a-later-mic-e-altitude-it-overlaps`). Reading `100}` as a Mic-E altitude first, as the libraries did during round 5, gave 406,417 feet and the comment `x/A=000` leniently and 100 feet strictly, from the same bytes. A whole `/A=` is what the sender wrote and wins over a Mic-E altitude anyway, while a run of three base-91 characters and `}` is easily made by accident from its last digits. The later Mic-E altitude is then the first that stands whole in the text left: in `x/A=000100}y"4e}z` it is `"4e}`, lifted with its warning, and the altitude is 100 feet (`mic-e/later-mic-e-altitude-clear-of-an-altitude`). Written back, a comment after the `/A=` needs no space to keep its digits out of a Mic-E altitude (`mic-e/leading-mic-e-altitude-and-an-altitude`). The Mic-E altitude at the start of the status text, the locator and a PHG, RNG or DFS straight after the type code, that altitude or the locator are read before any `/A=`, as before; of them only a PHGR's `/` can share a byte with a `/A=`, and it stays the PHGR's. A later Mic-E altitude is looked for before base-91 telemetry and a `!DAO!` ([below](#lifting-an-element-never-joins-the-text-either-side-of-it)), so in Mic-E status text the `/A=` comes before them too, and a `/A=` inside `|...|` makes the telemetry text, as a later Mic-E altitude inside it does (`mic-e/altitude-inside-telemetry-splits-it`); in other reports telemetry is lifted first. The whole order in Mic-E status text is the README's Mic-E rule: Rev 0 telemetry, the type code and device suffix; the altitude at the start; the locator; a PHG, RNG or DFS at the start; the `/A=`; a later Mic-E altitude; base-91 telemetry and the `!DAO!`; braces; a late PHG, RNG or DFS; the voice frequency. Each overlap is settled by that order, and nothing is read across the place an element was lifted from, a frequency's fields across the `/A=` excepted.

## An information field is at most 256 bytes

- APRS12c ch. 3: the AX.25 information field is 1 to 256 bytes. APRS-IS carries longer lines, and a digipeater or TNC may drop a frame over 256.
- At 1.1.0 every encoder wrote any length (a 2,000-character comment, a 309-digit telemetry number); only message text (67 characters) was refused.

**Decision:** an encoder or builder refuses data whose information field, as written, is over 256 bytes, as `information-field-too-long`, a refusal of its own. It is judged on the bytes written, whatever form they go in (TNC2, AX.25 or KISS carry the same information field), so it also bounds number text given without its text, which can run to hundreds of digits ([above](#numbers-given-without-their-text)). For a third-party packet it is the outermost information field that goes on air, so the `}`, the inner header and the inner information field count together. A decoder sets no limit, as before: what was received is read, and re-encodes `refused` with `information-field-too-long`, since writing it again would make the frame the spec forbids.

The size is the last check, on the bytes actually written, after every other rule, the read-back included. Data that any other rule refuses gets that rule's code, `value-given-twice` included (a builder given one quantity in two units names it, even when each one-unit build would also be over 256 bytes); only data with no other fault, whose information field as written is over 256 bytes, is `too-long` for its size. A field longer than its own limit (message text over 67 characters, a project title over 23, more than five analog values) stays `too-long` at that code's place in the order, after `invalid-character` and before `padding-space`; the size has its own id, last in the order, so a program and a comparison can tell the two apart. Measuring the size earlier, on a record that still has another fault, needed a rule for every corner (the delimiter of a field left out, two extensions that want one place, a timestamp with no place, an inner packet's later fault) and every library got at least one wrong. Checked last there is one rule and nothing hypothetical to measure, and a program told `information-field-too-long` knows the record is otherwise sound and only needs to be shorter.

The limit binds a program that only sends to APRS-IS too, on purpose: a packet sent there may be gated to RF, and APRS12c, which notes that longer comments are seen, still gives 256 bytes as the field. It binds encoders and builders, not a function that writes out a packet the program already holds (a decoded packet's TNC2, AX.25 or KISS form), which writes its information field as received.

## A library with a fixed capacity says so

- aprs-c allocates nothing: it holds an information field of 512 bytes, 16 path entries, 64 capabilities and 8 extra weather fields. At 1.1.0 it gave a different reading at each edge: an empty field, a header error, `invalid-capabilities`, or the ninth extra field moved into the comment, which changed the strict verdict.
- A reading that differs because of a buffer is wrong data, and a strict verdict that changes with it is worse: a program cannot tell it from the packet's own defect.

**Decision:** one diagnostic, `implementation-limit`, an error, which only an implementation with a fixed capacity gives. Such an implementation never gives a different reading instead: when a packet needs more than it holds, a limit met in the header makes the header unusable with `error:implementation-limit`, and any other makes the data `unrecognized` (`malformed`) with `error:implementation-limit`, lenient and strict alike; it re-encodes `none`. An implementation without the limit decodes the packet normally, and cases at each edge (513 and 2,000 bytes of information field, 17 path entries, 65 capabilities, 9 extra weather fields) show that. A test runner skips a case its capacity cannot hold, as it skips one its data cannot hold, and the implementation lists its capacities in its README; `compare.py` leaves such records out and counts them.

## Control characters in text

- APRS12c gives comments, status text and message text as printable ASCII, and later practice allows UTF-8 ("printable ASCII or UTF-8 characters", ch. 14). APRS12c ch. 5 forbids a CR or LF only at the end of the information field and says nothing else of control characters in text. UAP 5.13 and the vectors already treat a CR or LF that ends the information field as a line ending (`trailing-line-break`).
- At 1.1.0 a NUL or other control character in a comment, status or message decoded with no diagnostic, strict included, and every encoder wrote one raw. A control character in text is either damage or a byte meant for something other than a person, and a terminal or log that shows it can be made to do anything.

**Decision:** in text a decoder reads as text, a byte below 0x20 or the byte 0x7F is a defect: one `control-character-in-text` warning for the text, however many it holds (as `non-utf8-text` is one per text), tolerated, so a strict decoder rejects it, and the text is kept as sent. Text is a comment, status text, message, bulletin and NWS bulletin text, a telemetry name, unit or project title list, a capability value, and the free text a report leaves (`weather-comment` text, the text after an NMEA checksum). TAB is a control character, with no exception: the spec's text is printable characters, and TAB is not one. A CR or LF inside text is one too; only a CR or LF at the end of the information field is a line ending, taken off before anything in the field is read.

Bytes that are data are not judged: user-defined, raw weather, test and undecoded data, Mic-E's fixed bytes and its Rev 0 telemetry, and 0xFF padding, which is removed before the text is read. Nor is text another rule already confines, which keeps its own diagnosis: an object or item name is printable ASCII, so a control character in one is `invalid-object-name` or `invalid-item-name` (an error); a capability token with one makes the report free text (`free-text-capabilities`); an addressee, a header and an NMEA sentence have their own rules. A capability value is text, so one with a control character gives both `free-text-capabilities` and this warning. A third-party packet's inner text is judged as any packet's, with the warning on the inner packet; the inner field is carried as received, so a decoded third-party packet whose inner text holds a control character still re-encodes `identical`, the one place an encoder writes one. Only bytes below 0x20 and 0x7F are judged: a byte from 0x80 to 0x9F is either part of a UTF-8 character or is covered by `non-utf8-text`. The text before the `!` of a report whose position is not at the start (`position-not-at-start`) is not judged either: it is discarded, not kept as text. A control character in a capability token makes the report free text and gives no warning of its own, while one in a value gives both, as above: a token is fixed-form text, and a value is text.

A text's control characters are judged after everything else about it, its structure and its encoding: both `non-utf8-text` and this are judgements of the whole text, and the bytes must be read as characters before they are judged as characters. So a strict decoder rejects text with both by `non-utf8-text`, and a capabilities report with a control character in a value by `free-text-capabilities`. An encoder refuses such text as `invalid-character`, as it refused a line break before; a Mic-E status text starting with 0x1D, which it wrote after a `/` at 1.1.0, is refused too, since the 0x1D is in the text.

## Builder defaults

- At 1.1.0 a Mic-E builder given nothing else wrote "in service" and `'` in Python, "off duty" and `` ` `` in TypeScript, and "off duty" and `'` in the other four; an object built with no timestamp was stamped from the clock in C#, Python and TypeScript and refused in Rust, C and Go; a position with no symbol was `//` in TypeScript and refused in the other five. The survey is in the round 4 notes (DEFAULTS.md).
- A builder's output should depend only on what the program gives it, so that the same call gives the same bytes and a test of it is a test.

**Decision:** a builder never reads the clock: an object or a positionless weather report built with no timestamp is refused as `missing-field`, as neutral data without one is, and a report whose timestamp is optional has none. A library may offer a separate helper that gives the time now, which the program calls. A station not said to message does not: positions use `!` and `/`, and Mic-E the type code `'` ([above](#mic-e-messaging-from-a-builder)). The Mic-E message defaults to off duty, the standard message M0 and what a Mic-E radio sends until told otherwise. Every other default is the choice that writes the least the program did not ask for: no path, no ambiguity, no compression, no message ID or bulletin group, the destination `APZ001` (the experimental tocall APRS gives software without one of its own), an object or item alive, telemetry metadata addressed to the sending station (the station whose telemetry it describes, ch. 13). A status symbol given with no locator, like a locator with no symbol, is `missing-field`: a status has a place for a symbol, the locator form, so what is missing is its companion, as with a reply-ack given without a message ID; the same holds for neutral data. A positioned report with no symbol is refused as `invalid-symbol`, as neutral data with none is ([above](#absent-text-is-empty-text)), except a weather report, whose symbol is `/_` because it is a weather report. A telemetry report given no analog values writes five empty channels (`T#001,,,,,,00000000`), the form of a report whose channels are all unknown. A telemetry report with no sequence is `missing-field`, but one with no bits writes `00000000`: APRS12c ch. 13's report always carries the eight bits, a decoder gives `invalid-telemetry` for a report without them, so the builder must write something, and all zeros is what a station with no digital channels sends. Neutral data given to an encoder with no bits stays `missing-field`: data is not a builder, and its bits are what was received. Where a report has a value in every form (a Mic-E speed, the `c`, `s`, `g` and `t` of a weather report), one not given is written as unknown where the format has an unknown (dots), and as 0 where it has none (a Mic-E speed).

## A Mic-E altitude goes in the Mic-E altitude bytes

- APRS12c ch. 10 gives a Mic-E report its own altitude: three base-91 characters and `}`, in metres above 10,000 m below sea level, at the start of the status text. Ch. 6 gives `/A=` and six digits of feet for any report's comment.
- At 1.1.0 C# and Go wrote an altitude a builder was given in feet as `/A=` in the status text, and one given in metres in the Mic-E bytes. FAP (aprs.fi) and aprslib do not read `/A=` in a Mic-E report, so the first altitude was invisible to them ([below](#where-these-decisions-and-hamaprsfap-differ)).

**Decision:** a Mic-E builder writes an altitude in the Mic-E altitude bytes whatever unit it was given in, rounded once to the nearest metre from the value given ([above](#values-between-steps-are-rounded)): 1000 feet is 304.8 metres and is written as 305. One outside the bytes' range, -10,000 to 743,570 metres, is `value-out-of-range`; it is not moved to a `/A=`, which would hide it from those readers again.

An encoder does the same, except where the altitude came from a `/A=`. Decoded data knows where it came from, and since the `/A=` wins over the Mic-E bytes ([above](#a-a-altitude-wins-over-a-mic-e-or-compressed-one)) it is written back as a `/A=`, whatever its value (`mic-e/an-altitude-from-a-later-a-is-written-back-as-a`), so a decoded `/A=` re-encodes `identical`. Neutral data has one altitude, in feet, and does not say where it came from, but the value does: a `/A=` holds a whole number of feet, and the Mic-E bytes a whole number of metres. So neutral data goes in the Mic-E bytes unless only a `/A=` holds it exactly, that is when it is a whole number of feet within a `/A=`'s six digits that the Mic-E bytes do not hold exactly (not a whole number of metres, or outside their range), each judged within 1e-6 of a whole number in its unit. A multiple of 1250 feet (381 metres), 0 included, is held exactly by both, and goes in the Mic-E bytes. A value neither holds exactly (100.5 feet) is rounded into the Mic-E bytes (31 metres). This settles a value of -50,000 feet, which C#, Rust and Go refused at 1.1.0 and the others wrote as a `/A=`: the Mic-E bytes cannot hold it and a `/A=` holds it exactly, so it goes in the `/A=`. Where the Mic-E bytes have no clean form (an altitude whose first byte is a type code character, with no type code before it, README Refusal reasons) and a `/A=` holds the value exactly, it goes in the `/A=`, as before. When no `/A=` holds it exactly (not a whole number of feet, or beyond six digits), it has no form at all: `value-has-no-form`, not `text-reads-as-field`, since no comment changes (a decoded altitude of 231,932 metres written with no type code, whose first byte `>` would read back as one).

## A weather field that runs on by many digits

- APRS12c ch. 12 gives each weather field a fixed width: `t` is three characters, `h` two, `b` five. The README's Weather rule reads a field that runs on by one digit at the longer width (`non-standard-weather-field-width`), and one that runs on by two or more at its own width, ending the fields there, since digits at the start of a comment are common (`t0725.2V`, a battery voltage straight after the temperature).
- On 2026-11-14 a broken sensor sent `t2147483647` and `t4294967295` (the largest 32-bit numbers, signed and unsigned) with the rest of its report after them. By the 1.1.0 rule that was 214 F, and `7483647r000p000...` became `weather-comment` text: a temperature that was never measured, and the rain, humidity and pressure lost.

**Decision:** a fixed-width field whose digits run on by two or more, where the run is followed by the end of the information field or by a defined field the run goes on to read (a letter APRS12c defines, not already read, with a value), is a value out of range: `out-of-range-value` (tolerated), the value is dropped, and the fields carry on after the run. The run's own field counts as read, so in `t42005t4294967295` the second `t` does not qualify and the 1.1.0 rule stands (420 F, the rest comment text). A field the run reads next is what tells a run-on value from a comment: a comment does not go on to `r000p000`, and nothing goes on after the end of the field. "The end of the information field" means the end of the weather text: the end of the field, or the start of an element the Weather rule lifts in a positioned report (base-91 telemetry, a `!DAO!`), wherever it sits, so `t2147483647!W12!` drops the temperature too. A lifted element is bytes as sent, and taking it out never joins the text either side of it (as with a `!DAO!` and a Mic-E locator), so in `t2147483647|!!!!|7k SvxLink` the run reaches the telemetry and is dropped, and `7k SvxLink` is comment text on its own, not joined to the run's digits. A run followed by anything else keeps the 1.1.0 rule. This is a trade. A run of digits longer than its field cannot be split with certainty: the two observed packets it changes (`g001068r000`, `s0100048r000`) are senders that dropped a field's letter, and in the first the rule drops what may have been a valid gust of 1. But the 1.1.0 reading reports a value the sender may never have sent (214 F from `t2147483647`) and loses every field after it, while this one reports nothing uncertain and keeps the fields after the run. A decoder never reports a value the sender did not send. The dropped value was sent, so it counts as present for `incomplete-weather`, as a wind direction over 360 does. A temperature of 999 F, three digits, stays as sent: APRS12c gives temperature no range.

## A garbled timestamp before an uncompressed position

- APRS12c ch. 6: a DHM timestamp "is a fixed 7-character field, consisting of a 6-digit day/time group followed by a single time indicator character (z or /)", and an HMS one "a 6-digit time in hours, minutes and seconds, followed by the h time-indicator character". Ch. 8 gives the `/` or `@` report as the DTI, those 7 bytes, then an 8-byte latitude, the symbol table, a 9-byte longitude and the symbol code; ch. 6 gives the latitude as "a fixed 8-character field, in degrees and decimal minutes (to two decimal places), followed by the upper case letter N for north or S for south", and the longitude likewise with `E` or `W`. Ch. 9 gives the same report with a compressed position, 13 bytes in which "All bytes except for the / and $ are base-91 printable ASCII characters (!..{)", the `/` standing for the symbol table identifier: "The presence of the leading Symbol Table Identifier instead of a digit indicates that this is a compressed Position Report". Ch. 21 lists the identifiers a compressed position may start with (`/`, `\`, `A`-`Z`, `a`-`j`): "compressed positions never start with a digit".
- The README's rule (Timestamps that are not there) reads the position straight after the DTI when it decodes, for senders that put one there with no timestamp (`/3517.73N/...`, [below](#where-these-decisions-and-hamaprsfap-differ)), else after seven bytes. On 2026-11-14 a weather station in Florida sent `@R30549z2831.07N/08142.92W_015/001g006t058...`, its timestamp with `R` for a digit. `R30549z2831.0` reads as a compressed position, so all six libraries at 1.2.0 reported 54.06N 81.17W, symbol `R3`, course 64 and 1.7 knots, and no weather. FAP skips the seven bytes after `/` or `@` whatever they hold (warning `timestamp_inv_loc`); direwolf's `aprs_ll_pos_time` does the same (`get_timestamp` prints "Timestamp must be 6 digits followed by z, h, or /." and the position after the seven bytes is read). Both give 28.5178N 81.7153W, a weather station.
- In 297 million APRS-IS lines (40 days from 2026-10-01 to 2026-11-14), 21 packets from 13 stations have this shape: seven bytes ending in `z`, `/` or `h`, one of the first six a letter, an uncompressed position after them, and a compressed reading straight after the DTI. In every one the uncompressed position is the station's own (`@A22303h1519.53S/02810.44Ef235/000/A=003830 ...` comes from a station that always sends `A` for the first digit). No packet in those lines has a compressed position after such seven bytes where a compressed reading straight after the DTI also decodes.

**Decision:** in a `/` or `@` report whose timestamp is not 6 digits then `z`, `/` or `h`, when the seven bytes after the DTI end in `z`, `/` or `h` and an uncompressed position follows them, the timestamp is garbled: the position is read after the seven bytes, with `malformed-timestamp` (tolerated). Otherwise the rule is as before. "An uncompressed position follows" is judged as for an object: on the position itself (latitude, symbol table, longitude, symbol code), under the options in force, not on anything after it.

Any 13 bytes that start with a symbol table character and stay within base-91 read as a compressed position, so that one decodes is weak evidence that it is one; digits and `z`, `/` and `h` are all base-91 characters, so a timestamp whose first byte is damaged to a letter always does. An uncompressed position's shape (digits, a point, a hemisphere letter, twice over, either side of a symbol table) does not occur by accident, and seven bytes ending in a time indicator before it are a timestamp with a damaged byte. The object rule already asks this question: seven bytes that look like a timestamp, with a position after them, are `malformed-timestamp`. The time indicator is required: six digits after the DTI never read as a position (a compressed position never starts with a digit, and an uncompressed one has its point fifth), so seven bytes that look like a timestamp only by their digits are already skipped. An uncompressed reading straight after the DTI is never overruled, since its seventh byte is a digit or a space, so only a compressed reading gives way.

A compressed position after the seven bytes does not overrule a compressed reading straight after the DTI: both are equally weak evidence, the live traffic above has no packet where the choice matters, and the reading straight after the DTI keeps the reports that have no timestamp at all, whose seventh byte (the second of the compressed longitude) is `z`, `/` or `h` one time in thirty, from being read from bytes eight on (`position/compressed-without-timestamp-seventh-byte-z`, `position/garbled-timestamp-before-a-compressed-position`). The report is still `malformed-timestamp`, so a strict decoder rejects it, and its data has no timestamp, so it re-encodes as a report without one (`=` for `@`, `!` for `/`), as every garbled timestamp does (`corpus/0536`). The four existing cases with this shape (`corpus/0536`, `corpus/0991`, `corpus/1095`, `corpus/1307`) already read the position after the seven bytes, because their first bytes do not read as a compressed position. A status report has no position for a garbled timestamp to compete with; an object's seven bytes already follow the object rule (`object/garbled-timestamp`, where `ABCDEFz5301.` would also read as a compressed position).

## Lifting an element never joins the text either side of it

- The Comments rule lifts structured elements out of a comment in an order (base-91 telemetry, a `!DAO!`, a `/A=` altitude, braces, a late data extension, a voice frequency), the Mic-E rule adds a later Mic-E altitude, a PHG, RNG or DFS after the type code or locator, and a locator, and the Weather rule reads fields up to the first thing that is not one. Earlier rulings applied one principle piecemeal: a `!DAO!` is five bytes as sent, so taking another element out never joins one ([`!DAO!` datum digits](#dao-datum-digits)); telemetry is found first and a `!DAO!` only outside it ([above](#base-91-telemetry-and-dao)); a locator split by a Mic-E altitude is not one ([Where a Mic-E locator is read](#where-a-mic-e-locator-is-read)); a run-on weather value ends at a lifted element, and the text after it is on its own ([A weather field that runs on by many digits](#a-weather-field-that-runs-on-by-many-digits)).
- Elsewhere all six libraries read the text left once an element was lifted as if it had been sent that way: base-91 telemetry from `|!:&0hl!Y[/>"4e}='p|` once the Mic-E altitude `"4e}` was out, a PHG from `PH"4e}G3330`, `PH!W12!G3330` or `PH|!!!!|G3330`, a `/A=` from `/A=00!W12!0123`, a signpost from `{5!W12!5}`, a weather software type and unit from `X!W12!yz`, and a frequency's tone from `146.520MHz/A=000100 T100`. A strict Mic-E decoder had a rule of its own to reject an altitude that only lifting telemetry or a `!DAO!` made.

**Decision:** lifting an element never joins the text either side of it, for every element, in every kind of report (position, object, item, weather, Mic-E status text). An element is recognised only where its bytes stand whole in the text as sent (in Mic-E status text, once 0xFF padding is removed): base-91 telemetry is `|`, 2 to 14 characters (an even number) and `|`, contiguous as sent; a `!DAO!` is its five bytes; a PHG, RNG or DFS, a `/A=` altitude, a Mic-E altitude, signpost or corridor braces, a voice frequency with its tone, offset and range fields, a weather field and a weather software type and unit are each contiguous as sent. The order of lifting only settles overlaps (which of two readings of the same bytes wins). Once an element is lifted, the pieces either side of it are separate for recognising any other element: nothing is read across the place it came from, and where a rule asks for an element to be followed by a space or the end (a frequency field, a run-on weather value), the start of a lifted element counts as the end. An element is what the sender wrote; text a decoder assembles from two fragments was never sent as that element, and reading it so reports values the sender did not send (`RNG001` and the `1` of a frequency after a Mic-E altitude read as 11 miles).

One element is an exception, a `/A=` altitude, and the spec's wording alone does not single it out. APRS12c ch. 6 says "The altitude may appear anywhere in the comment", but ch. 5 says as much of a `!DAO!` ("a 5 byte field !DAO! appearing anywhere in the position comment field", only recommending "placing this option on the END of all other position comment text"), and ch. 13 lets a `!DAO!` follow base-91 telemetry ("The DAO extension MAY appear after the Base91 Telemetry extension"). The exception rests on ch. 6 together with live traffic: APRSdroid writes the altitude straight after the frequency and the user's tone or offset after it (below), while in 297 million lines no sender puts a `!DAO!` or base-91 telemetry among a frequency's fields. Ch. 18 lays a voice frequency out in 10-byte slots for radio displays (the frequency in "the first 10 bytes" of the comment, then "Optional Added fields (with leading space)" such as `Txxx` and `-060`); the slots are positional, so reading them as fields with an altitude allowed between them is a moderate stretch of ch. 18, taken because senders do it. The rule, in the sentence the libraries quote: **the `/A=` lifted as the altitude may stand between a voice frequency and its first field, or between two of its fields, without cutting them off; nothing else may stand there, so a space before the `/A=` ends the fields, and a `/A=` inside any element splits it.** The frequency itself needs no exception: it is read at the start of the text left, whatever was lifted before it (below), as in `PHG8270/A=000813147.490MHz`; its fields follow the `/A=` in `146.820MHz/A=-00016 T103 -060`, as APRSdroid sends. A `!DAO!` or base-91 telemetry between a frequency and its fields cuts them off (`position/tone-after-a-dao-after-a-frequency-is-text`, `position/tone-after-telemetry-after-a-frequency-is-text`), and so does a later Mic-E altitude in Mic-E status text (`mic-e/mic-e-altitude-between-a-frequency-and-its-tone-cuts-it-off`). Reading a `/A=` as not part of the comment at all, taken out before anything else is read so that the text either side joins, was considered and rejected: it would make `PHG2360/A=0001005/x` a PHGR (`position/phg-rate-after-an-altitude-is-text`) and give `146.520MHz /A=000100T100` a tone (`position/tone-after-an-altitude-with-its-space-before-the-altitude-is-text`), readings the sender never wrote.

A field is its space and value together as sent: ch. 18 gives the fields "with leading space", and the README asks a space before each. So a `/A=` may stand before a field's space but not between the space and the value: in `146.520MHz /A=000100T100 x` and `146.520MHz T100 /A=000100-060 x` the space and the value are on opposite sides of the altitude, and the value is text (`position/tone-after-an-altitude-with-its-space-before-the-altitude-is-text`, `position/offset-after-an-altitude-with-its-space-before-the-altitude-is-text`). The exception lets an altitude stand anywhere in the comment; it does not pair a field's value with a space left on the other side of the altitude. With a space either side of the `/A=`, two bytes stand between the frequency and the field, and the field is text too (`position/spaces-either-side-of-an-altitude-after-a-frequency`). In the APRS-IS captures from 2026-10-01 to 2026-11-15, 68,480 lines have a space before a `/A=` after a frequency and text straight after the altitude (`146.640MHz T131 -060 /A=001280Tanner-Carrollton`, from a direwolf digipeater); in none is that text a field (one corrupt packet has `T504.49W` there), so the choice changes no live packet.

Real traffic grounds both the principle and the exception. In 297,417,911 APRS-IS lines over 40 days (2026-10-01 to 2026-11-14), the principle with no exception changes 8,498 packets from 4 stations, every one APRSdroid writing the altitude straight after the frequency and the user's tone or offset after it (`corpus-finding/aprsdroid-tone-and-offset-after-an-altitude`, `corpus-finding/aprsdroid-tone-after-an-altitude`, `corpus-finding/aprsdroid-offset-in-the-wrong-unit-after-an-altitude`); with the exception, none changes. No joined telemetry, PHG, RNG, DFS, signpost or `/A=` occurs in live traffic at all. Where a rule places an element at the start as sent (a Mic-E locator, and a PHG, RNG or DFS after the type code, leading altitude or locator, [above](#where-a-mic-e-locator-is-read)), that stands.

Three judgements are made on the text left rather than on adjacency, and are not joining: a Mic-E locator's space, the one space dropped after a voice frequency and its fields, and the comment's leading space or `/`. They recognise no element; they decide where the comment begins, and the comment is by definition the text left. So a space or `/`, then a lifted element, then text gives that text as the comment (` |!!!!|x` and `/!W12!x` give `x`, `position/leading-space-before-telemetry`).

The start of a voice frequency is judged the same way. The one space or `/` it may follow is ch. 18's free text delimiter, the same byte as the comment's leading delimiter, and it recognises nothing; and the start is the start of the text left, so any lifted element may stand before the frequency, as `corpus/0493` (`/A=000524|#.!?|433.775Mhz`) and `object/signpost-frequency-and-altitude` (`/A=000100{55}146.520MHz`) already have it. So a delimiter, a lifted element and a frequency give the frequency: `/|!!!!|146.520MHz T100 x`, and Mic-E status text `/"4e}146.520MHz T100 x` once the later altitude is lifted (`position/frequency-after-a-slash-and-telemetry`, `mic-e/frequency-after-a-slash-and-a-later-altitude`). Judging that one byte as sent would make it the one place a start is not judged on the text left. The frequency itself still stands whole as sent.

Writing a comment back, the space before free text after a frequency separates it from the frequency's fields. A `/A=` written after the frequency or its fields does that already, and bytes straight after a lifted `/A=` cannot be a field, which needs its space; so free text that a space would make read as a field is written straight after the `/A=` (`146.520MHz T100/A=000100-060 x`, `position/text-reading-as-an-offset-after-a-tone-and-an-altitude`): the shortest form that reads back, the form `position/tone-split-by-an-altitude-is-text` already writes without fields, and the bytes APRSdroid sends. Braces cut a frequency off from what follows, so after them a space never makes the text a field: free text after a frequency and braces is written after a space, with a `/` only where it would not read back without one (`object/text-after-a-frequency-and-a-signpost-takes-its-space`, `object/text-after-a-tone-and-a-signpost-takes-no-slash`).

A PHG is its seven bytes. Its rate byte and `/` (a PHGR, "an extra character followed by a mandatory / character", ch. 7) are an optional suffix, read only where they follow the seven bytes as sent; split off by a lifted element (`PHG23605!W12!/x`, `PHG2360/A=0001005/x`), the PHG is read and they are text (`position/phg-rate-split-by-a-dao-is-text`, `position/phg-rate-after-an-altitude-is-text`). A weather report's software type and unit are one element: it must be the whole of the text left after the fields, and stand whole as sent. A lifted element before or after it changes nothing (`t058!W12!xRSW`, `weather/software-and-unit-after-a-dao`), and one inside it makes it text (`weather/software-and-unit-split-by-a-dao-is-text`); so does text after a lifted element that follows it, since the text left is then more than the software type and unit: `t058xRSW|!!!!|abc` has the comment `xRSWabc`, not the software `x`, the unit `RSW` and the comment `abc` (`weather/software-and-unit-before-telemetry-and-text-is-text`). The start of a lifted element does not end a software type and unit as it ends a run-on weather value: the software type and unit is judged on the whole text left, not read up to a place.

Of two `/A=` that stand whole, the first is the altitude, as Ham::APRS::FAP takes "the first occurrence"; a later one is comment text, and its `/` is treated like any other, so `/A=000100/A=000200` has the altitude 100 and the comment `A=000200`, the `/` dropped as the comment's leading delimiter (`position/second-altitude-is-text`, `position/second-altitude-after-a-space-is-text`). One split by a lifted element is not one, so the first whole one may come after it (`position/whole-altitude-after-one-split-by-a-dao`). Taking the last instead, or refusing the report, has no support in the spec, which gives one altitude "anywhere in the comment". The encoder writes the altitude before the free text, so a later `/A=` in the comment reads back as text.

The comment is the text left once every element is lifted: the fragments either side of each lifted element, in order, as one string, with nothing to mark where an element was; one leading space or `/` is then dropped from it as before ([Delimiters at the start of free text](#delimiters-at-the-start-of-free-text)). So `PH|!!!!|G3330 x` is telemetry and the comment `PHG3330 x`. The comment is the bytes left, in that order, decoded as text once, after lifting: text is not an element, so the principle does not apply to it, and the two bytes of a UTF-8 character either side of a lifted element make that one character (`PHG33`, 0xC3, `!W12!`, 0xA9, `30` gives the comment `PHG33é30`, `position/utf-8-character-split-by-a-dao-joins-in-the-comment`); whether the text is UTF-8 is judged on those bytes. Such a comment can hold text that, written back as a comment, reads as an element (`PHG3330`, `/A=000123` with no `/A=` altitude written before it, `{55}`, `|!:&0'p|`); an encoder writes a comment as one piece, so it has no form that reads back as itself, and under the Encoding rule the report re-encodes `refused`, `text-reads-as-field` (a delimiter before it helps only with the start of a comment, not with a late PHG or a `/A=` anywhere in it). Where the joined text reads back as text (`T100 x` after a frequency and a `/A=`), it re-encodes as usual.

A strict Mic-E decoder declines a later Mic-E altitude and reads it as text; since lifting telemetry or a `!DAO!` never joins the text either side into an altitude, it never rejects a report by `mic-e-altitude-not-first`, and the rule for an altitude left across a lifted place, with its precedence against a locator's missing space, is gone. `mic-e-altitude-not-first` stays a tolerable code whose strict side is a different reading rather than a rejection, as `data-extension-in-comment`'s is: a lenient decoder takes the later altitude and warns, a strict one leaves it in the comment. The single-tolerance check, whose form for a strict rejection by another code came from `mic-e/telemetry-split-by-an-altitude-is-text`, keeps that form; that case now names two tolerable codes, so the check does not apply to it, but four cases of a later altitude after a locator still need it (`mic-e/locator-space-judged-after-a-later-altitude` and the like).

## Where these decisions and Ham::APRS::FAP differ

Found by comparing Packet.Aprs with FAP on the same 33,000 APRS-IS packets (see [aprs-cs's validation notes](https://github.com/packet-net/aprs-cs/blob/main/docs/aprs-validation.md#5-against-hamaprsfap)):

| Case | FAP | These vectors | Why |
|---|---|---|---|
| `/3517.73N/...` (a `/` report with no timestamp) | skips 7 characters and decodes garbage (61.97N) | decodes the position that follows the DTI | a timestamp starts with 6 digits, so a position straight after the DTI is read first, unless seven bytes ending `z`, `/` or `h` and an uncompressed position follow it, where FAP's reading is taken ([above](#a-garbled-timestamp-before-an-uncompressed-position)) |
| `...wHP1000` or a comment containing `ESP32` after weather data | reads `P100` / `P32` as rain since midnight | stops weather fields at the first non-field | weather fields are a contiguous run (APRS12c §12) |
| compressed weather wind in cs | not decoded | decoded as wind direction and speed | APRS12c §12 compressed weather format |
| `!DAO!` in a weather report | not applied | applied | the DAO belongs to the position, not the comment |
| `rejAR}` | rejected ID `AR}` | rejected ID `AR`, reply-ack `""` | reply-ack format (APRS12c §14) |
| PHGR with rate `0` (`PHG01000/`) | accepted | plain PHG; `0/` stays in the comment | the rate is 1-9 then A-Z |
| Mic-E comment | keeps device prefix and suffix | lifts them into `type_code` / `device_suffix` | APRS12c §10 says applications should remove them |
| voice frequency | stays in the comment | lifted into `frequency` | APRS12c §18 |
| a weather symbol with fields that do not start `DDD/SSS`, `c...s...` or `g...t...` | no weather | weather, fields read as a run | the weather station symbol makes the report a weather report (README, Weather) |
| `/A=` in a Mic-E status text | not read; only the Mic-E altitude bytes | the altitude, ahead of the Mic-E bytes | [above](#a-a-altitude-wins-over-a-mic-e-or-compressed-one) |
| `000/000` straight after a compressed position | a course and speed, replacing the cs bytes | comment text, unless the report is weather | a compressed position has no `DDD/SSS` extension (APRS12c ch. 9) |
| a first byte of `,` and a `!` position later in the field | the position | test data | `,` is a data type identifier of its own (APRS12c ch. 5) |

## Errata in APRS12c's own examples

These examples in the spec cannot be what was meant; the cases use the corrected form.

- **§21 Overlays with Symbols**: `=BL!!<*e7>7P[` is 12 characters after the DTI; a compressed position is 13. The latitude `5L!!` has lost its `5`: `=B5L!!<*e7>7P[`.
- **§12 Complete Weather Report, compressed, no timestamp**: `=/5L!!<*e7>_7P[g005...` has a stray `>` before the `_` symbol code. As printed it decodes as a car (`/>`) with course 248 and a comment. The timestamped example beside it (`@092345z/5L!!<*e7_7P[g005...`) is right.
- **§11 Area Objects**: `;FLIGHTPTH*4903.50N\07201.75W l 610/310{100}` has no timestamp, though the same chapter says an object always has one. The spaces around `l` are typesetting, not data (a raw text extraction of the PDF gives `Wl610/310`). The `object-without-timestamp` tolerance exists partly for this.
- **§12 Complete Weather Report with Object**: `;BRENDA   *4903.50N/07201.75W_220/004g005t077...` likewise has no timestamp.
- **§8 examples** use `…` to mean "more fields here", not literal characters.
