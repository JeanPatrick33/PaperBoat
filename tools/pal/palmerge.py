"""usage: palmerge.py <port_file> <decomp_file> <out_file>
3-way merge: port file (resolved for PAL) + decomp's US->PAL delta. Writes <out_file>, prints conflict count."""
import sys, os, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vpp
port, dec, out = sys.argv[1:4]
pt = open(port).read(); dt = open(dec).read()
ours = vpp.process(pt, vpp.defs_for('PAL'))
base = vpp.process(dt, vpp.defs_for('US'))
theirs = vpp.process(dt, vpp.defs_for('PAL'))
d = tempfile.mkdtemp()
for n, t in (('o', ours), ('b', base), ('t', theirs)):
    open(d + '/' + n, 'w').write(t if t.endswith('\n') else t + '\n')
r = subprocess.run(['git', 'merge-file', '-p', '-L', 'port', '-L', 'decomp_us', '-L', 'decomp_pal', d + '/o', d + '/b', d + '/t'], capture_output=True, text=True)
open(out, 'w').write(r.stdout)
print('conflicts=%d' % r.returncode)
