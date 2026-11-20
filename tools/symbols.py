"""Symbols the calculator needs, drawn in the same monoline language (weight = Latin stroke, soft round joins):
′ ″ ← → ↑ ↓ ≈ ≤ ≥ ≠ ∞ ‰ ﷼ + thin/figure/hair/narrow spaces."""
import sys, math, pathops
sys.path.insert(0, '/home/claude/fa')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
import uharfbuzz as hb
from wt import OUT, WL, CFG, LCAP, LXH, WT
import draw as _dr
from draw import stroke, union, to_pathops, set_glyph
f = TTFont(OUT); gs = f.getGlyphSet(); cmap = f.getBestCmap(); glyf = f['glyf']
W = WL * (0.9 if WL > 100 else 1.0); _dr.SKY = CFG['sky']; H = W * CFG['sky'] / 2
AX = 322                                   # math axis (centre of minus)
SB = 60 + (W - 86) * 0.4
def P(p): return p if isinstance(p, pathops.Path) else to_pathops(p)
def add(name, uni, path, sb=SB, adv=None):
    p = P(path); b = BoundsPen(None); p.draw(b); bb = b.bounds
    o = pathops.Path(); p.draw(TransformPen(o.getPen(), (1, 0, 0, 1, sb - bb[0], 0)))
    a = adv if adv is not None else round(bb[2] - bb[0] + 2 * sb)
    if name not in f.getGlyphOrder():
        f.setGlyphOrder(f.getGlyphOrder() + [name])
    from fontTools.ttLib.tables._g_l_y_f import Glyph
    glyf[name] = Glyph(); f['hmtx'][name] = (a, 0)
    set_glyph(f, name, o, adv=a)
    for t in f['cmap'].tables:
        if t.isUnicode() and (uni <= 0xFFFF or t.format == 12): t.cmap[uni] = name
def space(name, uni, adv):
    from fontTools.ttLib.tables._g_l_y_f import Glyph
    if name not in f.getGlyphOrder(): f.setGlyphOrder(f.getGlyphOrder() + [name])
    glyf[name] = Glyph(); f['hmtx'][name] = (adv, 0)
    for t in f['cmap'].tables:
        if t.isUnicode(): t.cmap[uni] = name
S = lambda d: stroke(d, W)
# primes (minutes / seconds for pace)
top = LCAP + 10
prime = S(f'M 120 {top} L 70 {top - 230}')
add('minute', 0x2032, prime)
add('second', 0x2033, union(prime, S(f'M {120 + W + 70} {top} L {70 + W + 70} {top - 230}')))
# arrows: shaft + soft chevron head
L_ = 560; hd = 170
def arrow(rot):
    p = P(union(S(f'M 0 {AX} L {L_} {AX}'), S(f'M {L_ - hd} {AX + hd} L {L_} {AX} L {L_ - hd} {AX - hd}')))
    o = pathops.Path(); cx, cy = L_ / 2, AX
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    p.draw(TransformPen(o.getPen(), (c, s, -s, c, cx - c * cx + s * cy, cy - s * cx - c * cy)))
    return o
add('arrowright', 0x2192, arrow(0)); add('arrowleft', 0x2190, arrow(180))
add('arrowup', 0x2191, arrow(90)); add('arrowdown', 0x2193, arrow(-90))
# relations
def wave(y): return f'M 0 {y - 20} C 70 {y + 55} 150 {y + 55} 220 {y} C 290 {y - 55} 370 {y - 55} 440 {y + 20}'
add('approxequal', 0x2248, union(S(wave(AX + 85)), S(wave(AX - 85))))
add('lessequal', 0x2264, union(S(f'M 430 {AX + 230} L 30 {AX + 60} L 430 {AX - 110}'), S(f'M 30 {AX - 230} L 430 {AX - 230}')))
add('greaterequal', 0x2265, union(S(f'M 30 {AX + 230} L 430 {AX + 60} L 30 {AX - 110}'), S(f'M 30 {AX - 230} L 430 {AX - 230}')))
add('notequal', 0x2260, union(S(f'M 20 {AX + 95} L 440 {AX + 95}'), S(f'M 20 {AX - 95} L 440 {AX - 95}'), S(f'M 320 {AX + 260} L 140 {AX - 260}')))
add('infinity', 0x221E, S(f'M 330 {AX} C 390 {AX + 110} 460 {AX + 150} 520 {AX + 150} C 600 {AX + 150} 650 {AX + 85} 650 {AX} C 650 {AX - 85} 600 {AX - 150} 520 {AX - 150} C 460 {AX - 150} 390 {AX - 110} 330 {AX} C 270 {AX - 110} 200 {AX - 150} 140 {AX - 150} C 60 {AX - 150} 10 {AX - 85} 10 {AX} C 10 {AX + 85} 60 {AX + 150} 140 {AX + 150} C 200 {AX + 150} 270 {AX + 110} 330 {AX} Z'))
# per mille = our % + one more lower ring
def contours(n):
    rp = DecomposingRecordingPen(gs); gs[n].draw(rp); cs, cur = [], []
    for op, a in rp.value:
        cur.append((op, a))
        if op in ('closePath', 'endPath'): cs.append(cur); cur = []
    out = []
    for c in cs:
        b = BoundsPen(None)
        for op, a in c: getattr(b, op)(*a)
        out.append((c, b.bounds))
    return out
pc = contours(cmap[0x25]); p = pathops.Path(); pen = p.getPen()
for c, _ in pc:
    for op, a in c: getattr(pen, op)(*a)
low = [t for t in pc if t[1][3] < 0.55 * LCAP]           # lower ring (outer + counter)
if low:
    lb = (min(b[0] for _, b in low), max(b[2] for _, b in low)); dx = lb[1] - lb[0] + 0.55 * W
    for c, _ in low:
        for op, a in c: getattr(pen, op)(*[(x + dx, y) for x, y in a])
p.simplify()
add('perthousand', 0x2030, p, sb=f['hmtx'][cmap[0x25]][1])
# Rial sign = our own ريال as one glyph
hf = hb.Font(hb.Face(hb.Blob.from_file_path(OUT)))
buf = hb.Buffer(); buf.add_str('ريال'); buf.guess_segment_properties(); hb.shape(hf, buf)
rp = pathops.Path(); x = 0
for inf, pos in zip(buf.glyph_infos, buf.glyph_positions):
    n = hf.glyph_to_string(inf.codepoint)
    gs[n].draw(TransformPen(rp.getPen(), (1, 0, 0, 1, x + pos.x_offset, pos.y_offset))); x += pos.x_advance
rp.simplify()
add('riyal', 0xFDFC, rp, sb=40)
# spaces
tab = f['hmtx'][cmap[0x30]][0]
space('figurespace', 0x2007, tab); space('thinspace', 0x2009, 200); space('hairspace', 0x200A, 100); space('narrownbspace', 0x202F, 200)
# math signs share one width (centred) so columns of numbers stay aligned
MATH = [0x2B, 0x3C, 0x3D, 0x3E, 0xAC, 0xB1, 0xD7, 0xF7, 0x2212, 0x2248, 0x2260, 0x2264, 0x2265, 0x221E]
cm = f.getBestCmap(); mw = f['hmtx'][cm[0x2B]][0]
mw = max(mw, max(glyf[cm[u]].xMax - glyf[cm[u]].xMin + 2 * 30 for u in MATH if u in cm and glyf[cm[u]].numberOfContours))
for u in MATH:
    n = cm.get(u)
    if not n or not glyf[n].numberOfContours: continue
    g = glyf[n]; dx = round((mw - (g.xMax - g.xMin)) / 2 - g.xMin)
    g.coordinates.translate((dx, 0)); g.recalcBounds(glyf); f['hmtx'][n] = (mw, g.xMin)
f.save(OUT); print(WT, 'symbols added')
