# Round 4: builder defaults at 1.1.0 (R4 survey)

What each builder writes, through its own public API, when a program leaves an optional input unset. Read from source at each library's main on 2026-11-14 and checked by building recipes through the six dump tools. File and line are where the default is set. cs = aprs-cs/src/Packet.Aprs (B = AprsBuilder.cs, W = AprsWeatherBuilder.cs, M = AprsMessageBuilder.cs), rs = aprs-rs/src/builder.rs, py = aprs-py/src/pdn_aprs/builder.py, ts = aprs-ts/src/builder.ts, c = aprs-c/src/build.c (H = include/pdn_aprs.h), go = aprs-go/builder.go.

## Differing (each settled by R4)

| Input | cs | rs | py | ts | c | go | Round 4 |
|---|---|---|---|---|---|---|---|
| Mic-E message | off duty (B:384) | off duty (rs:103) | **in service** (py:433) | off duty (ts:585) | off duty, enum 0 (H:482, c:292) | off duty (go:96) | off duty |
| Mic-E type code, messaging not said | `'` (B:416) | `'` (rs:104) | `'` (py:477) | **`` ` ``**, messaging on (ts:586) | `'` (c:313) | `'` (go:451) | `'` |
| Object timestamp | **clock** (B:341) | missing-field (rs:593) | **clock**, DHM (py:327) | **clock** at construction (ts:503) | missing-field (encode.c:1134) | missing-field (go:385) | missing-field |
| Positionless weather timestamp | **clock**, MDHM (W:212) | missing-field (rs:865) | **clock**, MDHM (py:544) | **clock**, MDHM (ts:232) | **invalid-timestamp** (encode.c:2052) | missing-field (go:631) | missing-field |
| Symbol: position, object, item, Mic-E | refused (B:243) | missing-field (rs:294) | refused unless the Station has a default symbol (py:254) | **`//`, silently** (ts:349) | invalid-symbol (encode.c:311) | missing-field (go:249) | invalid-symbol |
| Telemetry report bits | `00000000` (M:148) | `00000000` (rs:159) | `00000000` (py:607) | required argument | `00000000` (c:602) | `00000000` (go:139) | `00000000` (ts: the argument becomes optional) |
| Telemetry report sequence | required | required | required | required | required | required | missing-field (rs's dump tool fills 0, diff_dump.rs:614) |
| Position report, `timestamp=True` | | | reads the clock (py:69) | | | | refused: a builder never reads the clock |

## Agreeing (written into the builder rules as they are)

| Input | All six |
|---|---|
| Messaging, position (compressed or not), positioned weather | off: `!`, or `/` with a timestamp (cs B:266, rs:82, py:225, ts:470, c:230, go:323) |
| Timestamp: position, status, positioned weather | left out |
| Symbol, weather report | `/_` (cs W:15, rs:115, py:501, ts:228, go:102; c's caller sets it, and the dump tool gives `/_` only when the recipe does) |
| Symbol, status with a locator | refused as missing-field (ts takes it as an argument of `locator()`, so it cannot be left out) |
| Path | none (cs AprsStation.cs:66, rs:51, py:223, ts:190, c:47, go) |
| Destination | `APZ001` (cs AprsStation.cs:46, rs:18, py:224, ts encode/common.ts:8, c:45, go:11); Mic-E computes its own |
| Ambiguity | none |
| Compression | uncompressed |
| Killed | alive |
| Message ID, reply-ack, bulletin group | none |
| Telemetry metadata addressee | the sending station (cs M:222, rs:166, py:635, ts:310, c:615, go:145) |
| Weather values left unset | `c`/`s`/`g`/`t` (or the extension's course and speed) written as unknown dots; the others left out |
| Mic-E speed | 0 (the only form: Mic-E has no unknown speed); course left out (0, unknown) |

## Dump tools that fill in an absent recipe key (and so hide a builder default)

- aprs-ts scripts/diff-dump.mjs:492 calls `messaging(a.messaging === true)` always, so its `` ` `` default never showed; :475 and :509 mark an object or positionless weather recipe without a timestamp `unsupported` rather than build it.
- aprs-py tools/diff_dump.py:441 passes messaging false, :445 the default destination, :444 an empty path, :496 bits `00000000`, :478 :485 :488 :504 empty text and project, :489 no status timestamp.
- aprs-rs examples/diff_dump.rs:614 fills a missing telemetry sequence with 0; :559 :582 :591 empty text.
- aprs-c tools/diffdump.c reports an absent `mic_e_message` as unsupported (~708), so its off-duty default never showed.
- aprs-cs DiffBuild.cs passes `text ?? ""` (439, 461, 467); an absent object or positionless weather timestamp reaches the builder's clock.
- aprs-go cmd/aprs-diffdump/build.go fills nothing.

From round 4 a dump tool passes only the keys a recipe gives (IMPLEMENT.md item 4), so the comparison sees each builder's own defaults.
