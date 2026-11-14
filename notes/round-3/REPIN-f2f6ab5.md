# Repin to vectors f2f6ab5 (final round-3 vectors unless a review finds more)

Vectors round-3 head is now f2f6ab5. Since cb5dcc0 it adds:
- 2c6c4e4: text-only. The absent-text rule covers only name, addressee, query type, positioned symbol; every other required field left out stays missing-field. Some case descriptions and dates changed; no expected result changed.
- 2bc55bc: Builder rule. A setter replaces that quantity whatever unit it was given in, so on a kept builder the last call wins (as 1.0.x); value-given-twice only when one input carries the same quantity in two units at once.
- f2f6ab5: encoders refuse third-party data nested more than four deep with invalid-third-party-header (header group, before any fault inside the nesting). New case encode/third-party-nested-five-deep. Neither encoder nor decoder may recurse past the fifth level: a caller-built chain thousands deep must be refused without stack or recursion failure, and also must not blow up in TNC2/AX.25 output, neutral conversion or the dump tool. Implement it iteratively (walk the chain counting depth before recursing). Add a test with a caller-built chain of 10,000 levels.

Do: repin the vectors submodule to f2f6ab5, implement the above, make every case pass, update CHANGELOG (including a short "Behaviour changes" note for 1.x callers if you haven't one: lower-case locators refused, AX.25 punctuation now invalid-address, telemetry counts, nesting caps), push to your round-3 PR. Report in two lines.
