# aprs-c public API inventory (0.3.0, main 4a41936)

Whole surface is `include/pdn_aprs.h` (identical to `dist/pdn_aprs.h`). C99, no allocation, caller owns every struct and buffer. Functions return `int`: bytes written (>= 0) or `PDN_APRS_OK`, else a negative `PDN_APRS_ERR_*`. Booleans are `uint8_t` 0/1; enumerated fields are stored as `uint8_t` holding an enum or `#define` value. Optional scalars carry a `has_` flag; optional text is `""`. Text is UTF-8 in fixed NUL-terminated arrays, with an explicit `_len` where text can hold a NUL.

## Decoding

- `pdn_aprs_decode_tnc2(const void *line, size_t len, const pdn_aprs_decode_options *, pdn_aprs_packet *)`: decode `SRC>DEST,PATH:info` (no line end).
- `pdn_aprs_decode_ax25(const void *frame, size_t len, const pdn_aprs_decode_options *, pdn_aprs_packet *)`: decode a UI frame as KISS carries it (no flags, no FCS).
- `pdn_aprs_decode_info(const pdn_aprs_header *, const void *info, size_t len, const pdn_aprs_decode_options *, pdn_aprs_packet *)`: decode an information field under a header (NULL header = N0CALL>APZ001).
- `pdn_aprs_decode_written(same as decode_info)`: as decode_info but keeps no copy of the field, so it may exceed `PDN_APRS_MAX_INFO`; reads back encoder output.
- `pdn_aprs_decode_third_party(const pdn_aprs_data *outer, const pdn_aprs_decode_options *, pdn_aprs_packet *inner)`: decode a `}` packet's inner packet.
- Return codes: `PDN_APRS_OK`, `PDN_APRS_ERR_HEADER` (header unusable, packet says why), `PDN_APRS_ERR_TOO_LONG` (info over `PDN_APRS_MAX_INFO`), `PDN_APRS_ERR_ARGUMENT`. Strict rejection of data is `OK` with data `unrecognized`/`malformed` plus an error diagnostic.
- `pdn_aprs_decode_options { uint8_t strict; uint8_t reject[PDN_APRS_CODE_COUNT]; const pdn_aprs_device_table *devices; }`: zero or NULL = lenient.
- `pdn_aprs_options_strict(pdn_aprs_decode_options *)`: sets `strict = 1`.
- `pdn_aprs_packet { uint8_t header_ok; pdn_aprs_header header; uint16_t info_len; uint8_t info[PDN_APRS_MAX_INFO]; pdn_aprs_data data; uint8_t diagnostic_count; pdn_aprs_diagnostic diagnostics[24]; }`: 3,440 bytes on x86-64.
- `pdn_aprs_diagnostic { uint8_t severity; uint8_t code; }`.
- `pdn_aprs_severity` enum: `INFO`, `WARNING`, `ERROR`.
- `pdn_aprs_code` enum: `NONE` then the 64 vectors codes in codes.json order, `PDN_APRS_CODE_COUNT`.
- `pdn_aprs_code_name(int) -> const char *`: kebab-case id, or NULL.
- `pdn_aprs_code_from_name(const char *, size_t) -> int`: code for an id, or `NONE`.
- `pdn_aprs_code_tolerable(int) -> int`: 1 if a lenient decoder may tolerate it.
- `pdn_aprs_severity_name(int) -> const char *`: "info", "warning", "error".
- `pdn_aprs_has_diagnostic(const pdn_aprs_packet *, int code, int severity) -> int`: severity -1 = any; code must be exact.

## Data model

- `pdn_aprs_data { uint8_t type; uint8_t reason; union { report, message, ack, directed_query, meta, status, telemetry, weather, raw_weather, nmea, maidenhead, query, capabilities, third_party, user_defined, test, agrelo } as; }`: 2,648 bytes.
- `pdn_aprs_type` enum: `UNRECOGNIZED, POSITION, MIC_E, OBJECT, ITEM, MESSAGE, ACK, REJECT, BULLETIN, NWS_BULLETIN, TELEMETRY_NAMES, TELEMETRY_UNITS, TELEMETRY_COEFFICIENTS, TELEMETRY_BITS, DIRECTED_QUERY, STATUS, TELEMETRY, WEATHER, RAW_WEATHER, NMEA, MAIDENHEAD_BEACON, QUERY, CAPABILITIES, THIRD_PARTY, USER_DEFINED, TEST, AGRELO_DF, COUNT`; `pdn_aprs_type_name(int)` gives the vectors' name.
- `pdn_aprs_reason` enum (for unrecognized): `EMPTY, NOT_APRS, RESERVED_DATA_TYPE, MALFORMED`.
- `pdn_aprs_report` (position, mic-e, object, item; 1,608 bytes):
  - `char timestamp[8]`: as sent, or "".
  - `uint8_t messaging`: `=`/`@`.
  - `char name[20]`, `uint8_t killed`: object/item.
  - `uint8_t mic_e_message` (`pdn_aprs_mic_e_message`), `uint8_t old_data`, `char type_code` (0 none), `char device_suffix[3]`, `char locator[7]`, `uint8_t has_legacy_telemetry`, `uint8_t legacy_telemetry[5]`, `uint8_t destination_ssid`: Mic-E.
  - `double latitude, longitude`: degrees, N/E positive.
  - `uint8_t ambiguity`: 0-4.
  - `pdn_aprs_symbol symbol`.
  - `uint8_t compressed`, `has_compression`, `pdn_aprs_compression compression { uint8_t fix, source, origin }`.
  - `has_course` + `double course_degrees` (whole when decoded); `has_speed` + `double speed_knots`; `has_altitude` + `double altitude_feet`.
  - `has_phg` + `pdn_aprs_phg { uint8_t power, height, gain, directivity, beacons_per_hour }`: codes as sent.
  - `has_range` + `double range_miles`.
  - `has_dfs` + `pdn_aprs_dfs { uint8_t strength, height, gain, directivity }`.
  - `has_area` + `pdn_aprs_area { uint8_t shape, color, lat_offset, lon_offset, has_corridor; uint16_t corridor_width_miles }`.
  - `has_df_bearing` + `pdn_aprs_df_bearing { uint16_t bearing_degrees; uint8_t number, range, quality }`.
  - `has_storm` + `pdn_aprs_storm { uint8_t type; uint16_t sustained_wind_knots, gust_knots, central_pressure_mbar, hurricane_radius_nm, tropical_storm_radius_nm; uint8_t has_whole_gale_radius; uint16_t whole_gale_radius_nm }`.
  - `has_dao` + `pdn_aprs_dao { char datum; uint8_t precision }`.
  - `has_telemetry` + `pdn_aprs_comment_telemetry { uint16_t sequence; uint8_t analog_count; uint16_t analog[5]; uint8_t has_digital; uint16_t digital }`.
  - `has_frequency` + `pdn_aprs_frequency { double mhz; uint8_t tone; uint16_t tone_value; uint8_t has_offset; int16_t offset_khz; uint8_t has_range, range, range_km (bool), narrow, ten_khz_resolution }`.
  - `has_weather` + `pdn_aprs_weather`.
  - `char signpost[16]`; `uint16_t comment_len`; `char comment[PDN_APRS_TEXT_SIZE]`.
- `pdn_aprs_weather { uint8_t has[12]; double value[12]; char software; char unit[5]; uint8_t extra_count; pdn_aprs_weather_extra extra[8] { char letter; char value[24] } }`: indexed by anonymous enum `PDN_APRS_WX_WIND_DIRECTION` (deg), `WIND_SPEED` (mph), `WIND_GUST` (mph), `TEMPERATURE` (F), `RAIN_1H`, `RAIN_24H`, `RAIN_MIDNIGHT` (in), `HUMIDITY` (%), `PRESSURE` (mbar), `LUMINOSITY` (W/m2), `SNOW_24H` (in), `RAIN_RAW`, `COUNT`; `pdn_aprs_weather_field_name(int)` gives the neutral name (`temperature_f`).
- `pdn_aprs_message` (message, bulletin, nws-bulletin): `char addressee[20]; char message_id[20]; uint8_t has_reply_ack; char reply_ack[20]; uint16_t text_len; char text[TEXT_SIZE]`.
- `pdn_aprs_ack` (ack, reject): `char addressee[20]; char id[20]; uint8_t has_reply_ack; char reply_ack[20]`.
- `pdn_aprs_directed_query`: `char addressee[20]; char query_type[MAX_INFO]; char target[20]`.
- `pdn_aprs_number { double value; uint8_t is_null; char text[24] }`: value plus its text as sent for identical re-encoding.
- `pdn_aprs_telemetry_meta` (names/units/coefficients/bits): `addressee[20]; message_id[20]; uint8_t count; uint16_t offset[15], length[15]; pdn_aprs_number coefficient[15]; char bits[9]; uint16_t project_len; char text[TEXT_SIZE+15]`; `pdn_aprs_meta_item(meta, i, size_t *len) -> const char *` reads the i-th name/unit.
- `pdn_aprs_status`: `char timestamp[8]; char locator[7]; pdn_aprs_symbol symbol; uint8_t has_beam; char beam_heading, beam_power; uint16_t text_len; char text[TEXT_SIZE]`.
- `pdn_aprs_telemetry`: `char sequence[MAX_INFO]; uint8_t analog_count; pdn_aprs_number analog[5]; uint8_t has_bits; char bits[9]; uint16_t comment_len; char comment[TEXT_SIZE]`.
- `pdn_aprs_weather_report`: `char timestamp[9]` (MDHM); `pdn_aprs_weather weather`; `comment_len`, `comment`.
- `pdn_aprs_raw_weather`: `uint8_t format` (`PDN_APRS_RAW_WX_PEET_BROS_HASH/_STAR`, `ULTIMETER_PACKET/_LOGGING`); `data_len`, `data`.
- `pdn_aprs_nmea`: `sentence_len`, `char sentence[MAX_INFO]`, `has_checksum`, `has_position` + `double latitude, longitude`, `has_fix` + `fix_valid`, `has_course` + `double course_degrees`, `has_speed` + `double speed_knots`, `has_altitude` + `double altitude_m`, `char time[MAX_INFO]`, `char waypoint[MAX_INFO]`, `comment_len`, `comment`.
- `pdn_aprs_maidenhead`: `char locator[7]`; `comment_len`, `comment`.
- `pdn_aprs_query`: `char query_type[MAX_INFO]; uint8_t has_footprint; double latitude, longitude, radius_miles; char latitude_text[24], longitude_text[24]`.
- `pdn_aprs_capabilities`: `uint8_t count; struct { uint16_t token_offset, token_length; uint8_t has_value; uint16_t value_offset, value_length } item[64]` (anonymous struct type); `char text[...]`.
- `pdn_aprs_third_party`: `uint16_t len; uint8_t packet[2*MAX_INFO]`: inner TNC2 as received.
- `pdn_aprs_user_defined`: `char user_id, packet_type; uint16_t data_len; uint8_t data[MAX_INFO]`.
- `pdn_aprs_test`: `data_len`, `char data[TEXT_SIZE]`.
- `pdn_aprs_agrelo`: `uint16_t bearing_degrees; uint8_t quality`.
- Enum-like `#define` groups: `PDN_APRS_FIX_*`, `PDN_APRS_NMEA_*`, `PDN_APRS_ORIGIN_*` (0-7), `PDN_APRS_AREA_*` (0-9), `PDN_APRS_STORM_*`, `PDN_APRS_DAO_NONE/THOUSANDTHS/BASE91`, `PDN_APRS_TONE_NONE/OFF/TONE/CTCSS/DCS/BURST`, `PDN_APRS_RAW_WX_*`. Colours 0-15 are documented as `PDN_APRS_COLOR_*` but no such constants exist.
- `pdn_aprs_mic_e_message` enum: `OFF_DUTY`..`PRIORITY`, `CUSTOM0`..`CUSTOM6`, `EMERGENCY`, `UNKNOWN`.

## Encoding

- `pdn_aprs_encode_info(const pdn_aprs_data *, const pdn_aprs_encode_options *, void *buf, size_t cap, pdn_aprs_encoded *) -> int`: info field, no NUL, any length that fits cap.
- `pdn_aprs_encode_tnc2(const pdn_aprs_header *, const pdn_aprs_data *, const pdn_aprs_encode_options *, char *buf, size_t cap, pdn_aprs_encoded *) -> int`: whole line, NUL-terminated if room.
- `pdn_aprs_encode_ax25(same, void *buf, ...) -> int`: UI frame, control 0x03, PID 0xF0, no flags/FCS.
- `pdn_aprs_encode_options { const pdn_aprs_device_table *devices; }`.
- `pdn_aprs_encoded { size_t len; char destination[10]; const char *reason; }`: Mic-E destination computed; reason is English text or NULL.
- Refusal: return `PDN_APRS_ERR_REFUSED` with `encoded->reason` (static plain-ASCII string, about 160 distinct texts, no code); `PDN_APRS_ERR_BUFFER` too small; `PDN_APRS_ERR_ARGUMENT`.
- `pdn_aprs_strerror(int) -> const char *`: text for a result code.

## Builders

All return bytes written or a negative `PDN_APRS_ERR_*`; write a NUL-terminated TNC2 line, or an AX.25 frame when `station->ax25`. None returns the refusal reason or the computed Mic-E destination.

- `pdn_aprs_station { const char *source; const char *destination /* NULL = APZ001 */; const char *path /* "WIDE1-1,WIDE2-1" */; uint8_t ax25; const pdn_aprs_device_table *devices; }`; `PDN_APRS_DEFAULT_DESTINATION "APZ001"`.
- `pdn_aprs_position` (input struct): `double latitude, longitude; pdn_aprs_symbol symbol; uint8_t ambiguity (0-4), compressed; has_course + double course_degrees (0 unknown, 360 north); has_speed + double speed_knots; has_altitude + double altitude_feet; const pdn_aprs_phg *phg; has_range + double range_miles; const pdn_aprs_frequency *frequency; const pdn_aprs_dao *dao; const pdn_aprs_weather *weather; const pdn_aprs_comment_telemetry *telemetry; const char *comment`.
- `pdn_aprs_build_position(station, const pdn_aprs_position *, const char *timestamp /* "DDHHMMz"|"HHMMSSh"|NULL */, int messaging, buf, cap)`.
- `pdn_aprs_build_object(station, const char *name, const char *timestamp, int killed, const pdn_aprs_position *, buf, cap)`.
- `pdn_aprs_build_item(station, const char *name, int killed, const pdn_aprs_position *, buf, cap)`.
- `pdn_aprs_mic_e` (input struct): `latitude, longitude; symbol; uint8_t message (pdn_aprs_mic_e_message), ambiguity; has_course + course_degrees; has_speed + speed_knots; has_altitude + altitude_feet (/A=); has_altitude_m + altitude_m (Mic-E bytes); char type_code ('`', '\'', 0); const char *device_suffix, *locator; frequency*, dao*, telemetry*; const char *comment`. No messaging flag, no PHG/range.
- `pdn_aprs_build_mic_e(station, const pdn_aprs_mic_e *, buf, cap)`.
- `pdn_aprs_build_weather(station, const char *timestamp /* "MMDDHHMM" */, const pdn_aprs_weather *, buf, cap)`: positionless; positioned weather is `build_position` with `weather`.
- `pdn_aprs_weather_init(pdn_aprs_weather *)`, `pdn_aprs_weather_set(pdn_aprs_weather *, int index, double value)`.
- `pdn_aprs_build_message(station, addressee, text, message_id /* NULL none */, buf, cap)`: OLD.
- `pdn_aprs_build_message_reply_ack(station, addressee, text, message_id, reply_ack /* NULL none, "" support only */, buf, cap)`: NEW, replaces the above.
- `pdn_aprs_build_ack(station, addressee, message_id, buf, cap)`, `pdn_aprs_build_reject(same)`.
- `pdn_aprs_build_bulletin(station, const char *id /* "0"-"9", "A"-"Z", or digit + group "4WX" */, text, buf, cap)`.
- `pdn_aprs_build_status(station, text, timestamp, buf, cap)`: OLD.
- `pdn_aprs_status_options { const char *text, *timestamp, *locator; pdn_aprs_symbol symbol; uint8_t has_beam; char beam_heading, beam_power; }` + `pdn_aprs_build_status_options(station, const pdn_aprs_status_options *, buf, cap)`: NEW, replaces the above.
- `pdn_aprs_build_telemetry(station, const char *sequence, const double analog[5], const char *bits /* NULL = "00000000" */, const char *comment, buf, cap)`: OLD.
- `pdn_aprs_build_telemetry_channels(station, sequence, analog[5], const uint8_t present[5] /* NULL all */, bits, comment, buf, cap)`: NEW, replaces the above.
- `pdn_aprs_build_telemetry_names(station, addressee, const char *const *names, size_t count, buf, cap)`, `_units(same)`: up to 13.
- `pdn_aprs_build_telemetry_coefficients(station, addressee, const double *, size_t count, buf, cap)`: up to 15.
- `pdn_aprs_build_telemetry_bits(station, addressee, const char *bits, const char *project, buf, cap)`.
- `pdn_aprs_build(station, const pdn_aprs_data *, buf, cap)`: write ready-made data with a station header.
- Recipe keys vs C: units are knots/feet/F/inches only (program converts km/h, m, C, mm); timestamps are pre-formatted strings (no UTC formatter); telemetry sequence is text (no 0-999 check); bulletin id and group are one string; Mic-E messaging is `type_code`; metadata addressee required (recipe defaults it to the station).

## The API view

- `source`, `destination`: `packet.header.source`, `.destination`.
- `path`: `header.path[i].call` + `used` (and `marked`); `path_count`.
- `q_construct`: `header.q_construct` index (-1 none), station is the next entry.
- `device`: `pdn_aprs_identify_device(const pdn_aprs_device_table *, const pdn_aprs_packet *, pdn_aprs_device *) -> int`; `pdn_aprs_device { const char *vendor, *model, *class_; }`; `pdn_aprs_devices() -> const pdn_aprs_device_table *` (only with optional `pdn_aprs_deviceid.c`); `pdn_aprs_device_table { tocalls, tocall_count, mice, mice_count, mice_legacy, mice_legacy_count }` of `pdn_aprs_device_entry { key, vendor, model, class_ }`.
- `symbol`: `pdn_aprs_symbol_description(pdn_aprs_symbol)`.
- `inner`: `pdn_aprs_decode_third_party()`.
- Not offered: `has_errors`/`has_warnings` (no any-code query), `tnc2`/`ax25` (no writer of a packet as received), `third_party` flag, `phg` derived values.

## Other

- Version: `PDN_APRS_VERSION_MAJOR/MINOR/PATCH`, `PDN_APRS_VERSION "0.3.0"`, `pdn_aprs_version()`.
- Capacities: `PDN_APRS_MAX_INFO` 512 (overridable 256-16384, sets struct sizes), `PDN_APRS_TEXT_SIZE` 2*MAX_INFO+1, `PDN_APRS_NAME_SIZE` 20, `PDN_APRS_ADDR_SIZE` 10, `PDN_APRS_MAX_PATH` 16 (overridable), `PDN_APRS_MAX_DIAGNOSTICS` 24, `PDN_APRS_MAX_ANALOG` 5, `PDN_APRS_MAX_META_ITEMS` 15, `PDN_APRS_MAX_CAPABILITIES` 64, `PDN_APRS_MAX_WEATHER_EXTRA` 8.
- Result codes: `PDN_APRS_OK` 0, `ERR_ARGUMENT` -1, `ERR_HEADER` -2, `ERR_TOO_LONG` -3, `ERR_BUFFER` -4, `ERR_REFUSED` -5 (macros).
- Header: `pdn_aprs_header { char source[10], destination[10]; uint8_t path_count; pdn_aprs_path_entry path[16] { char call[10]; uint8_t used, marked }; int8_t q_construct; }`.
- Symbols: `pdn_aprs_symbol { char table, code }`; `pdn_aprs_symbol_make(char, char)`; `pdn_aprs_symbol_description(sym)`; `pdn_aprs_symbol_name(sym)` ("CAR"); `pdn_aprs_symbol_overlay(sym, char overlay, pdn_aprs_symbol *out) -> int`; 164 initializer macros `PDN_APRS_SYMBOL_<NAME>`.
- Build-system surface: CMake target `pdn_aprs::pdn_aprs` (static or shared by `BUILD_SHARED_LIBS`, SOVERSION = major), pkg-config `pdn_aprs`; a non-amalgamation build exports 73 internal `pdn_aprs__*` symbols.
