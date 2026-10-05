import struct
def yay0_decomp(d, off):
    if d[off:off+4]!=b'Yay0': return None
    size,lo,co=struct.unpack('>III',d[off+4:off+16])
    out=bytearray(); li=off+lo; ci=off+co; mi=off+16
    # returns (data, compressed_len upper bound)
    maxl=max(li,ci,mi)
    bits=0; mask=0
    while len(out)<size:
        if mask==0:
            bits=struct.unpack('>I',d[mi:mi+4])[0]; mi+=4; mask=0x80000000
        if bits&mask:
            out.append(d[ci]); ci+=1
        else:
            l=struct.unpack('>H',d[li:li+2])[0]; li+=2
            n=l>>12; dist=(l&0xFFF)+1
            if n==0: n=d[ci]+18; ci+=1
            else: n+=2
            for _ in range(n): out.append(out[-dist])
        mask>>=1
    return bytes(out[:size]), max(li,ci,mi)-off
