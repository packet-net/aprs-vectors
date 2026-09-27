"""Quick encode-mode stand-in using the pristine aprs-py: data lines in, a summary out."""
import sys, json, gzip, collections
sys.path.insert(0, '/home/tf/.claude/jobs/a4805be3/tmp/pristine-py/src')
from pdn_aprs import decode_tnc2, ParseOptions, EncodeError, MicEReport, HeaderError
from pdn_aprs.neutral import from_neutral, to_neutral
from pdn_aprs.encode import encode_info, mic_e_destination
sys.path.insert(0, '/home/tf/src/aprs-vectors/tools')
from compare import key, norm
res=collections.Counter(); bad=collections.Counter(); ex={}
for line in gzip.open(sys.argv[1],'rt'):
    r=json.loads(line); d=r['data']; t=d['type']
    try:
        obj=from_neutral(d)
    except Exception as e:
        res[(t,'unsupported')]+=1; ex.setdefault((t,'unsupported',str(e)[:60]),line[:300]); continue
    try:
        info=encode_info(obj); dest=mic_e_destination(obj) if isinstance(obj,MicEReport) else 'APZ001'
    except EncodeError as e:
        res[(t,'refused')]+=1; ex.setdefault((t,'refused',str(e)[:70]),line[:300]); bad[(t,'refused: '+str(e)[:70])]+=1; continue
    except Exception as e:
        res[(t,'crash')]+=1; ex.setdefault((t,'crash',repr(e)[:70]),line[:300]); bad[(t,'crash: '+repr(e)[:70])]+=1; continue
    res[(t,'written')]+=1
    try:
        p=decode_tnc2(f'N0CALL>{dest}:'.encode()+info, ParseOptions.lenient())
    except HeaderError as e:
        bad[(t,'header error')]+=1; continue
    diags=[str(x) for x in p.diagnostics if not str(x).startswith('info:')]
    if diags:
        k=(t,'diags '+','.join(sorted(set(diags)))[:80]); bad[k]+=1; ex.setdefault(k,line[:300]+' => '+repr(info[:120])); continue
    if r['exact'] and key(to_neutral(p.data))!=key(d):
        a,b=norm(to_neutral(p.data)),norm(d)
        k=(t,'differs '+','.join(sorted(x for x in set(a)|set(b) if a.get(x)!=b.get(x))))
        bad[k]+=1; ex.setdefault(k,line[:300]+' => '+repr(info[:120]))
tot=sum(res.values())
print('results', collections.Counter({k[1]:v for k,v in res.items()}) , 'of', tot)
by=collections.Counter()
for (t,s),v in res.items(): by[s]+=v
print(by)
for k,v in bad.most_common(45): print(v, k)
json.dump({' | '.join(k):v for k,v in ex.items()}, open('pyenc.ex.json','w'), indent=0)
