# Pre-1.0 public API review: brief for one library

You review the PUBLIC API of one APRS library (named in your prompt) before it is frozen at 1.0.0. After 1.0, every change you do not propose now costs a major version. Tom's standing decisions: clean the interfaces up now; where a newer function or type replaces an older one, the old one is REMOVED (no deprecation shims); breaking changes are fine in this pass.

Context: five libraries implement the same APRS rules (aprs-cs C#, aprs-rs Rust, aprs-py Python, aprs-ts TypeScript, aprs-c C99) and agree byte for byte, checked by packet-net/aprs-vectors (`~/src/aprs-vectors`, README sections "Rules the cases rely on" and "Comparing implementations", which define the neutral data form, the builder recipe format and the API view every library exposes). Recent rounds added builder options and widened some types quickly; this review is about the shape of what a program sees.

Read the library's public surface completely (exports, public types and members, builder/fluent APIs, error types, constants, header for C), its README and CHANGELOG, and how its own tests and dump tool use it. Do not change code. Work in a separate worktree if you need to build (`/home/tf/aprs-exact/api/wt-<repo>`), and delete build output when done.

## Write two files

1. `/home/tf/aprs-exact/api/<repo>-inventory.md`: the public API in a compact common form so it can be compared with the other four. Sections, in this order: Decoding (entry points, result and error types); Data model (each report type and its fields with types and units, nullability); Encoding (entry points, refusal/error reporting); Builders (each builder, each option with type and units); The API view (header, path, device lookup, ax25, etc.); Other (constants, version, symbols, utilities). One line per item: name, signature or type, one-phrase meaning. No prose beyond that.

2. `/home/tf/aprs-exact/api/<repo>-proposals.md`: proposed changes, each with: what, why (concrete: superseded, inconsistent with the rest of this library, unidiomatic for the language, misleading name, wrong type or unit, missing symmetry, leaks internals, hard to use correctly), the exact new shape, and a class:
   - `remove`: superseded by a newer replacement (Tom has already approved these).
   - `fix`: clearly right, low controversy (naming slip, wrong visibility, missing doc, an internal that leaked public).
   - `decide`: a real design choice with trade-offs Tom should make; give the options and your recommendation.
   Rank by importance. Be concrete and brief. Do not propose new features beyond what the vectors' recipe format and API view need; do propose removing public surface nobody should depend on.

Specific things to look at in every library: names and units in field names (`_knots`, `_feet`, `_mph` and so on, consistent with the vectors' neutral form unless the language's idiom says otherwise); integer vs fractional types for values the encoder rounds (course, speed, altitude, weather) on BOTH the decoded data and the builder side; how refusals are reported (exception, Result, error code) and whether the reason is machine-readable; nullability of optional fields; builder entry points and option names compared with the recipe keys; anything public only so tests or the dump tool can reach it.

Rules: never write an em dash (U+2014) or an en dash (U+2013). One line per paragraph in markdown. Your final report back is two lines: counts of remove/fix/decide, and the single most important `decide` item.
