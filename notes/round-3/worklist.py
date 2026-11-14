import gzip,json,collections,sys
sys.path.insert(0,'/home/tf/src/aprs-vectors-r3/tools')
from precedence import ORDER
rank={c:i for i,c in enumerate(ORDER)}
prefix,inpf=sys.argv[1],sys.argv[2]
libs=['cs','rs','py','ts','c','go']
recs={l:gzip.open(f'{prefix}.{l}.gz','rt') for l in libs}
per=collections.defaultdict(collections.Counter); ex={}
wr=collections.Counter(); wex={}
def locator_bad(x): return isinstance(x,str) and not (len(x) in (4,6) and x==x.upper())
for line in gzip.open(inpf,'rt'):
    r={l:json.loads(recs[l].readline()) for l in libs}
    inp=json.loads(line); d=inp['data']; typ=d.get('type')
    res={l:x.get('result') for l,x in r.items() if x.get('result')!='unsupported'}
    if len(set(res.values()))>1:
        k=(typ,tuple(sorted(l for l in res if res[l]=='written')),tuple(sorted(l for l in res if res[l]=='refused')))
        wr[k]+=1; wex.setdefault(k,line.strip()[:250]); continue
    if set(res.values())!={'refused'}: continue
    codes={l:r[l].get('refusal') for l in res}
    if len(set(codes.values()))<2: continue
    cand=set(codes.values())
    if typ=='status':
        if 'symbol' not in d: cand.discard('invalid-symbol')
        if locator_bad(d.get('locator')): cand.add('malformed')
    want=min(cand,key=lambda c:rank.get(c,99))
    for l,c in codes.items():
        if c!=want:
            k=(want,c,typ); per[l][k]+=1; ex.setdefault((l,)+k,line.strip()[:250])
print('Code-only differences in a fresh --faults encode run (libraries at main). Expected = the earliest code in the Refusal reasons order that any library gave, plus a lower-case or wrong-length status locator counted as malformed and no invalid-symbol for a status with no symbol (a heuristic: it assumes a library names a code only for a fault that is there).')
tot_lines={}
for l in libs:
    tot=sum(per[l].values()); tot_lines[l]=tot
    print(f'\n== {l}: {tot} lines, {len(per[l])} patterns')
    for (want,got,typ),v in per[l].most_common(30):
        print(f'  {v:5} [{typ}] gives {got}, order says {want}')
        print('          e.g.', ex[(l,want,got,typ)][:220])
print('\n== write versus refuse')
for k,v in wr.most_common(): print(f'  {v:4} [{k[0]}] written by {"+".join(k[1])}, refused by {"+".join(k[2])}\n          e.g. {wex[k][:220]}')
print('\nlines per library:', tot_lines, file=sys.stderr)
