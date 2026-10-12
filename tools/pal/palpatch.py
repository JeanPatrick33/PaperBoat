"""usage: palpatch.py <port_file> <decomp_file> <out_file>
Applies the decomp's US->PAL diff (as a patch with fuzz) onto the port file. Rejected hunks are written
to <out_file>.rej for manual resolution."""
import sys, os, subprocess, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vpp
port, dec, out = sys.argv[1:4]
dt = open(dec).read()
base = vpp.process(dt, vpp.defs_for('US')); theirs = vpp.process(dt, vpp.defs_for('PAL'))
d = tempfile.mkdtemp()
open(d + '/b', 'w').write(base + '\n'); open(d + '/t', 'w').write(theirs + '\n')
diff = subprocess.run(['diff', '-u', d + '/b', d + '/t'], capture_output=True, text=True).stdout
shutil.copy(port, out)
open(d + '/p.diff', 'w').write(diff)
r = subprocess.run(['patch', '-F3', '-s', out, d + '/p.diff', '-r', out + '.rej'], capture_output=True, text=True)
print(r.stdout, r.stderr, 'rc=%d' % r.returncode)
print('hunks:', diff.count('\n@@ '), 'rejected:', open(out + '.rej').read().count('\n@@ ') if os.path.exists(out + '.rej') else 0)
