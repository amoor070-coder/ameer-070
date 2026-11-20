#!/bin/bash
# usage: WT=Bold ./build.sh
set -e
cd /home/claude/fa
python3 embolden.py
python3 glyphs_r.py | tail -1
python3 latin_r.py | tail -1
python3 ruler.py | tail -1
python3 hruler.py | tail -1
python3 druler.py
python3 accents.py | tail -1
python3 symbols.py
python3 kern.py 2>/dev/null | head -1
python3 spacing.py | tail -1
