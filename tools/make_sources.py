"""Write the final designs (sample TTFs) back into the UFO sources, rewrite features.fea for the new geometry,
and set family metadata for Google Fonts. Output: release/sources/*.ufo  (build with fontmake / gftools)."""
import sys, json, re, shutil, os
sys.path.insert(0, '/home/claude/fa')
import ufoLib2
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
REPO = 'https://github.com/amoor070-coder/ameer-070'
LXH, LCAP = 476, 636
WEIGHTS = {'Light': 300, 'Regular': 400, 'Bold': 700, 'Black': 900}
os.makedirs('release/sources', exist_ok=True)
def ink(gs, n):
    b = BoundsPen(gs); gs[n].draw(b); return b.bounds
def top_anchor(t, gs, n):
    """x: centre of the ink in the top band; y: top ink + gap"""
    rp = RecordingPen(); gs[n].draw(rp)
    pts = [p for op, a in rp.value for p in a]
    if not pts: return None
    ys = [p[1] for p in pts]; top, bot = max(ys), min(ys)
    band = [p[0] for p in pts if p[1] >= top - max(120, 0.22 * (top - bot))]
    bandb = [p[0] for p in pts if p[1] <= bot + max(120, 0.22 * (top - bot))]
    return ((min(band) + max(band)) / 2, top + 62, (min(bandb) + max(bandb)) / 2, min(bot, 0) - 58)

def lig_anchors(gs, n):
    """lam-alef ligatures: (lam top, lam bottom, alef top, alef bottom) anchors from the two stems"""
    import skia, numpy as np
    rp = RecordingPen(); gs[n].draw(rp)
    sp = skia.Path()
    for op, a in rp.value:
        if op == 'moveTo': sp.moveTo(*a[0])
        elif op == 'lineTo': sp.lineTo(*a[0])
        elif op == 'qCurveTo':
            pp = list(a)
            while len(pp) > 2:
                mid = ((pp[0][0] + pp[1][0]) / 2, (pp[0][1] + pp[1][1]) / 2); sp.quadTo(*pp[0], *mid); pp = pp[1:]
            sp.quadTo(*pp[0], *pp[1])
        elif op == 'curveTo': sp.cubicTo(*a[0], *a[1], *a[2])
        elif op == 'closePath': sp.close()
    Wd, Ht = 1200, 1400
    surf = skia.Surface(Wd, Ht); c = surf.getCanvas(); c.clear(0)
    m = skia.Matrix(); m.setAll(1, 0, 100, 0, -1, 1100, 0, 0, 1); c.concat(m)
    c.drawPath(sp, skia.Paint(AntiAlias=False, Color=0xFFFFFFFF))
    a = surf.toarray()[:, :, 0] > 0
    band = a[1100 - 600:1100 - 380, :]           # y 380..600: only the two stems are inked here
    cols = np.where(band.any(axis=0))[0]
    runs = np.split(cols, np.where(np.diff(cols) > 1)[0] + 1)
    runs = [r for r in runs if len(r) > 10]
    if len(runs) < 2: return None
    def top_at(r):
        x0, x1 = r[0] - 60, r[-1] + 60
        ys = np.where(a[:, max(0, x0):x1].any(axis=1))[0]
        return 1100 - ys.min()
    alef, lam = runs[0], runs[-1]
    lx, ax = (lam[0] + lam[-1]) / 2 - 100, (alef[0] + alef[-1]) / 2 - 100
    return lx, top_at(lam) + 62, ax, top_at(alef) + 62
for wt, wc in WEIGHTS.items():
    src = f'src/sources/Ameer070-{wt}.ufo'; dst = f'release/sources/Ameer070-{wt}.ufo'
    shutil.rmtree(dst, ignore_errors=True); shutil.copytree(src, dst)
    u = ufoLib2.Font.open(dst)
    t = TTFont(f'sample/Ameer070-{wt}-sample.ttf'); gs = t.getGlyphSet(); hm = t['hmtx']
    rev = {}
    for cp, n in t.getBestCmap().items(): rev.setdefault(n, []).append(cp)
    order = list(u.lib.get('public.glyphOrder', [])) or list(u.keys())
    for n in t.getGlyphOrder():
        g = u[n] if n in u else u.newGlyph(n)
        g.clearContours(); g.clearComponents(); g.anchors.clear() if hasattr(g.anchors, 'clear') else None
        gs[n].draw(ReverseContourPen(g.getPen()))   # UFO = PostScript direction
        g.width = hm[n][0]; g.unicodes = sorted(rev.get(n, []))
        if n not in order: order.append(n)
    u.lib['public.glyphOrder'] = order
    # ---- metadata
    i = u.info
    i.versionMajor, i.versionMinor = 2, 1
    i.copyright = (f'Copyright 2026 The Ameer 070 Project Authors ({REPO}). '
                   'Hamza forms adapted from Alexandria, Copyright 2022 The Alexandria Project Authors (https://github.com/Gue3bara/Alexandria).')
    i.openTypeNameDesigner = 'Ameer Ibrahim'
    i.openTypeNameDesignerURL = REPO; i.openTypeNameManufacturerURL = REPO
    i.openTypeNameManufacturer = 'Ameer 070 Project'
    i.openTypeNameLicense = ('This Font Software is licensed under the SIL Open Font License, Version 1.1. '
                             'This license is available with a FAQ at: https://openfontlicense.org')
    i.openTypeNameLicenseURL = 'https://openfontlicense.org'
    i.familyName = 'Ameer 070'
    i.styleName = wt
    i.xHeight, i.capHeight = LXH, LCAP
    i.openTypeOS2WeightClass = wc
    if wt in ('Regular', 'Bold'):
        i.styleMapFamilyName = 'Ameer 070'; i.styleMapStyleName = wt.lower()
        i.openTypeNamePreferredFamilyName = None; i.openTypeNamePreferredSubfamilyName = None
    else:
        i.styleMapFamilyName = f'Ameer 070 {wt}'; i.styleMapStyleName = 'regular'
        i.openTypeNamePreferredFamilyName = 'Ameer 070'; i.openTypeNamePreferredSubfamilyName = wt
    i.openTypeOS2WinAscent, i.openTypeOS2WinDescent = 1650, 920      # room for stacked tashkeel on Windows
    i.openTypeOS2TypoAscender, i.openTypeOS2TypoDescender, i.openTypeOS2TypoLineGap = 1104, -392, 0
    i.openTypeHheaAscender, i.openTypeHheaDescender, i.openTypeHheaLineGap = 1104, -392, 0
    i.openTypeOS2Selection = [7]
    i.openTypeOS2Type = []
    i.openTypeGaspRangeRecords = [{'rangeMaxPPEM': 65535, 'rangeGaspBehavior': [0, 1, 2, 3]}]
    i.openTypeOS2VendorID = 'NONE'
    i.openTypeNameUniqueID = None; i.openTypeNameVersion = None; i.postscriptFontName = None; i.postscriptFullName = None
    # ---- features
    fea = u.features.text
    neutral = set(json.load(open(f'work/neutral_{wt}.json')))
    # mark anchors from the new outlines
    def repl(m):
        n = m.group(1)
        if n not in gs: return m.group(0)
        a = top_anchor(t, gs, n)
        if not a: return m.group(0)
        return f'    pos base {n} <anchor {round(a[0])} {round(a[1])}> mark @MARK_TOP <anchor {round(a[2])} {round(a[3])}> mark @MARK_BOTTOM;'
    fea = re.sub(r'^    pos base (\S+) <anchor -?\d+ -?\d+> mark @MARK_TOP <anchor -?\d+ -?\d+> mark @MARK_BOTTOM;', repl, fea, flags=re.M)
    def lrepl(m):
        n = m.group(1)
        if n not in gs: return m.group(0)
        r = lig_anchors(gs, n)
        if not r: return m.group(0)
        lx, ly, ax, ay = r
        b1, b2 = m.group(3), m.group(5)
        return (f'    pos ligature {n} <anchor {round(lx)} {round(ly)}> mark @MARK_TOP <anchor {round(lx)} {b1}> mark @MARK_BOTTOM '
                f'ligComponent <anchor {round(ax)} {round(ay)}> mark @MARK_TOP <anchor {round(ax)} {b2}> mark @MARK_BOTTOM;')
    fea = re.sub(r'^    pos ligature (lamAlef\S*) <anchor (-?\d+) -?\d+> mark @MARK_TOP <anchor -?\d+ (-?\d+)> mark @MARK_BOTTOM ligComponent <anchor (-?\d+) -?\d+> mark @MARK_TOP <anchor -?\d+ (-?\d+)> mark @MARK_BOTTOM;', lrepl, fea, flags=re.M)
    # Latin kerning: the new optical pairs
    pairs = json.load(open(f'work/kern_{wt}.json'))
    body = '\n'.join(f'    pos {a} {b} {v};' for a, b, v in pairs)
    fea = re.sub(r'lookup KERN_LATN \{.*?\} KERN_LATN;', 'lookup KERN_LATN {\n    lookupflag IgnoreMarks;\n' + body + '\n} KERN_LATN;', fea, flags=re.S)
    # Arabic kerning: drop pairs that touch redrawn letters (their spacing is now in the outlines)
    def arab(m):
        lines = m.group(0).split('\n'); out = []
        for L in lines:
            mm = re.match(r'\s*pos (\S+) (\S+) ', L)
            if mm and (mm.group(1) in neutral or mm.group(2) in neutral): continue
            out.append(L)
        return '\n'.join(out)
    fea = re.sub(r'lookup KERN_ARAB \{.*?\} KERN_ARAB;', arab, fea, flags=re.S)
    fea = re.sub(r'feature ss01 \{.*?\} ss01;\n', '', fea, flags=re.S)
    # dotted circle carries Arabic marks (for showing tashkeel alone)
    if 'uni25CC' in gs and 'pos base uni25CC' not in fea:
        a = top_anchor(t, gs, 'uni25CC')
        fea = fea.replace('feature mark {\n  script arab;\n', 'feature mark {\n  script arab;\n' + f'    pos base uni25CC <anchor {round(a[0])} {round(a[1])}> mark @MARK_TOP <anchor {round(a[2])} {round(a[3])}> mark @MARK_BOTTOM;\n', 1)
    sv = f'work/solve_{wt}.fea'
    if os.environ.get('SOLVE') == '1' and os.path.exists(sv):
        fea += '\n# contextual tashkeel clearance (qa/ctxsolve.py)\n' + open(sv).read()
    u.features.text = fea
    u.save(dst, overwrite=True)
    print(wt, 'ufo written', len(t.getGlyphOrder()), 'glyphs, latin kern', len(pairs))
