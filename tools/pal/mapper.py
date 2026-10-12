import bisect, numpy as np
R='/tmp/claude-0/-home-claude/af314175-1a19-56c5-80ed-8807f421a7da/scratchpad/'
US=open(R+'romus/pm64_us.z64','rb').read()
PAL=open(R+'rom/pm64_pal.z64','rb').read()
PAL=PAL+PAL[0x2000000:0x3000000]
ex=sorted(tuple(map(int,l.split())) for l in open('/home/claude/work/extents.txt'))
good=[e for e in ex if e[2]>=0x60]
gstarts=[e[0] for e in good]
from mapfs import parse as _pm
_u=_pm(US,0x1e40000); _p=_pm(PAL,0x2600000)
MAPFS=[]
for (n,o,c,sz,_),(n2,o2,c2,sz2,_2) in zip(_u,_p):
    assert n==n2
    MAPFS.append((0x1e40020+o,0x1e40020+o+max(c,sz),0x2600000+o2-(0x1e40000+o),n,c==c2 and sz==sz2))
MAPFS.sort()
USF={n:(0x1e40020+o,max(c,sz)) for n,o,c,sz,_ in _u}
PALF={n:(0x2600020+o,max(c,sz)) for n,o,c,sz,_ in _p}
_ms=[m[0] for m in MAPFS]
def mapfs_file(a):
    i=bisect.bisect_right(_ms,a)-1
    if i>=0 and a<MAPFS[i][1]: return MAPFS[i]
def cand_deltas(a,win=0x30000,maxn=24):
    m=mapfs_file(a)
    if m: return [m[2]]
    i=bisect.bisect_left(gstarts,a)
    ds=[]
    j=i-1
    while j>=0 and a-good[j][0]<win and len(ds)<maxn:
        ds.append(good[j][1]-good[j][0]); j-=1
    j=i
    while j<len(good) and good[j][0]-a<win and len(ds)<2*maxn:
        ds.append(good[j][1]-good[j][0]); j+=1
    # always include nearest ones beyond window
    for j in (i-1,i):
        if 0<=j<len(good): ds.append(good[j][1]-good[j][0])
    out=[]
    for d in ds:
        if d not in out: out.append(d)
    return out
def score(a,n,d):
    if a+d<0 or a+d+n>len(PAL): return 0.0
    n&=~3
    if n<=0: return 0.0
    x=np.frombuffer(US,dtype='>u4',count=n//4,offset=a & ~3) if a%4==0 else None
    u=US[a:a+n]; p=PAL[a+d:a+d+n]
    if (a%4)==0 and (d%4)==0:
        x=np.frombuffer(u,dtype='>u4'); y=np.frombuffer(p,dtype='>u4')
        return float((x==y).mean())
    xa=np.frombuffer(u,dtype=np.uint8); ya=np.frombuffer(p,dtype=np.uint8)
    return float((xa==ya).mean())
def best(a,n,cap=0x800,**kw):
    n=min(max(n,16),cap)
    best=(None,0.0)
    for d in cand_deltas(a,**kw):
        s=score(a,n,d)
        if s>best[1]: best=(d,s)
    return best

def _needle(a,n):
    n=min(n,0x400)
    for k in range(0,max(1,n-31),4):
        w=US[a+k:a+k+32]
        if len(w)==32 and len(set(w))>=8: return k,w
    return None
def search_near(a,n,center_delta,radius=0x200000,maxhits=40):
    nd=_needle(a,n)
    if not nd: return None,0.0
    k,w=nd
    lo=max(0,a+center_delta-radius); hi=min(len(PAL),a+center_delta+radius)
    bestd,bests=None,0.0
    pos=lo; hits=0
    while hits<maxhits:
        h=PAL.find(w,pos,hi)
        if h<0: break
        d=h-k-a
        s=score(a,min(max(n,16),0x800),d)
        if s>bests or (s==bests and bestd is not None and abs(d-center_delta)<abs(bestd-center_delta)): bestd,bests=d,s
        hits+=1; pos=h+1
    return bestd,bests
def best2(a,n,cap=0x800):
    d,s=best(a,n,cap)
    if s>=0.95: return d,s,'cand'
    cds=cand_deltas(a)
    cd=d if d is not None else (cds[0] if cds else 0)
    d2,s2=search_near(a,n,cd)
    if d2 is not None and s2>s: return d2,s2,'search'
    return d,s,'cand'

from texarc import parse_tex
_texcache={}
def _tex(rom,key,start,size):
    k=(key,start)
    if k not in _texcache: _texcache[k]=parse_tex(rom,start,size)
    return _texcache[k]
def tex_map(a):
    """map absolute US address inside a *_tex mapfs file to PAL by texture name/role. returns (pal_addr,status) or None"""
    m=mapfs_file(a)
    if not m or not m[3].endswith('_tex'): return None
    n=m[3]
    us,usz=USF[n]; ps,psz=PALF[n]
    ut=_tex(US,'us'+n,us,usz); pt={t['name']:t for t in _tex(PAL,'pal'+n,ps,psz)}
    for t in ut:
        if t['start']<=a<t['end']:
            pt_=pt.get(t['name'])
            if not pt_: return None
            rel=a-t['start']
            # same header & same layout -> same relative offset
            if pt_['end']-pt_['start']==t['end']-t['start'] and pt_['hdr']==t['hdr']:
                return pt_['start']+rel,'name-same'
            # otherwise match by part role
            for role,off,l,*_ in t['parts']:
                if off<=a<off+l:
                    for r2,o2,l2,*_ in pt_['parts']:
                        if r2==role: return o2+(a-off),'name-role-diff-layout'
            return pt_['start']+rel,'name-hdr'
    return None

from splatseg import load as _sl
def _segtab(v):
    L=[(s,n,t) for s,n,t,_ in _sl(v) if isinstance(s,int)]
    return L
_USS=_segtab('us'); _PALS=_segtab('pal')
_pname={}
for s,n,t in _PALS:
    if n: _pname.setdefault(n,s)
_USS.sort(key=lambda x:x[0]); _usst=[x[0] for x in _USS]
def seg_delta(a):
    i=bisect.bisect_right(_usst,a)-1
    while i>=0:
        s,n,t=_USS[i]
        if n and n in _pname: return _pname[n]-s
        i-=1
    return None
_old_cd=cand_deltas
def cand_deltas(a,win=0x30000,maxn=24):
    out=_old_cd(a,win,maxn)
    sd=seg_delta(a)
    if sd is not None and sd not in out and not mapfs_file(a): out=[sd]+out
    return out

# ---- splat-name based mapping (exact for named assets) ----
from layout import simulate, IMGSZ
import collections as _c
def _tab(v):
    res,_=simulate(v)
    occ=_c.defaultdict(list)
    for e in res:
        if e['name'] and e['sim'] is not None and isinstance(e['sim'],int) and e['type'] is not None and not str(e['type']).startswith('SEG:'):
            occ[(e['type'],e['name'])].append(e['sim'])
    return occ
_UO=_tab('us'); _PO=_tab('pal')
_U2K={}
for k,l in _UO.items():
    for i,a in enumerate(l): _U2K.setdefault(a,(k,i))
def splat_map(a):
    r=_U2K.get(a)
    if not r: return None
    k,i=r
    pl=_PO.get(k)
    if pl and len(pl)==len(_UO[k]): return pl[i]
    if pl and i<len(pl): return pl[i]
    return None
