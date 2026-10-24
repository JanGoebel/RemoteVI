"""Post-compose fix for RemoteVI Fixture Scaffold.vi (pylabview composer, labview-mcp 2.2.0).

The composer numbers an Event Data Node's fields by their position among the TOP-LEVEL fields of
the event data cluster, while LabVIEW numbers them FLATTENED - every element of a cluster field
counts too. Fields after a cluster field (Coords, Mods) therefore come out shifted:

  Mouse Down / Mouse Up: Source 0, Type 1, Time 2, CtlRef 3, Coords 4 (Horizontal 5, Vertical 6),
                         Button 7, Mods 8 (Double Click 9, Menu Key 10), PlatMods 11
  Key Down:              ... CtlRef 3, Char 4, VKey 5, ScanCode 6, Mods 7 (Num Pad 8, Menu Key 9),
                         PlatMods 10
  Double Click (listbox): ... CtlRef 3, Coords 4 (5, 6), Button 7, Mods 8 (9, 10),
                         PlatMods 11 (Shift 12, Ctrl 13, Alt 14, Cmd 15, Opt 16), Row 17
  Mouse Wheel:           ... CtlRef 3, Coords 4 (5, 6), Delta 7

The composer writes Button as 5 and PlatMods as 7 (mouse), PlatMods as 8 (key), Row as 8 (double
click), Delta as 5 (wheel). Fields before the first cluster (MenuRef, ItemTag) need no fix. This script
extracts the VI with the bundled pylabview, rewrites those <i> indices and rebuilds it.

usage: fix_event_data_nodes.py <pylabview.cmd> <vi> <workdir>
"""
import os
import re
import subprocess
import sys

pylv, vi, work = sys.argv[1:4]
os.makedirs(work, exist_ok=True)
xml = os.path.join(work, "vi.xml")
subprocess.run([pylv, "-x", "-i", vi, "-m", xml], check=True, capture_output=True)
bd = os.path.join(work, "vi_BDHb.xml")
s = open(bd, encoding="utf-8").read()

MAPS = {(3, 4, 5, 7): {5: 7, 7: 11},     # CtlRef, Coords, Button, PlatMods of a mouse event
        (3, 4, 5, 8): {8: 10},           # CtlRef, Char, VKey, PlatMods of a key event
        (3, 8): {8: 17},                 # CtlRef, Row of a listbox Double Click
        (3, 5): {5: 7}}                  # CtlRef, Delta of a Mouse Wheel
out, pos, fixed = [], 0, 0
for m in re.finditer(r'class="eventDataNode".*?</dcoList>', s, re.S):
    block = m.group(0)
    idx = tuple(int(x) for x in re.findall(r"<i>(\d+)</i>", block))
    mp = MAPS.get(idx)
    if mp:
        block = re.sub(r"<i>(\d+)</i>", lambda k: "<i>%d</i>" % mp.get(int(k.group(1)), int(k.group(1))), block)
        fixed += 1
    out.append(s[pos:m.start()])
    out.append(block)
    pos = m.end()
out.append(s[pos:])
open(bd, "w", encoding="utf-8").write("".join(out))
subprocess.run([pylv, "-c", "-m", xml, "-i", vi], check=True, capture_output=True)
print("event data nodes fixed:", fixed)
