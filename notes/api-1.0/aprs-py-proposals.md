# aprs-py (pdn-aprs 0.3.0) pre-1.0 API proposals

Ranked by importance. No `remove` items: nothing in the public surface is an older form superseded by a newer one; the duplicates found are listed as `decide` or `fix`.

## 1. Builder keyword names: unit in the name, as in the data model and the recipes (decide)

What: `Station` keywords drop the unit that the data model and the recipe keys carry, so the same quantity has two names in one library: `course`/`course_degrees`, `speed`/`speed_knots` (beside `speed_kmh`), `altitude`/`altitude_feet` (beside `altitude_m`), `wind_direction`/`wind_direction_degrees`, `wind_speed`/`wind_speed_mph`, `gust`/`wind_gust_mph`, `temperature`/`temperature_f` (beside `temperature_c`), `rain_1h`/`rain_1h_in` (beside `rain_1h_mm`), `rain_since_midnight`/`rain_midnight_in` (beside `rain_since_midnight_mm`, recipe `rain_midnight_mm`), `humidity`/`humidity_percent`, `pressure`/`pressure_mbar`, `luminosity`/`luminosity_w_m2`, `snow_24h`/`snow_24h_in`; and `to`, `station` for what the model calls `addressee`.
Why: inconsistent with the rest of the library and with the recipe format; the metric pairs are lopsided (`speed` vs `speed_kmh` hides which unit the bare one is); `diff_dump.py` needs a 30-line rename table to call the builder.
Options: (a) keep the short names (they read well, units in docstrings); (b) use the data model's names exactly, metric variants beside them.
New shape (b): `position(latitude, longitude, symbol=None, *, comment, course_degrees, speed_knots | speed_kmh, altitude_feet | altitude_m, ...)`; `weather(..., wind_direction_degrees, wind_speed_mph, wind_gust_mph, temperature_f | temperature_c, rain_1h_in | rain_1h_mm, rain_24h_in | rain_24h_mm, rain_midnight_in | rain_midnight_mm, humidity_percent, pressure_mbar, luminosity_w_m2, snow_24h_in, ...)`; `message(addressee, text, ...)`, `ack(addressee, message_id)`, `reject(addressee, message_id)`, `telemetry_names(names, *, addressee=None)` and the other three likewise.
Recommendation: (b). Every name is then one a reader has already seen on the decoded data, and the recipe keys map one to one.

## 2. Voice frequency keywords: `tone` and `offset_khz` beside `frequency` (decide)

What: `position`, `object`, `item` and `mic_e` take `frequency: float | VoiceFrequency`, plus `tone: float` and `offset_khz: int`.
Why: (1) with a `VoiceFrequency`, `tone` and `offset_khz` are silently ignored (`_frequency` returns the object as given); (2) `tone` can only say `ToneType.TONE`, so CTCSS or DCS (recipe `frequency.tone`) need a `VoiceFrequency` anyway; (3) `int(tone)` truncates, so 88.5 Hz is written `T088` where every other value the library takes is rounded half away from zero.
Options: (a) drop `tone` and `offset_khz`: `frequency: float | VoiceFrequency | None`, a float meaning MHz with nothing else; (b) keep them, raise `ValueError` when given with a `VoiceFrequency`, round the tone, and add `tone_type`.
Recommendation: (a). Two fewer keywords on four methods, one way to say a tone, and no silent loss.

## 3. Builder refusals raise `EncodeError`, argument misuse `ValueError` (fix)

What: `Station.telemetry` raises plain `ValueError` for a sequence over 999, a refusal the vectors list beside name lengths and message IDs, which raise `EncodeError`.
Why: a program catching `EncodeError` for "the data cannot be sent" misses this one; `diff_dump.py` has to catch `ValueError` too.
New shape: `EncodeError("telemetry sequence 1000 is not 0-999")`. Keep `ValueError` only for misuse that is not about the data (a quantity given in both units, no symbol anywhere, latitude without longitude). Document that split in the `Station` docstring.

## 4. Builder numeric types for values the encoder rounds (fix)

What: `course: int`, `wind_direction: int`, `humidity: int`, `luminosity: int`, `offset_khz: int` on the builder.
Why: the Builder and Encoding rules round these (course 0.3 is unknown, humidity 99.7 is `h00`), the code accepts floats, but the hints tell a type-checked caller it may not pass one.
New shape: `float | None` for each (Python's `float` accepts an `int`).

## 5. Data model integer fields the encoder rounds (decide)

What: `course_degrees`, `Weather.wind_direction_degrees`, `humidity_percent`, `luminosity_w_m2`, `VoiceFrequency.tone_value`, `offset_khz` are `int`; `speed_knots`, `altitude_feet` and the other weather values are `float`.
Why: decoded values are always whole, so `int` is honest for a reader; but the encoder accepts and rounds floats here (vectors' encode records with `exact: false`), so constructing data with 88.6 is a type error that works.
Options: (a) keep `int` (decoded truth), document that the encoder also rounds a float; (b) widen to `float` so construction type-checks, losing "always whole" for readers.
Recommendation: (a), once item 4 gives builder callers the `float` they need; data built by hand is the rarer path.

## 6. `precise` and `message` keywords: use the data model's names (fix)

What: `precise=True` is the recipe's `dao` and adds `PositionedData.dao`; `Station.mic_e(message=...)` is `MicEReport.mic_e_message` and the recipe's `mic_e_message`.
Why: misleading name (`precise` does not say what it writes), and `message` collides in meaning with `Station.message()`.
New shape: `dao: bool = False` (adds `!DAO!`, datum `W`, base-91); `mic_e_message: MicEMessage = MicEMessage.IN_SERVICE`.

## 7. `Station(callsign, via=...)` and the derived `path` attribute (decide)

What: `via: str | Sequence[str]` is stored as given and a second field `path: tuple[str, ...]` (init=False) holds the parsed form; `build_packet` and `Packet` call the same things `source` and `path`.
Why: two public attributes for one value; names differ from `build_packet(source, ..., path=...)` and the recipe's `station.path`.
Options: (a) one field `path`, accepting `str | Sequence[str]` and normalised to a tuple in `__post_init__`, keeping `callsign`; (b) also rename `callsign` to `source`.
Recommendation: (a). `callsign` reads naturally on a station; the duplicate attribute is the real defect.

## 8. Leaked internals: make private, or export deliberately (fix)

What and new shape:
- `pdn_aprs.packet`: `tnc2_path` (listed in `__all__`), `is_q_construct`, `Q_CONSTRUCTS` (unused anywhere) -> `_tnc2_path`, `_is_q_construct`, delete `Q_CONSTRUCTS`.
- `pdn_aprs.devices`: `identify` (backs `Packet.device`), `mic_e_suffixes` (decoder internal) -> underscore. Keep `identify_tocall`, `identify_mic_e`, `DATABASE_VERSION` public, and export `DATABASE_VERSION` at top level.
- `pdn_aprs.builder`: `KMH_PER_KNOT`, `MM_PER_INCH` -> underscore (or move to `_util` beside `FEET_PER_METRE`).
- `pdn_aprs.symbols`: `PRIMARY_TABLE`, `ALTERNATE_TABLE` -> underscore (`Symbol.is_primary`/`is_alternate` cover them).
- `pdn_aprs.neutral.TYPES` -> `_TYPES`.
- `pdn_aprs.options.LENIENT`, `STRICT` (used by tests and as decoder defaults) -> underscore; tests use `ParseOptions.strict()`.
- `pdn_aprs.encode.DEFAULT_DESTINATION`, `MESSAGE_TEXT_LIMIT`: export at top level (programs need the default tocall; `diff_dump.py` imports it from the submodule).
Why: anything without an underscore in a public module is API by Python convention and would be frozen at 1.0.

## 9. `NeutralFormError` should subclass `AprsError` (fix)

What: `NeutralFormError(ValueError)`; every other library exception is an `AprsError`.
New shape: `class NeutralFormError(AprsError)`.

## 10. Compression enum names `Fix` and `NmeaSource` (fix)

What: `Fix` (old/current, the compression type's GPS fix) sits beside `NmeaFix` (valid/invalid); `NmeaSource` reads as something about `NmeaSentence`.
Why: misleading names in a flat namespace; both belong to `CompressionType`.
New shape: `CompressionFix`, `CompressionSource` (fields stay `fix`, `source`).

## 11. Machine-readable refusal reason on `EncodeError` (decide)

What: `EncodeError` carries only a message string.
Why: a program cannot tell "message too long" from "symbol invalid" without parsing English; `HeaderError` by contrast carries `DiagnosticCode`s.
Options: (a) leave it text-only for 1.0; (b) add `EncodeError.reason: RefusalReason`, an enum shared by the five libraries (needs a list in the vectors' `codes.json`); (c) a library-local enum.
Recommendation: (a) unless the other four libraries also want (b) now; (c) would only diverge. Adding a field later is not breaking.

## 12. `MicEReport.mic_e_message` default (fix)

What: the data model defaults to `OFF_DUTY`, the builder to `IN_SERVICE`.
Why: every Mic-E report has a message; a silent default on hand-built data is arbitrary and differs from the builder's.
New shape: `mic_e_message: MicEMessage` with no default (allowed, the dataclass is `kw_only`); the builder keeps `IN_SERVICE`.

## 13. `Phg.gain_dbi` (fix)

What: the property is `gain_dbi`; the API view key and APRS12c ch. 7 say dB.
New shape: `gain_db`.

## 14. `decode` alias of `decode_tnc2` (decide)

What: two public names for one function.
Options: (a) keep both; (b) keep only `decode_tnc2`, matching `decode_ax25` and `decode_kiss`; (c) keep only `decode`.
Recommendation: (a) is acceptable Python, but if Tom wants one name, (b), with the README examples changed.

## 15. `MicEReport.altitude_in_comment` (decide)

What: a builder hint living on the data model (compare=False, never set by the decoder, left out of the neutral form) so that `Station.mic_e(altitude=...)` writes `/A=` and `altitude_m=` writes Mic-E bytes.
Options: (a) keep, as documented; (b) move the choice into the builder only, by having it pass the encoder a private flag.
Recommendation: (a). It is how hand-built data says the same thing, and (b) would need a second encode entry point.
