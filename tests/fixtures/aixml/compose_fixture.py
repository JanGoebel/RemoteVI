"""Compose tests/fixtures/RemoteVI Fixture.vi from its AIXML with the labview-mcp pylabview composer.

Why not lvai_generate_vi: the fixture calls source/API/RemoteVI Start.vi and Stop.vi, which lie
outside the composer's search radius around tests/fixtures, so the composer must be run with
--search; List is a listbox, which the composer only writes through listbox_composer.py (adds
style="Listbox"); and the composed Event Data Nodes need fix_event_data_nodes.py afterwards.

After this, run RemoteVI Fixture Arrange.vi (path = the fixture) once with LabVIEW idle: it pastes
the tab control (AIXML cannot create one) from the prepared tab panel and lays out the panel.

usage: compose_fixture.py <labview-mcp bin dir> [<LabVIEW major, default 25>]
"""
import os
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))
fixtures = os.path.dirname(here)
repo = os.path.dirname(os.path.dirname(fixtures))
bin_dir = sys.argv[1]
major = sys.argv[2] if len(sys.argv) > 2 else "25"
py = os.path.join(bin_dir, "pylabview", "python.exe")
pylv = os.path.join(bin_dir, "pylabview", "pylabview.cmd")
composer = os.path.join(bin_dir, "scripts", "aixml-pylabview", "aixml2vi.py")

src = open(os.path.join(here, "RemoteVI Fixture.xml"), encoding="utf-8").read()
# the composer resolves bare names through --search; the relative spelling is only documentation
src = src.replace('target="../../source/API/RemoteVI Start.vi"', 'target="RemoteVI Start.vi"')
src = src.replace('target="../../source/API/RemoteVI Stop.vi"', 'target="RemoteVI Stop.vi"')
tmp = os.path.join(os.environ.get("TEMP", here), "RemoteVI Fixture.compose.xml")
open(tmp, "w", encoding="utf-8", newline="\n").write(src)
vi = os.path.join(fixtures, "RemoteVI Fixture.vi")
r = subprocess.run([py, os.path.join(here, "listbox_composer.py"), composer, "--lv-version", major, "--search", os.path.join(repo, "source", "API"), tmp, vi],
                   capture_output=True, text=True)
print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr)
if r.returncode:
    sys.exit(r.stderr)
work = os.path.join(os.environ.get("TEMP", here), "RemoteVI Fixture.edn")
subprocess.run([py, os.path.join(here, "fix_event_data_nodes.py"), pylv, vi, work], check=True)
