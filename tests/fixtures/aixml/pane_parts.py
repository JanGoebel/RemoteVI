"""Teach the labview-mcp pylabview composer and harvester the VI Server classes Pane and Splitter.

The composer's refnum table (parts/refnum-classes.tsv in the plugin) knows neither class, so a
Property or Invoke Node on a pane or a splitter bar can be neither harvested nor composed. This
module patches both tools in memory, without touching the plugin's files:

* LV.Pane is CtlFlags 0x004B (the type of {LV.Panel} Panes[] and {LV.Control} OwningPane in the
  harvested table), LV.Splitter 0x004C (read off NI's Slide Splitter.vi, see harvest below);
* parts are looked up in the plugin's parts directory first, then in EXTRA (this folder's
  `parts`), and the VI Server table of EXTRA is merged into the plugin's.

The parts in EXTRA are harvested from NI's own VIs with

    <labview-mcp>\\bin\\pylabview\\python.exe pane_parts.py harvest

so nothing in them is hand-made.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXTRA = os.path.join(HERE, "parts")
CLASSES = {"LV.Pane": "0x004B", "LV.Splitter": "0x004C"}

# NI VIs that carry Pane and Splitter nodes (read with the harvester; LabVIEW 2025)
LV = r"C:\Program Files\National Instruments\LabVIEW 2025"
DONORS = [
    LV + r"\vi.lib\MGI\Panel Manager\Panel\Window Position\Reference Position\Ref Ctrl\Reference Rectangle.vi",
    LV + r"\vi.lib\MGI\Monitored Actor\Classic Monitor\Logger\Classic Logger Actor\Slide Splitter.vi",
]


def patch_composer(a2v):
    """Pane and Splitter refnums, extra parts, merged VI Server table."""
    a2v.refnum_type("LV.VI", plain_class=True)  # loads the plugin's table first
    for cls, flags in CLASSES.items():
        a2v._REF_CLASSES.setdefault(cls, (flags, ""))
    _get = a2v.Parts.get

    def get(self, key):
        got = _get(self, key)
        if got is None and os.path.isdir(EXTRA) and self.d != EXTRA:
            got = _get(a2v.Parts(EXTRA), key)
        return got

    a2v.Parts.get = get
    _table = a2v.Composer._vi_server_table

    def table(self):
        t = getattr(self, "_vist", None)
        if t is not None:
            return t
        t = _table(self)
        p = os.path.join(EXTRA, "vi-server-props.json")
        if os.path.exists(p):
            extra = json.load(open(p, encoding="utf-8"))
            for k in ("classes", "props", "methods"):
                for cls, rows in extra.get(k, {}).items():
                    if isinstance(rows, dict) and k != "classes":
                        t.setdefault(k, {}).setdefault(cls, {}).update(
                            {n: r for n, r in rows.items() if n not in t[k].get(cls, {})})
                    else:
                        t.setdefault(k, {}).setdefault(cls, rows)
        self._vist = t
        return t

    a2v.Composer._vi_server_table = table


def harvest(plugin_scripts):
    sys.path.insert(0, plugin_scripts)
    import harvest_parts
    harvest_parts.ref_class(None)
    harvest_parts._REF_CLASS_BY_FLAGS = harvest_parts._REF_CLASS_BY_FLAGS or {}
    tsv = os.path.join(harvest_parts.lvheap.own_parts(), "refnum-classes.tsv")
    for line in open(tsv, encoding="utf-8"):
        row = line.rstrip("\r\n").split("\t")
        if line.startswith("#") or row[0] == "class" or len(row) < 2:
            continue
        harvest_parts._REF_CLASS_BY_FLAGS.setdefault(row[1].upper(), row[0])
    for cls, flags in CLASSES.items():
        harvest_parts._REF_CLASS_BY_FLAGS[flags.upper()] = cls
    os.makedirs(EXTRA, exist_ok=True)
    harvest_parts.main(["--props", EXTRA] + DONORS)


if __name__ == "__main__" and sys.argv[1:2] == ["harvest"]:
    harvest(sys.argv[2] if len(sys.argv) > 2 else os.path.expandvars(
        r"%USERPROFILE%\.claude\plugins\cache\zuehlke-labview\labview-mcp\2.2.0\bin\scripts\aixml-pylabview"))
