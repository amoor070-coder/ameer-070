"""post-build fixes for Google Fonts: smart dropout control (prep), gasp, keep fonts unhinted."""
import sys
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import ttProgram
for p in sys.argv[1:]:
    f = TTFont(p)
    prep = newTable('prep'); prep.program = ttProgram.Program()
    prep.program.fromAssembly(['PUSHW[ ]', '511', 'SCANCTRL[ ]', 'PUSHB[ ]', '4', 'SCANTYPE[ ]'])
    f['prep'] = prep
    gasp = newTable('gasp'); gasp.version = 1; gasp.gaspRange = {65535: 15}; f['gasp'] = gasp
    meta = newTable('meta'); meta.data = {'dlng': 'Arab, Latn', 'slng': 'Arab, Latn'}; f['meta'] = meta
    f.save(p); print('fixed', p)
