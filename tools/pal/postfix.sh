#!/bin/bash
P=/home/claude/PaperBoat/assets/yaml/pal
sed -i 's/virtual: \[0x800745E0, 0x4CCF0\]/virtual: [0x800718F0, 0x4CCF0]/' $P/theater.yml
sed -i 's/virtual: \[0x800DC500, 0x71D80\]/virtual: [0x80108050, 0xA1160]/' $P/misc/status_star_shimmer.yml
python3 - <<'PY'
import re
p='/home/claude/PaperBoat/assets/yaml/pal/world/world_pra_31.yml'
s=open(p).read()
order=[30,26,24,22,20,18,16,14,12,10,8,6,4,2]
def f(m):
    k=order.index(int(m.group(1))); return f"pra_31_unk_{m.group(1)}_mtx:\n  {{ type: MTX, offset: 0x{0xDF2490+k*0x40:X}"
s=re.sub(r"pra_31_unk_(\d\d)_mtx:\n  \{ type: MTX, offset: 0x[0-9A-F]+",f,s)
open(p,'w').write(s)
PY
