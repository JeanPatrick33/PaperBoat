import struct
def parse(rom, base):
    ents=[]; p=base+0x20
    while True:
        name=rom[p:p+0x10].split(b'\0')[0].decode()
        off,csz,dsz=struct.unpack('>III',rom[p+0x10:p+0x1c])
        if name=='end_data': break
        ents.append((name,off,csz,dsz,p)); p+=0x1c
    return ents
