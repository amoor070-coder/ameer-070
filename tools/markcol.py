"""Mark collision checker: shapes vocalised letter pairs; reports marks whose ink touches (or comes within GAP of) other ink."""
import uharfbuzz as hb, skia, numpy as np, sys, json, itertools
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
S=0.1; GAP=int(sys.argv[3]) if len(sys.argv)>3 else 20
path=sys.argv[1]
t=TTFont(path); go=t.getGlyphOrder(); gs=t.getGlyphSet(); gdef=t['GDEF'].table.GlyphClassDef.classDefs
f=hb.Font(hb.Face(hb.Blob.from_file_path(path)))
cache={}
def gpath(n):
    if n in cache: return cache[n]
    rp=RecordingPen(); gs[n].draw(rp); sp=skia.Path()
    for op,a in rp.value:
        if op=='moveTo': sp.moveTo(*a[0])
        elif op=='lineTo': sp.lineTo(*a[0])
        elif op=='qCurveTo':
            pp=list(a)
            while len(pp)>2:
                mid=((pp[0][0]+pp[1][0])/2,(pp[0][1]+pp[1][1])/2); sp.quadTo(*pp[0],*mid); pp=pp[1:]
            sp.quadTo(*pp[0],*pp[1])
        elif op=='curveTo': sp.cubicTo(*a[0],*a[1],*a[2])
        elif op=='closePath': sp.close()
    cache[n]=sp; return sp
def mask(sp,dx,dy,W,H):
    surf=skia.Surface(W,H); c=surf.getCanvas(); c.clear(0)
    m=skia.Matrix(); m.setAll(S,0,S*dx+20, 0,-S,S*(1500-dy), 0,0,1)
    c.concat(m); c.drawPath(sp,skia.Paint(AntiAlias=False,Color=0xFFFFFFFF))
    return surf.toarray()[:,:,0]>0
def dil(a,r):
    out=a.copy()
    for dx in range(-r,r+1):
        for dy in range(-r,r+1):
            if dx*dx+dy*dy<=r*r: out|=np.roll(np.roll(a,dx,1),dy,0)
    return out
def check(text):
    b=hb.Buffer(); b.add_str(text); b.guess_segment_properties(); hb.shape(f,b)
    tot=sum(p.x_advance for p in b.glyph_positions); W=int(tot*S)+40; H=int(2600*S)
    x=0; items=[]
    for i,p in zip(b.glyph_infos,b.glyph_positions):
        n=go[i.codepoint]; items.append((n,gdef.get(n)==3,i.cluster,mask(gpath(n),x+p.x_offset,p.y_offset,W,H))); x+=p.x_advance
    bad=[]
    r=max(1,int(GAP*S))
    for k,(n,ism,cl,m) in enumerate(items):
        if not ism: continue
        md=dil(m,r)
        for j,(n2,ism2,cl2,m2) in enumerate(items):
            if j==k: continue
            if (md&m2).any(): bad.append((n,n2,int((md&m2).sum())))
    return bad
if __name__=='__main__':
    words=open(sys.argv[2]).read().split()
    res={}
    for w in words:
        bd=check(w)
        if bd: res[w]=bd
    print(len(res),'/',len(words))
    json.dump(res,open(sys.argv[4] if len(sys.argv)>4 else '/tmp/markcol.json','w'),ensure_ascii=False)
