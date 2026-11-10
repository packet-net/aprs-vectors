# APRS libraries: removes and fixes that need no decision

Every `remove` and `fix` item from the five reviews, one line each. "Conflict" marks an item that disagrees with a recommendation in DECISIONS.md (D1 to D11); "Note" marks one whose final shape depends on a decision.

Totals: 6 removes, 48 fixes.

## aprs-cs (1 remove, 13 fixes)

- remove: `AprsTelemetryBuilder.Analog(params decimal[])`, superseded by `Analog(params decimal?[])`.
- fix: rename the eight `AprsParseOptions` flags that do not match their code (`StripTrailingLineBreaks` -> `AllowTrailingLineBreak` and seven more) so all 32 are `Allow` + code name.
- fix: `TelemetryNames/Units/Coefficients/Bits` return an `AprsTelemetryMetadataBuilder` with `Addressee(string)`, default the source. Agrees with D6.
- fix: `AprsMessageBuilder.WithId` -> `MessageId`.
- fix: `MaidenheadLocator` -> `Locator` on the Mic-E and status reports, and the status builder parameter.
- fix: `AprsPositionedData.RadioRangeMiles` -> `RangeMiles`.
- fix: `SnowfallLast24HoursInches` and `Snowfall()` from decimal to double. Agrees with D1.
- fix: `AprsVoiceFrequency.FrequencyMHz` to double, rounded to the field's step instead of refused; rename the shorthand's `tone` to `toneHz`. Conflict with D4: the shorthand should take a tone kind and a whole tone value, not Hz; the double and rounding part stands.
- fix: `WindDirection(double)` and `WindSpeedMph(double)` setters, keeping `Wind(...)` as a convenience. Conflict with D3: names should be `WindDirectionDegrees`/`WindSpeedMph` and `Wind(...)` should go (rs removes its equivalent).
- fix: `ToInformationField` leaks `ParamName == "writer"`. Note: superseded by the single refusal type in D5.
- fix: `AprsAddress.MaxLength` (16) becomes internal.
- fix: remove `AprsSymbolTable.Describe` (same as `AprsSymbol.Description`).
- fix: `Kill()` -> `Kill(bool killed = true)` on object and item builders, and document that builders mutate. Conflict with D3: name it `Killed(bool killed = true)` to match the field.
- fix: `AprsUserDefinedData.DataText` -> `Text`.

## aprs-rs (2 removes, 10 fixes)

- remove: `WeatherBuilder::wind(direction, speed)`, superseded by `wind_direction` plus a speed setter.
- remove: `TelemetryBuilder::analog(&[f64])`; `channels(&[Option<f64>])` takes the name `analog`.
- fix: `Code::ALL` becomes `&'static [Code]` and `ParseOptions` stores a u128, so a 65th code fits.
- fix: `Data::encode` refuses Mic-E instead of dropping the destination. Agrees with D7.
- fix: add `WeatherBuilder::wind_speed_mph(f64)`. Agrees with D3.
- fix: one comment-telemetry setter, `telemetry(CommentTelemetry)`; `telemetry_with_bits` goes.
- fix: `tocall()` and `database_version()` move to `Device::from_tocall` and `Device::DATABASE_VERSION`.
- fix: `impl Display for Severity`.
- fix: `course_degrees` doc: 0 is unknown, 360 is north.
- fix: `InvalidAddress` field private, with `text()`.
- fix: `TelemetryCoefficients::values()`. Conflict with D2: under its option A coefficients become numbers plus text, and this reader is not needed; keep it only if D2 goes to B.
- fix: `impl Display for Timestamp`; `to_bytes()` removed.

## aprs-py (no removes, 8 fixes)

- fix: builder refusals (telemetry sequence over 999) raise `EncodeError`, not `ValueError`. Agrees with D5.
- fix: builder `course`, `wind_direction`, `humidity`, `luminosity`, `offset_khz` hinted `float`. Agrees with D1 (D1 also widens the data fields, which the reviewer declined); note `offset_khz` stays whole in the data under D1.
- fix: `precise` -> `dao`, Mic-E `message` -> `mic_e_message`. Agrees with D3.
- fix: leaked internals made private (`tnc2_path`, `is_q_construct`, `Q_CONSTRUCTS` deleted, `devices.identify`, `mic_e_suffixes`, builder unit constants, symbol table constants, `neutral.TYPES`, `options.LENIENT/STRICT`); export `DEFAULT_DESTINATION`, `MESSAGE_TEXT_LIMIT`, `DATABASE_VERSION` at top level. Note: under D10 the whole `neutral` module becomes `_neutral`.
- fix: `NeutralFormError` subclasses `AprsError`. Note: moot if D10 makes the neutral module private.
- fix: `Fix`, `NmeaSource` -> `CompressionFix`, `CompressionSource`. Agrees with D3.
- fix: `MicEReport.mic_e_message` has no default.
- fix: `Phg.gain_dbi` -> `gain_db`. Agrees with D9.

## aprs-ts (no removes, 8 fixes)

- fix: `build()` checks header addresses; `to*` writers reuse the stored information field. Agrees with D5.
- fix: builder classes exported as types only; constructors not public.
- fix: `bytesToHex`, `hexToBytes`, `encodeUtf8`, `decodeUtf8`, `diagnostic()` no longer exported. Note: under D10 the neutral functions leave the root too.
- fix: `BuiltPacket.path` becomes `PathEntry[]`; `via()` accepts `string | PathEntry`.
- fix: `EncodedInformation.info` -> `information`.
- fix: `decodeInformation` options default to lenient; `DecodedInformation` fields readonly.
- fix: document `@throws RangeError` on `decodeKiss` and `unwrapKiss`.
- fix: the encoder uses the exported `DEFAULT_DESTINATION` instead of its own literal.

## aprs-c (3 removes, 9 fixes)

- remove: `pdn_aprs_build_telemetry`; `pdn_aprs_build_telemetry_channels` takes the name. Note: final signature depends on D5, D6 and the args-struct decision; do all in one pass.
- remove: `pdn_aprs_build_status`; `pdn_aprs_build_status_options` takes the name. Note: as above.
- remove: `pdn_aprs_build_message`; `pdn_aprs_build_message_reply_ack` takes the name. Note: as above.
- fix: builder error codes: REFUSED for anything APRS cannot carry, ARGUMENT only for misuse, new `PDN_APRS_ERR_UNSUPPORTED` (-6) for input that does not fit fixed buffers. Agrees with D5.
- fix: `PDN_APRS_WX_*` names gain units (`TEMPERATURE_F`, `RAIN_1H_IN` ...); enum typed `pdn_aprs_weather_field`. Agrees with D3.
- fix: `pdn_aprs_has_diagnostic` accepts code -1 for any code (gives has_errors and has_warnings). Agrees with D9.
- fix: build the installed library with hidden visibility so the 73 internal `pdn_aprs__*` symbols are not exported.
- fix: `pdn_aprs_ack.id` -> `message_id`. Conflict with D3: the neutral form calls it `acked_id`/`rejected_id`, and in rs `Ack.message_id` means the ack's own message ID, so `message_id` here would mean something different; keep `id` or use `acked_id` with a comment that it holds the rejected ID for a reject.
- fix: `#define` groups become typed enums; add the missing `PDN_APRS_COLOR_*` constants; `PDN_APRS_NMEA_*` -> `PDN_APRS_SOURCE_*`.
- fix: name the capabilities item struct `pdn_aprs_capability` and add token and value accessors.
- fix: remove `pdn_aprs_options_strict`.
- fix: renames: `beam_heading`/`beam_power` -> `_code`; `pdn_aprs_reason` -> `pdn_aprs_unrecognized_reason`; `pdn_aprs_meta_item` -> `pdn_aprs_telemetry_meta_item`; `pdn_aprs_decode_written` -> `pdn_aprs_decode_info_unbounded`.
