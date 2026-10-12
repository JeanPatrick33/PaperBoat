# usage: fnmerge.py <port_file> <decomp_file> <func_signature_regex> -> prints merged function (port US + decomp US->PAL delta)
import sys,re,subprocess,tempfile,os
sys.path.insert(0,'/home/claude/work')
from vpp import process,defs_for
def getfn(text,sig):
    m=re.search(sig,text,re.M)
    if not m: return None
    i=text.index('{',m.end()-1 if text[m.end()-1]=='{' else m.end())
    d=0;j=i
    while True:
        c=text[j]
        if c=='{':d+=1
        elif c=='}':
            d-=1
            if d==0:break
        j+=1
    return text[m.start():j+1]
port,dec,sig=sys.argv[1:4]
pt=open(port).read(); dt=open(dec).read()
pt_us=process(pt,defs_for('US')); 
us=getfn(process(dt,defs_for('US')),sig); pal=getfn(process(dt,defs_for('PAL')),sig); po=getfn(pt_us,sig)
d=tempfile.mkdtemp()
for n,t in (('o',po),('b',us),('t',pal)): open(d+'/'+n,'w').write(t+'\n')
r=subprocess.run(['git','merge-file','-p','-L','port','-L','decomp_us','-L','decomp_pal',d+'/o',d+'/b',d+'/t'],capture_output=True,text=True)
sys.stdout.write(r.stdout); sys.stderr.write(f'conflicts={r.returncode}\n')
