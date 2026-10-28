"""Run the labview-mcp pylabview composer (aixml2vi.py) with the fixtures' additions:
style="Listbox" (listbox_composer.py) and the VI Server classes Pane and Splitter
(tools/aixml/pane_parts.py, parts harvested from NI's VIs).

usage: <labview-mcp>\\bin\\pylabview\\python.exe complex_composer.py <aixml2vi.py> <aixml2vi args...>
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), "tools", "aixml"))
import listbox_composer  # noqa: E402
import pane_parts  # noqa: E402

a2v = listbox_composer.load(sys.argv[1])
listbox_composer.patch(a2v)
pane_parts.patch_composer(a2v)
sys.exit(a2v.main(sys.argv[2:]))
