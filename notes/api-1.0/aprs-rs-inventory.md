# aprs-rs public API inventory (pdn-aprs 0.4.0, main 8d7400d)

Crate root re-exports everything below; all modules are private. `no_std` + `alloc`, one dependency (libm).

## Decoding

- `Packet::decode_tnc2(line: &[u8], ParseOptions) -> Result<Packet, HeaderError>`: TNC2 / APRS-IS line.
- `Packet::decode_ax25(frame: &[u8], ParseOptions) -> Result<Packet, HeaderError>`: AX.25 UI frame, no flags or FCS.
- `Packet::decode(source: Address, destination: Address, path: Vec<PathEntry>, information: &[u8], ParseOptions) -> Packet`: information field under a header you already have; never fails.
- `ParseOptions` (Copy, Default = LENIENT; private u64 bitset): which tolerable codes are accepted.
- `ParseOptions::STRICT`, `ParseOptions::LENIENT`: consts.
- `ParseOptions::tolerates(self, Code) -> bool`, `with(self, Code) -> Self`, `without(self, Code) -> Self`: const fns.
- `HeaderError { pub diagnostics: Vec<Diagnostic> }`: unusable header; Display, Error.
- `Diagnostic { pub severity: Severity, pub code: Code, pub message: String, pub offset: Option<usize> }`: Display.
- `Severity { Info, Warning, Error }`: Ord; `name(self) -> &'static str` (`info`/`warning`/`error`); no Display.
- `Code` (#[non_exhaustive], 64 variants, CamelCase of vectors ids): `Code::ALL: [Code; 64]`, `id(self) -> &'static str` (kebab id), `is_tolerable(self) -> bool`, `from_id(&str) -> Option<Code>`, Display (the id).
- `Packet::has_errors(&self) -> bool`, `has_warnings(&self) -> bool`.

## Data model

Packet:
- `Packet { pub source: Address, pub destination: Address, pub path: Vec<PathEntry>, pub information: Vec<u8>, pub data: Data, pub diagnostics: Vec<Diagnostic>, pub third_party: bool }`: all fields public; Clone, PartialEq.
- `Address` (private String): `new(&str) -> Result<Address, InvalidAddress>`, `third_party_source(&str) -> Result<..>`, `as_str`, `callsign -> &str`, `ssid -> u8` (0 when none or not a number), `is_ax25 -> bool`; Display, FromStr, Ord, Hash.
- `InvalidAddress(pub String)`: Display, Error.
- `PathEntry { pub address: Address, pub used: bool }`, `PathEntry::new(Address)` (unused).
- `QConstruct<'a> { pub construct: &'a str, pub station: Option<&'a Address> }`.

`Data` enum (not non_exhaustive): `Position(PositionReport)`, `MicE(MicEReport)`, `Object(ObjectReport)`, `Item(ItemReport)`, `Message(Message)`, `Ack(Ack)`, `Reject(Reject)`, `Bulletin(Bulletin)`, `NwsBulletin(Bulletin)`, `TelemetryNames(TelemetryLabels)`, `TelemetryUnits(TelemetryLabels)`, `TelemetryCoefficients(..)`, `TelemetryBits(..)`, `DirectedQuery(..)`, `Status(..)`, `Telemetry(..)`, `Weather(WeatherReport)`, `RawWeather(..)`, `Nmea(..)`, `MaidenheadBeacon(..)`, `Query(..)`, `Capabilities(..)`, `ThirdParty(Box<Packet>)`, `UserDefined(..)`, `Test(TestData)`, `AgreloDf(..)`, `Unrecognized(Unrecognized)`.
- `Unrecognized { Empty, NotAprs, ReservedDataType, Malformed }`.

Positioned (every report below has `pub fields: Positioned`):
- `position: Position { latitude: f64 deg, longitude: f64 deg, ambiguity: u8 (0-4) }`.
- `symbol: Symbol { table: char, code: char }` (Default `//`).
- `compressed: bool`; `compression: Option<CompressionType { fix: GpsFix, source: NmeaSource, origin: CompressionOrigin }>`.
- `course_degrees: Option<u16>`: whole degrees; doc says 1-360, decoder gives 0 for `000`.
- `speed_knots: Option<f64>`; `altitude_feet: Option<f64>`; `range_miles: Option<f64>`.
- `phg: Option<Phg { power, height, gain, directivity: u8 codes, beacons_per_hour: Option<u8> }>`.
- `dfs: Option<DfSignalStrength { strength, height, gain, directivity: u8 }>`.
- `area: Option<AreaObject { shape: AreaShape, lat_offset: u8, color: AreaColor, lon_offset: u8, corridor_width_miles: Option<u16> }>`.
- `df_bearing: Option<DfBearing { bearing_degrees: u16, number: u8, range: u8, quality: u8 }>`.
- `storm: Option<Storm { kind: StormKind, sustained_wind_knots, gust_knots, central_pressure_mbar, hurricane_radius_nm, tropical_storm_radius_nm, whole_gale_radius_nm: Option<u16> }>`.
- `dao: Option<Dao { datum: char, precision: DaoPrecision {None, Thousandths, Base91} }>`.
- `telemetry: Option<CommentTelemetry { sequence: u16, analog: Vec<u16>, digital: Option<u8> }>`.
- `frequency: Option<VoiceFrequency { mhz: f64, tone: Option<Tone>, tone_value: Option<u16>, offset_khz: Option<i32>, range: Option<u16>, range_km: bool, narrow: bool, ten_khz_resolution: bool }>`; `Tone { Off, Tone, Ctcss, Dcs, ToneBurst }`.
- `weather: Option<Weather>`; `signpost: Option<String>`; `comment: String` (empty = none).

Reports:
- `PositionReport { timestamp: Option<Timestamp>, messaging: bool, fields }`.
- `MicEReport { message: MicEMessage, old_data: bool, type_code: Option<char>, device_suffix: String, locator: Option<String>, legacy_telemetry: Vec<u8>, destination_ssid: u8, fields }`.
- `MicEMessage { OffDuty, EnRoute, InService, Returning, Committed, Special, Priority, Custom(u8), Emergency, Unknown }`.
- `ObjectReport { name: String, killed: bool, timestamp: Option<Timestamp>, fields }`; `ItemReport { name, killed, fields }`.
- `Message { addressee, text: String, message_id: Option<String>, reply_ack: Option<String> }` (Some("") = supports reply-ack).
- `Ack { addressee, acked_id: String, message_id, reply_ack }`; `Reject { addressee, rejected_id, message_id, reply_ack }`.
- `Bulletin { addressee, text, message_id }` (also NWS).
- `TelemetryLabels { addressee, labels: Vec<String>, message_id }`; `TelemetryCoefficients { addressee, coefficients: Vec<String> as sent, message_id }`; `TelemetryBits { addressee, bits: String, project: String, message_id }`.
- `DirectedQuery { addressee, query_type: String, target: Option<String> }`.
- `Status { timestamp, locator: Option<String>, symbol: Option<Symbol>, beam: Option<BeamHeading { heading_code: char, power_code: char }>, text }`.
- `Telemetry { sequence: String as sent, analog: Vec<Option<String>> as sent, bits: Option<String>, comment }`; `Telemetry::values(&self) -> Vec<Option<f64>>`.
- `WeatherReport { timestamp, weather: Weather, comment }`.
- `Weather { wind_direction_degrees: Option<u16>, wind_speed_mph: Option<f64>, wind_gust_mph: Option<f64>, temperature_f: Option<f64>, rain_1h_in, rain_24h_in, rain_midnight_in: Option<f64>, rain_raw: Option<u32>, humidity_percent: Option<u8>, pressure_mbar: Option<f64>, luminosity_w_m2: Option<u16>, snow_24h_in: Option<f64>, software: Option<char>, unit: Option<String>, extra: Vec<WeatherField { letter: char, value: String }> }`.
- `RawWeather { format: RawWeatherFormat {PeetBrosHash, PeetBrosStar, UltimeterPacket, UltimeterLogging}, data: String }`.
- `Nmea { sentence, has_checksum: bool, latitude, longitude: Option<f64>, fix_valid: Option<bool>, course_degrees: Option<f64>, speed_knots: Option<f64>, altitude_m: Option<f64>, time: Option<String>, waypoint: Option<String>, comment: String }`.
- `MaidenheadBeacon { locator, comment }`.
- `Query { query_type, footprint: Option<Footprint> }`; `Footprint { latitude: String, longitude: String as sent, radius_miles: u32 }`, `Footprint::new(f64, f64, u32)`, `latitude_degrees()`, `longitude_degrees() -> Option<f64>`.
- `Capabilities { capabilities: Vec<(String, Option<String>)> }`.
- `UserDefined { user_id: char, packet_type: char, data: Vec<u8> }`; `TestData { data: String }`; `AgreloDf { bearing_degrees: u16, quality: u8 }`.
- `Timestamp { DayHourMinute{day,hour,minute,utc: bool}, HourMinuteSecond{hour,minute,second}, MonthDayHourMinute{month,day,hour,minute} }` (u8 fields, kept out of range).
- Enums `GpsFix`, `NmeaSource`, `CompressionOrigin`, `AreaShape`, `AreaColor`, `StormKind`: one variant per neutral kebab value.

## Encoding

- `Data::encode(&self) -> Result<Vec<u8>, EncodeError>`: information field; for MicE returns the info bytes only (destination lost).
- `Packet::create(source, destination, path, Data) -> Result<Packet, EncodeError>`: refuses MicE.
- `Packet::create_mic_e(source, MicEReport, path) -> Result<Packet, EncodeError>`: computes the destination.
- `Packet::to_tnc2(&self) -> Vec<u8>`: header + `information` (not `data`), `*` on last used entry only.
- `Packet::to_ax25(&self) -> Result<Vec<u8>, EncodeError>`: UI frame, no flags or FCS.
- `EncodeError { pub message: String }`: refusal, text only, no machine-readable reason; Display, Error.

## Builders

- `Station` (private fields): `new(source: &str) -> Result<Station, InvalidAddress>`, `to(&self, dest: &str) -> Result<..>`, `via(&self, &[&str]) -> Result<..>`, `source()`, `destination()`, `path()`.
- `DEFAULT_DESTINATION: &str = "APZ001"`.
- Every builder: `to_data(&self) -> Result<Data, EncodeError>`, `build(&self) -> Result<Packet, EncodeError>`; setters take `self` by value.
- `Station::position(lat: f64, lon: f64) -> PositionBuilder`: + `messaging()`, `timestamp(Timestamp)`.
- `Station::object(name: &str) -> ObjectBuilder`: + `at(lat, lon)` (in positioned set), `timestamp(Timestamp)`, `permanent()` (111111z), `kill()`.
- `Station::item(name: &str) -> ItemBuilder`: + `kill()`.
- `Station::mic_e(lat, lon) -> MicEBuilder`: + `message(MicEMessage)`, `messaging()`.
- Positioned setters (Position, Object, Item, MicE): `at(f64, f64)`, `symbol(Symbol)`, `course(impl Into<f64>)` degrees, `speed(f64)` knots, `speed_kmh(f64)`, `altitude(f64)` feet, `altitude_metres(f64)`, `comment(&str)`, `phg(Phg)` codes, `range(f64)` miles, `frequency(mhz: f64)`, `tone(hz: f64)` (Tone::Tone only, truncated), `offset_khz(i32)`, `voice_frequency(VoiceFrequency)`, `compressed()`, `ambiguity(u8)`, `dao()` (W, base-91), `telemetry(seq: u16, analog: &[u16])`, `telemetry_with_bits(seq, analog, digital: u8)`.
- `Station::weather() -> WeatherBuilder`: `at(f64, f64)`, `symbol(Symbol)`, `timestamp(Timestamp)`, `messaging()`, `compressed()`, `dao()`, `wind(dir: impl Into<f64>, speed_mph: f64)`, `wind_direction(impl Into<f64>)`, no speed-only setter, `gust(mph)`, `temperature(f)`, `temperature_celsius(c)`, `humidity(impl Into<f64>)`, `pressure(mbar)`, `rain_last_hour(in)`, `rain_last_24_hours(in)`, `rain_since_midnight(in)`, `rain_last_hour_mm`, `rain_last_24_hours_mm`, `rain_since_midnight_mm`, `luminosity(impl Into<f64>)` W/m2, `snowfall(in)`, `observations(Weather)` (replaces all).
- `Station::message(addressee, text) -> MessageBuilder`: `id(&str)`, `reply_ack(&str)`.
- `Station::ack(addressee, message_id)`, `Station::reject(addressee, message_id) -> AckBuilder`: `reply_ack(&str)`.
- `Station::bulletin(id: char, text) -> DataBuilder`; `Station::group_bulletin(id: char, group, text) -> DataBuilder`.
- `Station::status(text) -> StatusBuilder`: `timestamp(Timestamp)`, `locator(&str, Symbol)`, `beam(BeamHeading)`.
- `Station::telemetry(sequence: u16) -> TelemetryBuilder`: `analog(&[f64])`, `channels(&[Option<f64>])`, `digital(u8)`, `comment(&str)`.
- `Station::telemetry_names(&[&str])`, `telemetry_units(&[&str])`, `telemetry_coefficients(&[f64])`, `telemetry_bits(bits: u8, project: &str) -> DataBuilder`: addressee is always the station's own source.
- `Station::data(Data) -> DataBuilder`; `DataBuilder { to_data, build }`.
- Not reachable from the builder: telemetry metadata addressee, a wind speed alone, CTCSS/DCS except through `voice_frequency`.

## The API view

- `source`, `destination`: `packet.source.as_str()`, `packet.destination.as_str()`.
- `path`: `packet.path[i].address` + `used`.
- `q_construct`: `Packet::q_construct(&self) -> Option<QConstruct<'_>>`.
- `third_party`: `packet.third_party` field.
- `has_errors`, `has_warnings`: methods.
- `tnc2`: `Packet::to_tnc2()`.
- `ax25`: `Packet::to_ax25()`, Err = "refused".
- `device`: `Packet::device(&self) -> Option<Device>`; `Device { vendor, model, class, os: Option<&'static str>, features: &'static [&'static str] }`.
- `symbol`: not offered (no symbol descriptions).
- `phg`: not offered (no PHG arithmetic).
- `inner`: `Data::ThirdParty(Box<Packet>)`.

## Other

- `tocall(callsign: &str) -> Option<Device>`: free fn, database lookup.
- `database_version() -> &'static str`: free fn, aprs-deviceid commit and date.
- `Symbol::new(char, char)` const, `Symbol::with_overlay(self, char) -> Option<Symbol>`, about 190 named consts (`Symbol::CAR`, ...).
- `Timestamp::dhm`, `hms`, `mdhm` (const ctors), `parse(&[u8]) -> Option<Timestamp>` (7 bytes), `parse_mdhm(&[u8])`, `is_valid()`, `is_permanent_object_marker()`, `to_bytes() -> Vec<u8>`.
- No crate version constant (Cargo's `CARGO_PKG_VERSION` only).
