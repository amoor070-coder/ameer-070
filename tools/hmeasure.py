"""horizontal ruler measurements: body width (ink, no dots) and side bearings, vs Alexandria/Plex average (normalised to alef)."""
import sys, statistics; sys.path.insert(0, '/home/claude/fa')
import measure
from measure import F
from wt import OUT, ALEX, PLEX, WT
def info(fn, n):
    b = fn.body(n)
    if not b: return None
    adv = fn.tt['hmtx'][n][0]
    return b[2] - b[0], b[0], adv - b[2], adv
def table(path=OUT):
    ours = F(path); refs = [F(ALEX), F(PLEX)]
    rows = []
    for c in measure.LET:
        for form in measure.forms(c):
            n = ours.gid(c, form)
            if not n: continue
            o = info(ours, n)
            rs = []
            for r in refs:
                rn = r.gid(c, form)
                ri = info(r, rn) if rn else None
                if ri: k = 708 / r.alef; rs.append([v * k for v in ri])
            if not rs or not o: continue
            t = [sum(v[i] for v in rs) / len(rs) for i in range(4)]
            rows.append(dict(n=n, form=form, w=o[0], lsb=o[1], rsb=o[2], adv=o[3], tw=t[0], tlsb=t[1], trsb=t[2], tadv=t[3]))
    m = statistics.median(r['w'] / r['tw'] for r in rows)
    for r in rows: r['rel'] = r['w'] / (m * r['tw'])
    return m, rows
if __name__ == '__main__':
    m, rows = table(sys.argv[1] if len(sys.argv) > 1 else OUT)
    print(WT, 'median body-width ratio', round(m, 3))
    for r in sorted(rows, key=lambda r: -abs(r['rel'] - 1)):
        if abs(r['rel'] - 1) >= 0.1 or abs(r['lsb'] - r['tlsb']) > 40 or abs(r['rsb'] - r['trsb']) > 40:
            print(f"  {r['n']:22s} w {r['w']:.0f}/{r['tw']*m:.0f} rel {r['rel']:.2f}  lsb {r['lsb']:.0f}/{r['tlsb']:.0f}  rsb {r['rsb']:.0f}/{r['trsb']:.0f}")
