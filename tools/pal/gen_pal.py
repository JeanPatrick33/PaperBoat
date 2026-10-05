import sys,os,re,glob,json,collections,shutil
sys.path.insert(0,'/home/claude/work')
from convert import *
SRC='/home/claude/PaperBoat/assets/yaml/us'
DST='/home/claude/PaperBoat/assets/yaml/pal'
THR=0.5
def inherit(emap):
    items=sorted(((v,k,ak) for (k,ak),(p,sc,v) in emap.items()),key=lambda x:x[0])
    res={}
    for i,(v,k,ak) in enumerate(items):
        p,sc,_=emap[(k,ak)]
        if p is not None and sc>=THR: continue
        # neighbors
        prev=next((items[j] for j in range(i-1,max(-1,i-6),-1) if emap[(items[j][1],items[j][2])][1]>=0.95 and emap[(items[j][1],items[j][2])][0] is not None),None)
        nxt=next((items[j] for j in range(i+1,min(len(items),i+6)) if emap[(items[j][1],items[j][2])][1]>=0.95 and emap[(items[j][1],items[j][2])][0] is not None),None)
        dp=dn=None
        if prev and v-prev[0]<=0x2000: pe=emap[(prev[1],prev[2])]; dp=pe[0]-pe[2]
        if nxt and nxt[0]-v<=0x2000: ne=emap[(nxt[1],nxt[2])]; dn=ne[0]-ne[2]
        if dp is not None and dp==dn: res[(k,ak)]=(v+dp,0.6,v,'inherit-both')
        elif dp is not None and v-prev[0]<=0x400: res[(k,ak)]=(v+dp,0.55,v,'inherit-prev')
        elif dn is not None and nxt[0]-v<=0x400: res[(k,ak)]=(v+dn,0.55,v,'inherit-next')
    return res
def hx(n,like):
    s='%X'%n
    w=len(like)-2
    return '0x'+s.rjust(w,'0')
flag=[]; stats=collections.Counter()
def process(f):
    rel=os.path.relpath(f,SRC)
    d,c,segs,segmap,emap,vmap=convert_file(f)
    inh=inherit(emap)
    final={}
    for key,(p,sc,v) in emap.items():
        if key in inh: p,sc,v,tag=inh[key]; 
        final[key]=(p,sc,v)
    out=[]; cur=None
    lines=open(f).read().split('\n')
    segidx=0
    for ln in lines:
        m=re.match(r'^([^\s#][^:]*):\s*$',ln)
        if m and m.group(1)!=':config': cur=m.group(1)
        mm=re.match(r'^(\s*- \[)(0x[0-9A-Fa-f]+|\d+), (0x[0-9A-Fa-f]+|\d+)\](.*)$',ln)
        if mm and cur is None:
            s=int(mm.group(2),0); b=int(mm.group(3),0)
            if s in segmap:
                pb,sc=segmap[s]
                if pb is not None and sc>=0.9:
                    ln=f"{mm.group(1)}{mm.group(2)}, {hx(pb,mm.group(3))}]{mm.group(4)}"; stats['seg']+=1
                else:
                    flag.append((rel,'SEG',hex(b),pb and hex(pb),round(sc,2))); stats['seg_flag']+=1
        vm=re.match(r'^(\s*virtual: \[)(0x[0-9A-Fa-f]+), (0x[0-9A-Fa-f]+)\](.*)$',ln)
        if vm:
            if vmap and vmap[1] is not None and vmap[2]>=THR:
                ln=f"{vm.group(1)}{vm.group(2)}, {hx(vmap[1],vm.group(3))}]{vm.group(4)}"; stats['virt']+=1; vromold=int(vm.group(3),0); vromnew=vmap[1]
            else: flag.append((rel,'VIRT',vm.group(3),None,0)); stats['virt_flag']+=1
        if '{ type:' in ln and cur is not None:
            def rep(mo):
                ak=mo.group(1); val=mo.group(2); v=int(val,0)
                ent=final.get((cur,ak))
                if ent is None: return mo.group(0)   # segmented or n/a
                p,sc,v0=ent
                assert v0==v,(rel,cur,ak,hex(v0),val)
                if p is not None and sc>=THR:
                    stats['ent' if sc>=0.9 else 'ent_mid']+=1
                    return f"{ak}: {hx(p,val)}"
                flag.append((rel,cur,ak,val,p and hex(p),round(sc,2))); stats['ent_flag']+=1
                return mo.group(0)
            ln=re.sub(r'\b(offset|tlut|raster_header|raster_sets|raster_descriptors|raster_image_data): (0x[0-9A-Fa-f]+)',rep,ln)
        out.append(ln)
    text='\n'.join(out)
    # comment ROM addresses for overlays
    if vmap and vmap[1] is not None:
        text=re.sub(r'ROM: 0x[0-9A-Fa-f]+',lambda m:'ROM: '+hx(vmap[1],m.group(0)[5:]),text)
    dst=os.path.join(DST,rel); os.makedirs(os.path.dirname(dst),exist_ok=True)
    open(dst,'w').write(text)
if __name__=='__main__':
    if os.path.exists(DST): shutil.rmtree(DST)
    for f in sorted(glob.glob(SRC+'/**/*.y*ml',recursive=True)):
        if f.endswith('messages.yml'):
            continue
        process(f)
    import shutil as sh
    for f in glob.glob('/home/claude/work/overrides/**/*.y*ml',recursive=True):
        rel=os.path.relpath(f,'/home/claude/work/overrides'); os.makedirs(os.path.dirname(os.path.join(DST,rel)),exist_ok=True); sh.copy(f,os.path.join(DST,rel))
    print(stats); json.dump(flag,open('/home/claude/work/flag.json','w'),indent=0)
    print(len(flag)); 
    for x in flag[:80]: print(x)
