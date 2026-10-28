"""Compose the VIs of tests/fixtures/RemoteVI Complex Fixture.vi from their AIXML.

Uses complex_composer.py (the plugin composer plus style="Listbox" and the Pane/Splitter classes),
then fix_event_data_nodes.py on every VI with an event structure. Writes:

  tests/fixtures/RemoteVI Complex Fixture <helper>.vi   helpers, views, the inspector window, Arrange
  tests/fixtures/build/Complex Scaffold.vi              the fixture's diagram and controls, to be
                                                        grafted into the splitter panel (see below)

The panel itself cannot be composed (no splitters in AIXML). The full build is:

  1. python compose_complex.py <labview-mcp bin>
  2. copy NI's examples\\Controls and Indicators\\Containers\\Resizable Panel with Splitter Bars.vi
     to tests/fixtures/build/Complex Panel.vi and run RemoteVI Complex Fixture Prep Panel.vi on it
     (deletes the example's controls and decorations, keeps the panes and the splitter bars)
  3. lvai_graft_diagram panel=build/Complex Panel.vi scaffold=build/Complex Scaffold.vi
     output=tests/fixtures/RemoteVI Complex Fixture.vi allowNewControls replaceDiagram
     (graft needs an active project; any empty one does). The fixture's diagram has no Event
     Structure - the graft re-registers static Value Change events only - so its event loop is the
     subVI RemoteVI Complex Fixture Events.vi with every event registered dynamically.
  4. run RemoteVI Complex Fixture Paste.vi once (pastes the tab control, subpanel, slide, knob, tree
     and cursor graph, which AIXML cannot make - the composer's slide and knob parts crash LabVIEW
     2025 on load), with
       Donors       [tests\\fixtures\\build\\Fixture Tab Panel.vi,
                     <examples>\\Controls and Indicators\\Containers\\Multiple VIs in a Subpanel.vi,
                     <examples>\\Signal Processing\\Signal Generation\\Function Generator with FM.vi (twice),
                     <examples>\\Controls and Indicators\\Tree\\Tree.vi,
                     <examples>\\Controls and Indicators\\Graphs and Charts\\Graphs - General\\Graph Cursors.vi]
       Donor Labels [Tab, Subpanel, FM Deviation (Hz), Baseband Frequency (Hz), Single Selection Tree,
                     Mixed Signal Graph]
       Labels       [Settings, Viewer, Rate, Level, Nav, Scope]
       Pane         [2, 2, 2, 2, 0, 2]
  5. run RemoteVI Complex Fixture Arrange.vi (Fixture, Views = View A, View B, Inspector): lays every
     control out in its pane or tab page, adds the third page, sets pane scaling, tip strips and the
     window, hides the views' Quit switches, and saves.

The larger AIXML files are written by the generators in gen/ (their frames and rows repeat).

usage: compose_complex.py <labview-mcp bin dir> [name ...]   (no names: all, in dependency order)
"""
import os
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))
fixtures = os.path.dirname(here)
repo = os.path.dirname(os.path.dirname(fixtures))
bin_dir = sys.argv[1]
py = os.path.join(bin_dir, "pylabview", "python.exe")
pylv = os.path.join(bin_dir, "pylabview", "pylabview.cmd")
composer = os.path.join(bin_dir, "scripts", "aixml-pylabview", "aixml2vi.py")

ORDER = [
    ("RemoteVI Complex Fixture Children", None),
    ("RemoteVI Complex Fixture All Controls", None),
    ("RemoteVI Complex Fixture Layout", None),
    ("RemoteVI Complex Fixture Find Controls", None),
    ("RemoteVI Complex Fixture Value Text", None),
    ("RemoteVI Complex Fixture Refs", None),
    ("RemoteVI Complex Fixture Button Refs", None),
    ("RemoteVI Complex Fixture Events", None),
    ("RemoteVI Complex View A", None),
    ("RemoteVI Complex View B", None),
    ("RemoteVI Complex Inspector", None),
    ("RemoteVI Complex Fixture Prep Panel", None),
    ("RemoteVI Complex Fixture Paste", None),
    ("RemoteVI Complex Fixture Arrange", None),
    ("RemoteVI Complex Fixture", os.path.join(fixtures, "build", "Complex Scaffold.vi")),
]
want = sys.argv[2:]
for name, out in ORDER:
    if want and name not in want:
        continue
    src = os.path.join(here, name + ".xml")
    vi = out or os.path.join(fixtures, name + ".vi")
    text = open(src, encoding="utf-8").read()
    text = text.replace('target="../../source/API/RemoteVI Start.vi"', 'target="RemoteVI Start.vi"')
    text = text.replace('target="../../source/API/RemoteVI Stop.vi"', 'target="RemoteVI Stop.vi"')
    tmp = os.path.join(os.environ.get("TEMP", here), name + ".compose.xml")
    open(tmp, "w", encoding="utf-8", newline="\n").write(text)
    r = subprocess.run([py, os.path.join(here, "complex_composer.py"), composer, "--lv-version", "25",
                        "--search", fixtures, "--search", os.path.join(repo, "source", "API"), "--search", os.path.join(repo, "source", "Server"), "--search", os.path.join(repo, "source", "Win32"), tmp, vi],
                       capture_output=True, text=True)
    last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    print(name, "->", last if not r.returncode else "FAILED\n" + (r.stderr or r.stdout)[-2000:])
    if r.returncode:
        sys.exit(1)
    if "Event Structure" in text:
        work = os.path.join(os.environ.get("TEMP", here), name + ".edn")
        subprocess.run([py, os.path.join(here, "fix_event_data_nodes.py"), pylv, vi, work], check=True)
