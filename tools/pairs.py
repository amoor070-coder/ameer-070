"""collision checker: every Arabic letter pair, shaped with HarfBuzz; min ink distance between neighbours
(join band of connected pairs excluded). python3 pairs.py [report]  -> uses WT"""
import sys, numpy as np, cv2, skia, uharfbuzz as hb
sys.path.insert(0, '/home/claude/fa')
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from draw import parse
import measure
from wt import OUT, W, WT
S = 0.25
LET = 'ابتثجحخدذرزسشصضطظعغفقكلمنهوي' + 'ةىئؤأإآء'
def load(path=OUT):
    tt = TTFont(path); gs = tt.getGlyphSet(); f = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
    return tt, gs, f
CACHE = {}
def gmask(gs, n):
    if n in CACHE: return CACHE[n]
    r = DecomposingRecordingPen(gs); gs[n].draw(r); sv = SVGPathPen(None); r.replay(sv)
    p = parse(sv.getCommands().replace(',', ' ')); b = p.computeTightBounds()
    if b.isEmpty(): CACHE[n] = None; return None
    x0, y0, x1, y1 = b.left(), b.top(), b.right(), b.bottom()
    w = int((x1 - x0) * S) + 3; h = int((y1 - y0) * S) + 3
    surf = skia.Surface(w, h)
    with surf as c:
        c.clear(skia.ColorBLACK); c.scale(S, -S); c.translate(-x0, -y1)
        c.drawPath(p, skia.Paint(Color=skia.ColorWHITE, AntiAlias=False))
    m = (surf.makeImageSnapshot().toarray()[:, :, 0] > 127).astype(np.uint8)
    CACHE[n] = (m, x0, y1); return CACHE[n]
def pair_gap(tt, gs, f, text):
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties(); hb.shape(f, buf)
    infos, pos = buf.glyph_infos, buf.glyph_positions
    names = [f.glyph_to_string(i.codepoint) for i in infos]
    xs = []; x = 0
    for p_ in pos: xs.append(x + p_.x_offset); x += p_.x_advance
    if len(names) != 2: return None
    (n1, n2), (xa, xb) = names, xs           # visual order: n1 is LEFT (hb gives RTL runs left-to-right visually)
    A, B = gmask(gs, n1), gmask(gs, n2)
    if A is None or B is None: return None
    joined = n1.endswith(('.fina', '.medi')) and n2.endswith(('.init', '.medi'))
    # common canvas in font units
    mA, ax0, ay1 = A; mB, bx0, by1 = B
    X0 = min(xa + ax0, xb + bx0) - 50; Y1 = max(ay1, by1) + 50
    Wd = int((max(xa + ax0 + mA.shape[1] / S, xb + bx0 + mB.shape[1] / S) - X0) * S) + 4
    Hd = int((Y1 - min(ay1 - mA.shape[0] / S, by1 - mB.shape[0] / S) + 50) * S) + 4
    ca = np.zeros((Hd, Wd), np.uint8); cb = np.zeros((Hd, Wd), np.uint8)
    def put(c, m, gx, gy1):
        ox = int(round((gx - X0) * S)); oy = int(round((Y1 - gy1) * S))
        c[oy:oy + m.shape[0], ox:ox + m.shape[1]] |= m
    put(ca, mA, xa + ax0, ay1); put(cb, mB, xb + bx0, by1)
    if joined:   # ignore the shared baseline stroke near the junction
        jx = int(round((xb - X0) * S)); r = int(1.3 * W * S)
        y_top = int(round((Y1 - (W + 15)) * S)); y_bot = int(round((Y1 + 15) * S))
        for c in (ca, cb): c[y_top:y_bot, max(0, jx - r):jx + r] = 0
    if not ca.any() or not cb.any(): return None
    dt = cv2.distanceTransform(1 - ca, cv2.DIST_L2, 5)
    d = dt[cb > 0].min() / S
    return d, n1, n2, joined
def scan(path=OUT):
    tt, gs, f = load(path); out = []
    for a in LET:
        for b in LET:
            r = pair_gap(tt, gs, f, a + b)
            if r: out.append((r[0], a + b) + r[1:])
    return out
if __name__ == '__main__':
    res = scan(); G = 0.35 * W
    bad = sorted([r for r in res if r[0] < G])
    print(WT, 'pairs', len(res), 'tight (<%.0f)' % G, len(bad))
    for r in bad[:60]: print(f'{r[0]:6.1f} {r[1]}  {r[2]} | {r[3]}  joined={r[4]}')
