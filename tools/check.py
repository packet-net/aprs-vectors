#!/usr/bin/env python3
"""Checks the vectors are well formed and consistent. CI runs it on every change.

  python3 tools/check.py

Needs the jsonschema package (pip install jsonschema). Checks, beyond the schema:
- case ids are unique across all files;
- every diagnostic names a code in codes.json, with a valid severity;
- every interpretation a case links to is a heading in interpretations.md;
- an interpretation case links at least one interpretation;
- canonical_info appears exactly with an equivalent or rounded re-encoding;
- every tolerable code has a case showing both sides of it: a strict result that differs from
  the lenient one, where that code is the only tolerance the lenient decoding used;
- every `refusal` (in expect) and `reencode_refusal` names an id in the `refusals` list of codes.json,
  and no case names the fallback `does-not-read-back`;
- every refusal id except the exempt ones (EXEMPT_REFUSALS) is named by at least one case;
- every refused case names its refusal code (REFUSALS_REQUIRED);
- (by the schema) a build case's report is one the README lists, with only the args that report takes,
  and each input form has its own expect form: decode keys, info for encode, tnc2 for build;
- cases/precedence.json is what tools/precedence.py writes.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    sys.exit("tools/check.py needs the jsonschema package: pip install jsonschema")

ROOT = Path(__file__).resolve().parent.parent
SEVERITIES = {"info", "warning", "error"}
FALLBACK = "does-not-read-back"
EXEMPT_REFUSALS = {
    FALLBACK,
    "not-a-number",  # JSON cannot carry NaN or infinity
    "invalid-address",  # needs a packet header, which an encode case does not give
    "ax25-cannot-carry",  # needs a packet header
    "tnc2-cannot-carry",  # needs a packet header
    "not-encodable",  # undecoded data: no form of it is held by all six libraries (rs not inside third-party, cs not at top level)
}
# Every refused case names its code, and every refusal id is named by a case except these, each of
# which an encode or decode case cannot produce (see the README's Refusal reasons rule).
REFUSALS_REQUIRED = True


def slug(heading):
    """GitHub's anchor for a markdown heading."""
    text = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return text.replace(" ", "-")


def diagnostics_in(case):
    """Every severity:code string a case names, including a third-party packet's inner ones."""
    found = []

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("diagnostics", "header_error") and isinstance(value, list):
                    found.extend(v for v in value if isinstance(v, str))
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(case.get("expect", {}))
    if isinstance(case.get("strict"), dict):
        walk(case["strict"])
    return found


def main():
    schema = json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    document_codes = json.loads((ROOT / "codes.json").read_text(encoding="utf-8"))
    catalogue = document_codes["codes"]
    refusal_ids = {c["id"] for c in document_codes["refusals"]}
    named_refusals = set()
    codes = {c["id"] for c in catalogue}
    tolerable = {c["id"] for c in catalogue if c["tolerable"]}
    anchors = {
        slug(line.lstrip("#"))
        for line in (ROOT / "interpretations.md").read_text(encoding="utf-8").splitlines()
        if line.startswith("## ")
    }

    problems = []
    seen = {}
    shown_both_sides = set()
    files = sorted((ROOT / "cases").glob("*.json"))
    count = 0
    for path in files:
        name = path.relative_to(ROOT)
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            problems.append(f"{name}: not JSON: {e}")
            continue

        for error in validator.iter_errors(document):
            where = "/".join(str(p) for p in error.absolute_path)
            problems.append(f"{name}: {where}: {error.message[:200]}")

        for case in document.get("cases", []):
            count += 1
            cid = case.get("id", "?")

            def problem(what):
                problems.append(f"{name}: {cid}: {what}")

            if cid in seen:
                problem(f"id also used in {seen[cid]}")
            seen[cid] = name

            if case.get("authority") == "interpretation" and not case.get("interpretations"):
                problem("an interpretation case must link the interpretation it depends on")
            for anchor in case.get("interpretations", []):
                if anchor not in anchors:
                    problem(f"no heading '#{anchor}' in interpretations.md")

            for diagnostic in diagnostics_in(case):
                severity, _, code = diagnostic.partition(":")
                if severity not in SEVERITIES or code not in codes:
                    problem(f"'{diagnostic}' is not severity:code with a code from codes.json")

            strict = case.get("strict", "same")
            if isinstance(strict, dict) and "rejected_by" in strict and strict["rejected_by"] not in codes:
                problem(f"rejected_by '{strict['rejected_by']}' is not in codes.json")

            if REFUSALS_REQUIRED:
                if case.get("expect", {}).get("refused") and "refusal" not in case["expect"]:
                    problem("a refused case must name its refusal code")
                if case.get("reencode") == "refused" and "reencode_refusal" not in case:
                    problem("reencode 'refused' needs reencode_refusal")

            if case.get("reencode") in ("equivalent", "rounded") and "canonical_info" not in case:
                problem(f"reencode '{case['reencode']}' needs canonical_info, the bytes an encoder writes")
            if "canonical_info" in case and case.get("reencode") not in ("equivalent", "rounded"):
                problem("canonical_info belongs with reencode 'equivalent' or 'rounded'")

            for key, value in (("refusal", case.get("expect", {}).get("refusal")),
                               ("reencode_refusal", case.get("reencode_refusal"))):
                if value is None:
                    continue
                named_refusals.add(value)
                if value not in refusal_ids:
                    problem(f"{key} '{value}' is not in the refusals list of codes.json")
                if value == FALLBACK:
                    problem(f"{key} names the fallback '{FALLBACK}', which no case may expect")

            tolerated = {
                d.partition(":")[2]
                for d in case.get("expect", {}).get("diagnostics", [])
                if d.startswith("warning:") and d.partition(":")[2] in tolerable
            }
            if isinstance(strict, dict) and len(tolerated) == 1:
                shown_both_sides |= tolerated

    for code in sorted(tolerable - shown_both_sides):
        problems.append(f"codes.json: tolerable code '{code}' has no case whose strict result differs because of it alone")

    if REFUSALS_REQUIRED:
        for rid in sorted(refusal_ids - named_refusals - EXEMPT_REFUSALS):
            problems.append(f"codes.json: refusal id '{rid}' is named by no case")

    made = subprocess.run([sys.executable, str(ROOT / "tools" / "precedence.py"), "--check"], capture_output=True, text=True)
    if made.returncode != 0:
        problems.append("cases/precedence.json: " + (made.stderr.strip() or "out of date"))

    for p in problems:
        print(p)
    print(f"{count} cases in {len(files)} files, {len(codes)} codes ({len(tolerable)} tolerable), "
          f"{len(refusal_ids)} refusal ids, {len(anchors)} interpretations: "
          + ("ok" if not problems else f"{len(problems)} problems"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
