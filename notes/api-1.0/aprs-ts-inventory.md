# aprs-ts public API inventory (@packet-net/pdn-aprs 0.3.0, main d33474d)

Everything below is exported from the package root (`src/index.ts`); there are no subpath exports. TypeScript has one number type, so "number" fields may hold fractions wherever the wire does (rain hundredths, pressure tenths, compressed cs values); optional fields are `?:` (absent means undefined), except `TelemetryReport.analog`, which uses `null` for an empty channel.

## Decoding

- `decodeTnc2(line: string | Uint8Array, options = ParseOptions.lenient): AprsPacket`: TNC2 / APRS-IS line; string taken as UTF-8; throws `AprsHeaderError`.
- `decodeAx25(frame: Uint8Array, options?): AprsPacket`: AX.25 UI frame without flags or FCS; throws `AprsHeaderError`.
- `decodeKiss(frame: Uint8Array, options?): AprsPacket`: KISS frame; throws `RangeError` if not a data frame, then as `decodeAx25`.
- `unwrapKiss(frame: Uint8Array): Uint8Array`: strip FEND, un-escape, drop command byte; throws `RangeError`.
- `decodeInformation(info: Uint8Array, destination: string, options: ParseOptions): DecodedInformation`: information field only; options required.
- `DecodedInformation { data: AprsData; diagnostics: Diagnostic[] }`: mutable fields.
- `AprsHeaderError extends Error { readonly diagnostics: readonly Diagnostic[] }`: header unusable; last diagnostic is the error.
- `Diagnostic { severity: Severity; code: DiagnosticCode; message: string }`: readonly.
- `Severity = 'info' | 'warning' | 'error'`.
- `DiagnosticCode`: string union, one per vectors codes.json code.
- `TolerableCode`: subset a lenient decoder may tolerate.
- `ParseOptions`: class, private constructor.
- `ParseOptions.lenient`, `ParseOptions.strict`: static presets.
- `ParseOptions.tolerating(codes: Iterable<TolerableCode>)`: exact set; `RangeError` on a non-tolerable code.
- `.with(code)`, `.without(code)`: copy plus or minus one code.
- `.tolerates(code: DiagnosticCode): boolean`, `.toleratedCodes: readonly TolerableCode[]`.
- `diagnostic(severity, code, detail?): Diagnostic`: builds a diagnostic with the standard text.
- `formatDiagnostic(d): string`: `severity:code`.
- `DIAGNOSTIC_MEANINGS: Record<DiagnosticCode, string>`, `DIAGNOSTIC_CODES`, `TOLERABLE_CODES`, `isTolerable(code)`: code tables.

## Data model

- `AprsPacket`: `source: string`, `destination: string`, `path: readonly PathEntry[]`, `information: Uint8Array` (as received), `data: AprsData`, `diagnostics: readonly Diagnostic[]`, `qConstruct?: QConstruct`, `device?: DeviceInfo`.
- `AprsData`: union on `type`; `AprsDataType = AprsData['type']`; `PositionedData = PositionReport | MicEReport | ObjectReport | ItemReport`.
- `PositionedFields`: `latitude`, `longitude` (degrees, N/E positive, DAO applied, ambiguity centre), `ambiguity?` (1-4), `symbol: AprsSymbol`, `compressed?: boolean`, `compression?: CompressionType`, `courseDegrees?`, `speedKnots?`, `altitudeFeet?`, `phg?: Phg`, `rangeMiles?`, `dfs?: Dfs`, `area?: AreaObject`, `dfBearing?: DfBearing`, `storm?: Storm`, `dao?: Dao`, `telemetry?: CommentTelemetry`, `frequency?: VoiceFrequency`, `weather?: Weather`, `signpost?: string`, `comment?: string`.
- `PositionReport` (`position`): positioned fields + `timestamp?: AprsTimestamp`, `messaging?: boolean`.
- `MicEReport` (`mic-e`): positioned fields + `micEMessage: MicEMessage`, `oldData?`, `typeCode?` (one char), `deviceSuffix?`, `locator?`, `legacyTelemetry?: number[]`, `destinationSsid?: number`.
- `ObjectReport` (`object`): positioned fields + `name`, `killed?`, `timestamp?`.
- `ItemReport` (`item`): positioned fields + `name`, `killed?`.
- `Message` (`message`): `addressee`, `text`, `messageId?`, `replyAck?` (empty string = capable, nothing to ack).
- `Ack` (`ack`): `addressee`, `ackedId`, `replyAck?`.
- `Reject` (`reject`): `addressee`, `rejectedId`, `replyAck?`.
- `Bulletin` (`bulletin`), `NwsBulletin` (`nws-bulletin`): `addressee`, `text`, `messageId?`.
- `TelemetryNames` (`telemetry-names`): `addressee`, `names: string[]`, `messageId?`.
- `TelemetryUnits` (`telemetry-units`): `addressee`, `units: string[]`, `messageId?`.
- `TelemetryCoefficients` (`telemetry-coefficients`): `addressee`, `coefficients: number[]`, `coefficientsText?: string[]` (as sent), `messageId?`.
- `TelemetryBits` (`telemetry-bits`): `addressee`, `bits` (8 chars, B1 first), `project?`, `messageId?`.
- `DirectedQuery` (`directed-query`): `addressee`, `queryType`, `target?`.
- `StatusReport` (`status`): `timestamp?`, `locator?`, `symbol?`, `beam?: { headingCode, powerCode }`, `text?`.
- `TelemetryReport` (`telemetry`): `sequence: string` (as sent), `analog: (number | null)[]`, `analogText?: (string | null)[]`, `bits?`, `comment?`.
- `WeatherReport` (`weather`): `timestamp?`, `weather: Weather`, `comment?`.
- `RawWeather` (`raw-weather`): `format: RawWeatherFormat`, `data?`.
- `NmeaSentence` (`nmea`): `sentence`, `hasChecksum?`, `latitude?`, `longitude?`, `fix?: 'valid' | 'invalid'`, `courseDegrees?`, `speedKnots?`, `altitudeM?`, `time?` (text), `waypoint?`, `comment?`.
- `MaidenheadBeacon` (`maidenhead-beacon`): `locator`, `comment?`.
- `Query` (`query`): `queryType`, `footprint?: QueryFootprint`.
- `QueryFootprint`: `latitude`, `longitude`, `radiusMiles`, `latitudeText?`, `longitudeText?` (as sent).
- `Capabilities` (`capabilities`): `capabilities: Capability[]`; `Capability = [token] | [token, value]`.
- `ThirdParty` (`third-party`): `packet: AprsPacket`.
- `UserDefined` (`user-defined`): `userId`, `packetType`, `data?` (one char per byte).
- `TestData` (`test`): `data?`.
- `AgreloDf` (`agrelo-df`): `bearingDegrees`, `quality`.
- `Unrecognized` (`unrecognized`): `reason: UnrecognizedReason` (`empty | not-aprs | reserved-data-type | malformed`).
- `AprsSymbol { table: string; code: string }`.
- `AprsTimestamp`: union on `kind`: `dhm-zulu` / `dhm-local` {day, hour, minute}, `hms` {hour, minute, second}, `mdhm` {month, day, hour, minute}.
- `CompressionType { fix: CompressionFix; source: CompressionSource; origin: CompressionOrigin }`: kebab-case string unions.
- `Phg { power, height, gain, directivity, beaconsPerHour? }`: codes as sent, not derived values.
- `Dfs { strength, height, gain, directivity }`: codes.
- `DfBearing { bearingDegrees, number, range, quality }`.
- `AreaObject { shape: AreaShape; color: AreaColor; latOffset; lonOffset; corridorWidthMiles? }`.
- `Storm { type: StormType; sustainedWindKnots?; gustKnots?; centralPressureMbar?; hurricaneRadiusNm?; tropicalStormRadiusNm?; wholeGaleRadiusNm? }`.
- `Dao { datum: string; precision: DaoPrecision }`; `DaoPrecision = 'none' | 'thousandths' | 'base91'`.
- `CommentTelemetry { sequence: number; analog: number[]; digital?: number }` (0-255).
- `VoiceFrequency { mhz; tone?: ToneType; toneValue?; offsetKhz?; range?; rangeKm?: boolean; narrow?; tenKhzResolution? }`: `range` in miles unless `rangeKm`.
- `Weather { windDirectionDegrees?; windSpeedMph?; windGustMph?; temperatureF?; rain1hIn?; rain24hIn?; rainMidnightIn?; rainRaw?; humidityPercent?; pressureMbar?; luminosityWM2?; snow24hIn?; software?; unit?; extra?: ExtraWeatherField[] }`.
- `ExtraWeatherField { letter; value }`: undefined weather letter, value as sent.
- `MicEMessage`: kebab-case union (`off-duty` ... `emergency`, `custom0-6`, `unknown`).
- `PathEntry { address: string; used: boolean }`.
- `QConstruct { construct: string; station?: string }`.
- `DeviceInfo { vendor?; model?; class?; os?; features?: string[] }`.

## Encoding

- `encodeInformation(data: AprsData): EncodedInformation`: information field; throws `AprsEncodeError`.
- `EncodedInformation { info: Uint8Array; destination?: string }`: `destination` for Mic-E only; mutable fields.
- `PacketToEncode { source; destination? (default APZ001, ignored for Mic-E); path?: (string | PathEntry)[]; data }`.
- `encodeTnc2(p): string`: refuses if the information field is not UTF-8.
- `encodeTnc2Bytes(p): Uint8Array`: checks addresses against APRS-IS rules.
- `encodeAx25(p): Uint8Array`: UI frame, no flags or FCS; refuses non-AX.25 addresses, over 8 digipeaters.
- `wrapKiss(frame, port = 0): Uint8Array`: KISS data frame.
- `AprsEncodeError extends Error`: refusal; reason in `message` only, no code.

## Builders

- `Aprs.from(source): PacketBuilder`: entry point (object with one method).
- `DEFAULT_DESTINATION = 'APZ001'`.
- `PacketBuilder` (public constructor taking an unexported `Header`):
  - `.to(destination)`, `.via(...path: string[])`: header.
  - `.position(lat, lon): PositionBuilder`.
  - `.weather(lat, lon, weather: WeatherInput): PositionBuilder`: position report, symbol `/_`.
  - `.weatherReport(weather: WeatherInput, at: Date = now): DataBuilder`: positionless, `mdhm`.
  - `.object(name, lat, lon): ObjectBuilder`, `.item(name, lat, lon): ItemBuilder`, `.micE(lat, lon): MicEBuilder`.
  - `.message(addressee, text): MessageBuilder`.
  - `.ack(addressee, id)`, `.reject(addressee, id)`: `DataBuilder`.
  - `.bulletin(id, text, group = '')`: `DataBuilder`.
  - `.status(text?): StatusBuilder`.
  - `.telemetry(sequence: number | string, analog: (number | null)[], bits: string): TelemetryBuilder`: number 0-999 else refused at build.
  - `.telemetryNames(addressee, names)`, `.telemetryUnits(addressee, units)`, `.telemetryCoefficients(addressee, coefficients: number[])`, `.telemetryBits(addressee, bits, project?)`: `DataBuilder`.
  - `.data(data: AprsData): DataBuilder`: anything by hand.
- `DataBuilder`: `.build(): BuiltPacket`, `.toTnc2(): string`.
- Positioned options (Position, Object, Item, MicE builders):
  - `.symbol(AprsSymbol | string)`.
  - `.course(degrees)`: 0 unknown, 360 north.
  - `.speed(knots)`, `.speedKmh(kmh)`.
  - `.altitude(feet)`, `.altitudeMetres(metres)`: Mic-E puts metres in its altitude bytes.
  - `.comment(text)`.
  - `.frequency(mhz, details?: Omit<VoiceFrequency, 'mhz'>)`.
  - `.commentTelemetry(sequence, analog: number[], digital?)`.
  - `.dao(datum = 'W', precision = 'base91')`.
  - `.ambiguity(digits)`.
- Report options (Position, Object, Item builders only):
  - `.phg(power, height, gain, directivity = 0, beaconsPerHour?)`: codes.
  - `.range(miles)`.
  - `.weather(weather: WeatherInput)`.
  - `.compressed(compression?: CompressionType)`.
- `PositionBuilder`: `.timestamp(at: Date | AprsTimestamp, kind?: 'dhm-zulu' | 'hms')`, `.messaging(capable = true)`, `.build()`, `.toTnc2()`.
- `ObjectBuilder`: `.timestamp(...)` (default: clock at `object()`), `.killed(killed = true)`, `.build()`, `.toTnc2()`.
- `ItemBuilder`: `.killed(killed = true)`, `.build()`, `.toTnc2()`.
- `MicEBuilder`: `.micEMessage(MicEMessage)` (default `off-duty`), `.messaging(capable = true)` (type code `` ` `` or `'`), `.locator(text)`, `.old(old = true)`, `.build()`, `.toTnc2()`.
- `MessageBuilder`: `.id(string | number)`, `.replyAck(id = '')`, `.build()`, `.toTnc2()`.
- `StatusBuilder`: `.timestamp(Date | AprsTimestamp)` (dhm-zulu), `.locator(locator, symbol)`, `.beam(headingCode, powerCode)`, `.build()`, `.toTnc2()`.
- `TelemetryBuilder`: `.comment(text)`, `.build()`, `.toTnc2()`.
- `WeatherInput extends Weather { temperatureC?; rain1hMm?; rain24hMm?; rainMidnightMm? }`: converted to F / inches; a value in both units throws `AprsEncodeError` when `.weather()` / `.weatherReport()` is called.
- `BuiltPacket { source; destination; path: readonly string[]; data: AprsData; information: Uint8Array; toTnc2(); toTnc2Bytes(); toAx25(); toKiss(port?) }`: frozen; header addresses checked only by the `to*` writers.
- `timestampOf(date: Date, kind = 'dhm-zulu' | 'hms'): AprsTimestamp`: UTC, cut not rounded.

## The API view

- `source`, `destination`, `path`: `AprsPacket` fields; path text via `formatPath`.
- `q_construct`: `AprsPacket.qConstruct` (from `findQConstruct`).
- `third_party`: not offered (no marker on an inner packet).
- `has_errors`, `has_warnings`: not offered (only the `diagnostics` array).
- `tnc2`: no single writer; `formatTnc2Header(source, destination, path)` + `information`.
- `ax25`: not offered for a received packet (`encodeAx25` re-encodes the data).
- `device`: `AprsPacket.device`.
- `symbol`: `describeSymbol(symbol)`.
- `phg`: not offered (codes only, no watts / feet / dB / degrees derivation).
- `inner`: `ThirdParty.packet`.
- `formatPath(path: PathEntry[]): string`: last used entry gets `*`.
- `formatTnc2Header(source, destination, path): string`: without the colon.
- `findQConstruct(path): QConstruct | undefined`.
- `isAprsIsAddress(text): boolean`: 1-9 of `[A-Za-z0-9-]`.
- `identifyTocall(destination): DeviceInfo | undefined`: case-sensitive, `n` is a digit.
- `identifyMicE(typeCode?, suffix?): DeviceInfo | undefined`.
- `DEVICEID_SOURCE { repository, commit, date }`, `DEVICE_CLASSES: { class, shown, description }[]`.

## Other

- `Symbols: Record<SymbolName, AprsSymbol>`; `SymbolName`: camelCase names.
- `symbolOf(text): AprsSymbol` (`RangeError` unless 2 chars), `symbolText(s)`, `symbolName(s)`, `describeSymbol(s)`, `withOverlay(s, c)`, `withoutOverlay(s)`, `overlayOf(s)`, `acceptsOverlay(s)`, `sameSymbol(a, b)`.
- `formatTimestamp(t): string`, `parseTimestamp(text): AprsTimestamp | undefined`: on-air timestamp text.
- `toNeutralData(d)`, `toNeutralHeader(p)`, `toNeutralPacket(p)`, `fromNeutralData(json): AprsData`, `Neutral = { [key: string]: unknown }`: vectors neutral form.
- `bytesToHex`, `hexToBytes`, `encodeUtf8`, `decodeUtf8` (undefined on invalid UTF-8): byte helpers.
- Version: none exported (package.json only, `./package.json` is exported).
