# aprs-c pre-1.0 API proposals

Ranked by importance. Classes: `remove` (superseded, already approved), `fix` (clearly right), `decide` (Tom's call; options and a recommendation). Line references are to `include/pdn_aprs.h` at 4a41936.

## 1. remove: `pdn_aprs_build_telemetry`, and `pdn_aprs_build_telemetry_channels` takes the plain name

- What: delete the old five-values call; rename the channels call.
- Why: superseded in 0.3.0; the old one is a wrapper that passes `present = NULL`.
- New shape: `int pdn_aprs_build_telemetry(const pdn_aprs_station *station, const char *sequence, const double analog[5], const uint8_t present[5] /* NULL: all present */, const char *bits, const char *comment, void *buf, size_t cap);` (subject to items 6 and 9, which may change `sequence` and the parameter list).
- Note: old callers get a compile error (wrong argument count against the prototype), not a silent change. README example `examples/build.c` and `tests/api.c` need updating.

## 2. remove: `pdn_aprs_build_status`, and `pdn_aprs_build_status_options` takes the plain name

- What: delete the text-plus-timestamp call; rename the options call.
- Why: superseded in 0.3.0; the old one fills a `pdn_aprs_status_options` and calls the new.
- New shape: `int pdn_aprs_build_status(const pdn_aprs_station *station, const pdn_aprs_status_options *status, void *buf, size_t cap);` (struct name per item 9). `examples/ax25.c` uses the old form.

## 3. remove: `pdn_aprs_build_message`, and `pdn_aprs_build_message_reply_ack` takes the plain name

- What: delete the four-string call; rename the reply-ack call.
- Why: superseded in 0.3.0; `reply_ack = NULL` is exactly the old behaviour.
- New shape: `int pdn_aprs_build_message(const pdn_aprs_station *station, const char *addressee, const char *text, const char *message_id /* NULL none */, const char *reply_ack /* NULL none, "" support only */, void *buf, size_t cap);`. `examples/build.c` uses the old form.

## 4. decide: what 1.0 freezes, source API or binary ABI

- Why: every decoded struct's size depends on `PDN_APRS_MAX_INFO` and `PDN_APRS_MAX_PATH`, which a user may override with `-D`; `pdn_aprs_decode_options.reject` is sized by `PDN_APRS_CODE_COUNT`, so every new vectors code (several were added this year) changes that struct's size; `pdn_aprs_weather.has[]`/`value[]` are sized by `PDN_APRS_WX_COUNT`; any new decoded field (as in 0.2.0 and 0.3.0) changes `pdn_aprs_report`/`pdn_aprs_packet` layout. Yet CMake will build a shared library with `SOVERSION` = major and there is no export macro for a Windows DLL. Padding is not the problem (about 40 small holes from `uint8_t has_x` before `double x`; worth tidying only if layouts are frozen).
- Options: (a) promise source compatibility only within 1.x: struct layouts may change in a minor release, the library is meant to be compiled into the program (amalgamation) or linked statically, and the CMake target is forced `STATIC`; (b) freeze layouts: fixed `reject[128]`, fixed weather arrays with spare slots, `uint8_t reserved[N]` tails on report/packet/data, `MAX_INFO`/`MAX_PATH` no longer overridable for shared builds, an export macro, and a size check such as `pdn_aprs_abi_check(sizeof(pdn_aprs_packet))`; (c) as (a) but keep shared builds with `SOVERSION` tied to major.minor.
- Recommendation: (a). The README sells it as two files dropped into a daemon, the overridable capacities already make a binary ABI meaningless, and reserved fields in 3 KB structs buy little. Write the rule in the README and header: "1.x keeps source compatibility; rebuild everything that includes `pdn_aprs.h` on upgrade; new optional fields may be added to any struct, with zero meaning absent, so zero-initialise every input struct". Even under (a), make `reject` a fixed `PDN_APRS_MAX_CODES` (128) so a designated initializer never meets a size change; that costs nothing.

## 5. decide: builders lose the refusal reason and the Mic-E destination

- Why: every `pdn_aprs_build_*` ends in `pdn_aprs_build()`, which passes `encoded = NULL` (`src/build.c:50`), so a program building a packet gets `PDN_APRS_ERR_REFUSED` and nothing else, while `pdn_aprs_encode_*` gives `encoded->reason`. `pdn_aprs_strerror(-5)` only says "the encoder refuses this data". The reason is English text in any case (about 160 distinct strings, no code), so it is not machine-readable anywhere.
- Options: (a) add a trailing `pdn_aprs_encoded *result` (may be NULL) to every build call, giving `len`, `reason` and the Mic-E `destination`; (b) put a `pdn_aprs_encoded *result` pointer in `pdn_aprs_station`; (c) also add a refusal code enum.
- Recommendation: (a), done in the same pass as items 1-3 since those signatures change anyway. Not (b): the station is shared configuration, the result is per call, and a shared station would break the "reentrant with your own buffers" rule. Not (c) for 1.0: the vectors define no refusal taxonomy, so a code list would be this library's own and would have to be frozen; document that `reason` text is not part of the stable API.

## 6. decide: builder inputs that do not match the recipe keys

- Why: the vectors' recipe is how "a program would have" the values, and the C builder makes the program do part of the rule's work, so the rule can be broken outside the library: (1) telemetry `sequence` is text, so `"1234"` or `"MIC"` is accepted and the B6 rule (a program's number is 0-999, three digits, refused above) is enforced only by `tools/diffdump.c`; (2) timestamps are pre-formatted strings, so the "cut, not rounded" rule lives in each caller (diffdump formats them itself); (3) bulletin `id` and `group` are one string (`"4WX"`), where the recipe has `id` (one character) and `group`; (4) telemetry metadata `addressee` is required, where the recipe defaults it to the station itself.
- Options and recommendation, per point: (1) take `unsigned sequence` and refuse over 999, leaving free-text sequences to `pdn_aprs_build()` with ready-made data: recommended. (2) add `int pdn_aprs_format_timestamp(int year, int month, int day, int hour, int minute, int second, int format /* PDN_APRS_TIMESTAMP_DHM, _HMS, _MDHM */, char out[9])` and keep the builders taking strings: recommended (no `time.h` dependency; a daemon may have its own clock form). (3) `pdn_aprs_build_bulletin(station, char id, const char *group /* NULL none */, text, ...)`: recommended, low cost. (4) NULL addressee means `station->source`: recommended; this one is really a `fix`.

## 7. decide: Mic-E builder messaging

- Why: the recipe has `messaging`, and the builder rule says write `` ` `` when the station can message and `'` when not, unless a device type is given. `pdn_aprs_mic_e` has no messaging flag: the program must know to put `` ` `` or `'` in `type_code`, and `type_code = 0` writes no type code at all, which leaves capability unstated. Every other report builder takes `messaging`.
- Options: (a) add `uint8_t messaging` and use `type_code` only for a device type (`>`, `]`, space), `` ` ``/`'` being derived; (b) keep `type_code` and document it.
- Recommendation: (a). Zero-initialised it gives `'`, matching the rule for a program that says nothing; a device type, when given, wins as the rule says.

## 8. fix: consistent error codes from builders

- What: in builders, a value APRS cannot carry returns `PDN_APRS_ERR_REFUSED` whatever its length; `PDN_APRS_ERR_ARGUMENT` only for a NULL required pointer or nonsense (count with NULL array); and a new `PDN_APRS_ERR_UNSUPPORTED` (-6) for input APRS allows but this library's fixed buffers cannot hold (text over 1,024 bytes, text holding a NUL as far as detectable).
- Why: today the code depends on the C buffer: an object name of 12 characters is `REFUSED` by the encoder but 25 characters is `ARGUMENT` (it does not fit `name[20]`); a message ID of `""` is `REFUSED` but 25 characters is `ARGUMENT`; a bulletin id over 6 is `ARGUMENT`; 14 telemetry names is `REFUSED`. The README already calls the buffer limit "unsupported", and the diff dump has to guess it.
- New shape: `#define PDN_APRS_ERR_UNSUPPORTED (-6) /* APRS allows it, but it does not fit this library's fixed buffers */`, and `pdn_aprs_strerror` text for it.

## 9. decide: one input-struct pattern for builders

- Why: position, object, item and Mic-E take a struct; status takes a struct named `_options` (because `pdn_aprs_status` is the decoded type) although its `text` is content, not an option, and `_options` elsewhere means settings (`decode_options`, `encode_options`); message, telemetry and the metadata calls take 5-8 positional arguments; `pdn_aprs_build_position` puts the struct before `timestamp, messaging` while object and item put it after `name, timestamp, killed`. Positional calls cannot grow an optional field later without a new function, which is how the three superseded calls in items 1-3 came about.
- Options: (a) a struct for every builder with optional inputs, one naming rule: `pdn_aprs_position_args`, `pdn_aprs_mic_e_args`, `pdn_aprs_status_args`, `pdn_aprs_message_args { addressee, text, message_id, reply_ack }`, `pdn_aprs_telemetry_args { sequence, analog[5], empty[5], bits, comment }`, with `name`/`timestamp`/`killed`/`messaging` inside the relevant struct; ack, reject and metadata stay positional (no optional fields); (b) keep positional calls, rename only `pdn_aprs_status_options` to `pdn_aprs_status_args` and fix the argument order (struct last everywhere).
- Recommendation: (a), done in this pass with items 1-3 and 5, since every builder signature is breaking anyway; it is the only shape that lets 1.x add an option without another `_v2` call. Under item 4's rule, a zero-initialised struct is the default and new fields go at the end. For telemetry, use `uint8_t empty[5]` (zero = present) rather than `present[5]`, so zero-initialisation means all present without a NULL special case.

## 10. fix: weather index names carry their units

- What: rename `PDN_APRS_WX_*` to `PDN_APRS_WX_WIND_DIRECTION_DEGREES`, `WIND_SPEED_MPH`, `WIND_GUST_MPH`, `TEMPERATURE_F`, `RAIN_1H_IN`, `RAIN_24H_IN`, `RAIN_MIDNIGHT_IN`, `HUMIDITY_PERCENT`, `PRESSURE_MBAR`, `LUMINOSITY_W_M2`, `SNOW_24H_IN`, `RAIN_RAW`, and give the enum a type name, `pdn_aprs_weather_field`.
- Why: every other quantity in the library has its unit in the name (`speed_knots`, `altitude_feet`), as the neutral form does; these are the one place the unit is only in a comment, and a builder caller with Celsius in hand has nothing in the name to stop them.

## 11. fix: `pdn_aprs_has_diagnostic` takes any code

- What: `code = -1` means any code, as `severity = -1` already means any severity.
- Why: gives `has_errors`/`has_warnings` of the API view (`pdn_aprs_has_diagnostic(p, -1, PDN_APRS_SEVERITY_ERROR)`) with no new function; today a program has to loop over the diagnostics.

## 12. decide: the rest of the API view

- Why: the view lists `tnc2` and `ax25` (the packet written back as received), `phg` (watts, height in feet, gain in dB, directivity) and `third_party`; C offers none (diffdump says so at `tools/diffdump.c:204`).
- Options: (a) add `int pdn_aprs_write_tnc2(const pdn_aprs_packet *, char *buf, size_t cap)` and `int pdn_aprs_write_ax25(const pdn_aprs_packet *, void *buf, size_t cap)` (header plus info as received; `PDN_APRS_ERR_REFUSED` for an address AX.25 cannot carry), and `int pdn_aprs_phg_values(pdn_aprs_phg, double *watts, double *height_feet, double *gain_db, int *directivity_degrees /* -1 omni */)`; skip `third_party` (a C program knows it called `pdn_aprs_decode_third_party`); (b) add nothing.
- Recommendation: (a) for the two writers, which an IGate or digipeater needs (forwarding a packet as heard, gating to RF) and cannot do from the public structs without re-implementing AX.25 address packing; (b) for PHG, which is arithmetic a program can do and is not a station's need.

## 13. fix: internal symbols leak from the installed library

- What: build the CMake target with hidden visibility (`C_VISIBILITY_PRESET hidden` plus a `PDN_APRS_API` attribute on public declarations), or build the installed library from the amalgamation, where they are already `static`.
- Why: a default (non-amalgamation) build exports 73 `pdn_aprs__*` functions from `libpdn_aprs.a`/`.so` (`nm` on `build/libpdn_aprs.a`), which a program can link against and which then become de facto API.

## 14. fix: `pdn_aprs_ack.id` becomes `message_id`

- Why: the builder parameter, `pdn_aprs_message.message_id` and `pdn_aprs_telemetry_meta.message_id` all say `message_id`; the neutral form says `acked_id`/`rejected_id`, so the bare `id` matches neither. New shape: `char message_id[PDN_APRS_NAME_SIZE]; /* the message ID acked or rejected */`.

## 15. fix: enumerations as typedef enums, and the missing colour constants

- What: turn the `#define` groups (`PDN_APRS_FIX_*`, `PDN_APRS_NMEA_*`, `PDN_APRS_ORIGIN_*`, `PDN_APRS_AREA_*`, `PDN_APRS_STORM_*`, `PDN_APRS_DAO_*`, `PDN_APRS_TONE_*`, `PDN_APRS_RAW_WX_*`) into named `typedef enum`s like `pdn_aprs_type` already is, fields staying `uint8_t`; add `PDN_APRS_COLOR_BLACK` .. `PDN_APRS_COLOR_GRAY` and `_LOW` variants (0-15), which the `pdn_aprs_area.color` comment refers to but which do not exist; rename `PDN_APRS_NMEA_*` (the compression source) to `PDN_APRS_SOURCE_*` so it is not confused with the `nmea` data type.
- Why: one style for enumerations; a debugger and a `switch` with `-Wswitch` both see the type; a documented constant that does not exist.

## 16. fix: name the capabilities item struct

- What: `typedef struct pdn_aprs_capability { uint16_t token_offset, token_length; uint8_t has_value; uint16_t value_offset, value_length; } pdn_aprs_capability;` and `pdn_aprs_capability item[PDN_APRS_MAX_CAPABILITIES];`, plus `const char *pdn_aprs_capability_token(const pdn_aprs_capabilities *, unsigned i, size_t *len)` and `_value` to mirror `pdn_aprs_meta_item`.
- Why: an anonymous struct type cannot be named in C, so a program cannot hold a pointer to one item; telemetry metadata has an accessor for the same offset/length scheme and capabilities does not.

## 17. fix: remove `pdn_aprs_options_strict`

- Why: it only sets `options->strict = 1` (`src/decode.c:253`); the README and examples use `{.strict = 1}`, which is shorter and clearer. Public surface nobody needs.

## 18. fix: small renames for clarity

- `pdn_aprs_status.beam_heading`, `beam_power` to `beam_heading_code`, `beam_power_code`: they are codes, not a heading or a power, as the neutral form's `heading_code`/`power_code` say.
- `pdn_aprs_reason` (why data is unrecognized) to `pdn_aprs_unrecognized_reason`, and `PDN_APRS_REASON_*` to `PDN_APRS_UNRECOGNIZED_*`: "reason" also names `pdn_aprs_encoded.reason`, the refusal text.
- `pdn_aprs_meta_item` to `pdn_aprs_telemetry_meta_item`, matching its struct.
- `pdn_aprs_decode_written` to `pdn_aprs_decode_info_unbounded`: "written" says where the bytes came from, not what the call does differently (keeps no copy, takes any length).

## 19. decide: enumeration name helpers

- Why: the library gives the vectors' names for codes, severities, types and weather fields, but the names for Mic-E messages, unrecognized reasons, raw weather formats, tones, DAO precision, compression fix/source/origin and area shapes live only in `tests/neutral.c`.
- Options: (a) add `pdn_aprs_mic_e_message_name()` and the rest; (b) leave them in the test code.
- Recommendation: (b). They exist for the neutral form, which the brief says the API view does not need; a daemon prints its own words. Keep the four that exist, since diagnostics are what programs log.
