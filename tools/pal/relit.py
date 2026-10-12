#!/usr/bin/env python3
"""usage: relit.py <decomp_file> <port_file> [--write]
Version PAL. Where the (PAL-resolved) port hardcodes a literal in place of a decomp macro / language table,
replace the port line by the decomp's unexpanded line (1:1 line replacements only, decomp line must use a
local macro or a D_PAL_ table)."""
import sys,re,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import vpp
from macrodiff_lib import expand,norm
dec,port=sys.argv[1:3]; outf=sys.argv[sys.argv.index('--out')+1] if '--out' in sys.argv else None
def lines(f): return vpp.process(open(f,errors='ignore').read(),vpp.defs_for('PAL')).split('\n')
dl=lines(dec); pl=open(port).read().split('\n')
# Only operate on the port's raw lines through resolved text: build raw->resolved line mapping by resolving PAL branch of port text
pr=lines(port)
def defs_of(v):
    t=vpp.process(open(dec,errors='ignore').read(),vpp.defs_for(v))
    return {m.group(1):m.group(2).strip() for m in re.finditer(r'(?m)^[ \t]*#[ \t]*define[ \t]+([A-Za-z_]\w*)[ \t]+(.+?)[ \t]*$',t)}
_dp=defs_of('PAL'); _du=defs_of('US')
diffnames=[k for k in _dp if _du.get(k)!=_dp[k]]
NAMERE=re.compile(r'\b('+'|'.join(map(re.escape,diffnames))+r'|D_PAL_\w+|D_filemenu_\w+|gCurrentLanguage)\b') if diffnames else re.compile(r'\b(D_PAL_\w+|D_filemenu_\w+|gCurrentLanguage)\b')
def nl(l): return norm(expand(l))
dn=[nl(l) for l in dl]; pn=[nl(l) for l in pr]
sm=difflib.SequenceMatcher(None,[ ''.join(x) for x in dn],[''.join(x) for x in pn],autojunk=False)
out=list(pr); n=0
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='replace' and (i2-i1)==(j2-j1):
        for k in range(i2-i1):
            d=dl[i1+k]; p=pr[j1+k]
            if NAMERE.search(d) and d.strip()!=p.strip():
                out[j1+k]=d; n+=1
                print('%d: %s\n   -> %s'%(j1+k+1,p.strip()[:110],d.strip()[:110]))
print('replaced',n)
if outf: open(outf,'w').write('\n'.join(out))
