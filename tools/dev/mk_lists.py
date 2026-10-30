"""Writes items.txt and callers.txt for Add To Library Files.vi.
Items = every source VI without LIBN (read with pylabview) - after libdrop of their lvlib entries.
Callers = every other source VI plus the extra paths given on the command line."""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

d = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(d, '..', '..'))
src = os.path.join(REPO, 'source')
def _newest_lvmcp_bin():
    """bin folder of the newest labview-mcp plugin version installed for Claude Code."""
    root = os.path.expandvars(r"%USERPROFILE%\.claude\plugins\cache\zuehlke-labview\labview-mcp")
    vers = [v for v in os.listdir(root) if os.path.isdir(os.path.join(root, v, "bin"))] if os.path.isdir(root) else []
    vers.sort(key=lambda v: [int(x) if x.isdigit() else 0 for x in v.split(".")])
    return os.path.join(root, vers[-1], "bin") if vers else os.path.join(root, "bin")


B = os.path.join(os.environ.get('LVMCP_BIN') or _newest_lvmcp_bin(), 'pylabview')


def has_libn(vi):
    t = tempfile.mkdtemp()
    x = os.path.join(t, 'x.xml')
    subprocess.run([os.path.join(B, 'python.exe'), os.path.join(B, 'app', 'pylabview', 'readRSRC.py'), '-x', '-i', vi, '-m', x], capture_output=True)
    s = open(x, encoding='utf-8', errors='replace').read() if os.path.exists(x) else ''
    shutil.rmtree(t, ignore_errors=True)
    return bool(re.search(r'<LIBN>', s))


vis = sorted(glob.glob(os.path.join(src, '*', '*.vi')))
items = [v for v in vis if not has_libn(v)]
callers = [v for v in vis if v not in items] + sys.argv[1:]
open(os.path.join(d, 'items.txt'), 'w').write('\n'.join(items))
open(os.path.join(d, 'callers.txt'), 'w').write('\n'.join(callers))
# drop the stale lvlib entries of the items
lib = os.path.join(src, 'RemoteVI.lvlib')
t = open(lib, encoding='utf-8', newline='').read()
lines = t.split('\n')
names = [os.path.basename(v) for v in items]
out = [l for l in lines if not any(('Name="%s"' % n) in l for n in names)]
open(lib, 'w', encoding='utf-8', newline='').write('\n'.join(out))
print(len(items), 'items,', len(callers), 'callers,', len(lines) - len(out), 'lvlib entries dropped')
