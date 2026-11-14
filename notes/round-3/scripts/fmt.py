import json
def j(v): return json.dumps(v, ensure_ascii=False)
def fmt_case(c):
    lines = ['    {']
    items = list(c.items())
    for i, (k, v) in enumerate(items):
        comma = ',' if i < len(items) - 1 else ''
        if k == 'expect' and isinstance(v, dict) and v:
            lines.append(f'      "{k}": {{')
            sub = list(v.items())
            for m, (k2, v2) in enumerate(sub):
                lines.append(f'        "{k2}": {j(v2)}' + (',' if m < len(sub) - 1 else ''))
            lines.append('      }' + comma)
        else:
            lines.append(f'      "{k}": {j(v)}{comma}')
    lines.append('    }')
    return '\n'.join(lines)
def fmt_doc(doc):
    return '{\n  "cases": [\n' + ',\n'.join(fmt_case(c) for c in doc['cases']) + '\n  ]\n}\n'
if __name__ == '__main__':
    import glob, sys
    for f in sorted(glob.glob('/home/tf/src/aprs-vectors-r3/cases/*.json')):
        t = open(f, encoding='utf-8').read()
        print(f, fmt_doc(json.loads(t)) == t)
