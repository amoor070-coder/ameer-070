import uharfbuzz as hb, json, sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.boundsPen import BoundsPen
LET = 'ابتثجحخدذرزسشصضطظعغفقكلمنهوي'+'ةىئؤأإآ'
ZWJ='\u200d'
NONJOIN=set('اأإآدذرزوؤة')
def forms(c):
    out={'isol':c}
    if c not in NONJOIN and c!='ء':
        out['init']=c+ZWJ; out['medi']=ZWJ+c+ZWJ
    if c!='ء': out['fina']=ZWJ+c
    return out
class F:
    def __init__(s,path):
        s.tt=TTFont(path); s.gs=s.tt.getGlyphSet()
        s.hb=hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        s.alef=s.body(s.gid('ا','isol'))[3]
    def gid(s,c,form):
        t=forms(c).get(form)
        if t is None: return None
        buf=hb.Buffer();buf.add_str(t);buf.guess_segment_properties();hb.shape(s.hb,buf)
        for i in buf.glyph_infos:
            n=s.hb.glyph_to_string(i.codepoint)
            if n not in ('uni200D','zwj','uni200d','space', s.tt.getBestCmap().get(0x200D)) and i.cluster==t.index(c): return n
        return None
    def body(s,n):
        r=DecomposingRecordingPen(s.gs); s.gs[n].draw(r)
        cs=[];cur=[]
        for op,a in r.value:
            cur.append((op,a))
            if op in('closePath','endPath'):cs.append(cur);cur=[]
        bb=None; ah=getattr(s,'alef',740)
        for c in cs:
            b=BoundsPen(None)
            for op,a in c:getattr(b,op)(*a)
            x=b.bounds
            if not x: continue
            if (x[2]-x[0])<0.27*ah and (x[3]-x[1])<0.27*ah: continue   # dots / small marks
            bb=x if bb is None else (min(bb[0],x[0]),min(bb[1],x[1]),max(bb[2],x[2]),max(bb[3],x[3]))
        return bb
if __name__=='__main__':
    ours=F(sys.argv[1] if len(sys.argv)>1 else 'sample/Ameer070-Regular-sample.ttf')
    refs=[F('alex400.ttf'),F('plexR.ttf')]
    res={}
    for c in LET:
        for form in forms(c):
            n=ours.gid(c,form)
            if not n: continue
            ob=ours.body(n)
            tops=[];bots=[]
            for r in refs:
                rn=r.gid(c,form); rb=r.body(rn) if rn else None
                if not rb: continue
                k=708/r.alef; tops.append(rb[3]*k); bots.append(rb[1]*k)
            if not tops or not ob: continue
            tt=sum(tops)/len(tops); tb=sum(bots)/len(bots)
            res[n]={'c':c,'form':form,'top':ob[3],'bot':ob[1],'ttop':round(tt),'tbot':round(tb)}
    json.dump(res,open('ruler.json','w'),ensure_ascii=False,indent=0)
    for n,v in res.items():
        dt=v['ttop']-v['top']; db=v['tbot']-v['bot']
        flag=('TOP%+d'%dt if abs(dt)>15 else '')+(' BOT%+d'%db if abs(db)>15 else '')
        if flag: print(f"{v['c']} {v['form']:5s} {n:22s} top {v['top']:.0f}->{v['ttop']}  bot {v['bot']:.0f}->{v['tbot']}  {flag}")
