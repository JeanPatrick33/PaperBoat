"""Tiny version preprocessor: resolves #if/#elif/#else/#endif blocks whose condition only
involves the VERSION_* macros (and ! && || () defined()). Anything else is left untouched.
Used to compute the decomp's US->PAL delta so it can be 3-way merged into the port sources."""
import re

VERSIONS = ['VERSION_JP', 'VERSION_US', 'VERSION_PAL', 'VERSION_IQUE', 'VERSION_CN']

def defs_for(v):
    return {k: (1 if k == 'VERSION_' + v else 0) for k in VERSIONS}

TOK = re.compile(r'\s*(defined|VERSION_[A-Z]+|\d+|&&|\|\||!|\(|\)|[A-Za-z_]\w*)')

def evaluate(expr, defs):
    """Return True/False, or None if the expression can't be resolved from defs."""
    expr = re.sub(r'/\*.*?\*/|//.*', '', expr).strip()
    toks, pos = [], 0
    while pos < len(expr):
        m = TOK.match(expr, pos)
        if not m:
            return None
        toks.append(m.group(1)); pos = m.end()
    out = []
    i = 0
    while i < len(toks):
        t = toks[i]
        if t == 'defined':
            if i + 1 < len(toks) and toks[i + 1] == '(' and i + 3 < len(toks) and toks[i + 3] == ')':
                name = toks[i + 2]; i += 4
            elif i + 1 < len(toks):
                name = toks[i + 1]; i += 2
            else:
                return None
            if name not in defs:
                return None
            out.append('1' if defs[name] else '0')
            continue
        if t in defs:
            out.append(str(defs[t]))
        elif t in ('&&', '||', '!', '(', ')') or t.isdigit():
            out.append({'&&': ' and ', '||': ' or ', '!': ' not '}.get(t, t))
        else:
            return None
        i += 1
    try:
        return bool(eval(''.join(out), {}, {}))
    except Exception:
        return None

def process(text, defs):
    lines = text.split('\n')
    out = []
    # stack entries: dict(kind='resolve'|'keep', parent_active, taken, active)
    stack = []
    def active():
        return all(s['active'] for s in stack)
    for ln in lines:
        m = re.match(r'\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)', ln)
        if not m:
            if active():
                out.append(ln)
            continue
        d, rest = m.group(1), m.group(2)
        if d in ('if', 'ifdef', 'ifndef'):
            expr = rest if d == 'if' else (('defined(%s)' % rest.strip()) if d == 'ifdef' else ('!defined(%s)' % rest.strip()))
            v = evaluate(expr, defs)
            if v is None:
                stack.append({'kind': 'keep', 'active': True, 'taken': False})
                if active():
                    out.append(ln)
            else:
                stack.append({'kind': 'resolve', 'active': v, 'taken': v})
        elif d == 'elif':
            s = stack[-1]
            if s['kind'] == 'keep':
                if all(x['active'] for x in stack[:-1]):
                    out.append(ln)
            else:
                v = evaluate(rest, defs)
                if v is None:
                    raise ValueError('unresolvable #elif after resolved #if: ' + ln)
                if s['taken']:
                    s['active'] = False
                else:
                    s['active'] = v; s['taken'] = v
        elif d == 'else':
            s = stack[-1]
            if s['kind'] == 'keep':
                if all(x['active'] for x in stack[:-1]):
                    out.append(ln)
            else:
                s['active'] = not s['taken']; s['taken'] = True
        else:  # endif
            s = stack.pop()
            if s['kind'] == 'keep' and all(x['active'] for x in stack):
                out.append(ln)
    return '\n'.join(out)
