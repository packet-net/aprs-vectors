# aprs-cs public API inventory (Packet.Aprs 0.56.0, main b6691d5)

Namespace `Packet.Aprs`. Data types are C# records (value equality, `with`); "req" marks a `required` init property. `?` is nullable. Source: `tests/Packet.Aprs.Tests/PublicApi.approved.txt`.

## Decoding

- `AprsPacket.Decode(string tnc2, AprsParseOptions? options = null)`: AprsPacket; decode a TNC2 line; throws AprsFormatException only for an unusable header.
- `AprsPacket.Decode(ReadOnlySpan<byte> tnc2, AprsParseOptions? options = null)`: AprsPacket; same, from bytes.
- `AprsPacket.Decode(AprsAddress source, AprsAddress destination, IEnumerable<AprsPathEntry> path, ReadOnlySpan<byte> information, AprsParseOptions? options = null)`: AprsPacket; decode with a header parsed elsewhere.
- `AprsPacket.DecodeAx25(ReadOnlySpan<byte> frame, AprsParseOptions? options = null)`: AprsPacket; decode a UI frame without flags/FCS.
- `AprsPacket.TryDecode(string|ReadOnlySpan<byte> tnc2, out AprsPacket? packet, AprsParseOptions? options = null)`: bool; false instead of throwing.
- `AprsPacket.TryDecodeAx25(ReadOnlySpan<byte> frame, out AprsPacket? packet, AprsParseOptions? options = null)`: bool.
- `AprsPacket` (sealed class, value equality): `Source` AprsAddress, `Destination` AprsAddress, `Path` IReadOnlyList<AprsPathEntry>, `QConstruct` AprsQConstruct?, `Information` ReadOnlyMemory<byte> (as received), `Data` AprsData (never null), `Diagnostics` IReadOnlyList<AprsDiagnostic>, `HasErrors` bool, `HasWarnings` bool.
- `AprsParseOptions` (sealed record class): 32 bool init flags, one per tolerable code; `Lenient` (default when options is null), `Strict`; `new()` is all false.
- `AprsParseOptions` flags: AllowBraceInMessageText, AllowCompressionTypeReservedBits, AllowDaoWithAmbiguity, AllowEmptyDestination, AllowEmptyPathEntry, AllowFreeTextCapabilities, AllowIncompleteTelemetry (invalid-telemetry), AllowIncompleteWeather, AllowInvalidAddresseeCharacters, AllowInvalidAx25AddressCharacters, AllowInvalidTimestamp, AllowKenwoodFfPadding, AllowLetterGroupBulletin, AllowLowercaseHemisphere, AllowMalformedTimestamp, AllowMessageIdOnAck, AllowMicEAltitudeAnywhere (mic-e-altitude-not-first), AllowMissingSpaceAfterLocator, AllowMultipleUsedMarkers, AllowNonStandardWeatherFieldWidths, AllowNonUtf8Text, AllowNulPaddedAddress, AllowObjectWithoutTimestamp, AllowOutOfRangeValues, AllowPositionNotAtStart, AllowShortObjectName (object-name-not-padded), AllowUnpaddedAddressee, AllowWeatherComment, AllowWindExtensionAfterCompressed, AllowWindFieldsInPositionWeather (wind-fields-instead-of-extension), RecognizeDataExtensionInComment (data-extension-in-comment), StripTrailingLineBreaks (trailing-line-break).
- `AprsDiagnostic` (record struct): `Code` AprsDiagnosticCode, `Severity` AprsDiagnosticSeverity, `Message` string, `Offset` int?; public ctor.
- `AprsDiagnosticCode` (enum, explicit grouped values 1-161): one member per vectors code, PascalCase of the kebab id.
- `AprsDiagnosticSeverity` (enum): Info, Warning, Error.
- `AprsFormatException : FormatException`: `Diagnostics` IReadOnlyList<AprsDiagnostic>; three standard ctors.
- `AprsUnrecognizedReason` (enum): Empty, NotAprs, ReservedDataType, Malformed.

## Data model

Base types:
- `AprsData` (abstract record): `DataTypeIdentifier` char; `ToInformationField()` byte[] (encode, see Encoding).
- `AprsPositionedData : AprsData` (abstract): position, Mic-E, object, item.
- `AprsMessage : AprsData` (abstract): `Addressee` string req, `MessageId` string?; DTI `:`.

`AprsPositionedData` fields:
- `Position` AprsPosition req; degrees, DAO applied, ambiguous = box centre.
- `Symbol` AprsSymbol req.
- `IsCompressed` bool; compressed format.
- `CompressionType` AprsCompressionType?; the type byte.
- `CourseDegrees` double?; degrees (decoded whole; 0.56.0 widened from int).
- `SpeedKnots` double?; knots.
- `AltitudeFeet` double?; feet.
- `Phg` AprsPhg?; PHG/PHGR codes.
- `RadioRangeMiles` double?; RNG or compressed range, miles.
- `DfSignalStrength` AprsDfSignalStrength?; DFS codes.
- `AreaObject` AprsAreaObject?; area extension.
- `DfBearing` AprsDfBearing?; `/BRG/NRQ`.
- `Storm` AprsStorm?; storm data.
- `Frequency` AprsVoiceFrequency?; APRS 1.2 voice frequency.
- `Dao` AprsDao?; `!DAO!` datum and precision.
- `Telemetry` AprsCommentTelemetry?; base-91 comment telemetry.
- `Weather` AprsWeather?; weather on a position.
- `SignpostText` string?; signpost braces.
- `Comment` string (non-null, "" default); free text left.

Report types:
- `AprsPositionReport : AprsPositionedData`: `Timestamp` AprsTimestamp?, `MessagingCapable` bool.
- `AprsMicEReport : AprsPositionedData`: `Message` AprsMicEMessage (default OffDuty), `IsCurrent` bool (default true; neutral `old_data` inverted), `TypeCode` char?, `DeviceSuffix` string, `MaidenheadLocator` string?, `DestinationSsid` int, `LegacyTelemetry` IReadOnlyList<int>?, `MessagingCapable` bool? (derived from TypeCode), `Device` AprsDevice? (derived lookup).
- `AprsObjectReport : AprsPositionedData`: `Name` string req, `IsAlive` bool (default true; neutral `killed` inverted), `Timestamp` AprsTimestamp?.
- `AprsItemReport : AprsPositionedData`: `Name` string req, `IsAlive` bool (default true).
- `AprsTextMessage : AprsMessage`: `Text` string req, `ReplyAck` string? ("" = supports reply-acks), `RequestsAck` bool (derived).
- `AprsMessageAck : AprsMessage`: `AcknowledgedId` string req, `ReplyAck` string?.
- `AprsMessageReject : AprsMessage`: `RejectedId` string req, `ReplyAck` string?.
- `AprsBulletin : AprsMessage`: `Text` string req, `Id` char (derived), `GroupName` string? (derived), `Kind` AprsBulletinKind (derived); `Create(char id, string text)`, `CreateGroup(char id, string group, string text)`.
- `AprsBulletinKind` (enum): General, Announcement, Group.
- `AprsNwsBulletin : AprsMessage`: `Text` string req, `Severity` string (derived from addressee).
- `AprsDirectedQuery : AprsMessage`: `QueryType` string req, `Target` string?; static `KnownTypes` IReadOnlyList<string>.
- `AprsTelemetryParameterNames : AprsMessage`: `Names` IReadOnlyList<string> req.
- `AprsTelemetryUnits : AprsMessage`: `Units` IReadOnlyList<string> req.
- `AprsTelemetryCoefficients : AprsMessage`: `Coefficients` IReadOnlyList<double> req; `Scale(int channel, decimal raw)` double.
- `AprsTelemetryBitSense : AprsMessage`: `Bits` byte req (bit 0 = B1), `ProjectTitle` string.
- `AprsStatusReport : AprsData`: public parameterless ctor; `Text` string, `Timestamp` AprsTimestamp?, `MaidenheadLocator` string?, `Symbol` AprsSymbol?, `BeamHeading` AprsBeamHeading?.
- `AprsTelemetryReport : AprsData`: `Sequence` string req (as sent), `Analog` IReadOnlyList<decimal?> req (null = empty channel), `Digital` byte?, `Comment` string.
- `AprsWeatherReport : AprsData`: positionless; `Timestamp` AprsTimestamp req, `Weather` AprsWeather req, `Comment` string.
- `AprsRawWeatherReport : AprsData`: `Format` AprsRawWeatherFormat req, `Data` string req.
- `AprsRawWeatherFormat` (enum): PeetBrosHash, PeetBrosStar, UltimeterPacket, UltimeterLogging.
- `AprsNmeaReport : AprsData`: `Sentence` string req (no `$`), `SentenceType` string (derived), `HasChecksum` bool (derived), `Position` AprsPosition?, `FixValid` bool?, `CourseDegrees` double?, `SpeedKnots` double?, `AltitudeMetres` double?, `Time` TimeOnly?, `TimeText` string?, `WaypointName` string?, `Comment` string.
- `AprsMaidenheadBeacon : AprsData`: `Locator` string req, `Comment` string.
- `AprsGeneralQuery : AprsData`: `QueryType` string req, `Footprint` AprsQueryFootprint?.
- `AprsQueryFootprint` (record struct): `Latitude` decimal, `Longitude` decimal, `RadiusMiles` int.
- `AprsStationCapabilities : AprsData`: `Capabilities` IReadOnlyList<AprsCapability> req.
- `AprsCapability` (record struct): `Token` string, `Value` string?.
- `AprsThirdPartyTraffic : AprsData`: `Packet` AprsPacket req, `CameFromInternet` bool (derived).
- `AprsUserDefinedData : AprsData`: `UserId` char req, `PacketType` char req, `Data` IReadOnlyList<byte> req, `DataText` string (Latin-1 view).
- `AprsTestData : AprsData`: `Data` string req.
- `AprsAgreloDfReport : AprsData`: `BearingDegrees` int req, `Quality` int req.
- `AprsUnrecognizedData : AprsData`: `Reason` AprsUnrecognizedReason req, `Raw` IReadOnlyList<byte> req, `Text` string.

Value types:
- `AprsPosition` (record struct): `Latitude` double, `Longitude` double, `Ambiguity` int (0-4); `AmbiguityRadiusNauticalMiles` double; static `Null` (0,0).
- `AprsSymbol` (record struct): `Table` char, `Code` char; `Overlay` char?, `Description` string?, `IsPrimaryTable`, `IsAlternateTable`, `IsValid`, `IsWeatherStation` bool; `WithOverlay(char)`, `Parse(string)`; about 160 named statics (`Car`, `Repeater`, ...).
- `AprsCompressionType` (record struct): `Fix` AprsGpsFix, `Source` AprsNmeaSource, `Origin` AprsCompressionOrigin; static `Default`.
- `AprsGpsFix` (enum): Old, Current. `AprsNmeaSource` (enum): Other, Gll, Gga, Rmc. `AprsCompressionOrigin` (enum): Compressed, TncBeaconText, Software, Reserved3, Kpc3, Pico, OtherTracker, DigipeaterConversion.
- `AprsPhg` (record struct): `PowerCode`, `HeightCode`, `GainCode`, `DirectivityCode` int, `BeaconsPerHour` int?; derived `PowerWatts` int, `HeightFeet` double, `GainDbi` int, `DirectivityDegrees` int? (null omni), `RangeMiles` double.
- `AprsDfSignalStrength` (record struct): `StrengthCode`, `HeightCode`, `GainCode`, `DirectivityCode` int; derived `HeightFeet` double, `DirectivityDegrees` int?.
- `AprsDfBearing` (record struct): `BearingDegrees` int, `Number` int, `Range` int, `Quality` int (codes); derived `RangeMiles` double, `BeamwidthDegrees` double?.
- `AprsAreaObject` (record struct): `Shape` AprsAreaShape, `Color` AprsAreaColor, `LatitudeOffsetCode` int, `LongitudeOffsetCode` int, `CorridorWidthMiles` int?; derived `LatitudeOffsetDegrees`, `LongitudeOffsetDegrees` double.
- `AprsAreaShape` (enum, 10 members), `AprsAreaColor` (enum, 16 members incl. `*Low`).
- `AprsStorm` (record class): `Type` AprsStormType req, `SustainedWindKnots` int?, `GustKnots` int?, `CentralPressureMillibars` int?, `HurricaneWindRadiusNauticalMiles` int?, `TropicalStormWindRadiusNauticalMiles` int?, `WholeGaleRadiusNauticalMiles` int?.
- `AprsStormType` (enum): TropicalStorm, Hurricane, TropicalDepression.
- `AprsDao` (record struct): `Datum` char, `Precision` AprsDaoPrecision; static `Wgs84Base91`. `AprsDaoPrecision` (enum): None, Thousandths, Base91.
- `AprsCommentTelemetry` (record class): `Sequence` int req, `Analog` IReadOnlyList<int> req, `Digital` byte?; const `MaxValue` = 8280.
- `AprsVoiceFrequency` (record class): `FrequencyMHz` decimal req, `TenKilohertzResolution` bool, `ToneType` AprsToneType?, `ToneValue` int? (whole Hz or DCS code), `Narrow` bool, `OffsetKHz` int?, `Range` int?, `RangeInKilometres` bool.
- `AprsToneType` (enum): Tone, Ctcss, Dcs, ToneBurst, Off.
- `AprsWeather` (record class, public ctor): `WindDirectionDegrees` double?, `WindSpeedMph` double?, `WindGustMph` double?, `TemperatureFahrenheit` double?, `RainLastHourInches` double?, `RainLast24HoursInches` double?, `RainSinceMidnightInches` double?, `RainRawCounter` int?, `HumidityPercent` double?, `PressureMillibars` double?, `LuminosityWattsPerSquareMetre` double?, `SnowfallLast24HoursInches` decimal?, `SoftwareType` char?, `UnitType` string?, `AdditionalFields` IReadOnlyList<AprsWeatherField>.
- `AprsWeatherField` (record struct): `Letter` char, `Value` string.
- `AprsBeamHeading` (record struct): `HeadingCode` char, `PowerCode` char; derived `HeadingDegrees` int, `ErpWatts` int.
- `AprsMicEMessage` (enum): Emergency, OffDuty, EnRoute, InService, Returning, Committed, Special, Priority, Custom0-Custom6, Unknown.
- `AprsTimestamp` (record struct, private ctor): `Format` AprsTimestampFormat, `Month`, `Day`, `Hour`, `Minute`, `Second` int (0 when absent), `IsValid` bool, `IsPermanentObjectMarker` bool; `Resolve(DateTime reference)` DateTime?; `DayHoursMinutes(int day, int hour, int minute, bool utc = true)`, `HoursMinutesSeconds(int, int, int)`, `MonthDayHoursMinutes(int, int, int, int)`, `FromDateTime(DateTime utc, AprsTimestampFormat format = DayHoursMinutesUtc)`.
- `AprsTimestampFormat` (enum): DayHoursMinutesUtc, DayHoursMinutesLocal, HoursMinutesSecondsUtc, MonthDayHoursMinutesUtc.

## Encoding

- `AprsData.ToInformationField()`: byte[]; encode the data alone; refusal = ArgumentException (message text, ParamName).
- `AprsPacket.Create(AprsAddress source, AprsAddress destination, AprsData data, IEnumerable<AprsPathEntry>? path = null)`: AprsPacket; throws ArgumentException for Mic-E ("use CreateMicE").
- `AprsPacket.Create(string source, string destination, AprsData data, string path = "")`: AprsPacket; text header; FormatException for a bad address.
- `AprsPacket.CreateMicE(AprsAddress source, AprsMicEReport report, IEnumerable<AprsPathEntry>? path = null)`: AprsPacket; computes the Mic-E destination.
- `AprsPacket.ToTnc2()`: byte[]; header plus information field as received.
- `AprsPacket.ToString()`: string; TNC2 text.
- `AprsPacket.ToAx25Frame()`: byte[]; UI frame without flags/FCS; ArgumentException when an address is not AX.25.
- Refusals: ArgumentException / ArgumentOutOfRangeException from the encoder (about 150 sites, message text only), InvalidOperationException from builders for a missing position/symbol, FormatException from address parsing. No reason code.

## Builders

Entry: `Aprs.From(string|AprsAddress source)` = `AprsStation.From(...)`: AprsStation. `Aprs.DefaultDestination` const "APZ001".

`AprsStation` (immutable):
- `Source` AprsAddress, `Destination` AprsAddress, `Path` IReadOnlyList<AprsPathEntry>.
- `To(string destination)`: AprsStation; recipe `station.destination`.
- `Via(params string[] path)`: AprsStation; recipe `station.path`.
- `Position(double latitude, double longitude)` / `Position(AprsPosition)`: AprsPositionBuilder; recipe `position`.
- `Object(string name)`: AprsObjectBuilder; recipe `object`.
- `Item(string name)`: AprsItemBuilder; recipe `item`.
- `MicE(double latitude, double longitude)`: AprsMicEBuilder; recipe `mic-e`.
- `Weather()`: AprsWeatherBuilder; recipe `weather`.
- `Message(string addressee, string text)`: AprsMessageBuilder; recipe `message`.
- `Ack(string addressee, string messageId)` / `Reject(...)`: AprsAckBuilder; recipe `ack`, `reject`.
- `Bulletin(char id, string text)` / `GroupBulletin(char id, string group, string text)`: AprsDataBuilder; recipe `bulletin`.
- `Status(string text = "")`: AprsStatusBuilder; recipe `status`.
- `Telemetry(int sequence)`: AprsTelemetryBuilder; recipe `telemetry`; 0-999 else ArgumentOutOfRangeException at once.
- `TelemetryNames(params string[])`, `TelemetryUnits(params string[])`, `TelemetryCoefficients(params double[])`, `TelemetryBits(byte bits, string projectTitle = "")`: AprsDataBuilder; addressed to Source only (recipe `addressee` needs `Data(...)`).
- `Data(AprsData data)`: AprsDataBuilder; any hand-built record (Mic-E handled).

`AprsBuilder` (abstract): `Station` AprsStation; `ToData()` AprsData (covariant per builder); `Build()` AprsPacket.

`AprsPositionedBuilder<TSelf>` (all mutate and return this):
- `At(double latitude, double longitude)` / `At(AprsPosition)`; degrees.
- `Symbol(AprsSymbol)`; recipe `symbol`.
- `Course(double degrees)`; recipe `course_degrees`; 0 = unknown, rounded once.
- `Speed(double knots)`; recipe `speed_knots`.
- `SpeedKmh(double kilometresPerHour)`; recipe `speed_kmh`.
- `Altitude(double feet)`; recipe `altitude_feet`.
- `AltitudeMetres(double metres)`; recipe `altitude_m`.
- `Comment(string text)`; recipe `comment`.
- `Phg(AprsPhg)`; recipe `phg` (codes).
- `Range(double miles)`; recipe `range_miles`.
- `Frequency(double mhz, double? tone = null, int? offsetKHz = null)`; tone truncated to whole Hz, type Tone.
- `Frequency(AprsVoiceFrequency)`; recipe `frequency`.
- `Compressed(bool compressed = true)`; recipe `compressed`.
- `Ambiguity(int digits)`; recipe `ambiguity`.
- `Dao(AprsDao? dao = null)`; recipe `dao` (default W base-91).
- `Telemetry(int sequence, params int[] analog)`, `Telemetry(int sequence, int[] analog, byte digital)`, `Telemetry(AprsCommentTelemetry)`; recipe `telemetry`.
- `ToData()`: AprsPositionedData.

Concrete:
- `AprsPositionBuilder`: `Messaging(bool capable = true)`, `Timestamp(AprsTimestamp)`, `Timestamp(DateTime utc)`; ToData AprsPositionReport.
- `AprsObjectBuilder`: `Kill()`, `Permanent()`, `Timestamp(AprsTimestamp)`, `Timestamp(DateTime utc)`; no timestamp = now; ToData AprsObjectReport.
- `AprsItemBuilder`: `Kill()`; ToData AprsItemReport.
- `AprsMicEBuilder`: `Message(AprsMicEMessage)`, `Messaging(bool capable = true)` (sets type code); `Build()` computes destination; ToData AprsMicEReport.
- `AprsWeatherBuilder`: `At(double, double)` / `At(AprsPosition)`, `Symbol(AprsSymbol)`, `Timestamp(AprsTimestamp|DateTime)`, `Messaging(bool = true)`, `Compressed(bool = true)`, `Dao(AprsDao? = null)`, `Wind(double directionDegrees, double speedMph, double? gust = null)`, `Gust(double mph)`, `Temperature(double fahrenheit)`, `TemperatureCelsius(double celsius)`, `Humidity(double percent)`, `Pressure(double millibars)`, `Rain(double? lastHour, double? last24Hours, double? sinceMidnight)` (inches), `RainMillimetres(...)`, `Luminosity(double wattsPerSquareMetre)`, `Snowfall(decimal inches)`, `Observations(AprsWeather)`; ToData AprsData (position report or weather report).
- `AprsMessageBuilder`: `WithId(string id)` (recipe `message_id`), `ReplyAck(string theirId = "")` (recipe `reply_ack`); ToData AprsTextMessage.
- `AprsAckBuilder`: `ReplyAck(string theirAck)`; ToData AprsMessage (ack or reject).
- `AprsStatusBuilder`: `Timestamp(AprsTimestamp|DateTime)`, `Locator(string maidenheadLocator, AprsSymbol symbol)` (recipe `locator` + `symbol` together), `Beam(AprsBeamHeading)`; ToData AprsStatusReport.
- `AprsTelemetryBuilder`: `Analog(params decimal[])`, `Analog(params decimal?[])`, `Digital(byte bits)`, `Digital(string bits)` (recipe `bits`), `Comment(string)`; ToData AprsTelemetryReport.
- `AprsDataBuilder`: ToData AprsData; Build handles Mic-E via CreateMicE.

## The API view

- source, destination: `AprsPacket.Source.Value`, `AprsPacket.Destination.Value`.
- path: `AprsPacket.Path[i].ToString()` (`*` when `HasBeenRepeated`).
- q_construct: `AprsPacket.QConstruct` (`Construct` string, `Station` AprsAddress?, `PathIndex` int, `IsFromRf` bool).
- third_party: not offered (no back-reference from an inner packet).
- has_errors, has_warnings: `AprsPacket.HasErrors`, `HasWarnings`.
- tnc2: `AprsPacket.ToTnc2()`.
- ax25: `AprsPacket.ToAx25Frame()`, ArgumentException = refused.
- device: `AprsDeviceIdentification.Identify(AprsPacket)` -> `AprsDevice` (`Vendor`, `Model`, `DeviceClass`, `OperatingSystem` string?, `Features` IReadOnlyList<string>, `SupportsMessaging` bool).
- symbol: `AprsSymbol.Description` (also `AprsSymbolTable.Describe`).
- phg: `AprsPhg.PowerWatts`, `HeightFeet`, `GainDbi`, `DirectivityDegrees`.
- inner: `AprsThirdPartyTraffic.Packet`.
- `AprsAddress` (record struct): `Value`, `Base`, `Ssid` string, `NumericSsid` int?, `IsAx25` bool, const `MaxLength` = 16; `IsSameStation`, `TryGetCallsign(out Callsign)`, `FromAx25(string callsign, int ssid = 0)`, `FromCallsign(Callsign)`, `Parse`, `TryParse`.
- `AprsPathEntry` (record struct): `Address` AprsAddress, `HasBeenRepeated` bool; `ToString()`, static `FormatList(IEnumerable<AprsPathEntry>)`, `ParseList(string)`.
- `AprsDeviceIdentification`: `DatabaseVersion` string, `FromDestination(AprsAddress)`, `FromTocall(string)`, `FromMicE(char? typeCode, string suffix)`, `Identify(AprsPacket)`; all AprsDevice?.

## Other

- `AprsSymbolTable`: `Describe(AprsSymbol)` string?, `FromDestination(AprsAddress)` AprsSymbol? (GPSxyz etc.), `FromSourceSsid(int)` AprsSymbol?.
- `Aprs.DefaultDestination` const string "APZ001".
- `AprsCommentTelemetry.MaxValue` const int 8280.
- No public version constant beyond the assembly version; `AprsDeviceIdentification.DatabaseVersion` for the embedded database.
- Dependency in the public surface: `Packet.Core.Callsign` (AprsAddress conversions).
- Internals reach the test project and the `aprs-corpus` tool through InternalsVisibleTo, not public API.
