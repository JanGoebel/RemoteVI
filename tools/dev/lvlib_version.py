"""Marks LabVIEW library files (.lvlib) as saved by an older LabVIEW, by default 2020 (20.0).

    python tools/dev/lvlib_version.py [--major 20] <file.lvlib> ...

The repository is kept loadable in LabVIEW 2020. A library saved by a newer LabVIEW carries
that version in three places, and LabVIEW 2020 refuses the whole library (error 122, "created
in a more recent version"), which breaks every member VI:
  * <Library LVVersion="25008000">
  * NI.Lib.SourceVersion (the same number in decimal)
  * NI.Lib.Icon: LabVIEW's flattened image, ASCII-encoded 6 bits per character from '!';
    its first three bytes are the version again (2020: ")!#!", 2025: "*1#!").
The image data after that header is the same in 2020 and later, so only the header changes.
Line endings and everything else in the file are kept byte for byte.
"""
import re
import sys


def encode_version_prefix(major_bcd):
    # bytes major, 0x00, 0x80 -> four 6-bit characters offset by '!'
    bits = (major_bcd << 16) | 0x0080
    return bytes(33 + ((bits >> s) & 0x3F) for s in (18, 12, 6, 0))


def convert(path, major):
    major_bcd = int(str(major), 16)              # 20 -> 0x20
    version = (major_bcd << 24) | 0x8000         # 0x20008000
    with open(path, "rb") as f:
        data = f.read()
    out = re.sub(rb'LVVersion="\d+"', b'LVVersion="%08X"' % version, data, count=1)
    out = re.sub(rb'(NI\.Lib\.SourceVersion" Type="Int">)\d+<', rb"\g<1>%d<" % version, out)
    prefix = encode_version_prefix(major_bcd)
    out = re.sub(rb'(NI\.Lib\.Icon" Type="Bin">)....', lambda m: m.group(1) + prefix, out)
    if out != data:
        with open(path, "wb") as f:
            f.write(out)
    return out != data


def main(argv):
    major = 20
    if argv[:1] == ["--major"]:
        major, argv = int(argv[1]), argv[2:]
    for p in argv:
        print("%s %s" % ("converted" if convert(p, major) else "unchanged", p))


if __name__ == "__main__":
    main(sys.argv[1:])
