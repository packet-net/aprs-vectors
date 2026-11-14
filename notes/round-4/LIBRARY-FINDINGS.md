# Library bugs found on v1.1.0 to fix in round 4 (from aprs-watch one-off runs, 2026-11-14)

Each needs a case in aprs-vectors as well as the fix.

## aprs-ts: a Mic-E locator joined across a lifted altitude

Header `N0CALL>S32UVT`, information field (as text): `` `(_fn"Oj/>IO9"4-}1SX/G Hellowor!d `` (the Mic-E altitude bytes `"4-}` sit inside what would otherwise read as the locator `IO91SX/G`). cs, rs, py, c and go give comment `IO91SX/G Hellowor!d` and no locator. ts gives locator `IO91SX`, comment `Hellowor!d`, and writes it back without the altitude in the middle. By interpretations.md "Where a Mic-E locator is read" a locator is read at the start of the status text, after the type code, or straight after a Mic-E altitude; here `IO9` comes before the altitude, and taking an element out never joins the text either side of it. ts is wrong.

## aprs-cs: refusal precedence with a non-finite value

Encode, neutral data: a compressed weather position with longitude 180.00008333 and altitude_feet -Infinity (generate.py --faults --nonfinite, seed 288591650, line 474). cs refuses `value-out-of-range`; rs, py, ts and go refuse `not-a-number`. The README's Refusal reasons order lists `not-a-number` before `value-out-of-range`. cs is wrong.
