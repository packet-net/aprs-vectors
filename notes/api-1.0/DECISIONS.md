# APRS libraries: API decisions before 1.0

Eleven decisions that apply to all five libraries, then eight that belong to one library. Each has a recommendation; "changes" says what each library does if you accept it. The remove and fix items that need no decision are in AUTO.md.

Short names: cs (aprs-cs, C#), rs (aprs-rs, Rust), py (aprs-py), ts (aprs-ts), C (aprs-c).

## Cross-cutting decisions

### 1. Whole or fractional numbers for values the encoder rounds

Today course, wind direction, humidity and luminosity are fractional in cs, ts and C, but whole numbers in rs and py. In all five the data types are also the encoder's input, so a whole-number field means hand-built data cannot carry 88.6 degrees and rs cannot run some vectors encode cases at all.

- A. Fractional for every measured quantity the encoder rounds: course_degrees, wind_direction_degrees, humidity_percent, luminosity_w_m2, and the query footprint's radius_miles. Codes, counters and sequence numbers stay whole (PHG and DFS codes, storm values, DF bearing, rain_raw, tone_value, offset_khz). Rounding happens once, in the encoder. Doc on each field: "whole when decoded; rounded once when encoded".
- B. Whole numbers wherever the air format is whole, which also means making temperature and gust whole in rs and the others.

Recommendation: A. It is what three libraries already do, and it gives one rounding in one place.

Changes: rs: the four fields to f64, builder rounding moves into the encoder, Footprint radius to f64. py: the four fields to float (the py reviewer preferred keeping int; I disagree, for the reason above). cs: Footprint RadiusMiles to double. ts, C: none.

### 2. Numbers kept as sent: telemetry values, coefficients, query footprint, digital bits

Same data, three shapes: py, ts and C hold a number plus the text as sent; rs holds only the text with reader methods (`values()`, `latitude_degrees()`); cs holds exact `decimal`. Digital telemetry bits are eight-character text in rs, py, ts and C (as in the vectors and the recipe) but a `byte` in cs (`AprsTelemetryReport.Digital`, `AprsTelemetryBitSense.Bits`), and the rs and cs builders take a byte.

- A. A number field plus an as-sent text field (analog + analog_text, coefficients + coefficients_text, latitude + latitude_text); bits as text named `bits`, builders take the eight-character text.
- B. Leave each library as it is; all five already re-encode identically.

Recommendation: A, but it is the lowest-value item here; B is a fair choice if you would rather not churn cs and rs.

Changes under A: rs: Telemetry.analog to numbers plus analog_text, TelemetryCoefficients to numbers plus text, Footprint to f64 plus text, readers removed; builder `digital(u8)` becomes `bits(&str)`. cs: decimal to double plus text properties; Digital and Bits (byte) become `Bits` string; `Digital(byte)` builder overload goes. py, ts, C: none.

### 3. One naming rule for fields and builder options

The builders use their own vocabulary: `speed` (knots) beside `speed_kmh`, `altitude` (feet) beside `altitude_metres`, `gust`, `temperature`, `rain_last_hour`, `precise` for dao, `message` for mic_e_message, `to` and `station` for addressee, `Kill()` against `killed`, `IsAlive`/`IsCurrent` against `killed`/`old_data`. The vectors' recipe keys and every library's own data fields already carry the unit.

- A. The rule: a data field has the neutral name in the language's casing (cs may keep its spelled-out unit words, `TemperatureFahrenheit`, as the .NET idiom); a builder setter or keyword has exactly the name of the field it fills; the converting sibling changes only the unit (`speed_kmh`, `altitude_m`, `temperature_c`, `rain_1h_mm`); one setter per value, no two-at-once conveniences; booleans named for the less usual state (`killed`, `old_data`).
- B. Keep the short friendly names (the ts reviewer's preference).
- C. Only regularise the metric names.

Recommendation: A. The unit is then visible at every call site (`.altitude(300)` today reads as metres to most of the world), and the recipe maps one to one.

Changes:
- cs: setters take their property names (CourseDegrees, SpeedKnots, AltitudeFeet, RangeMiles, WindDirectionDegrees, WindSpeedMph, WindGustMph, TemperatureFahrenheit, RainLastHourInches and the rest); `Wind(...)` and `Rain(...)` split into one setter each; `Kill()` becomes `Killed(bool killed = true)`; `IsAlive`/`IsCurrent` become `IsKilled`/`IsOldData` defaulting false; Mic-E `Message` becomes `MicEMessage` on report and builder; `AprsPathEntry.HasBeenRepeated` becomes `Used`; `ProjectTitle` becomes `Project`; `AprsGpsFix`/`AprsNmeaSource` become `AprsCompressionFix`/`AprsCompressionSource`.
- rs: setters take field names (course_degrees, speed_knots, altitude_feet, altitude_m, range_miles, temperature_f, temperature_c, rain_1h_in, rain_1h_mm, humidity_percent, pressure_mbar, luminosity_w_m2, snow_24h_in, message_id, killed()); MicEReport `message` becomes `mic_e_message`; `GpsFix`/`NmeaSource` become `CompressionFix`/`CompressionSource`; TelemetryLabels `labels` becomes `names` and `units`.
- py: keywords take field names (course_degrees, speed_knots, wind_gust_mph, temperature_f, rain_midnight_in and so on); `to`/`station` become `addressee`; `identifier` becomes `id`; `PathEntry.call` becomes `address`.
- ts: courseDegrees, speedKnots, altitudeFeet, altitudeM, rangeMiles; `commentTelemetry()` becomes `telemetry()` like the data field (the ts reviewer recommended no change; I disagree).
- C: input structs already follow it; weather index names gain units (in AUTO); `pdn_aprs_mic_e.message` becomes `mic_e_message`.

### 4. Voice frequency in builders

cs, rs and py offer a tone in Hz as a float that only means a plain tone, and truncate it (88.5 Hz is written 88; everything else rounds); CTCSS and DCS need the whole value object. ts and C take the full value. The recipe has `mhz`, `tone` (tone, ctcss or dcs), a whole `tone_value` as sent, and `offset_khz`.

- A. Builders take what the recipe has: MHz, an optional tone kind with its whole value, an optional offset, or the voice frequency value itself. No Hz float.
- B. Keep the Hz shorthand but round it, and add CTCSS and DCS forms.

Recommendation: A. Also: a frequency in MHz is fractional and rounded to its field's step, never refused for extra decimals (cs refuses 145.7251 today and holds it as decimal).

Changes: cs: shorthand becomes `Frequency(double mhz, AprsToneType? tone = null, int? toneValue = null, int? offsetKHz = null)`, FrequencyMHz to double, rounded. rs: `tone(kind, value)` replaces `tone(hz)`. py: drop the `tone` and `offset_khz` keywords; `frequency` is MHz or a VoiceFrequency (py reviewer's choice, which also works). ts, C: none. All five: check against a rounded-frequency vectors case.

### 5. How a refusal is reported, and whether the reason is machine-readable

Decoding is consistent (a header error carrying coded diagnostics). Encoding is not: cs throws three unrelated exception types (ArgumentException, which also means "bug", InvalidOperationException, FormatException); py raises EncodeError but plain ValueError for a telemetry sequence over 999; ts throws from the middle of a chain (`.weather()`) and checks header addresses only when writing; C builders return ERR_REFUSED and drop the reason text. Nowhere is the reason machine-readable.

- A. For 1.0: one refusal type per library, distinct from programming errors, carrying the reason as text that is not part of the stable API, shaped so a reason code can be added later without a major version. Refusals come from build or encode (an eager setter check is fine if it raises the same type).
- B. As A plus a field name (cs reviewer: `Field = "course_degrees"`).
- C. A shared reason-code list in the vectors' codes.json now, used by all five.

Recommendation: A now, C later as an additive five-library change. B only if all five do it; one library alone would diverge.

Changes: cs: one `AprsEncodeException : ArgumentException` for every refusal, including the `Telemetry(int)` range check and Mic-E misuse; missing builder input stays InvalidOperationException. rs: `EncodeError` becomes `#[non_exhaustive]` with a private field and `message()`. py: builder range refusals raise EncodeError. ts: weather unit clash and header address checks move into `build()`. C: every build call gains a trailing `pdn_aprs_encoded *result` (may be NULL) giving reason and Mic-E destination; add ERR_UNSUPPORTED (in AUTO).

### 6. Builder inputs that differ from the recipe

Small mismatches where a program has to do part of the rule's work, or cannot say something at all.

- Telemetry metadata addressee: optional, default the station itself. cs and rs cannot set it; ts and C require it (ts first); py calls it `station`.
- Telemetry sequence: a number 0-999, refused above. C takes text (the rule lives only in its dump tool); py and ts also accept text (text sequences stay possible through hand-built data).
- Bulletin: one-character id plus an optional group. C takes one string ("4WX"); py calls the id `identifier`.
- Mic-E messaging: a messaging flag, with the type code only for a device type. C has only `type_code`.
- Timestamps from a UTC time are cut inside the library. C takes pre-formatted strings; add `pdn_aprs_format_timestamp()`.
- Weather: one weather entry with an optional position, as cs, rs and py have. ts has `weather(lat, lon, w)` and `weatherReport(w, at)`; the ts reviewer suggests renaming the second `positionlessWeather`; I prefer one `weather(w, { latitude, longitude, at })` like the recipe and the other four.

Recommendation: fix all six as listed. Changes: cs and rs: metadata builder with `addressee`; ts: `telemetryNames(names, addressee?)` and the other three, weather merged; py: rename keywords, number-only sequence; C: unsigned sequence, char id plus group, messaging flag, timestamp formatter, NULL addressee means the source.

### 7. Mic-E: one create call, and never drop the destination

cs and rs refuse Mic-E in `Create` and offer a separate `CreateMicE`/`create_mic_e`; rs's `Data::encode` on Mic-E returns the information field and silently drops the computed destination (half the position). py, ts and C compute the destination in one call.

Recommendation: one packet-create call that computes the destination for Mic-E (cs: fold CreateMicE into Create, destination optional; rs: fold create_mic_e into create). An information-only encode either returns the destination with it (ts, C) or refuses Mic-E (rs, and cs's `ToInformationField` should be checked for the same silent drop).

### 8. Mic-E altitude in feet or metres

A Mic-E altitude given in feet goes in a `/A=`, one in metres in the Mic-E bytes. py records the choice in a public data field (`altitude_in_comment`); cs in an internal property; rs and C only inside the builder; ts in a hidden WeakSet. So in cs, rs and ts, encoding a copy of a built packet's data can give different bytes from the built packet.

- A. A public field `altitude_in_comment` on the Mic-E report (outside the neutral form), set by the decoder when the altitude came from `/A=`, honoured by the encoder.
- B. Builder-only, and document that re-encoding the data may move the altitude.

Recommendation: A. Data then says everything needed to write it again. Changes: cs: make the property public under that name; rs, ts, C: add the field (ts drops the WeakSet); py: none.

### 9. The API view at 1.0

Gaps: cs lacks third_party; rs lacks symbol description and PHG values; ts lacks has_errors, has_warnings, a TNC2 and AX.25 writer of a received packet, PHG values and third_party; C lacks has_errors (one-line fix in AUTO), the two writers, PHG values and third_party.

- A. Every library offers every key except third_party, which is not required (a program that unwrapped an inner packet knows it).
- B. Leave the gaps.

Recommendation: A. The TNC2 and AX.25 writers matter most: an IGate or digipeater needs them and cannot write them from the public types. PHG names: power_watts, height_feet, gain_db, directivity_degrees (cs `GainDbi` and py `gain_dbi` become gain_db). The C reviewer would skip PHG in C as simple arithmetic; I would add it for a complete view, but it is optional. rs and py keep their existing third_party field.

### 10. Is the vectors' neutral form public API?

py exports it as `pdn_aprs.neutral`, ts from the package root; cs, rs and C keep it in tests and dump tools.

- A. Not public anywhere: py renames the module `_neutral`, ts stops exporting it and its dump tool imports the internal file.
- B. Public in py and ts as a documented module or subpath (ts reviewer's choice).

Recommendation: A. A frozen public form would tie each library's major version to changes in the vectors' format, and only two libraries offer it.

### 11. What 1.0 promises in C

Struct sizes depend on overridable capacities, on the number of vectors codes and on every new field, yet CMake can build a shared library with SOVERSION = major.

- A. Source compatibility only within 1.x: rebuild on upgrade, link statically or compile in the amalgamation, CMake target forced STATIC, zero-initialise input structs, new fields may appear with zero meaning absent. Make `reject[]` a fixed 128 now.
- B. Freeze binary layouts: reserved tails, fixed arrays, export macro, size check.
- C. As A but keep shared builds with SOVERSION tied to major.minor.

Recommendation: A (the C reviewer's view, and I agree).

### Left as they are (right for each language)

Fluent builders (cs, rs, ts), keyword methods (py) and input structs (C); exceptions, Result and return codes; null, None, undefined, empty string or has_ flags for absence; mutable versus by-value builders; cs's spelled-out unit words; KISS helpers only in py and ts; TryDecode only in cs; version constants where the language has a habit for them. One note: cs and rs diagnostics carry a byte offset the vectors never test, which 1.0 will freeze; fine if you are happy to keep it.

## Per-library decisions

### cs

- The `Aprs` static class duplicates `AprsStation.From` and clashes with its own namespace, so half the callers cannot use it. Reviewer: remove it, move `DefaultDestination` to `AprsStation`. Agree.

### rs

- Quantity setters take `impl Into<f64>` for five values and `f64` for the rest, so `.course(88)` compiles and `.speed(36)` does not. Reviewer: plain `f64` everywhere. Agree.
- What is `#[non_exhaustive]` at 1.0. Reviewer: types only the crate constructs (Data, Packet, Diagnostic, Device, EncodeError, HeaderError, Unrecognized); data structs a program fills by hand stay exhaustive with Default. Agree.

### py

- `Station(via=...)` plus a derived `path` attribute hold one value twice. Reviewer: one `path` field accepting text or a list; keep `callsign`. Agree.
- `decode` is an alias of `decode_tnc2`. Reviewer: keep both is acceptable. My view: keep only `decode_tnc2`, matching `decode_ax25`, `decode_kiss` and the other libraries.

### ts

- `WeatherInput` lets a value be given in both units and refuses it at run time from mid-chain. Reviewer: make each unit pair exclusive in the type (`OneUnit<...>`), keep a run-time check in `build()` for JavaScript callers. Agree; now or never, since tightening the type later breaks callers.

### C

- One input pattern for builders. Reviewer: an `_args` struct for every builder with optional inputs (position, mic_e, status, message, telemetry), name, timestamp, killed and messaging inside, ack, reject and metadata positional; telemetry uses `empty[5]` so zero means all present. Agree, and do it in one pass with the three removes and decision 5, since every builder signature breaks anyway.
- Name helpers for the remaining enumerations (Mic-E message, tone, DAO and so on). Reviewer: do not add; they exist only for the neutral form. Agree.

### Reviewer decide items folded into the cross-cutting ones

cs 1, 2, 3, 11, 20; rs 1, 3, 11, 12, 13, 14; py 1, 2, 5, 11, 15; ts 2, 9, 10, 11, 12, 13, 16; C 4, 5, 6, 7, 12.
