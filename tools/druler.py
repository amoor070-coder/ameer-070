"""'مسطرة الأرقام': Latin + Arabic-Indic digits brought to the Alexandria/Plex average height
(band-compress so stroke thickness is kept) and set on one tabular width, centred."""
import sys; sys.path.insert(0, '/home/claude/fa')
from fontTools.ttLib import TTFont
from wt import OUT, W, WT
TAB = 580
LAT = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
tt = TTFont(OUT); glyf = tt['glyf']; hmtx = tt['hmtx']; cmap = tt.getBestCmap()
ARA = [cmap[c] for c in range(0x660, 0x66a)]
def squash(n, top_to):
    g = glyf[n]
    if g.isComposite() or not g.numberOfContours: return
    co = g.coordinates; top = g.yMax
    if top < 400: return                       # ٠ (a dot) stays
    d = top_to - top; R = 0.75 * W
    lo, hi = R + 10, top - R
    def fy(y):
        if y <= lo: return y
        if y >= hi: return y + d
        return lo + (y - lo) * (hi + d - lo) / (hi - lo)
    for i in range(len(co)): co[i] = (co[i][0], round(fy(co[i][1])))
    g.recalcBounds(glyf)
def centre(n, TAB=TAB):
    g = glyf[n]
    if not g.numberOfContours: return
    w = g.xMax - g.xMin; dx = round((TAB - w) / 2 - g.xMin)
    co = g.coordinates
    for i in range(len(co)): co[i] = (co[i][0] + dx, co[i][1])
    g.recalcBounds(glyf); hmtx[n] = (TAB, g.xMin)
for n in LAT:
    g = glyf[n]
    if g.yMax > 700: squash(n, 650)          # only figures not yet on the ruler
for n in ARA:
    squash(n, 620)
_mw = max(glyf[n].xMax - glyf[n].xMin for n in LAT if glyf[n].numberOfContours)
TABW = max(TAB, round(_mw + 2 * 22))     # tabular width grows with weight so digits never touch
for n in LAT: centre(n, TABW)
# Arabic-Indic: proportional like Alexandria/Plex (average advance, normalised to alef), scaled with weight
ASB = [80, 79, 49, 47, 35, 38, 46, 31, 31, 47]      # side bearings: Alexandria/Plex average (normalised)
for n, sb in zip(ARA, ASB):
    g = glyf[n]; w = g.xMax - g.xMin
    centre(n, round(w + 2 * sb * (1 + (W - 79) / 400)))
tt.save(OUT); print('digits ruled', WT)
