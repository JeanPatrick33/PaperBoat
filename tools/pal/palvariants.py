#!/usr/bin/env python3
"""Add PAL-only map textures (per-language sign variants, localized gv__ letters)
to assets/yaml/pal/textures/*.yaml, include/assets/map_textures.h and MapTextureMeta.inc.c.
usage: palvariants.py <rom64.z64> <repo> [--dry]"""
import sys,re,struct,os
sys.path.insert(0,os.path.dirname(__file__))
from texarc import parse_tex
rom=open(sys.argv[1],'rb').read(); repo=sys.argv[2]; dry='--dry' in sys.argv
FM={(0,2):'RGBA16',(0,3):'RGBA32',(2,0):'CI4',(2,1):'CI8',(3,0):'IA4',(3,1):'IA8',(3,2):'IA16',(4,0):'I4',(4,1):'I8'}
metaf=repo+'/src/port/patches/MapTextureMeta.inc.c'
meta=open(metaf).read()
mnames=set(re.findall(r'\{ "(\w+)",',meta))
# archive of each name from yaml
yd=repo+'/assets/yaml/pal/textures/'
arc_of={}
for f in os.listdir(yd):
    a=f[:-5]
    for n in re.findall(r'^(\w+):\s*$',open(yd+f).read(),re.M): arc_of[n]=a
ents=parse_tex(rom,0x2D37C7E-0x30,0x200000)
def row(e,arc):
    aw,mw,ah,mh,var,extra,comb,fm,dp,hw,vw,flt=struct.unpack('>HHHHBBBBBBBB',e['hdr'])
    n=e['name']
    auxp=n+'_aux' if extra in (2,3) else 'NULL'
    return '    { "%s", %s, %s, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d },'%(
        n,n,auxp,mw,mh,fm&15,dp&15,hw&15,vw&15,flt,comb>>2,comb&3,extra,var,aw,ah,fm>>4,dp>>4,hw>>4,vw>>4,1 if extra==1 else 0)
# validate generator against existing rows
bad=0
cur=None
for e in ents:
    n=e['name']
    if n in arc_of: cur=arc_of[n]
    m=re.search(r'^\s*\{ "%s",.*\},$'%re.escape(n),meta,re.M)
    if m and re.sub(r'\s+',' ',m.group(0))!=re.sub(r'\s+',' ',row(e,cur)):
        bad+=1
        if bad<4: print('MISMATCH',m.group(0),'\n         ',row(e,cur))
print('row mismatches vs existing meta:',bad)
cur=None; prev=None; add=[]
for e in ents:
    n=e['name']
    if n in arc_of: cur=arc_of[n]
    if n not in mnames:
        assert e['hdr'][5]==0, n
        add.append((cur,prev,e))
    prev=n
print(len(add),'new textures')
for arc,prev,e in add:
    aw,mw,ah,mh,var,extra,comb,fm,dp,hw,vw,flt=struct.unpack('>HHHHBBBBBBBB',e['hdr'])
    print(arc,prev,'->',e['name'],FM[(fm&15,dp&15)],mw,mh,'var',var)
if dry: sys.exit()
# yaml + header + meta
hdr=open(repo+'/include/assets/map_textures.h').read()
pos=e_pal=None
for arc,prev,e in add:
    aw,mw,ah,mh,var,extra,comb,fm,dp,hw,vw,flt=struct.unpack('>HHHHBBBBBBBB',e['hdr'])
    n=e['name']; fmt=FM[(fm&15,dp&15)]
    main=e['parts'][0][1]
    line='%s:\n  { type: TEXTURE, format: %s, offset: 0x%X, width: %d, height: %d, symbol: %s }\n'%(n,fmt,main,mw,mh,n)
    pal=[p for p in e['parts'] if p[0]=='pal']
    if pal:
        t=pal[0][1]; cols=16 if fmt=='CI4' else 256
        line='%s:\n  { type: TEXTURE, format: %s, offset: 0x%X, width: %d, height: %d, tlut: 0x%X, symbol: %s }\n%s_tlut:\n  { type: TEXTURE, format: TLUT, offset: 0x%X, colors: %d, symbol: %s_tlut }\n'%(n,fmt,main,mw,mh,t,n,n,t,cols,n)
    open(yd+arc+'.yaml','a').write(line)
    hdr+='#if VERSION_PAL\nstatic const ALIGN_ASSET(2) char %s[] = "__OTR__textures/%s/%s";\n#endif\n'%(n,arc,n)
    # meta: insert after predecessor row inside archive array
    r=row(e,arc)
    pm=re.search(r'^\s*\{ "%s",.*\},$'%re.escape(prev),meta,re.M)
    assert pm,prev
    meta=meta[:pm.end()]+'\n#if VERSION_PAL\n'+r+'\n#endif'+meta[pm.end():]
open(metaf,'w').write(meta)
open(repo+'/include/assets/map_textures.h','w').write(hdr)
