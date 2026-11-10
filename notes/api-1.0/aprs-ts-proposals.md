# aprs-ts pre-1.0 API proposals

Ranked by importance. Counts: remove 0, fix 8, decide 8. Nothing in aprs-ts is a superseded older form with a newer replacement beside it, so there are no `remove` items; the public surface that should go is leakage, listed as `fix`.

## 1. decide: the shape of `WeatherInput`

What: `WeatherInput extends Weather` adds `temperatureC`, `rain1hMm`, `rain24hMm`, `rainMidnightMm`. A value given in both units compiles, and is refused at run time with an `AprsEncodeError` thrown from `.weather()`, `PacketBuilder.weather()` or `.weatherReport()` itself, in the middle of the chain, not from `build()`.

Why: the field names are right (they match the recipe keys `temperature_c`, `rain_1h_mm` and so on and pair with `temperatureF` / `rain1hIn`), and an object rather than per-unit methods is the TypeScript idiom (aprs-py does the same with keyword arguments). What is wrong is that the mistake the runtime check catches is one the type system can catch, and the throw site contradicts the documented rule that refusals come from `build()`. Tightening the type after 1.0 is a breaking change, so it is now or never.

Options:
- (a) Keep the object, make each pair exclusive in the type, keep the run-time check for JavaScript callers but move it into `build()`. Checked with `tsc --strict`: a decoded `Weather` still passes as a `WeatherInput`, and `{ temperatureF: 61, temperatureC: 16 }` is a compile error.
- (b) A weather sub-builder with per-unit methods (`temperatureCelsius()`, `rainMillimetres()`), as aprs-cs and aprs-rs have. Consistent with `speedKmh()` / `altitudeMetres()` on positions, but more surface and less idiomatic for a value object.
- (c) Leave it as is.

Recommendation: (a). New shape:

```ts
type OneUnit<A extends string, B extends string> =
  | ({ readonly [K in A]?: number } & { readonly [K in B]?: never })
  | ({ readonly [K in B]?: number } & { readonly [K in A]?: never });
export type WeatherInput = Omit<Weather, 'temperatureF' | 'rain1hIn' | 'rain24hIn' | 'rainMidnightIn'> &
  OneUnit<'temperatureF', 'temperatureC'> & OneUnit<'rain1hIn', 'rain1hMm'> &
  OneUnit<'rain24hIn', 'rain24hMm'> & OneUnit<'rainMidnightIn', 'rainMidnightMm'>;
```

No metric wind or snow: the recipe format has none, so none is proposed.

## 2. decide: where the neutral-form functions live

What: `toNeutralData`, `toNeutralHeader`, `toNeutralPacket`, `fromNeutralData` and `Neutral` are exported from the package root.

Why: they exist for the conformance harness and `scripts/diff-dump.mjs`; the README never mentions them. Moving them later is breaking.

Options: (a) a subpath export, `@packet-net/pdn-aprs/neutral`; (b) keep at the root as a documented JSON form; (c) remove from the public API and have the tests import `src/neutral.js`. The dump tool imports from `dist/index.js`, so (c) would need it to import `dist/neutral.js` instead.

Recommendation: (a). It keeps a stable JSON form for anyone who wants the vectors' shape, keeps the root to what applications use, and costs one `exports` entry. `formatTimestamp` / `parseTimestamp` stay at the root (they are on-air text, not neutral form).

## 3. fix: check the header in `build()`, not in `toTnc2()`

What: `build()` encodes the data but a bad source, destination or path entry is refused only when `toTnc2()`, `toTnc2Bytes()`, `toAx25()` or `toKiss()` is called (the dump tool has a second catch for this). `BuiltPacket` also re-encodes the data on every `to*` call instead of using its `information`.

Why: the docs say `build()` throws if the spec does not allow the packet; a `BuiltPacket` that cannot be written is a trap.

New shape: `build()` validates the APRS-IS form of every address once and throws `AprsEncodeError` there; the `to*` writers use the stored `information` and only add their own limits (`toAx25`: AX.25 address form, 8 digipeaters; `toTnc2`: UTF-8).

## 4. fix: builder constructors are public and take an unexported type

What: `PacketBuilder`, `DataBuilder`, `PositionBuilder`, `ObjectBuilder`, `ItemBuilder`, `MicEBuilder`, `MessageBuilder`, `StatusBuilder` and `TelemetryBuilder` all have public constructors whose first parameter is the internal `Header` interface.

Why: leaks internals; `Aprs.from()` is the only intended entry point, and the constructor signatures cannot change after 1.0 if they are public.

New shape: export the classes as types only (`export type { PositionBuilder, ... }`), or mark the constructors `/** @internal */` and build with `stripInternal: true`. Prefer type-only exports: callers name the types, never construct them.

## 5. fix: remove leaked helpers from the root

What: `bytesToHex`, `hexToBytes`, `encodeUtf8`, `decodeUtf8` (byte utilities), and `diagnostic()` (the internal diagnostic factory).

Why: public only for tests and the dump tool; the platform has `TextEncoder` / `TextDecoder({ fatal: true })`; no program constructs a `Diagnostic`. Tests can import from `src/bytes.js`, and the dump tool can carry its own hex helper.

New shape: not exported. Keep `formatDiagnostic`, the code tables and `isTolerable`, which programs filtering diagnostics do use.

## 6. fix: `BuiltPacket.path` is `string[]`, `AprsPacket.path` is `PathEntry[]`

What: the built packet's path is text (`'WIDE1-1*'` possible), the decoded packet's is `{ address, used }`.

Why: missing symmetry; `formatPath` and `formatTnc2Header` take `PathEntry[]`, so a built packet's path cannot go through them.

New shape: `BuiltPacket.path: readonly PathEntry[]`; `via(...path: (string | PathEntry)[])` as `PacketToEncode.path` already accepts.

## 7. fix: `EncodedInformation.info` is named differently from everything else

What: `EncodedInformation { info; destination? }` while `AprsPacket.information` and `BuiltPacket.information` hold the same bytes.

Why: inconsistent name for one concept.

New shape: `EncodedInformation { readonly information: Uint8Array; readonly destination?: string }`.

## 8. fix: `decodeInformation` options and result

What: `decodeInformation(info, destination, options)` requires `options`, unlike every other decoder; `DecodedInformation` has mutable fields while every other result type is readonly.

New shape: `decodeInformation(information: Uint8Array, destination: string, options = ParseOptions.lenient)`; `DecodedInformation { readonly data: AprsData; readonly diagnostics: readonly Diagnostic[] }`.

## 9. decide: Mic-E altitude unit kept in a hidden `WeakSet`

What: `MicEBuilder.altitude(feet)` marks the data object in a module-level `WeakSet` (`ALTITUDE_GIVEN_IN_FEET`) so the encoder writes a `/A=` rather than the Mic-E altitude bytes. The data model cannot say this, so `encodeTnc2({ ...built, data: { ...built.data } })` writes different bytes from `built.toTnc2()`.

Why: hidden state outside the data; a copy of plain data should encode the same.

Options: (a) a field on `MicEReport`, `altitudeInComment?: boolean` (decoder sets it when the altitude came from a `/A=`, encoder honours it, the neutral form ignores it); (b) leave it, document that `BuiltPacket.data` must not be copied.

Recommendation: (a). It is additive, so it could follow 1.0, but it removes the only piece of builder state that lives outside the data.

## 10. decide: machine-readable encode refusals

What: `AprsEncodeError` carries only `message`. Decoding problems have codes (`Diagnostic.code`); encoding refusals do not.

Options: (a) add `readonly code: EncodeRefusal`, a small union shared with the other four libraries (`out-of-range`, `invalid-text`, `invalid-address`, `not-representable`, `would-not-read-back`); (b) leave message-only.

Recommendation: (a), but only as a five-library change agreed in the vectors; adding a field is not breaking, so it need not hold up 1.0.

## 11. decide: API view keys aprs-ts cannot answer

What: the API view's `third_party`, `has_errors`, `has_warnings`, `phg` and `ax25` are left out of aprs-ts dumps because the API has no way to say them.

Options: (a) free functions, keeping packets plain data: `hasErrors(p)`, `hasWarnings(p)`, `phgValues(phg): { watts; heightFeet; gainDb; directivityDegrees: number | null }`, `packetToAx25(p): Uint8Array` (header and information as received, refusing what AX.25 cannot carry), and `ThirdParty.packet` marked by an `AprsPacket.thirdParty?: true`; (b) leave them out.

Recommendation: (a) for `hasErrors` / `hasWarnings` and `phgValues` (cheap, and every other library has them); `packetToAx25` and `thirdParty` only if Tom wants full API-view parity. All additive.

## 12. decide: `weatherReport()` beside `weather()`

What: `PacketBuilder.weather(lat, lon, w)` makes a position report with weather; `PacketBuilder.weatherReport(w, at)` makes a positionless one. Both are weather reports.

Options: (a) rename `weatherReport` to `positionlessWeather`; (b) one `weather(w, { latitude, longitude, at })` as the recipe has it; (c) leave.

Recommendation: (a): the name says the difference, and the spec discourages the positionless form, which the longer name also signals.

## 13. decide: telemetry metadata addressee first and required

What: `telemetryNames(addressee, names)`, `telemetryUnits`, `telemetryCoefficients`, `telemetryBits` require the addressee first; the recipe defaults it to the sending station, which is the usual case.

Options: (a) `telemetryNames(names, addressee = source)` and the same for the others; (b) leave.

Recommendation: (a). Breaking (argument order), so now or never.

## 14. fix: document `RangeError` from the KISS functions

What: `decodeKiss` and `unwrapKiss` throw `RangeError` for a frame that is not a KISS data frame; every other decode failure is `AprsHeaderError`, and the doc comment of `decodeKiss` does not say what it throws.

New shape: unchanged signature; doc comment `@throws RangeError` on both. (Turning it into `AprsHeaderError` would need a vectors code for it, which none exists.)

## 15. fix: `DEFAULT_DESTINATION` duplicated

What: the encoder's `resolve()` uses its own literal `'APZ001'` while the builder uses the exported `DEFAULT_DESTINATION`.

Why: two sources for one public default; the exported constant should be the one both use, and `PacketToEncode.destination`'s doc should name it.

## 16. decide: builder unit method names (no change recommended)

What: `speed(knots)` / `speedKmh()` and `altitude(feet)` / `altitudeMetres()`, while the recipe keys are `speed_knots` / `speed_kmh`, `altitude_feet` / `altitude_m`, and `NmeaSentence` has `altitudeM`.

Options: (a) rename to `speedKnots()`, `altitudeFeet()`, `altitudeM()`; (b) leave.

Recommendation: (b). The APRS unit is the default and the short name; the metric forms are spelt out for readability; the data fields keep the neutral-form suffixes, which is where comparisons happen.
