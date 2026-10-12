import yaml
IMGSZ={'ci4':lambda w,h:w*h//2,'ci8':lambda w,h:w*h,'ia4':lambda w,h:w*h//2,'ia8':lambda w,h:w*h,'ia16':lambda w,h:w*h*2,'i4':lambda w,h:w*h//2,'i8':lambda w,h:w*h,'rgba16':lambda w,h:w*h*2,'rgba32':lambda w,h:w*h*4}
def entries(v):
    d=yaml.safe_load(open(f'/home/claude/papermario/ver/{v}/splat.yaml'))
    out=[]
    def rec(items,top,dirs):
        for it in items:
            if isinstance(it,list):
                off=it[0]; typ=it[1] if len(it)>1 else None
                name=it[2] if len(it)>2 and isinstance(it[2],str) else None
                args=it[3:]
                out.append(dict(off=off,type=typ,name=name,args=args,top=top))
            elif isinstance(it,dict):
                nm=it.get('name') or it.get('dir')
                if 'subsegments' in it:
                    out.append(dict(off=it.get('start','auto'),type='SEG:'+str(it.get('type')),name=nm,args=[],top=nm))
                    rec(it['subsegments'],nm,dirs)
                else:
                    out.append(dict(off=it.get('start','auto'),type=it.get('type'),name=nm,args=[],top=top))
    rec(d['segments'],None,[])
    return out
def simulate(v):
    E=entries(v); cur=None; lastimg=None; res=[]; issues=[]
    for e in E:
        off=e['off']
        if off=='auto':
            e['sim']=cur
        else:
            if cur is not None and e['type'] in IMGSZ or e['type']=='palette':
                if cur is not None and off!=cur and e['top'] is not None: issues.append((e['name'],hex(off),hex(cur)))
            e['sim']=off; cur=off
        t=e['type']
        if t in IMGSZ and len(e['args'])>=2 and isinstance(e['args'][0],int):
            sz=IMGSZ[t](e['args'][0],e['args'][1]); lastimg=t; e['size']=sz; cur=(e['sim'] or 0)+sz
        elif t=='palette':
            sz=0x20 if lastimg in ('ci4',) else 0x200 if lastimg=='ci8' else 0x20
            e['size']=sz; cur=(e['sim'] or 0)+sz
        else:
            e['size']=None
            if str(t).startswith('SEG:') and off!='auto': cur=off
            elif str(t).startswith('SEG:'): pass
            else: cur=None
        res.append(e)
    return res,issues
