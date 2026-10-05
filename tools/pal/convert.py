import glob,yaml,re,sys,json,os,collections
sys.path.insert(0,'/home/claude/work')
from mapper import *
SRC='/home/claude/PaperBoat/assets/yaml/us'
BPP={'RGBA32':32,'RGBA16':16,'IA16':16,'IA8':8,'IA4':4,'I8':8,'I4':4,'CI8':8,'CI4':4}
def esize(e):
    t=e.get('type')
    if t=='TEXTURE':
        if e['format']=='TLUT': return e['colors']*2
        return e['width']*e['height']*BPP[e['format']]//8
    if t in('BLOB','PM64:AUDIO','PM64:CHARSET','PM64:TITLE_DATA'): return e.get('size',64)
    if t=='VTX': return e.get('count',1)*16
    if t=='MTX': return 64
    if t=='GFX': return e.get('size',64)
    if t=='LIGHTS': return 24
    if t=='VEC3S': return e.get('count',1)*6
    return 64
ADDR_KEYS=('offset','tlut','raster_header','raster_sets','raster_descriptors','raster_image_data')
def is_ident_seg(s,b): return b==(s<<24)
def convert_file(f):
    d=yaml.safe_load(open(f)); c=d.pop(':config',None) or {}
    segs={s[0]:s[1] for s in c.get('segments',[])}
    ident={s for s,b in segs.items() if is_ident_seg(s,b)}
    # sizes per segment span
    span=collections.defaultdict(int)
    for k,e in d.items():
        if not isinstance(e,dict) or 'offset' not in e: continue
        s=e['offset']>>24
        if s in segs and s not in ident:
            span[s]=max(span[s],(e['offset']&0xFFFFFF)+esize(e))
    segmap={}
    for s,b in segs.items():
        if s in ident: continue
        n=min(span.get(s,0x400),0x800) or 0x400
        dl,sc,_m=best2(b,n)
        segmap[s]=(b+dl if dl is not None else None, sc)
    emap={}
    for k,e in d.items():
        if not isinstance(e,dict): continue
        for ak in ADDR_KEYS:
            if ak not in e: continue
            v=e[ak]; s=v>>24
            if s in segs and s not in ident and ak in('offset','tlut'): continue  # segmented
            n=esize(e) if ak=='offset' else 64
            tm=tex_map(v)
            if tm:
                pa,_st=tm; sc=score(v,min(max(n,16),0x800),pa-v); emap[(k,ak)]=(pa,max(sc,0.95) if _st=='name-same' else sc,v); continue
            dl,sc,_m=best2(v,n)
            sp=splat_map(v)
            if sp is not None:
                s2=score(v,min(max(n,16),0x800),sp-v)
                if sc<0.95 or s2>=0.95 or sp-v!=dl:
                    # prefer the splat name when alignment is weak or ambiguous (duplicated content)
                    if s2>=sc or s2>=0.9 or sc<0.5: dl,sc=sp-v,max(s2,0.9) if s2>=0.5 else 0.7
            if sc<0.5:
                mf=mapfs_file(v)
                if mf: dl,sc=mf[2],0.6   # file layout identical per mapfs table; contents localized
            emap[(k,ak)]=(v+dl if dl is not None else None, sc, v)
    virt=c.get('virtual')
    vmap=None
    if virt:
        rom=virt[1]; dl,sc,_m=best2(rom,0x400); vmap=(virt[0],rom+dl if dl is not None else None,sc)
    return d,c,segs,segmap,emap,vmap
if __name__=='__main__':
    stats=collections.Counter(); low=[]
    for f in sorted(glob.glob(SRC+'/**/*.y*ml',recursive=True)):
        if f.endswith('messages.yml'): continue
        d,c,segs,segmap,emap,vmap=convert_file(f)
        for s,(pb,sc) in segmap.items():
            stats['seg_ok' if pb and sc>=0.9 else 'seg_bad']+=1
            if not(pb and sc>=0.9): low.append((f.split('us/')[1],'SEG',s,hex(segs[s]),pb and hex(pb),round(sc,2)))
        for (k,ak),(p,sc,v) in emap.items():
            stats['ok' if p and sc>=0.9 else ('mid' if p and sc>=0.5 else 'bad')]+=1
            if not(p and sc>=0.9): low.append((f.split('us/')[1],k,ak,hex(v),p and hex(p),round(sc,2)))
        if vmap: stats['virt_ok' if vmap[1] and vmap[2]>=0.9 else 'virt_bad']+=1
    print(stats)
    json.dump(low,open('low.json','w'))
    cat=collections.Counter(x[0].split('/')[0] for x in low); print(cat.most_common(30))
