import json, sys
from collections import defaultdict
def one(v): return json.dumps(v, separators=(', ', ': '))
def fmt(c):
    lines=[]
    for k,v in c.items():
        if k=='expect' and isinstance(v,dict):
            inner=',\n'.join(f'        {json.dumps(ek)}: {one(ev)}' for ek,ev in v.items())
            lines.append(f'      "expect": {{\n{inner}\n      }}')
        else:
            lines.append(f'      {json.dumps(k)}: {one(v)}')
    return '    {\n'+',\n'.join(lines)+'\n    }'
cases=json.load(open(sys.argv[1]))
by=defaultdict(list)
for c in cases:
    f=c.pop('_file'); by[f].append(c)
for f,cs in by.items():
    p='cases/'+f; s=open(p).read()
    ids={c['id'] for c in json.loads(s)['cases']}
    for c in cs: assert c['id'] not in ids, c['id']
    end=s.rstrip().rindex('\n  ]')
    body=s[:end].rstrip()
    assert body.endswith('}')
    s=body+',\n'+',\n'.join(fmt(c) for c in cs)+'\n  ]\n}\n'
    json.loads(s); open(p,'w').write(s)
    print(p, len(cs))
