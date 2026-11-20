"""Latin optical kerning: band-sampled white space between neighbours vs the nn/HH reference.
Old Latin kerning is cleared; one new PairPos lookup (kern, latn+DFLT) is added. Accented letters kern like their base."""
import sys, unicodedata, numpy as np
sys.path.insert(0, '/home/claude/fa')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.otlLib.builder import buildPairPosGlyphs, buildValue
from fontTools.ttLib.tables import otTables as ot
import skia
from draw import parse
from wt import OUT, WL, LXH, LCAP, WT
f = TTFont(OUT); gs = f.getGlyphSet(); cmap = f.getBestCmap(); hm = f['hmtx']
STEP = 10
def profile(n):
    r = DecomposingRecordingPen(gs); gs[n].draw(r); sv = SVGPathPen(None); r.replay(sv)
    p = parse(sv.getCommands().replace(',', ' ')); adv = hm[n][0]
    ys = np.arange(-200, 800, STEP); L = np.full(len(ys), np.nan); R = np.full(len(ys), np.nan)
    b = p.computeTightBounds()
    if b.isEmpty(): return None
    for i, y in enumerate(ys):
        rect = skia.Path(); rect.addRect(skia.Rect(-2000, y - 1, 4000, y + 1))
        s = skia.Op(p, rect, skia.PathOp.kIntersect_PathOp)
        if s.isEmpty(): continue
        bb = s.computeTightBounds(); L[i] = bb.left(); R[i] = adv - bb.right()
    return ys, L, R, b.top(), b.bottom()
LETTERS = [c for c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,"\'']
names = {c: cmap[ord(c)] for c in LETTERS if ord(c) in cmap}
P = {c: profile(n) for c, n in names.items()}
D = 0.42 * LXH
def white(a, b):
    pa, pb = P[a], P[b]
    if pa is None or pb is None: return None
    ys = pa[0]
    lo = max(pa[3], pb[3], -200); hi = min(pa[4], pb[4])
    if hi - lo < 60:   # little vertical overlap (e.g. quote + letter): use union band
        lo, hi = min(pa[3], pb[3]), max(pa[4], pb[4])
    m = (ys >= lo) & (ys <= hi)
    ga = np.where(np.isnan(pa[2][m]), D, np.minimum(pa[2][m], D)); gb = np.where(np.isnan(pb[1][m]), D, np.minimum(pb[1][m], D))
    w = ga + gb
    return float(np.mean(w)), float(np.min(w))
ref_lc = white('n', 'n')[0]; ref_uc = white('H', 'H')[0]
pairs = {}
for a in names:
    for b in names:
        r = white(a, b)
        if r is None: continue
        mean, mn = r
        tgt = ref_uc if (a.isupper() and b.isupper()) else (ref_lc if not (a.isupper() or b.isupper()) else (ref_lc + ref_uc) / 2)
        if not (a.isalnum() and b.isalnum()): tgt = ref_lc
        k = 0.4 * (tgt - mean)
        if a.islower() and b.isupper(): k *= 0.5
        k = max(-95, min(30, k))
        if mn + k < 0.25 * WL: k = 0.25 * WL - mn          # never let ink touch
        if a.isdigit() or b.isdigit(): continue               # tabular figures stay untouched
        punct = not (a.isalnum() and b.isalnum())
        if punct and not ((a in 'TVWYFPLAvwyr\'"' and b in '.,') or (a in 'AL' and b in '\'"') or (a in '\'"' and b in 'AJ') or (a in '-' or b in '-')):
            continue
        RO = set('TVWYFPLKXZArvwyxkfJ\'"')            # shapes with open/overhanging right side
        LO = set('AVWYTXZjvwyx\'"')                  # shapes with open/overhanging left side
        if not (a in RO or b in LO): continue
        if abs(k) >= (18 if not punct else 25): pairs[(names[a], names[b])] = int(round(k / 5) * 5)
# accented letters kern like their base
base_of = {}
for u, n in cmap.items():
    if 0xC0 <= u <= 0x24F:
        d = unicodedata.decomposition(chr(u)).split()
        if d and not d[0].startswith('<'):
            bc = chr(int(d[0], 16))
            if bc in names: base_of[n] = names[bc]
groups = {}
for n, b in base_of.items(): groups.setdefault(b, []).append(n)
full = dict(pairs)
for (a, b), k in pairs.items():
    for a2 in [a] + groups.get(a, []):
        for b2 in [b] + groups.get(b, []):
            full[(a2, b2)] = k
# clear old Latin pair kerning
lat = set(names.values()) | set(base_of)
gpos = f['GPOS'].table
for lk in gpos.LookupList.Lookup:
    sts = [x.ExtSubTable for x in lk.SubTable] if lk.LookupType == 9 else lk.SubTable
    for st in sts:
        if type(st).__name__ != 'PairPos': continue
        if st.Format == 1:
            for i, g in enumerate(st.Coverage.glyphs):
                for pvr in st.PairSet[i].PairValueRecord:
                    if g in lat or pvr.SecondGlyph in lat:
                        for v in (pvr.Value1, getattr(pvr, 'Value2', None)):
                            if v is not None:
                                for at in ('XAdvance', 'XPlacement'):
                                    if hasattr(v, at): setattr(v, at, 0)
        else:
            c1 = st.ClassDef1.classDefs; c2 = st.ClassDef2.classDefs; cov = set(st.Coverage.glyphs)
            k1 = {c1.get(g, 0) for g in lat if g in cov}; k2 = {c2.get(g, 0) for g in lat if g in c2}
            for i, r1 in enumerate(st.Class1Record):
                for j, r2 in enumerate(r1.Class2Record):
                    if i in k1 or j in k2:
                        for v in (r2.Value1, getattr(r2, 'Value2', None)):
                            if v is not None:
                                for at in ('XAdvance', 'XPlacement'):
                                    if hasattr(v, at): setattr(v, at, 0)
# new lookup
order = f.getGlyphOrder()
pp = {k: (buildValue({'XAdvance': v}), None) for k, v in full.items()}
subs = buildPairPosGlyphs(pp, f.getReverseGlyphMap())
lk = ot.Lookup(); lk.LookupType = 2; lk.LookupFlag = 0; lk.SubTable = subs; lk.SubTableCount = len(subs)
gpos.LookupList.Lookup.append(lk); gpos.LookupList.LookupCount = len(gpos.LookupList.Lookup); li = len(gpos.LookupList.Lookup) - 1
for fr in gpos.FeatureList.FeatureRecord:
    if fr.FeatureTag == 'kern' and li not in fr.Feature.LookupListIndex:
        fr.Feature.LookupListIndex.append(li); fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)
import json as _j; _j.dump([[a, b, v] for (a, b), v in full.items()], open(f'/home/claude/fa/work/kern_{WT}.json', 'w'))
f.save(OUT)
top = sorted(pairs.items(), key=lambda t: t[1])[:25]
print(WT, 'kern pairs', len(pairs), '(+accented', len(full) - len(pairs), ') ref nn/HH', round(ref_lc), round(ref_uc))
print(' '.join(f'{a}/{b}:{k}' for (a, b), k in top))
lt=[(k,v) for k,v in pairs.items() if all(len(x)==1 for x in k)]
print('letters:', ' '.join(f'{a}{b}:{k}' for (a,b),k in sorted(lt,key=lambda t:t[1])[:40]))
print('letters+:', ' '.join(f'{a}{b}:{k}' for (a,b),k in sorted(lt,key=lambda t:-t[1])[:20]))
print('positive:', ' '.join(f'{a}/{b}:{k}' for (a, b), k in sorted(pairs.items(), key=lambda t: -t[1])[:12]))
