# aprs-rs pre-1.0 API proposals (pdn-aprs 0.4.0, main 8d7400d)

Ranked by importance. Classes: `remove` (superseded), `fix` (low controversy), `decide` (Tom's call, recommendation given).

## 1. decide: fractional or whole numbers in the decoded data (course, wind direction, humidity, luminosity)

What: `Positioned::course_degrees: Option<u16>`, `Weather::wind_direction_degrees: Option<u16>`, `humidity_percent: Option<u8>` and `luminosity_w_m2: Option<u16>` are integers, while the builder takes `f64` for all four, and `temperature_f` and `wind_gust_mph`, which are just as whole on air, are already `f64`.

Why: the crate follows no single rule. Because `Data` is also the encoder's input, a program that fills `Data` by hand (or `Packet::create`) cannot give a fractional course, so the builder rounds and then the encoder rounds again at the 4-degree compressed step; the 0.4.0 CHANGELOG had to call the neutral-form encode of a fractional compressed course or wind direction `unsupported` for this reason, so aprs-rs is the one library the vectors cannot test there. C# (`double?`), TypeScript (`number`) and C (`double`, "whole degrees when decoded; rounded when encoded") are fractional; Python is `int`.

Options:
- A. `f64` for every measured quantity the encoder rounds: `course_degrees: Option<f64>`, `wind_direction_degrees: Option<f64>`, `humidity_percent: Option<f64>`, `luminosity_w_m2: Option<f64>`. Codes, counters and sequence numbers stay integers (`rain_raw`, `CommentTelemetry`, `Phg`, `DfBearing`, `Storm`, `AgreloDf`, `Footprint::radius_miles`). `Data::encode` rounds once, as it already does for speed, altitude, pressure, temperature and rain. The builder's own rounding of course and wind direction moves into the encoder, and the runner's and dump tool's `unsupported` case goes away. Cost: a decoder user reads `f64` for a value that is always whole when decoded.
- B. Whole numbers wherever every on-air form is whole: keep the four as integers and also make `temperature_f: Option<i16>` and `wind_gust_mph: Option<u16>`. The builder stays the only place a fractional value can come in; fractional neutral data stays `unsupported` for compressed course and wind direction.

Recommendation: A. One rounding, in one place (the encoder), for every input path, and the same model as three of the other four libraries. Document on each field "whole when decoded; rounded once when encoded".

## 2. fix: `Code::ALL` and `ParseOptions` cannot take a 65th code

What: `Code` is `#[non_exhaustive]`, but `Code::ALL: [Code; 64]` puts the count in the type, and `ParseOptions` stores tolerated codes in a `u64` indexed by `code as u8`, which already holds 64 codes. Adding any code after 1.0 breaks `ALL`'s type and overflows the shift in `Code::bit`.

New shape: `pub const ALL: &'static [Code]`; `ParseOptions` stores a private `u128` (or `[u64; 2]`). No other public change.

## 3. decide: builder setter names follow the recipe keys and the data fields

What: the builder uses its own vocabulary with units sometimes in the name, sometimes in the parameter name only: `speed` (knots) next to `speed_kmh`, `altitude` (feet) next to `altitude_metres` (data and recipe say `altitude_m`), `range` (miles), `temperature` / `temperature_celsius` (recipe `temperature_f` / `temperature_c`), `gust`, `rain_last_hour` / `rain_last_hour_mm` (recipe `rain_1h_in` / `rain_1h_mm`), `snowfall`, `pressure`, `luminosity`, `humidity`, `MessageBuilder::id` (recipe and data `message_id`), `kill()` (data and recipe `killed`).

Why: three vocabularies (data fields, recipe keys, builder methods) for the same values; the unit is invisible at the call site (`.altitude(300.0)`), and the metric names are spelled three ways (`_kmh`, `_metres`, `_celsius`, `_mm`).

New shape (recommended): the method is the recipe key. Positioned: `course_degrees`, `speed_knots`, `speed_kmh`, `altitude_feet`, `altitude_m`, `range_miles`, `offset_khz` (unchanged), `frequency` (unchanged, `mhz` parameter). Weather: `wind_direction_degrees`, `wind_speed_mph`, `wind_gust_mph`, `temperature_f`, `temperature_c`, `rain_1h_in`, `rain_24h_in`, `rain_midnight_in`, `rain_1h_mm`, `rain_24h_mm`, `rain_midnight_mm`, `humidity_percent`, `pressure_mbar`, `luminosity_w_m2`, `snow_24h_in`. Message: `message_id`. Object and item: `killed()`.

Alternative: keep the friendly names and only regularise the metric ones (`altitude_m`, `temperature_c`, `rain_1h_mm`...). Recommendation: the recipe keys; the dump tool's `--build` mode then becomes a straight key-to-method table.

## 4. decide: one parameter type for every quantity setter

What: `course`, `wind`, `wind_direction`, `humidity` and `luminosity` take `impl Into<f64>`; every other quantity (`speed`, `altitude`, `pressure`, `temperature`, rain...) takes `f64`.

Why: `.course(88)` compiles but `.speed(36)` does not; the generic cannot be coerced to a function pointer (the dump tool's rain table needs that); it exists only to keep 0.3 code compiling.

Options: all `f64` (idiomatic, matches std, literal needs `.0`), or all `impl Into<f64>`. Recommendation: all plain `f64`.

## 5. decide: what is `#[non_exhaustive]` at 1.0

What: only `Code` is. 0.3.0 had to break for `Nmea::comment` and `Packet::third_party`; after 1.0 every new field or variant is a major version.

Options:
- A. `#[non_exhaustive]` on what only the crate constructs: `Data`, `Packet`, `Diagnostic`, `Device`, `EncodeError`, `HeaderError`, `Unrecognized`. Data structs a program builds by hand for `Data::encode` (`Positioned`, `Weather`, the reports...) stay exhaustive with `Default`, so `..Default::default()` keeps working; a new field there is a major version.
- B. All public structs and enums non-exhaustive, which forbids struct literals outside the crate, so every data type then needs a constructor or the builder.
- C. Nothing more.

Recommendation: A. `Packet` then cannot be built by literal (use `Packet::create` / `Packet::decode`), which is also what keeps `information` and `data` in step.

## 6. fix: `Data::encode` on Mic-E data drops half the position

What: `Data::encode` on `Data::MicE` returns the information field and throws away the computed destination address, which carries the latitude and message code; `Packet::create` already refuses Mic-E for this reason.

New shape: `Data::encode` refuses `Data::MicE` with the same message as `Packet::create` ("use Packet::create_mic_e").

## 7. fix: add `WeatherBuilder::wind_speed_mph(f64)`

What: there is a direction-only setter but no speed-only one; the dump tool sets a speed alone through `observations(Weather { wind_speed_mph, .. })`, which only works because it is called before everything else.

New shape: `wind_speed_mph(mph: f64)` (or `wind_speed(mph)` if item 3 is declined).

## 8. remove: `WeatherBuilder::wind(direction, speed)`

Superseded by `wind_direction` (0.4.0) plus the speed setter from item 7.

## 9. remove: `TelemetryBuilder::analog(&[f64])`

Superseded by `channels(&[Option<f64>])` (0.4.0), which says everything it does. New shape: one method, `analog(values: &[Option<f64>])` (the recipe key and the data field name), and `channels` goes.

## 10. fix: one comment-telemetry setter

What: positioned builders have `telemetry(sequence, &[u16])` and `telemetry_with_bits(sequence, &[u16], u8)`, while every other structured extension is one setter taking its data type (`phg(Phg)`, `voice_frequency(VoiceFrequency)`, `beam(BeamHeading)`).

New shape: `telemetry(CommentTelemetry)`; `telemetry_with_bits` removed.

## 11. decide: voice frequency tone

What: `tone(hz: f64)` always means `Tone::Tone`, and casts with `as u16` (cut, not rounded, unlike every other value); CTCSS and DCS, both in the recipe format, need the whole `voice_frequency(VoiceFrequency { .. })`.

Options: A. `tone(kind: Tone, value: u16)` replacing `tone(hz)`: one setter for `tone`, `ctcss` and `dcs`, the value as sent (`88` for 88.5 Hz, as APRS12c writes it). B. Keep `tone(hz)` and add `ctcss(hz)` and `dcs(code)`. C. Leave it; `voice_frequency` covers the rest. Recommendation: A.

## 12. decide: telemetry metadata for another station

What: `telemetry_names`, `telemetry_units`, `telemetry_coefficients` and `telemetry_bits` always address the station's own source; the recipe format has `addressee` ("the station itself when absent"), and the dump tool reports any other as unsupported.

Options: A. The four return a `TelemetryMetadataBuilder` with `addressee(&str)`, `to_data()` and `build()`. B. Leave it; `Station::data(Data::TelemetryNames(..))` covers it. Recommendation: A, since metadata for a sensor station sent by its gateway is ordinary use.

## 13. decide: the API view's `symbol` and `phg`

What: the crate has no symbol descriptions and no PHG arithmetic, so its dump leaves out two API view keys and is untested on them.

New shape: `Symbol::description(&self) -> Option<&'static str>` (the text is already generated into `symbols.rs`'s doc comments, about 190 strings); `Phg::watts() -> u32`, `Phg::height_feet() -> u32`, `Phg::gain_db() -> u8`, `Phg::directivity_degrees() -> Option<u16>` (None for omni). Recommendation: add both; the cost is a few kilobytes of strings, acceptable for `no_std` targets that already carry the device database.

## 14. decide: `EncodeError` reason

What: `EncodeError { pub message: String }` is text only. `HeaderError` carries coded diagnostics; a refusal does not.

Options: A. Make it `#[non_exhaustive]`, field private with `message(&self) -> &str`, so a machine-readable reason can be added after 1.0 without a major. B. Add a reason enum now (no other implementation has one; hundreds of refusal sites). C. Leave it. Recommendation: A.

## 15. fix: device lookup functions live on `Device`

What: crate-root free functions `pdn_aprs::tocall(callsign)` and `pdn_aprs::database_version()`: vague names at the root of an APRS crate (`tocall` reads as a noun).

New shape: `Device::from_tocall(callsign: &str) -> Option<Device>`, `Device::DATABASE_VERSION: &'static str`.

## 16. fix: `Severity` implements `Display`

What: `Code` has `id()` and `Display`; `Severity` has `name()` and no `Display`, though `Diagnostic`'s `Display` prints it.

New shape: `impl Display for Severity` (the vectors name); keep `name()`.

## 17. fix: course doc says 1-360

What: `Positioned::course_degrees` says "1-360; 360 is north", but the decoder gives `Some(0)` for `000` and the encoder writes 0 as the unknown course.

New shape: doc "0 is the spec's unknown course, 360 is north (1-360 known)".

## 18. fix: `InvalidAddress(pub String)`

What: a public tuple field on an error type fixes its representation.

New shape: private field, `InvalidAddress::text(&self) -> &str`.

## 19. fix: `TelemetryCoefficients` has no numeric reader

What: `Telemetry::values()` and `Footprint::latitude_degrees()` read as-sent text as numbers; coefficients, also kept as sent, have no such reader.

New shape: `TelemetryCoefficients::values(&self) -> Vec<Option<f64>>`.

## 20. fix: `Timestamp` text form

What: `Timestamp::to_bytes() -> Vec<u8>` for what is always ASCII; no `Display`.

New shape: `impl Display for Timestamp` (`092345z`, `10090556`), and `to_bytes` removed.
