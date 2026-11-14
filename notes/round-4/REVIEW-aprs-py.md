# Review findings to fix: aprs-py (reproducers in /tmp/r4-review-aprs-py/repro/)
1. Low. builder.py:80: `timestamp=False` now raises TypeError ("timestamp=True is gone"). In 1.1.0 False was legal and meant no timestamp. Accept False as None again.
2. Low. builder.py:510: `mic_e(51, -1, altitude_m=1e308)` gives not-a-number; the value is finite so it must be value-out-of-range (feet = metres * FEET_PER_METRE overflows to infinity before the range fault is ranked). Check the same overflow for every unit conversion in the builders (km/h to knots, Celsius, mm, hPa).
3. Low. tests/test_api.py test_delimiter_only_where_needed: the input lost its \x00 and may no longer test what it was meant to; restore the intent with a printable character that needs the delimiter.
