import re,os
O='/home/claude/work/overrides'
src=open('/home/claude/PaperBoat/assets/yaml/pal/level_up.yml').read() if False else None
def ent(name,typ,off,sym,**kw):
    extra=''.join(f', {k}: {v}' for k,v in kw.items())
    return f"{name}:\n  {{ type: {typ}, offset: 0x{off:X}{extra}, symbol: {sym} }}\n"
# ---------- main overlay (textures) ----------
t=["# PAL level-up overlay: textures (ver/pal/splat.yaml 'level_up', rom 0x7F2BE0 vram 0x802A1000)\n\n:config:\n  virtual: [0x802A1000, 0x7F2BE0]\n\n"]
def tex(name,off,w,h,pre='level_up'):
    return ent(name,'TEXTURE',off,f"{pre}_{name.replace('.','_')}_png",format='CI4',width=w,height=h)
def pal(name,off,pre='level_up'):
    return ent(name+'.pal','TEXTURE',off,f"{pre}_{name.replace('.','_')}_pal",format='TLUT',colors=16)
src=open('/home/claude/papermario/ver/pal/splat.yaml').read().split('\n')
i=next(k for k,l in enumerate(src) if l.strip()=='name: level_up' and 'code' in src[k-1]) 
rows=[]
for l in src[i:]:
    m=re.match(r'\s+- \[0x([0-9A-F]+)(?:, (\w+), ([\w/.]+)(?:, (\d+), (\d+))?)?\]',l)
    if l.startswith('  - type: code') and rows and 'level_up_letters' in ''.join(src[src.index(l):src.index(l)+2]): break
    if m and m.group(2): rows.append((int(m.group(1),16),m.group(2),m.group(3),m.group(4),m.group(5)))
for off,ty,nm,w,h in rows:
    base=nm.split('/')
    if ty=='ci4':
        key='_'.join(base[:-1]+[base[-1]]) if base[0] in('de','fr','es') else base[-1]
        pre='level_up'
        if base[0] in ('de','fr','es'): key=f"{base[0]}_{base[-1]}"
        t.append(tex(key,off,w,h))
    elif ty=='palette':
        key=(f"{base[0]}_{base[-1]}" if base[0] in('de','fr','es') else base[-1])
        t.append(pal(key,off))
open(f'{O}/level_up.yml','w').write(''.join(t))
# ---------- letters ----------
def letters(fn,lights,rom,vram,vtxs,imgs,gfxs,dls,pre):
    o=[f"# PAL level-up letters ({fn}): rom 0x{rom:X} vram 0x{vram:X}\n\n:config:\n  virtual: [0x{vram:X}, 0x{rom:X}]\n\n"]
    o.append(ent('lights','LIGHTS',lights,f'{pre}_lights_data'))
    for n,off in vtxs: o.append(ent(n,'VTX',off,f'{pre}_{n}_vtx',count=8))
    for n,off,w,h,fmt in imgs: o.append(ent(n,'TEXTURE',off,f'{pre}_{n}_png',format=fmt,width=w,height=h))
    for n,off in gfxs: o.append(ent(n+'.gfx','GFX',off,f'{pre}_{n}_gfx'))
    for n,off in dls: o.append(ent(n+'.gfx','GFX',off,f'{pre}_{n}_gfx'))
    open(f'{O}/{fn}.yml','w').write(''.join(o))
# en_de
names=['second_E','V','E','second_L','L','P','U','exclamation_mark']
vt=[(f'draw_{n}',0x7F8018+0x80*k) for k,n in enumerate(names)]
bigs=['V','P','exclamation_mark','U','L','E']
im=[(f'big_{n}',0x7F8418+0x1078*k,64,64,'IA8') for k,n in enumerate(bigs)]
gf=[(f'big_{n}',0x7F9418+0x1078*k) for k,n in enumerate(bigs)]
dn=['exclamation_mark','U','P','L','second_L','E','V','second_E']
dl=[(f'draw_{n}',0x7FE6E8+0x68*k) for k,n in enumerate(dn)]+[('letters_chain',0x7FEA28),('chain',0x7FEA88)]
letters('level_up_letters_en_de',0x7F8000,0x7F8000,0x802A6420,vt,im,gf,dl,'level_up')
# fr
frn=['NI','VE','AU','SU','PE','RI','EU','R_exclamation_mark']
vt=[(f'draw_{n}',0x7FEAE8+0x80*k) for k,n in enumerate(frn)]
sizes={'NI':54,'VE':52,'AU':55,'SU':55,'RI':55,'EU':55,'R_exclamation_mark':56}
offs={'NI':0x7FEEE8,'VE':0x7FFC68,'AU':0x800968,'SU':0x801728,'RI':0x8024E8,'EU':0x8032A8,'R_exclamation_mark':0x804068}
im=[(f'big_{n}',offs[n],64,sizes[n],'IA8') for n in offs]+[('big_PE',0x804E68,64,32,'IA16')]
gf=[(f'big_{n}',0x805E68+0x78*k) for k,n in enumerate(frn)]
dl=[(f'draw_{n}',0x806228+0x68*k) for k,n in enumerate(frn)]+[('letters_chain',0x806568),('chain',0x8065C8)]
letters('level_up_letters_fr',0x7FEAD0,0x7FEAD0,0x802A6420,vt,im,gf,dl,'fr_level_up')
# es
esn=['inverted_excl_mark_S','UB','ES','UN','NI','L_exclamation_mark','VE']
vorder=['UB','ES','UN','inverted_excl_mark_S','NI','L_exclamation_mark','VE']
vt=[(f'draw_{n}',0x806628+0x80*k) for k,n in enumerate(vorder)]
im=[(f'big_{n}',0x8069A8+0x1078*k,64,64,'IA8') for k,n in enumerate(esn)]
gf=[(f'big_{n}',0x8079A8+0x1078*k) for k,n in enumerate(esn)]
dl=[(f'draw_{n}',0x80DCF0+0x68*k) for k,n in enumerate(esn)]
dl+=[('letters_chain',0x80DFC8),('chain',0x80E020)]
letters('level_up_letters_es',0x806610,0x806610,0x802A6420,vt,im,gf,dl,'es_level_up')
