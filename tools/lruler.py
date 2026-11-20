"""Latin horizontal ruler: body width (relative to our own median) + side bearings vs Alexandria/Plex average,
normalised to alef. Writes work/latin_ruler_<WT>.json (skeleton x-factor + side bearings), compounding each run."""
import sys, json, os, statistics, string
sys.path.insert(0, '/home/claude/fa')
from measure import F
from wt import OUT, ALEX, PLEX, WT
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
P = f'/home/claude/fa/work/latin_ruler_{WT}.json'
LR = json.load(open(P)) if os.path.exists(P) else {}
REG = '/home/claude/fa/work/latin_ruler_Regular.json'
def info(fn, ch):
    n = fn.tt.getBestCmap().get(ord(ch))
    if not n: return None
    r = DecomposingRecordingPen(fn.gs); fn.gs[n].draw(r); b = BoundsPen(None); r.replay(b)
    if not b.bounds: return None
    k = 708 / fn.alef; adv = fn.tt['hmtx'][n][0]
    return n, (b.bounds[2] - b.bounds[0]) * k, b.bounds[0] * k, (adv - b.bounds[2]) * k
ours = F(OUT); refs = [F(ALEX), F(PLEX)]
rows = []
for ch in string.ascii_letters:
    o = info(ours, ch); rs = [info(r, ch) for r in refs]; rs = [x for x in rs if x]
    if not o or not rs: continue
    t = [sum(x[i] for x in rs) / len(rs) for i in (1, 2, 3)]
    rows.append((ch, o[0], o[1], o[2], o[3], *t))
m = statistics.median(r[2] / r[5] for r in rows)
out = []
for ch, n, w, l, rr, tw, tl, tr in rows:
    rel = w / tw                                   # absolute: the ruler is the references' average
    e = LR.get(n, {'sx': 1.0})
    if ch not in 'ilIj' and abs(rel - 1) >= 0.04:
        e['sx'] = round(e['sx'] * (1 + 0.7 * (1 / rel - 1)), 4)
    if WT in ('Bold', 'Black') and os.path.exists(REG):   # keep the Regular proportions: heavy letters may not be squeezed
        rs = json.load(open(REG)).get(n, {}).get('sx', 1.0)
        e['sx'] = round(min(max(e['sx'], rs * 0.96), rs * 1.08), 4)
    e['lsb'] = round(l + 0.6 * (tl - l)); e['rsb'] = round(rr + 0.6 * (tr - rr))
    LR[n] = e
    out.append(f'{ch} w {w:.0f}/{tw:.0f} rel {rel:.2f} sx {e["sx"]:.3f}  lsb {l:.0f}->{e["lsb"]} ({tl:.0f})  rsb {rr:.0f}->{e["rsb"]} ({tr:.0f})')
json.dump(LR, open(P, 'w'), indent=1)
print(WT, 'median width ratio', round(m, 3)); print('\n'.join(out))
