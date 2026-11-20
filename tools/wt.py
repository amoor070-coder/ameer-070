"""Per-weight configuration. Select with env WT=Light|Regular|Bold|Black (default Regular)."""
import os
WT = os.environ.get('WT', 'Regular')
CFG = {
    # W: Arabic monoline stroke, WL: Latin stroke, old: stem of v1.200, alex: Alexandria wght, plex: IBM Plex ref
    'Light':   dict(W=57,  WL=62,  old=52,  alex=300, plex='/home/claude/fa/refs/plexLight.ttf', skx=0.985, sky=1.0),
    'Regular': dict(W=79,  WL=86,  old=77,  alex=400, plex='/home/claude/fa/plexR.ttf',          skx=1.0, sky=1.0),
    'Bold':    dict(W=124, WL=140, old=106, alex=700, plex='/home/claude/fa/plexB.ttf',          skx=1.07, sky=0.86),
    'Black':   dict(W=155, WL=164, old=135, alex=900, plex='/home/claude/fa/plexB.ttf',          skx=1.15, sky=0.74),
}[WT]
W, WL, OLD = CFG['W'], CFG['WL'], CFG['old']
K = W / 79.0                     # weight ratio vs the approved Regular
OLDSRC = f'/home/claude/fa/ameer/Ameer070-{WT}.ttf'
BASE = f'/home/claude/fa/work/Ameer070-{WT}-base.ttf'
OUT = f'/home/claude/fa/sample/Ameer070-{WT}-sample.ttf'
ALEX = f'/home/claude/fa/alex{CFG["alex"]}.ttf'
PLEX = CFG['plex']
DOTMAX = 140 * (1 + (K - 1) * 0.6)   # contour size below which a contour counts as a dot

# Latin vertical ruler (average of Alexandria + IBM Plex, normalised to our alef 708) - same in every weight
LXH, LCAP, LASC, LDSC = 476, 636, 675, -180
