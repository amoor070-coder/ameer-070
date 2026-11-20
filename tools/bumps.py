"""نتوءات / شقوق detector.  python3 bumps.py font.ttf W [glyph ...]
spur  = ink removed by morphological opening (disc r=0.30W) -> thin protrusions narrower than ~0.6W
notch = background filled by closing (disc r=0.22W) that is connected to the outside -> nicks/slits
tight = enclosed counter whose inscribed radius < 0.30W (counter about to close)"""
import sys, numpy as np, cv2, skia
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
sys.path.insert(0, '/home/claude/fa')
from draw import parse
S = 0.5
def mask(gs, g):
    b = BoundsPen(gs); gs[g].draw(b)
    if not b.bounds: return None, None
    x0, y0, x1, y1 = b.bounds; pad = 40
    w = int((x1 - x0) * S) + 2 * pad; h = int((y1 - y0) * S) + 2 * pad
    sv = SVGPathPen(gs); gs[g].draw(sv)
    p = parse(sv.getCommands().replace(',', ' '))
    surf = skia.Surface(w, h)
    with surf as c:
        c.clear(skia.ColorBLACK)
        c.translate(pad - x0 * S, h - pad + y0 * S); c.scale(S, -S)
        c.drawPath(p, skia.Paint(Color=skia.ColorWHITE, AntiAlias=False))
    a = surf.makeImageSnapshot().toarray()[:, :, 0] > 127
    return a.astype(np.uint8), (x0, y0, pad, h)
def disc(r):
    r = max(1, int(round(r))); return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
def check(gs, g, W):
    m, geo = mask(gs, g)
    if m is None: return []
    out = []
    r = 0.30 * W * S
    op = cv2.morphologyEx(m, cv2.MORPH_OPEN, disc(r))
    spur = (m & (1 - op)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(spur, 8)
    for i in range(1, n):
        a = st[i, cv2.CC_STAT_AREA]
        if a > 0.9 * r * r:
            out.append(('spur', a / (r * r), st[i, :4].tolist()))
    r2 = 0.22 * W * S
    cl = cv2.morphologyEx(m, cv2.MORPH_CLOSE, disc(r2))
    gap = (cl & (1 - m)).astype(np.uint8)
    # outside region
    ff = (1 - m).copy(); h, w = ff.shape
    outside = np.zeros((h + 2, w + 2), np.uint8); tmp = (1 - m).astype(np.uint8).copy()
    cv2.floodFill(tmp, outside, (0, 0), 2)
    outside = (tmp == 2)
    n, lab, st, _ = cv2.connectedComponentsWithStats(gap, 8)
    for i in range(1, n):
        comp = lab == i
        a = st[i, cv2.CC_STAT_AREA]
        if (comp & outside).any() and a > 0.9 * r2 * r2:
            out.append(('notch', a / (r2 * r2), st[i, :4].tolist()))
    holes = ((1 - m) == 1) & ~outside
    n, lab, st, _ = cv2.connectedComponentsWithStats(holes.astype(np.uint8), 8)
    for i in range(1, n):
        comp = (lab == i).astype(np.uint8)
        dt = cv2.distanceTransform(comp, cv2.DIST_L2, 3).max()
        if dt < 0.30 * W * S and st[i, cv2.CC_STAT_AREA] > 4:
            out.append(('tight', dt / (W * S), st[i, :4].tolist()))
    return out
if __name__ == '__main__':
    f = TTFont(sys.argv[1]); W = float(sys.argv[2]); gs = f.getGlyphSet()
    names = sys.argv[3:] or [g for g in f.getGlyphOrder() if not g.startswith('.')]
    tot = 0
    for g in names:
        try: res = check(gs, g, W)
        except Exception as e: print(g, 'ERR', e); continue
        if res:
            tot += 1
            print(g, ' '.join(f'{k}:{v:.1f}' for k, v, _ in res))
    print('flagged', tot)

def viz(font, W, names, out, cols=8, cell=260):
    f = TTFont(font); gs = f.getGlyphSet()
    tiles = []
    for g in names:
        m, geo = mask(gs, g)
        if m is None: continue
        r = 0.30 * W * S; r2 = 0.22 * W * S
        op = cv2.morphologyEx(m, cv2.MORPH_OPEN, disc(r)); spur = m & (1 - op)
        cl = cv2.morphologyEx(m, cv2.MORPH_CLOSE, disc(r2)); gap = cl & (1 - m)
        img = np.full(m.shape + (3,), 255, np.uint8)
        img[m == 1] = (40, 40, 40); img[spur == 1] = (0, 0, 255); img[gap == 1] = (0, 160, 255)
        h, w = m.shape; s = min((cell - 30) / h, cell / w)
        img = cv2.resize(img, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_AREA)
        t = np.full((cell, cell, 3), 255, np.uint8)
        t[:img.shape[0], :img.shape[1]] = img
        cv2.putText(t, g[:24], (4, cell - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 0, 0), 1)
        cv2.rectangle(t, (0, 0), (cell - 1, cell - 1), (210, 210, 210), 1)
        tiles.append(t)
    rows = [np.hstack(tiles[i:i + cols] + [np.full((cell, cell, 3), 255, np.uint8)] * (cols - len(tiles[i:i + cols]))) for i in range(0, len(tiles), cols)]
    cv2.imwrite(out, np.vstack(rows))
