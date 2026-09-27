"""Edits cases in place by id, keeping each file's formatting: set reencode, set or drop canonical_info."""
import json, glob, re, sys
ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'

def one(v): return json.dumps(v, ensure_ascii=False, separators=(', ', ': '))

def edit(case_id, reencode=None, canonical=..., ):
    for p in sorted(glob.glob(f'{ROOT}/cases/*.json')):
        s = open(p, encoding='utf-8').read()
        m = re.search(r'\n(\s*)"id": ' + re.escape(json.dumps(case_id)) + r',?\n', s)
        if not m:
            continue
        indent = m.group(1)
        start = s.rfind('\n', 0, m.start()) + 1  # the line with "{"
        close = re.compile(r'\n' + indent[:-2] + r'\}')
        end = close.search(s, m.end()).start()
        block = s[start:end]
        lines = block.split('\n')
        if reencode is not None:
            found = False
            for i, l in enumerate(lines):
                if l.strip().startswith('"reencode":'):
                    lines[i] = re.sub(r'"reencode": "[a-z]+"', f'"reencode": "{reencode}"', l); found = True
            assert found, case_id
        if canonical is not ...:
            idx = [i for i, l in enumerate(lines) if l.strip().startswith('"canonical_info":')]
            for i in reversed(idx):
                del lines[i]
            if canonical is not None:
                lines.append(f'{indent}"canonical_info": {one(canonical)}')
            # fix trailing commas: every line but the last key line ends with ','
            keylines = [i for i, l in enumerate(lines) if re.match(r'^' + indent + r'"[a-z_]+":', l)]
            # rebuild: ensure commas between top-level keys
            out = []
            for i, l in enumerate(lines):
                out.append(l)
            text = '\n'.join(out)
            # normalise: remove comma at the very end, then add commas before each top-level key line
            parts = re.split(r'\n(?=' + indent + r'"[a-z_]+":)', text)
            parts = [x.rstrip().rstrip(',') for x in parts]
            text = parts[0] + '\n' + ',\n'.join(parts[1:]) if len(parts) > 1 else parts[0]
            lines = text.split('\n')
        s = s[:start] + '\n'.join(lines) + s[end:]
        json.loads(s)
        open(p, 'w', encoding='utf-8').write(s)
        return p
    raise SystemExit(f'no case {case_id}')
