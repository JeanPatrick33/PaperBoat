"""usage: audit.py <decomp_root> <port_root>
Reports decomp US->PAL hunks whose PAL-added lines are not found anywhere in the port tree."""
import sys, os, re, subprocess, tempfile, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vpp
dec, port = sys.argv[1:3]
def norm(l): return re.sub(r'\s+', '', l)
corpus = set()
for root in ('src', 'include'):
    for f in glob.glob(os.path.join(port, root, '**', '*.[ch]'), recursive=True) + glob.glob(os.path.join(port, root, '**', '*.cpp'), recursive=True):
        try:
            for l in open(f, errors='ignore'): corpus.add(norm(l))
        except Exception: pass
trivial = re.compile(r'^[{}();,#]*$|^#(if|else|endif|elif)|^//|^/\*|^\*')
tmp = tempfile.mkdtemp()
rep = {}
for f in glob.glob(os.path.join(dec, 'src', '**', '*.[ch]'), recursive=True) + glob.glob(os.path.join(dec, 'include', '**', '*.h'), recursive=True):
    t = open(f, errors='ignore').read()
    if 'VERSION_PAL' not in t: continue
    try:
        us = vpp.process(t, vpp.defs_for('US')); pal = vpp.process(t, vpp.defs_for('PAL'))
    except ValueError: continue
    if us == pal: continue
    open(tmp + '/b', 'w').write(us + '\n'); open(tmp + '/t', 'w').write(pal + '\n')
    d = subprocess.run(['diff', '-U0', tmp + '/b', tmp + '/t'], capture_output=True, text=True).stdout
    hunks = re.split(r'(?m)^@@.*@@.*\n', d)[1:]
    heads = re.findall(r'(?m)^@@ -(\d+)', d)
    for hd, h in zip(heads, hunks):
        added = [l[1:] for l in h.split('\n') if l.startswith('+')]
        sig = [norm(l) for l in added if not trivial.match(norm(l)) and len(norm(l)) > 12]
        if not sig: continue
        miss = [l for l in sig if l not in corpus]
        if len(miss) * 2 >= len(sig):
            rep.setdefault(os.path.relpath(f, dec), []).append((hd, len(miss), len(sig), [l for l in added if norm(l) in miss][:2]))
tot = 0
for f in sorted(rep):
    print('%s: %d hunks' % (f, len(rep[f])))
    for hd, m, s, ex in rep[f]:
        tot += 1
        print('   @%s missing %d/%d  e.g. %s' % (hd, m, s, ex[0].strip()[:90] if ex else ''))
print('TOTAL hunks missing', tot, 'in', len(rep), 'files')
