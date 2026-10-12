import struct
FMT_CI=2
def isz(depth,w,h):
    return {0:w*h//2,1:w*h,2:w*h*2,3:w*h*4}[depth]
def palsz(fmt,depth):
    return (0x20 if depth==0 else 0x200) if fmt==FMT_CI else 0
def parse_tex(rom,start,size):
    """returns list of dict(name,start,end,parts=[(role,off,len,fmt,depth,w,h)])"""
    out=[]; p=start; end=start+size
    while p+0x30<=end:
        name=rom[p:p+32].split(b'\0')[0].decode('ascii','replace')
        if not name or not name.isprintable(): break
        aw,mw,ah,mh,var,extra,comb,fm,dp,hw,vw,flt=struct.unpack('>HHHHBBBBBBBB',rom[p+32:p+48])
        afmt,mfmt=fm>>4,fm&15; adp,mdp=dp>>4,dp&15
        q=p+0x30; parts=[]
        def add(role,l,fmt=None,dep=None,w=0,h=0):
            nonlocal q; parts.append((role,q,l,fmt,dep,w,h)); q+=l
        if extra==0:
            add('main',isz(mdp,mw,mh),mfmt,mdp,mw,mh)
            if mfmt==FMT_CI: add('pal',palsz(mfmt,mdp))
        elif extra==1:
            add('main',isz(mdp,mw,mh),mfmt,mdp,mw,mh)
            div=2
            if mw>=(32>>mdp):
                i=1
                while True:
                    if mw//div<=0: break
                    add('mm%d'%i,isz(mdp,mw//div,mh//div),mfmt,mdp,mw//div,mh//div); i+=1
                    div*=2
                    if mw//div<(16>>mdp): break
            if mfmt==FMT_CI: add('pal',palsz(mfmt,mdp))
        elif extra==2:
            add('main',isz(mdp,mw,mh//2),mfmt,mdp,mw,mh//2)
            add('aux',isz(mdp,mw,mh//2),mfmt,mdp,mw,mh//2)
            if mfmt==FMT_CI: add('pal',palsz(mfmt,mdp))
        elif extra==3:
            add('main',isz(mdp,mw,mh),mfmt,mdp,mw,mh)
            if mfmt==FMT_CI: add('pal',palsz(mfmt,mdp))
            add('aux',isz(adp,aw,ah),afmt,adp,aw,ah)
            if afmt==FMT_CI: add('auxpal',palsz(afmt,adp))
        else: break
        out.append(dict(name=name,start=p,end=q,parts=parts,hdr=rom[p+32:p+48]))
        p=q
    return out
