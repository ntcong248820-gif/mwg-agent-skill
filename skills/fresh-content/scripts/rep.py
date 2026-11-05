import re
SP = '[  ]'
def make(t):
    st = {'t': t}
    def R(a, b, n=1):
        parts = [re.escape(x) for x in a.split(' ')]
        pat = SP.join(parts)
        m = re.findall(pat, st['t'])
        assert len(m) == n, (len(m), a[:80])
        st['t'] = re.sub(pat, lambda _: b, st['t'])
    return st, R
