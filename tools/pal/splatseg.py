import yaml
def load(v):
    d=yaml.safe_load(open(f'/home/claude/papermario/ver/{v}/splat.yaml'))
    segs=d['segments']; out=[]
    def nm(x):
        if isinstance(x,dict): return x.get('start'),x.get('name'),x.get('type'),x.get('dir')
        return x[0],(x[2] if len(x)>2 and isinstance(x[2],str) else (x[1] if len(x)>1 else None)),(x[1] if len(x)>1 else None),None
    for s in segs:
        st,n,t,dr=nm(s)
        out.append((st,n,t,dr))
        if isinstance(s,dict) and 'subsegments' in s:
            for ss in s['subsegments']:
                a,b,c,e=nm(ss); out.append((a,b,c,e))
    return out
