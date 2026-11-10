# aprs-py (pdn-aprs 0.3.0) public API inventory

Import name `pdn_aprs`. Top level re-exports everything in `pdn_aprs.__all__`; submodules `neutral`, `encode`, `devices`, `options`, `packet`, `symbols`, `builder`, `model`, `diagnostics`, `errors` are importable too. Frozen dataclasses throughout; enums are `str` enums whose value is the neutral form's kebab-case string.

## Decoding

- `decode_tnc2(line: bytes | str, options: ParseOptions = LENIENT) -> Packet`: TNC2 / APRS-IS line.
- `decode`: alias of `decode_tnc2`.
- `decode_ax25(frame: bytes, options=LENIENT) -> Packet`: AX.25 UI frame without flags or FCS.
- `decode_kiss(frame: bytes, options=LENIENT) -> Packet`: KISS frame with FENDs.
- `ParseOptions(tolerated: frozenset[DiagnosticCode])`: which tolerable defects are accepted; `.lenient()`, `.strict()`, `.tolerates(code) -> bool`, `.tolerating(*codes)`, `.without(*codes)`, `.is_strict`; raises `ValueError` for a non-tolerable code.
- `pdn_aprs.options.LENIENT`, `STRICT`: module constants, not in `__all__`.
- `Packet(source: str, destination: str, path: tuple[PathEntry, ...], info: bytes, data: AprsData, diagnostics: tuple[Diagnostic, ...] = (), third_party: bool = False)`: decoded or built packet.
- `Packet.errors`, `Packet.warnings -> tuple[Diagnostic, ...]`: diagnostics filtered by severity.
- `Packet.data`: always present; `Unrecognized` when nothing decoded.
- `HeaderError(AprsError)`: header unusable; `.diagnostics: tuple[Diagnostic, ...]`.
- `AprsError(ValueError)`: base exception.
- `Diagnostic(severity: Severity, code: DiagnosticCode)`: `str()` is `severity:code`; `Diagnostic.parse(text)`.
- `Severity`: `INFO`, `WARNING`, `ERROR`.
- `DiagnosticCode`: 67 codes from vectors `codes.json`; `.tolerable -> bool`, `.meaning -> str`.
- `UnrecognizedReason`: `EMPTY`, `NOT_APRS`, `RESERVED_DATA_TYPE`, `MALFORMED`.

## Data model

Every type subclasses `AprsData`, `kind: ClassVar[str]` = neutral `type`. Absent = `None`, `""`, `()` or `False`.

- `PositionedData` (kw_only base): `latitude: float` deg N+, `longitude: float` deg E+, `symbol: Symbol`, `ambiguity: int = 0` (0-4), `compressed: bool`, `compression: CompressionType | None`, `course_degrees: int | None`, `speed_knots: float | None`, `altitude_feet: float | None`, `phg: Phg | None`, `range_miles: float | None`, `dfs: Dfs | None`, `area: AreaObject | None`, `df_bearing: DfBearing | None`, `storm: Storm | None`, `dao: Dao | None`, `telemetry: CommentTelemetry | None`, `frequency: VoiceFrequency | None`, `weather: Weather | None`, `signpost: str | None`, `comment: str = ""`.
- `PositionReport(PositionedData)`: `timestamp: Timestamp | None`, `messaging: bool`.
- `MicEReport(PositionedData)`: `mic_e_message: MicEMessage = OFF_DUTY`, `old_data: bool`, `type_code: str | None`, `device_suffix: str | None`, `locator: str | None`, `legacy_telemetry: tuple[int, ...]`, `destination_ssid: int = 0`, `altitude_in_comment: bool` (encoder hint, compare=False, not in neutral form).
- `ObjectReport(PositionedData)`: `name: str`, `killed: bool`, `timestamp: Timestamp | None`.
- `ItemReport(PositionedData)`: `name: str`, `killed: bool`.
- `Message`: `addressee: str`, `text: str`, `message_id: str | None`, `reply_ack: str | None` (`""` = capable).
- `Ack`: `addressee`, `acked_id: str`, `reply_ack: str | None`.
- `Reject`: `addressee`, `rejected_id: str`, `reply_ack: str | None`.
- `Bulletin`: `addressee`, `text`, `message_id: str | None`; properties `identifier`, `group`, `is_announcement`.
- `NwsBulletin`: `addressee`, `text`, `message_id`.
- `TelemetryNames`: `addressee`, `names: tuple[str, ...]`, `message_id`.
- `TelemetryUnits`: `addressee`, `units: tuple[str, ...]`, `message_id`.
- `TelemetryCoefficients`: `addressee`, `coefficients: tuple[float, ...]`, `message_id`, `coefficients_text: tuple[str, ...]` (as sent, compare=False).
- `TelemetryBits`: `addressee`, `bits: str`, `project: str = ""`, `message_id`.
- `DirectedQuery`: `addressee`, `query_type: str`, `target: str | None`.
- `StatusReport`: `text: str`, `timestamp: Timestamp | None`, `locator: str | None`, `symbol: Symbol | None`, `beam: Beam | None`.
- `TelemetryReport`: `sequence: str` (as sent), `analog: tuple[float | None, ...]`, `bits: str | None`, `comment: str`, `analog_text: tuple[str, ...]` (as sent, compare=False).
- `PositionlessWeather`: `timestamp: Timestamp` (mdhm), `weather: Weather`, `comment: str`.
- `RawWeather`: `format: RawWeatherFormat`, `data: str`.
- `NmeaSentence`: `sentence: str`, `has_checksum: bool`, `latitude: float | None`, `longitude: float | None`, `fix: NmeaFix | None`, `course_degrees: float | None`, `speed_knots: float | None`, `altitude_m: float | None`, `time: str | None` (`HH:MM:SS[.f]`), `waypoint: str | None`, `comment: str`.
- `MaidenheadBeacon`: `locator: str`, `comment: str`.
- `Query`: `query_type: str`, `footprint: Footprint | None`.
- `Capabilities`: `capabilities: tuple[tuple[str, ...], ...]` (1- or 2-tuples).
- `ThirdParty`: `packet: Packet`.
- `UserDefined`: `user_id: str`, `packet_type: str`, `data: str` (one code point per byte).
- `TestData`: `data: str`.
- `AgreloDf`: `bearing_degrees: int`, `quality: int`.
- `Unrecognized`: `reason: UnrecognizedReason`.
- `Weather`: `wind_direction_degrees: int | None`, `wind_speed_mph: float | None`, `wind_gust_mph: float | None`, `temperature_f: float | None`, `rain_1h_in`, `rain_24h_in`, `rain_midnight_in: float | None`, `rain_raw: int | None`, `humidity_percent: int | None`, `pressure_mbar: float | None`, `luminosity_w_m2: int | None`, `snow_24h_in: float | None`, `software: str | None`, `unit: str | None`, `extra: tuple[WeatherExtra, ...]`.
- `WeatherExtra`: `letter: str`, `value: str` (as sent).
- `Timestamp(text: str)`: as sent; ctors `dhm(day, hour, minute, *, zulu=True)`, `hms(h, m, s)`, `mdhm(month, day, hour, minute)`; properties `kind: TimestampKind | None`, `month`, `day`, `hour`, `minute`, `second: int | None`, `is_valid`.
- `TimestampKind`: `DHM_ZULU`, `DHM_LOCAL`, `HMS`, `MDHM`.
- `CompressionType(fix: Fix = CURRENT, source: NmeaSource = OTHER, origin: CompressionOrigin = SOFTWARE)`: `.value -> int` (0-63), `from_value(int)`.
- `Fix`: `OLD`, `CURRENT` (compression GPS fix).
- `NmeaSource`: `OTHER`, `GLL`, `GGA`, `RMC` (compression NMEA source).
- `CompressionOrigin`: 8 values, `COMPRESSED` ... `DIGIPEATER_CONVERSION`.
- `Phg(power: int, height: int, gain: int, directivity: int, beacons_per_hour: int | None)`: codes as sent; properties `power_watts: int`, `height_feet: int`, `gain_dbi: int`, `directivity_degrees: int | None`, `range_miles: float`.
- `Dfs(strength, height, gain, directivity: int)`: codes as sent.
- `AreaObject(shape: AreaShape, color: AreaColor, lat_offset: int, lon_offset: int, corridor_width_miles: int | None)`; `lat_offset_degrees`, `lon_offset_degrees: float`.
- `AreaShape` (10, `.code` 0-9), `AreaColor` (16, `.code` 0-15).
- `DfBearing(bearing_degrees: int, number: int, range: int, quality: int)`: codes as sent.
- `Storm(type: StormType, sustained_wind_knots, gust_knots, central_pressure_mbar, hurricane_radius_nm, tropical_storm_radius_nm, whole_gale_radius_nm: int | None)`.
- `StormType`: `TROPICAL_STORM`, `HURRICANE`, `TROPICAL_DEPRESSION`.
- `Dao(datum: str, precision: DaoPrecision)`; `DaoPrecision`: `NONE`, `THOUSANDTHS`, `BASE91`.
- `CommentTelemetry(sequence: int, analog: tuple[int, ...], digital: int | None)`: base-91 comment telemetry, digital 0-255.
- `VoiceFrequency(mhz: float, tone: ToneType | None, tone_value: int | None, offset_khz: int | None, range: int | None, range_km: bool, narrow: bool, ten_khz_resolution: bool)`.
- `ToneType`: `OFF`, `TONE`, `CTCSS`, `DCS`, `TONE_BURST`.
- `Beam(heading_code: str, power_code: str)`; `heading_degrees: int | None`.
- `Footprint(latitude: float, longitude: float, radius_miles: float, latitude_text: str, longitude_text: str)` (texts as sent, compare=False).
- `MicEMessage`: 16 values incl. `CUSTOM0`-`CUSTOM6`, `EMERGENCY`, `UNKNOWN`.
- `RawWeatherFormat`: 4 values. `NmeaFix`: `VALID`, `INVALID`.

## Encoding

- `encode_info(data: AprsData) -> bytes`: information field; raises `EncodeError`.
- `mic_e_destination(data: MicEReport) -> str`: computed Mic-E destination; raises `EncodeError`.
- `build_packet(source: str, data: AprsData, *, destination: str = "APZ001", path: Iterable[str | PathEntry] = ()) -> Packet`: header checked, Mic-E destination computed (`destination` ignored).
- `EncodeError(AprsError)`: refusal; reason is free text in `str(e)` only, no code.
- `pdn_aprs.encode.DEFAULT_DESTINATION = "APZ001"`, `MESSAGE_TEXT_LIMIT = 67`: in `encode.__all__`, not top level.
- `pdn_aprs.neutral`: `to_neutral(data) -> dict`, `from_neutral(dict) -> AprsData`, `header_to_neutral(packet)`, `packet_to_neutral(packet, *, inner=False)`, `NeutralFormError(ValueError)`, `TYPES: dict[str, type]` (public by name, not in `__all__`).

## Builders

`Station(callsign: str, via: str | Sequence[str] = (), destination: str = "APZ001", messaging: bool = False, symbol: Symbol | None = None)`; derived attribute `path: tuple[str, ...]`. Every method returns an encoded `Packet`; refusals raise `EncodeError` or plain `ValueError`.

- `send(data: AprsData) -> Packet`: any data from this station.
- `position(latitude, longitude, symbol=None, *, comment="", course: int | None, speed: float | None (kn), altitude: float | None (ft), speed_kmh, altitude_m, timestamp: TimestampLike = None, compressed=False, ambiguity=0, phg: Phg | None, range_miles: float | None, frequency: float | VoiceFrequency | None (MHz), tone: float | None (Hz), offset_khz: int | None, telemetry: CommentTelemetry | None, precise=False)`; `messaging` from the Station.
- `object(name, latitude, longitude, symbol=None, *, comment, killed=False, timestamp: TimestampLike = True, ...same positioned options)`; timestamp required.
- `item(name, latitude, longitude, symbol=None, *, comment, killed=False, ...same positioned options)`.
- `mic_e(latitude, longitude, symbol=None, *, message: MicEMessage = IN_SERVICE, course, speed, altitude, speed_kmh, altitude_m, comment, ambiguity, frequency, tone, offset_khz, telemetry, precise)`; no phg/range/compressed; type code from `Station.messaging`; `altitude_m` -> Mic-E bytes, `altitude` -> `/A=`.
- `weather(latitude=None, longitude=None, *, wind_direction: int (deg), wind_speed: float (mph), gust: float (mph), temperature: float (F), rain_1h, rain_24h, rain_since_midnight: float (in), humidity: int (%), pressure: float (mbar), luminosity: int (W/m2), snow_24h: float (in), timestamp: TimestampLike, symbol: Symbol = WEATHER_STATION, software, unit: str | None, temperature_c, rain_1h_mm, rain_24h_mm, rain_since_midnight_mm)`; no position -> positionless, mdhm stamped now by default.
- `message(to, text, *, message_id: str | None, reply_ack: str | None)`.
- `ack(to, message_id)`, `reject(to, message_id)`.
- `bulletin(identifier: str, text, *, group: str = "")`.
- `status(text="", *, timestamp, locator: str | None (upper-cased), symbol: Symbol | None, beam: Beam | None)`.
- `telemetry(sequence: int | str, analog: Iterable[float | None], bits: str = "00000000", *, comment="")`; int sequence 0-999 else `ValueError`.
- `telemetry_names(names, *, station: str | None)`, `telemetry_units(units, *, station)`, `telemetry_coefficients(coefficients: Iterable[float], *, station)`, `telemetry_bits(bits, project="", *, station)`; `station` = addressee, default own callsign.
- `TimestampLike = Timestamp | datetime | bool | None` (`True` = now, naive datetime = UTC); not exported.
- `pdn_aprs.builder.KMH_PER_KNOT = 1.852`, `MM_PER_INCH = 25.4`: public by name.

Recipe key to builder name (from `tools/diff_dump.py`): `course_degrees`->`course`, `speed_knots`->`speed`, `altitude_feet`->`altitude`, `dao`->`precise`, `mic_e_message`->`message`, `addressee`->`to`/`station`, `id`->`identifier`, `wind_direction_degrees`->`wind_direction`, `wind_speed_mph`->`wind_speed`, `wind_gust_mph`->`gust`, `temperature_f`->`temperature`, `rain_*_in`->`rain_*`, `rain_midnight_*`->`rain_since_midnight*`, `humidity_percent`->`humidity`, `pressure_mbar`->`pressure`, `luminosity_w_m2`->`luminosity`, `snow_24h_in`->`snow_24h`; `frequency.tone` (type) has no keyword (needs a `VoiceFrequency`); recipe `messaging` per report goes on `Station`.

## The API view

- `source`, `destination`: `Packet.source`, `Packet.destination`.
- `path`: `Packet.path: tuple[PathEntry, ...]`; `PathEntry(call: str, used: bool)`, `str()` adds `*`.
- `q_construct`: `Packet.q_construct -> QConstruct | None`; `QConstruct(construct: str, station: str | None)`; `None` on an inner packet.
- `third_party`: `Packet.third_party: bool`.
- `has_errors`, `has_warnings`: `bool(Packet.errors)`, `bool(Packet.warnings)`.
- `tnc2`: `Packet.to_tnc2() -> bytes`; also `Packet.header -> str`, `str(packet)`.
- `ax25`: `Packet.to_ax25() -> bytes`, raises `EncodeError` when refused; `Packet.to_kiss(port=0) -> bytes`.
- `device`: `Packet.device -> Device | None`; `Device(vendor: str, model: str, device_class: str, os: str, features: tuple[str, ...])`, `class_description`, `str()`.
- `symbol`: `Symbol.description -> str | None`.
- `phg`: `Phg.power_watts`, `height_feet`, `gain_dbi` (view key `gain_db`), `directivity_degrees`.
- `inner`: `ThirdParty.packet`.

## Other

- `__version__ = "0.3.0"`.
- `Symbol(table: str, code: str)`: 164 named class attributes (`Symbol.CAR`...); `parse(text)`, `from_name(name)`, `is_primary`, `is_alternate`, `overlay`, `base`, `with_overlay(ch)`, `name`, `description`, `is_valid`.
- `pdn_aprs.symbols.PRIMARY_TABLE`, `ALTERNATE_TABLE`: public by name.
- `pdn_aprs.devices`: `DATABASE_VERSION: str`, `identify(packet)`, `identify_tocall(destination)`, `identify_mic_e(type_code, suffix)`, `mic_e_suffixes(type_code)` (public by name; only `Device` re-exported).
- `pdn_aprs.packet`: `tnc2_path(path) -> str` (in `__all__`), `is_q_construct(call)`, `Q_CONSTRUCTS` (unused).
