"""Compose a VI from an AIXML source with labview-mcp's pylabview composer, directly.

Why this exists: the Server VIs carry TCP connection refnums on their wires. The composer
refuses a wire type it has not measured yet ("net ... carries a Refnum.TCPNetConn, which no
composed wire has carried yet"), and the MCP tool offers no way to opt in. The composer itself
does: AIXML2VI_TRY_WIRES=Refnum.TCPNetConn. Measured 2026-10-23 on LabVIEW 2025 64-bit: a probe
VI that accepts a connection, type-casts the refnum to U32 and back, writes and reads over it
ran clean (no insanity), and so do the Server VIs built with this script.

Usage (bundled Python of labview-mcp; it ignores PYTHONPATH):
    <labview-mcp>\\bin\\pylabview\\python.exe tools\\aixml\\compose.py <source.xml> <target.vi>

The source may use symbolic uids (uid="read", nets "read.data"); they are numbered here,
the same way the MCP server numbers them, before the composer sees the file.
"""
import os
import re
import subprocess
import sys
import tempfile

def _newest_lvmcp_bin():
    """bin folder of the newest labview-mcp plugin version installed for Claude Code."""
    root = os.path.expandvars(r"%USERPROFILE%\.claude\plugins\cache\zuehlke-labview\labview-mcp")
    vers = [v for v in os.listdir(root) if os.path.isdir(os.path.join(root, v, "bin"))] if os.path.isdir(root) else []
    vers.sort(key=lambda v: [int(x) if x.isdigit() else 0 for x in v.split(".")])
    return os.path.join(root, vers[-1], "bin") if vers else os.path.join(root, "bin")


LVMCP_BIN = os.environ.get("LVMCP_BIN") or _newest_lvmcp_bin()
COMPOSER = os.path.join(LVMCP_BIN, "scripts", "aixml-pylabview", "aixml2vi.py")
PYTHON = os.path.join(LVMCP_BIN, "pylabview", "python.exe")


def number_symbols(text):
    """Replace every non-numeric uid with a number from 5000 up, in uid/uid_parent and in every
    net reference (`sym.terminal`) inside inputs/outputs/selectin/selectout/maxin/count/cond."""
    syms = []
    for m in re.finditer(r'\buid="([^"]+)"', text):
        s = m.group(1)
        if not s.isdigit() and s not in syms:
            syms.append(s)
    num = {s: str(5000 + i) for i, s in enumerate(syms)}

    def fix_uid(m):
        return '%s="%s"' % (m.group(1), num.get(m.group(2), m.group(2)))
    text = re.sub(r'\b(uid|uid_parent)="([^"]*)"', fix_uid, text)

    def fix_nets(m):
        attr, val = m.group(1), m.group(2)
        parts = []
        for entry in val.split(","):
            # entry is "terminal:net" (inputs/outputs) or a bare net (selectin, maxin, count ...)
            if attr in ("inputs", "outputs"):
                if ":" not in entry:
                    parts.append(entry)
                    continue
                term, net = entry.split(":", 1)
            else:
                term, net = None, entry
            if "." in net:
                head, rest = net.split(".", 1)
                net = num.get(head, head) + "." + rest
            parts.append(net if term is None else term + ":" + net)
        return '%s="%s"' % (attr, ",".join(parts))
    text = re.sub(r'\b(inputs|outputs|selectin|selectout|maxin|maxout|count|cond)="([^"]*)"', fix_nets, text)
    return text


def main(argv):
    src, out_vi = argv[0], os.path.abspath(argv[1])
    with open(src, encoding="utf-8") as f:
        text = number_symbols(f.read())
    fd, tmp = tempfile.mkstemp(suffix=".xml", prefix=os.path.splitext(os.path.basename(src))[0] + "_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    env = dict(os.environ)
    env["AIXML2VI_TRY_WIRES"] = "Refnum.TCPNetConn"
    # pane_parts.py: the composer plus the VI Server classes Pane and Splitter (Read Tips converts pane coordinates)
    cmd = [PYTHON, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pane_parts.py"), "compose", "--lv-version", "25", tmp, out_vi] + sum((["--search", d] for d in argv[2:]), [])
    rc = subprocess.call(cmd, env=env)
    if rc == 0:
        os.remove(tmp)
    else:
        print("numbered source kept: %s" % tmp, file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
