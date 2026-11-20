# Ameer 070 — أمير ٠٧٠

Bilingual Arabic + Latin sans-serif family, four weights (Light, Regular, Bold, Black).

## Building

```
pip install gftools
cd sources
gftools builder config.yaml
```

Fonts are written to `fonts/ttf`.

`tools/` contains the scripts used to draw and balance the design (Python + skia-pathops); the UFOs in `sources/` are the canonical source.

## License

SIL Open Font License 1.1 — see `OFL.txt`. Hamza forms adapted from Alexandria (OFL).

Note: `tools/` is the design archive (the scripts that drew and balanced the letters from the v1.200 masters
with the reference rulers). It is not part of the build; the UFOs in `sources/` are the canonical source.
