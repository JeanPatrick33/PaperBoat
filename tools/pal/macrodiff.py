#!/usr/bin/env python3
"""usage: macrodiff.py <decomp_file> <port_file> [PAL|US]
Resolves VERSION_* conditionals, expands the file-local object-like #defines of the decomp file and
diffs the result against the (also resolved) port file. Shows where the port hardcodes values of another
version (decomp 'PAL' result != port)."""
import sys,re,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import vpp
dec,port=sys.argv[1:3]; ver=sys.argv[3] if len(sys.argv)>3 else 'PAL'
def load(f,v): return vpp.process(open(f,errors='ignore').read(),vpp.defs_for(v))
def expand(t):
    defs={}
    for m in re.finditer(r'(?m)^[ \t]*#[ \t]*define[ \t]+([A-Za-z_]\w*)[ \t]+(.+?)[ \t]*$',t):
        v=re.sub(r'/\*.*?\*/|//.*','',m.group(2)).strip()
        if v and not v.endswith('\\'): defs[m.group(1)]=v
    lines=[l for l in t.split('\n') if not re.match(r'\s*#\s*(define|undef)\b',l)]
    s='\n'.join(lines)
    for _ in range(4):
        for k,v in defs.items(): s=re.sub(r'\b%s\b'%re.escape(k),'('+v+')' if not re.fullmatch(r'-?\w+',v) else v,s)
    return s
def norm(s):
    out=[]
    for l in s.split('\n'):
        l=re.sub(r'//.*','',l); l=re.sub(r'\s+','',l); l=l.replace('(','').replace(')','')
        l=re.sub(r'\b0x([0-9A-Fa-f]+)\b',lambda m:str(int(m.group(1),16)),l)
        l=re.sub(r'\b(\d+)[fF]\b',r'\1',l)
        if l and not l.startswith('#'): out.append(l)
    return out
a=norm(expand(load(dec,ver))); b=norm(expand(load(port,ver)))
for l in difflib.unified_diff(a,b,'decomp','port',lineterm='',n=0):
    print(l)
