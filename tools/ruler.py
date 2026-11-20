"""'المسطرة': align every Arabic letter's top/bottom to the average of Alexandria + IBM Plex (normalised to our alef)."""
import json, subprocess, sys
from fontTools.ttLib import TTFont
sys.path.insert(0, '/home/claude/fa')
from measure import F
from wt import OUT as P, ALEX, PLEX, DOTMAX
import measure
ours = F(P); refs = [F(ALEX), F(PLEX)]
SKIP = {'heh.fina', 'tehMarbuta.fina', 'ain.fina', 'ghain.fina', 'ain.isol', 'ghain.isol', 'ain.init', 'ghain.init', 'heh.init', 'heh.medi', 'yehHamza.init', 'yehHamza.medi'}
JOINED_BLEND = 0.5      # init/medi forms: move halfway to the reference average (flexibility, keeps approved shapes)
from wt import WT as _WT
if _WT in ('Bold', 'Black'):           # heavy weights: the heh needs the references' height or its counters choke
    SKIP -= {'heh.init', 'heh.medi'}
HEAVY_FULL = {'heh.init', 'heh.medi'}
MARKGL = {'alefHamzaAbove.isol', 'alefHamzaAbove.fina', 'alefMadda.isol', 'alefMadda.fina', 'wawHamza.isol', 'wawHamza.fina', 'yehHamza.fina', 'yehHamza.isol'}
tt = TTFont(P); glyf = tt['glyf']
log = []
def contours(g):
    out = []; s = 0
    for e in g.endPtsOfContours:
        out.append(list(range(s, e + 1))); s = e + 1
    return out
def adjust(n, top, ttop, bot, tbot, markfloor=None, markd=None):
    g = glyf[n]
    if g.isComposite(): return
    co = g.coordinates
    d = ttop - top if abs(ttop - top) >= 15 and top > 180 else 0
    if markd is not None and not d: d = 0
    e = tbot - bot if abs(tbot - bot) >= 15 and bot < -100 else 0
    if not d and not e: return
    R = 90
    def fy(y):
        if d and y > 0:
            if y >= top - R: return y + d
            if y > R: return R + (y - R) * ((top - R + d - R) / (top - 2 * R))
        if e and y < 0:
            if y <= bot + R: return y + e
            if y < 0 - 0: return y * ((bot + R + e) / (bot + R)) if (bot + R) != 0 else y
        return y
    for idxs in contours(g):
        xs = [co[i][0] for i in idxs]; ys = [co[i][1] for i in idxs]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        area = sum(co[idxs[i - 1]][0] * co[idxs[i]][1] - co[idxs[i]][0] * co[idxs[i - 1]][1] for i in range(len(idxs)))
        small = w < DOTMAX and h < DOTMAX and area < 0
        mark = markfloor is not None and min(ys) >= markfloor
        if small or mark:
            cy = (max(ys) + min(ys)) / 2
            dy = (d if cy > 0 else e) if markd is None or not mark else markd
            for i in idxs: co[i] = (co[i][0], co[i][1] + dy)
        else:
            for i in idxs: co[i] = (co[i][0], round(fy(co[i][1])))
    g.recalcBounds(glyf)
    log.append(f'{n}: top {top:.0f}->{top+d:.0f}  bottom {bot:.0f}->{bot+e:.0f}')
data = {}
for c in measure.LET:
    for form in measure.forms(c):
        n = ours.gid(c, form)
        if not n or n in SKIP: continue
        tops = []; bots = []
        for r in refs:
            rn = r.gid(c, form); rb = r.body(rn) if rn else None
            if rb: k = 708 / r.alef; tops.append(rb[3] * k); bots.append(rb[1] * k)
        if not tops: continue
        ob = ours.body(n)
        if not ob: continue
        tt_, tb_ = sum(tops) / len(tops), sum(bots) / len(bots)
        if n in MARKGL:
            # body only: ignore the mark when measuring, then move the mark with the body top
            continue
        if form in ('init', 'medi') and n not in HEAVY_FULL:
            tt_ = ob[3] + JOINED_BLEND * (tt_ - ob[3]); tb_ = ob[1] + JOINED_BLEND * (tb_ - ob[1])
        data[n] = (ob[3], tt_, ob[1], tb_)
# apply the same correction to every form that shares the shape family (init/medi of the same letter keep their own measurement)
for n, (top, tt_, bot, tb_) in data.items():
    adjust(n, top, tt_, bot, tb_)
# letters carrying hamza / madda: follow their base letter, marks ride along
base = {'wawHamza.isol': 'waw.isol', 'wawHamza.fina': 'waw.fina', 'yehHamza.isol': 'yeh.isol', 'yehHamza.fina': 'alefMaksura.fina'}
for n, b in base.items():
    if b in data:
        top, tt_, bot, tb_ = data[b]
        adjust(n, top, tt_, bot, tb_, markfloor=30 if 'yeh' in n else 400)
# alef + hamza/madda: shorter alef (650) and the mark sits closer, like the references
for n in ('alefHamzaAbove.isol', 'alefHamzaAbove.fina', 'alefMadda.isol', 'alefMadda.fina'):
    adjust(n, 708, 650, 0, 0, markfloor=720, markd=-80)
tt.save(P)
print('\n'.join(log)); print(len(log), 'glyphs aligned')
