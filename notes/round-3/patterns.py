import gzip,json,sys,collections
sys.path.insert(0,'/home/tf/src/aprs-vectors-r3/tools')
from precedence import ORDER
rank={c:i for i,c in enumerate(ORDER)}
prefix,inp=sys.argv[1],sys.argv[2]
libs=['cs','rs','py','ts','c','go']
recs={l:gzip.open(f'{prefix}.{l}.gz','rt') for l in libs}
ins=gzip.open(inp,'rt')
pat=collections.Counter(); ex={}; wr=collections.Counter(); wex={}
per=collections.Counter()
for line in ins:
    r={l:json.loads(recs[l].readline()) for l in libs}
    inp_rec=json.loads(line)
    typ=(inp_rec.get('data') or {}).get('type') or inp_rec.get('report')
    res={l:x.get('result') for l,x in r.items() if x.get('result')!='unsupported'}
    if len(res)<2: continue
    if len(set(res.values()))>1:
        key=(typ,)+tuple(sorted((v,tuple(sorted(l for l in res if res[l]==v))) for v in set(res.values())))
        wr[key]+=1; wex.setdefault(key,line.strip()[:300]); continue
    if set(res.values())!={'refused'}: continue
    codes={l:r[l].get('refusal') for l in res}
    if len(set(codes.values()))<2: continue
    want=min(set(codes.values()),key=lambda c:rank.get(c,99))
    d=inp_rec.get('data') or {}
    if d.get('type')=='status' and isinstance(d.get('locator'),str) and d['locator']!=d['locator'].upper(): want='malformed'
    out=tuple(sorted(l for l in codes if codes[l]!=want))
    got=tuple(sorted(set(codes[l] for l in out)))
    key=(typ,want,got,out)
    pat[key]+=1; ex.setdefault(key,line.strip()[:400])
    for l in out: per[l]+=1
print('code-only patterns (expected by R1 = earliest code reported):')
for k,v in pat.most_common(40):
    print(f'{v:5} [{k[0]}] want {k[1]}; {"+".join(k[3])} give {",".join(k[2])}')
    print('       ', ex[k][:260])
print('per library lines outside:',dict(per))
print('write-vs-refuse:')
for k,v in wr.most_common(15): print(v,k); print('       ',wex[k][:260])
