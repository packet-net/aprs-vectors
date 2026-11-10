# Batch 2 rulings (draft)

Each ruling cites its spec basis; where the spec is silent, the reasoning is given. None is settled by what an implementation or a majority does.

## Encoder (neutral data in, bytes out)

F1. **Course 0 is written only where it reads back as 0.** APRS12c ch. 7 gives an uncompressed course of `000` as unknown, and the decoder reports it as course 0, so data holding `course_degrees: 0` is written `000` there. Mic-E course 0 ("unknown or indefinite", ch. 10) reads back as no course, and a compressed c of 0 reads back as 360, so in Mic-E and compressed reports a course of 0 is refused.

F2. **Values between steps.** A number that lies between the steps its field holds is rounded to the nearest step, halves away from zero, and refused only if the rounded value is outside the field. Rounding comes first and every other check (F1, F5, F6) applies to the rounded value: a course of -0.3 rounds to 0 and is then refused, a compressed speed of -0.3 rounds to 0 and is written (so 99.7 percent humidity is `h00`, a course of 360.4 is `360`, a humidity of 0.4 is refused under F6). This extends the cs rounding of E9 to every field: course, speed, `/A=` feet, Mic-E speed and course, latitude and longitude minutes, DAO digits, weather values, RNG miles, a query footprint's radius, a voice frequency. Halves are decided on the value computed in binary floating point, where a value within 1e-6 of a step's half, measured in steps, is the half and goes away from zero: a latitude of 0.9764166666666666 degrees is 58.584999999999996 minutes, which is the half 58.585 and is written 58.59; a pressure of 986.9499999999999 is 986.95 and is written 9870 tenths. A neutral value is decimal text whose nearest binary number often lies a few ulps either side of the half the text means, and minutes derived from degrees almost never have an exact decimal; the tolerance makes the half the text means win in every language without decimal arithmetic. A value derived from another (minutes from degrees, knots from km/h) is computed from the value given and rounded once, never rounded twice. Reason: the spec gives each field's resolution but no rounding rule; rounding to the nearest is the only choice that keeps the written value nearest the one given, and one rule for every field leaves nothing to choose.

F3. **Snowfall** follows F2 on the three forms of E8: a value that rounds to under 1 in hundredths is `.dd`, else one that rounds to under 10 in tenths is `d.d`, else whole (9.96 is `010`, 0.995 is `001`); one that rounds past 999 is refused.

F4. **A DAO on an ambiguous position is refused**, whatever its precision (including `!W  !`): the decoder reports `dao-with-ambiguity` (codes.json: a DAO "adds precision to an ambiguous position, which contradicts it"), so no clean form exists.

F5. **Compressed course and speed come together.** A compressed course with no speed, or a speed with no course, is refused: the cs bytes hold both, so writing one adds a value the data does not have (interpretations.md "Compressed course 0 is north" already refuses an unknown course).

F6. **Humidity 0 is refused** (after F2 rounding): APRS12c ch. 12 gives `h00` as 100 percent, so 0 percent has no form.

F7a. **An area, DF bearing or storm extension does not count as the data extension** for the late search, as a course/speed does not (README Comments rule): each describes the object or the bearing, not the station's radio, and APRS12c ch. 7 lists Tyy/Cxx with the other seven-byte fields. So a later PHG, RNG or DFS in its comment is found, and comment text holding one after an area (`l710/310RNG12 RNG0050`) has no clean form and is refused.

F7. **One data extension.** A course/speed (or an area, DF or storm extension) with a PHG, RNG or DFS is refused: the second extension can only be written later in the comment, where it reads back with `data-extension-in-comment` (UAP 5.15), a warning, so no clean form exists. (Mic-E status text, which carries a PHG or RNG without a course/speed extension, is unaffected.)

F8. **DF or storm data with no course and speed** is written after `.../...`: APRS12c ch. 7 allows `000/000`, `.../...` or spaces for an unknown course and speed, and `.../...` is the form that reads back as unknown (a course of `000` is a fixed DF station).

F9. **A frequency after a DF bearing or storm data** follows a `/`, as after a seven-byte extension (E4): the bearing and storm fields extend the course/speed, and APRS12c ch. 18 adds the delimiter "to make the packet more readable".

F10. **Third-party packets** whose inner packet reads back with only `info:` diagnostics are written: an info is not a defect (Encoding: refused only when the inner header has a tolerated defect).

F11. **Numbers given without their text.** Where a number arrives as data rather than as the text sent (E1 keeps the text when there is one):
- a telemetry report's analog value that is a whole number from 0 to 999 is three digits (`005`, `000`), as APRS12c ch. 13's `aaa` field and its examples write it; the sequence the same (`sss`);
- every other number (another analog value, an `EQNS.` coefficient, a query footprint's latitude and longitude) is the shortest decimal that reads back as the same number, with no exponent and no `+`, a leading `0` before a point (`0.53`), and no trailing `.0` (`190.0` is `190`); `1e61` is `1` and 61 zeros. APRS12c gives no number format beyond its examples (`45.7`, `-7.3`, `.53`, `34.02`); this is the plain decimal form every language can write and every decoder reads;
- a query footprint's positive latitude and longitude each get a leading space (APRS12c ch. 15: "North and east coordinates are positive values, indicated by a leading space"), and its radius is four digits in whole miles (same, "a fixed 4-digit number").

F12. **`T#MIC` with an empty first channel is refused.** Under the README telemetry rule no form reads back with the first channel empty after `MIC` (`T#MIC,,033` reads back otherwise in four decoders), so there is no clean form. The decode rule is not changed.

F13. **NMEA data whose fields disagree with its sentence** (by more than the vectors' 1e-9 tolerance) is refused: written, it reads back with the sentence's values.

F14. **A compressed GGA altitude with no place for a `/A=`** (a compressed weather report, which has no comment) is rounded to the cs step, as E9 rounds any value the cs bytes carry in steps; the report re-encodes `rounded`.

F15. **A query footprint coordinate of 0 takes the leading space.** APRS12c ch. 15 gives the space to north and east and a minus to south and west; 0 is the equator or the prime meridian, which APRS writes N and E elsewhere (`0000.00N`), and without the space a 0 latitude joins the query type (`?WX?0`). The decode rule changes to "one leading space before a value that is not negative".

F16. **A Mic-E locator followed by base-91 telemetry or a DAO**, with no comment, is written (`IO91|...|`): telemetry and the DAO are lifted from the status text before the locator is read (README Comments order), so it reads back clean.

F17. **A Mic-E locator is read only at the start of the status text** (or straight after a Mic-E altitude, `mic-e/locator-after-altitude`), as APRS12c ch. 10's examples place it (`IO91SX/G Helloworld`, `>IO91SX/G`, `]IO91SX/G`). So comment text that looks like a locator after a PHG or RNG (`]PHG3330IO91SX/G`) is text, reads back as itself, and is written straight on (E7).

## Builder (an application's values in)

B1. **A builder's course of 0 is the spec's 0: unknown.** APRS12c gives 0 as unknown and 360 as north in both ch. 7 (`000`) and ch. 10 (Mic-E), so a builder that takes APRS courses takes that convention: an uncompressed report writes `000`, Mic-E writes 0, and a compressed report refuses it (the cs bytes have no unknown course, F5). North is 360. After F2 rounding, a course of 0.3 is 0 and so unknown.

B2. **Units.** km/h is converted to knots (1 knot = 1.852 km/h), metres to feet (1 foot = 0.3048 m), Celsius to Fahrenheit, millimetres to inches (25.4), and the result rounded once by F2. A Mic-E altitude given in metres goes in the Mic-E altitude bytes, whose unit is the metre (APRS12c ch. 10), rounded to the metre; one given in feet goes in a `/A=`.

B3. **Ambiguity on a raw position** reports the box that holds the position: the digits are cut, not rounded, then blanked (49 deg 03.596 min with one level is box 03.5x, centre 03.55). Rounding first can move the position into the next box, whose centre is further away. The centre is written into the Mic-E longitude digits a decoder ignores (README Mic-E rule).

B4. **A DAO on a raw position**: the position is taken in DAO steps (thousandths of a minute, or ninety-firsts of a hundredth), rounded once by F2, and split into the main digits and the DAO digits (interpretations.md "DAO digits").

B5. **Timestamps** from a UTC time are cut to the field's resolution, not rounded (09:23:59 is `0923` in `dhm`): a clock shows a minute until the next begins.

B6. **Telemetry from a program**: the sequence is 0-999 written in three digits (APRS12c ch. 13 `sss`); a larger one is refused, not wrapped. Values follow F11.

B7. **Mic-E messaging.** The Mic-E status text's type code is how a Mic-E report says whether the station can message (APRS 1.2 Mic-E type codes: `` ` `` messaging, `'` not). A builder writes `` ` `` when the program says the station can message and `'` when it does not, unless the program gives a device type.

B8. **Out of range is refused, never clamped**: an object name over 9 characters, an item name outside 3-9, a message ID that is empty or over 5 characters (APRS12c ch. 14: 1-5 alphanumerics), a sequence over 999.

## API view

A1. **Device lookup is case-sensitive.** aprs-deviceid lists tocalls in upper case, and a destination is a callsign; `APNl02` matches nothing. Its wildcard `n` is a digit.

A2. **Every packet's view has its device**, an inner packet's too, and an unrecognised packet's: the device comes from the destination, not the data.

## Follow-ups from the batch 2 self-checks

G1. **A PHG or RNG straight after a Mic-E locator and its space** is lifted before a later Mic-E altitude is looked for, as one straight after the type code is (`` `IO91SX/G PHG1060}AB ``: `060}` is the PHG's, not an altitude). Same reason as the type-code rule: the PHG holds the place of a data extension, and its digits are never an altitude.

G2. **The ambiguity cut (B3) takes F2's tolerance**: a value within 1e-6 of the box edge above it, in the box's units, is on that edge (80.49 degrees is 29.40 minutes, box 29.4x), so the box the text means wins.

G3. **cs steps beyond the byte.** A cs field's steps follow its formula for every whole s, and a value rounds to the nearest of them; when that s is outside the byte's range the value is refused. A speed of -0.03 knots is written as 0, -0.3 is refused (nearest s = -5); a range of 1.95 is written as 2 miles, 1.9 is refused (nearest s = -1). This replaces F2's draft example "a compressed speed of -0.3 rounds to 0", which never reached the README. It is the same rule a field of whole units follows: -0.3 knots rounds to 0, -5 stays -5 and is refused.
