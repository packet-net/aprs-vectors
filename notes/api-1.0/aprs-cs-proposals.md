# aprs-cs public API proposals before 1.0 (Packet.Aprs 0.56.0, main b6691d5)

Ranked by importance. Classes: `remove` (superseded, already approved), `fix` (low controversy), `decide` (Tom's call; options and a recommendation given).

## 1. decide: how an encoder or builder refusal is reported

What: a refusal today is an `ArgumentException` or `ArgumentOutOfRangeException` from about 150 encoder sites (reason only in `Message`), an `InvalidOperationException` from a builder missing a position or symbol, and a `FormatException` from address parsing in `Aprs.From`/`To`/`Via`. The corpus tool has to catch all three by type (`DiffBuild.cs`) and cannot say why.

Why: after 1.0 the exception type a caller catches is frozen. Three unrelated types for "the library will not write this" is hard to use correctly, and `ArgumentException` also covers genuine programming errors (null arguments), so `catch (ArgumentException)` cannot tell "refused" from "bug". The reason is not machine-readable.

Options:
- A. Keep as is, and document the three types.
- B. One `public sealed class AprsEncodeException : ArgumentException` thrown for every refusal by `AprsData.ToInformationField`, `AprsPacket.Create*`, `AprsBuilder.Build` and builder setters that check eagerly (`Telemetry(int)` range), with `public string Field { get; }` naming the data field in the vectors' neutral form (`course_degrees`, `weather.humidity_percent`, `message_id`). Deriving from `ArgumentException` keeps existing catches working. Missing builder input stays `InvalidOperationException` (a programming error, not data the spec declines); null arguments stay `ArgumentNullException`.
- C. As B plus `public AprsRefusal Reason { get; }`, an enum (`OutOfRange`, `NoCleanForm`, `Conflict`, `TooLong`, `InvalidCharacter`).
- D. A non-throwing `bool TryBuild(out AprsPacket? packet, out AprsEncodeException? refusal)` alongside B.

Recommendation: B. It gives one catchable type and a stable machine-readable field name without inventing a reason taxonomy the other four libraries would then have to match. Fold in item 15 (the leaked `writer` parameter name).

## 2. decide: unit names on builder methods

What: decoded properties carry their unit (`SpeedKnots`, `AltitudeFeet`, `RadioRangeMiles`, `TemperatureFahrenheit`, `WindGustMph`, `RainLastHourInches`), and so do the vectors' recipe keys (`speed_knots`, `altitude_feet`, `temperature_f`), but the builder's default-unit methods do not: `Speed(double knots)`, `Altitude(double feet)`, `Range(double miles)`, `Temperature(double fahrenheit)`, `Gust(double mph)`, `Rain(...)` (inches), `Pressure(double millibars)`, `Luminosity(...)`, `Snowfall(...)`. The converting siblings do (`SpeedKmh`, `AltitudeMetres`, `TemperatureCelsius`, `RainMillimetres`).

Why: `Altitude(120)` next to `AltitudeMetres(120)` reads as metres to anyone outside the US; the asymmetry is the trap.

Options:
- A. Keep the short names (the README examples read `.Course(88).Speed(36).Altitude(120)`).
- B. Rename the default-unit ones to carry the unit: `SpeedKnots`, `AltitudeFeet`, `RangeMiles`, `TemperatureFahrenheit`, `WindGustMph` (was `Gust`), `RainInches` (was `Rain`), `PressureMillibars`, `LuminosityWattsPerSquareMetre`, `SnowfallInches`; keep `Course` (degrees is unambiguous). Old names removed, no shims.

Recommendation: B. The builder then reads like the data it produces and like the recipe.

## 3. decide: fold `CreateMicE` into `Create`

What: `AprsPacket.Create` throws for Mic-E ("use CreateMicE"); `AprsPacket.CreateMicE` computes the destination; `AprsDataBuilder.Build` already dispatches between them, as does the corpus tool by hand.

Why: two entry points where the caller must know which data type needs which is hard to use correctly, and the builder already proves the library can choose.

Options:
- A. Keep both.
- B. `public static AprsPacket Create(AprsAddress source, AprsData data, AprsAddress? destination = null, IEnumerable<AprsPathEntry>? path = null)`: a null destination is `AprsStation`'s default (`APZ001`), or the computed one for Mic-E; a destination given with Mic-E is refused. The string overload follows: `Create(string source, AprsData data, string? destination = null, string path = "")`. Remove `CreateMicE`.

Recommendation: B.

## 4. decide: the `Aprs` static class

What: `Packet.Aprs.Aprs` (`From`, `DefaultDestination`) duplicates `AprsStation.From`; the README and XML docs already explain that code in any `Packet.*` namespace must write `AprsStation.From` because `Aprs` resolves to the namespace.

Why: a type named like its own namespace is a .NET design-guideline violation (CA1724) and the duplication exists only to give a shorter spelling that does not work for half the callers.

Options:
- A. Keep both spellings.
- B. Remove `Aprs`; move `DefaultDestination` to `AprsStation.DefaultDestination`. Every example becomes `AprsStation.From("M0LTE-9")`.

Recommendation: B.

## 5. remove: `AprsTelemetryBuilder.Analog(params decimal[] values)`

What: superseded by `Analog(params decimal?[] values)` (0.56.0). Calls with literal arguments (`Analog(1m, 2m)`) still compile against the remaining overload; only a caller holding a `decimal[]` variable must change.

## 6. fix: `AprsParseOptions` flag names one to one with diagnostic codes

What: rename the eight flags whose name does not say which code they tolerate: `StripTrailingLineBreaks` -> `AllowTrailingLineBreak`, `RecognizeDataExtensionInComment` -> `AllowDataExtensionInComment`, `AllowShortObjectName` -> `AllowObjectNameNotPadded`, `AllowIncompleteTelemetry` -> `AllowInvalidTelemetry`, `AllowNonStandardWeatherFieldWidths` -> `AllowNonStandardWeatherFieldWidth`, `AllowWindFieldsInPositionWeather` -> `AllowWindFieldsInsteadOfExtension`, `AllowMicEAltitudeAnywhere` -> `AllowMicEAltitudeNotFirst`, `AllowOutOfRangeValues` -> `AllowOutOfRangeValue`.

Why: every other flag is `Allow` + the `AprsDiagnosticCode` member name. With all 32 matching, a program that sees a warning code finds the flag that turns it into an error by name, and the vectors' tolerance check (turn off only the one tolerance a case used) is a name lookup.

## 7. fix: telemetry metadata from the station can be addressed

What: `AprsStation.TelemetryNames/TelemetryUnits/TelemetryCoefficients/TelemetryBits` always address the station's own source; the recipe keys `telemetry-names` etc. take an `addressee`, which the corpus tool can only satisfy by building the record by hand and calling `Data(...)`.

Shape: these four return a new `public sealed class AprsTelemetryMetadataBuilder : AprsBuilder` with `public AprsTelemetryMetadataBuilder Addressee(string addressee)` (default: the station's source) and covariant `ToData()` returning `AprsMessage`. An overload taking the addressee as a leading `string` would be ambiguous with `params string[]`, so a setter is the shape.

## 8. fix: `AprsMessageBuilder.WithId` -> `MessageId`

What: `public AprsMessageBuilder MessageId(string id)`. Why: the only `With`-prefixed builder method; the data property is `MessageId` and the recipe key `message_id`.

## 9. fix: one name for a Maidenhead locator

What: `AprsMicEReport.MaidenheadLocator` and `AprsStatusReport.MaidenheadLocator` -> `Locator`; `AprsStatusBuilder.Locator(string maidenheadLocator, ...)` parameter -> `locator`. Why: `AprsMaidenheadBeacon` already calls it `Locator`, as does the neutral form (`locator`) in all three types.

## 10. fix: `AprsPositionedData.RadioRangeMiles` -> `RangeMiles`

Why: the builder is `Range`, the neutral key `range_miles`, and `AprsPhg.RangeMiles` and `AprsDfBearing.RangeMiles` already use the short form.

## 11. decide: positive booleans that default to true

What: `AprsObjectReport.IsAlive`, `AprsItemReport.IsAlive` and `AprsMicEReport.IsCurrent` default to `true`; the builder says `Kill()` and the neutral form `killed` and `old_data`.

Options:
- A. Keep.
- B. `IsKilled` and `IsOldData`, default `false`, matching `Kill()`, the neutral form, and C#'s default for `bool` (a record copied from a `default`-initialised source can never silently become killed).

Recommendation: B.

## 12. fix: snowfall as `double`

What: `AprsWeather.SnowfallLast24HoursInches` `decimal?` -> `double?`; `AprsWeatherBuilder.Snowfall(decimal inches)` -> `(double inches)` (or `SnowfallInches`, item 2). Why: the only `decimal` weather value, and the only `decimal` builder input besides telemetry; the Encoding rule judges a half in binary floating point with a 1e-6 tolerance, so `decimal` gains nothing and forces a cast on every caller.

## 13. fix: voice frequency type and rounding

What: `AprsVoiceFrequency.FrequencyMHz` is `decimal`, and `Validate` refuses a frequency with more than 3 decimals (2 at 10 kHz resolution), so `Frequency(145.7251)` throws, while the vectors' Encoding rule lists a voice frequency among the values rounded to the nearest step. Shape: `public required double FrequencyMHz`, rounded once to the field's step by the encoder like every other value; rename the shorthand's `double? tone` parameter to `toneHz`. Check against a rounded encode case before changing; if the vectors have none, add one.

## 14. fix: wind direction and speed set separately

What: `AprsWeatherBuilder.Wind(double directionDegrees, double speedMph, double? gust = null)` needs both; the recipe gives `wind_direction_degrees` and `wind_speed_mph` as separate keys and the corpus tool falls back to `Observations(new AprsWeather {...})`. Shape: `WindDirection(double degrees)` and `WindSpeedMph(double mph)` (naming per item 2), with `Wind(...)` kept as the two-at-once convenience and its `gust` parameter renamed `gustMph`.

## 15. fix: internal parameter name leaks into `ArgumentException.ParamName`

What: `AprsData.ToInformationField` throws `new ArgumentException(..., nameof(writer))`, so a caller sees `ParamName == "writer"`, a local of the encoder. Use the data field (or item 1's `Field`).

## 16. fix: `AprsAddress.MaxLength` (16) internal

Why: its own doc says APRS-IS addresses are at most 9 characters, and the neutral rules say 1-9; 16 is an implementation limit for `Parse`, not something a program should code against. Make it `internal`.

## 17. fix: remove `AprsSymbolTable.Describe`

Why: identical to `AprsSymbol.Description`, which the API view and README use. Keep `FromDestination` and `FromSourceSsid`, which have no other home.

## 18. fix: `Kill()` takes a flag like its siblings

What: `AprsObjectBuilder.Kill(bool killed = true)` and `AprsItemBuilder.Kill(bool killed = true)`, as `Messaging(bool capable = true)` and `Compressed(bool compressed = true)` already do. Why: builders are mutable, so README example 5 (`repeater.Kill().Build()`) leaves the reusable `repeater` killed with no way back. Also say in `AprsBuilder`'s XML doc that builders mutate and return themselves, unlike `AprsStation`.

## 19. fix: `AprsUserDefinedData.DataText` -> `Text`

Why: `AprsUnrecognizedData` has `Raw` bytes plus `Text`; the user-defined record's `Data` bytes plus `DataText` is the same pair under another name.

## 20. decide: `third_party` in the API view

What: the API view's `third_party` key ("a packet carried inside a third-party packet") has no accessor in aprs-cs; the corpus tool leaves it out.

Options: A. leave it out (a program that unwrapped `AprsThirdPartyTraffic.Packet` already knows). B. add `public bool IsThirdParty { get; }` on `AprsPacket`, set on inner packets.

Recommendation: A; it adds surface with no use beyond the view.

## Looked at and left alone

- Fractional types on the data side (`CourseDegrees`, wind, temperature, humidity, luminosity as `double?` since 0.56.0): records are both decoder output and encoder input (`with`, `Data(...)`, the encode mode), so one `double` per quantity is right; decoded values are whole where the format is.
- `AprsTelemetryReport.Sequence` (`string`, as sent) beside `AprsStation.Telemetry(int)`: matches the neutral form and the builder rule.
- `AprsMicEReport.Device`, `AprsBulletin.Create/CreateGroup`, the `Timestamp(DateTime utc)` overloads: conveniences with no replacement.
- Nothing is public only for tests or the corpus tool: both reach internals through InternalsVisibleTo.
