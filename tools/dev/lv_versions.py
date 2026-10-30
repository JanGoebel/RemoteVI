"""Prints the LabVIEW version each VI/CTL file was saved in (its 'vers' resource), and a summary.

    python tools/dev/lv_versions.py [root] [--expect 20.0]

With --expect, exits 1 when a file was saved in another version. The repository is kept saved
for LabVIEW 2020 (20.0) so that 2020 and every newer LabVIEW can open it.
"""
import os
import struct
import sys
from collections import Counter

EXTS = (".vi", ".ctl", ".vit", ".vim", ".ctt")
SKIP = {".git", "builds", "node_modules"}


def bcd(b):
    return (b >> 4) * 10 + (b & 0xF)


def version(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:6] != b"RSRC\r\n":
        raise ValueError("not a LabVIEW resource file")
    rsrc_off, _, data_off, _ = struct.unpack(">4I", data[16:32])
    info = rsrc_off + 32
    bi_off = struct.unpack(">I", data[info + 12:info + 16])[0]
    bi = rsrc_off + bi_off
    count = struct.unpack(">I", data[bi:bi + 4])[0] + 1
    for i in range(count):
        ident, _, sec_off = struct.unpack(">4sII", data[bi + 4 + 12 * i:bi + 16 + 12 * i])
        if ident == b"vers":
            sec = bi + sec_off
            d_off = struct.unpack(">I", data[sec + 12:sec + 16])[0]
            p = data_off + d_off + 4
            major, minor = data[p], data[p + 1]
            return "%d.%d" % (bcd(major), minor >> 4)
    raise ValueError("no vers block")


def main(argv):
    expect = None
    if "--expect" in argv:
        i = argv.index("--expect")
        expect = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    root = argv[0] if argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    counts, wrong = Counter(), []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP and not x.startswith(".")]
        for name in files:
            if name.lower().endswith(EXTS):
                p = os.path.join(d, name)
                try:
                    v = version(p)
                except Exception as ex:  # noqa: BLE001 - report and go on
                    v = "unreadable (%s)" % ex
                counts[v] += 1
                if expect and v != expect:
                    wrong.append((v, os.path.relpath(p, root)))
    for v, n in sorted(counts.items()):
        print("%s\t%d" % (v, n))
    for v, p in sorted(wrong):
        print("  %s\t%s" % (v, p))
    return 1 if wrong else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
