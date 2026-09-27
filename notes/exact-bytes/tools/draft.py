"""Drafts a case's expect/strict from the pristine aprs-py decoder. Usage: import draft; draft.case(...)"""
import sys, json
sys.path.insert(0, '/home/tf/.claude/jobs/a4805be3/tmp/pristine-py/src')
from pdn_aprs import decode_tnc2, ParseOptions, HeaderError
from pdn_aprs.neutral import packet_to_neutral

def result(line, opts):
    try:
        return packet_to_neutral(decode_tnc2(line, opts))
    except HeaderError as e:
        return {"header_error": [str(d) for d in e.diagnostics]}

def case(cid, desc, source, authority, line, reencode, canonical=None, interpretations=None, file=None, info_only=False):
    raw = line if isinstance(line, bytes) else line.encode('utf-8')
    L = result(raw, ParseOptions.lenient()); S = result(raw, ParseOptions.strict())
    c = {"_file": file, "id": cid, "description": desc, "source": source, "authority": authority}
    if interpretations: c["interpretations"] = interpretations
    try:
        text = raw.decode('utf-8'); c["input"] = {"tnc2": text}
    except UnicodeDecodeError:
        c["input"] = {"tnc2_hex": raw.hex()}
    exp = {}
    if "header_error" in L:
        exp["header_error"] = L["header_error"]
    else:
        exp["data"] = L["data"]
        if L.get("diagnostics"): exp["diagnostics"] = L["diagnostics"]
    c["expect"] = exp
    if S == L:
        c["strict"] = "same"
    else:
        errs = [d.split(':',1)[1] for d in S.get("diagnostics", []) if d.startswith("error:")]
        if S.get("data", {}).get("type") == "unrecognized" and errs:
            c["strict"] = {"rejected_by": errs[0]}
        else:
            c["strict"] = {"data": S.get("data"), "diagnostics": S.get("diagnostics", [])}
    c["reencode"] = reencode
    if canonical is not None: c["canonical_info"] = canonical
    return c
