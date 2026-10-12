import re,os
O='/home/claude/work/overrides/misc'; os.makedirs(O,exist_ok=True)
def ent(n,t,o,sym,**kw):
    return f"{n}:\n  {{ type: {t}, offset: 0x{o:X}{''.join(f', {k}: {v}' for k,v in kw.items())}, symbol: {sym} }}\n"
# digits + dummy
src=open('/home/claude/papermario/ver/pal/splat.yaml').read().split('\n')
o=["# PAL starpoint digits (rom 0x80E070 vram 0x802A1000)\n\n:config:\n  virtual: [0x802A1000, 0x80E070]\n\n"]
for d in range(10):
    b=0x80E070+0x1120*d
    o.append(ent(f'digit_{d}','TEXTURE',b+0x40,f'starpoint_digit_{d}_png',format='IA8',width=64,height=64))
    o.append(ent(f'digit_{d}.vtx','VTX',b,f'starpoint_digit_{d}_vtx',count=4))
    for k,(n,off) in enumerate([('load_digit',0x1040),('__render_digit',0x10B8),('_render_digit',0x1100),('render_digit',0x1110)]):
        o.append(ent(f'{n}_{d}.gfx','GFX',b+off,f'starpoint_{n}_{d}_gfx'))
o.append(ent('dummy_end.gfx','GFX',0x818CC8,'starpoint_dummy_end_gfx'))
open(f'{O}/starpoint.yml','w').write(''.join(o))
def lang(code,S,en=False):
    pre='starpoint' if code=='en' else f'{code}_starpoint'
    o=[f"# PAL starpoint labels ({code}) rom 0x{S:X} vram 0x802ABC80\n\n:config:\n  virtual: [0x802ABC80, 0x{S:X}]\n\n"]
    o.append(ent('lights1','LIGHTS',S,f'{pre}_lights1'))
    o.append(ent('starpoint','TEXTURE',S+0x18,f'{pre}_starpoint_png',format='IA8',width=128,height=32))
    o.append(ent('load_starpoint.gfx','GFX',S+0x1018,f'{pre}_load_starpoint_gfx'))
    o.append(ent('starpoint.vtx','VTX',S+0x1090,f'{pre}_starpoint_vtx',count=4))
    for n,off in [('render_starpoint',0x10D0),('render_starpoint_wrap',0x1130),('render_starpoint_top',0x1158)]:
        o.append(ent(n+'.gfx','GFX',S+off,f'{pre}_{n}_gfx'))
    o.append(ent('lights2','LIGHTS',S+0x1180,f'{pre}_lights2'))
    if en:
        v,t,l,r=S+0x1198,S+0x11D8,S+0x21D8,S+0x2250
    else:
        t,l,v,r=S+0x1198,S+0x2198,S+0x2210,S+0x2250
    o.append(ent('starpoints.vtx','VTX',v,f'{pre}_starpoints_vtx',count=4))
    o.append(ent('starpoints','TEXTURE',t,f'{pre}_starpoints_png',format='IA8',width=128,height=32))
    o.append(ent('load_starpoints.gfx','GFX',l,f'{pre}_load_starpoints_gfx'))
    for n,off in [('render_starpoints',0),('render_starpoints_wrap',0x60),('render_starpoints_top',0x88)]:
        o.append(ent(n+'.gfx','GFX',r+off if not en else S+0x2250+off-(0 if True else 0)+(-0x10 if False else 0),f'{pre}_{n}_gfx'))
    open(f'{O}/starpoint_{code}.yml','w').write(''.join(o))
lang('en',0x818CF0,True); lang('de',0x81B030); lang('fr',0x81D370); lang('es',0x81F6B0)
