import struct
def parse_bank(rom, base, limit):
    d=rom[base:limit]
    secs=[]; pos=0
    while True:
        o=struct.unpack('>I',d[pos:pos+4])[0]
        if o==0: break
        secs.append(o); pos+=4
    msgs=[]  # (section,index,offset)
    for i,so in enumerate(secs):
        pos=so; j=0
        while True:
            o=struct.unpack('>I',d[pos:pos+4])[0]
            if o==so: break
            msgs.append((i,j,o)); j+=1; pos+=4
    return secs,msgs
def with_sizes(msgs, bank_end_rel):
    offs=sorted(set(o for _,_,o in msgs))
    nxt={o:(offs[k+1] if k+1<len(offs) else bank_end_rel) for k,o in enumerate(offs)}
    return [(s,i,o,nxt[o]-o) for s,i,o in msgs]
