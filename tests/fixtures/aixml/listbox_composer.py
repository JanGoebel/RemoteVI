"""Run the labview-mcp pylabview composer (aixml2vi.py) with one addition: style="Listbox".

The composer has harvested listbox parts (parts/fpdco__listbox__*), but no AIXML style selects
them, so a listbox cannot be written - and a static Double Click frame is refused on anything else
("an event of a listbox only"). This wrapper makes a <Control style="Listbox" type="int32"> use a
listbox-class part, exactly as style="Ring" selects the ring part. Nothing else changes; the plugin's
files are not touched.

Which part: the system-style list of NI's dlgRenamedOnDisk.vi (an indicator part, flipped to a
control the way the composer flips any part). LabVIEW loads it as a MULTICOLUMN listbox (class
MulticolumnListbox, measured); RemoteVI Fixture Arrange.vi cuts it to one column without headers,
so it looks and behaves like a listbox, Double Click event included. Its rows start 2 px inside the
body, as the tests assume (first row at body top + 8). The plain listbox part, from Exporting
VIs.vi, has a 12 px frame - a click at body top + 8 lands on the frame (measured) - so it is left
out.

usage: <labview-mcp>\\bin\\pylabview\\python.exe listbox_composer.py <aixml2vi.py> <aixml2vi args...>
"""
import importlib.util
import os
import sys

composer_py = sys.argv[1]
sys.path.insert(0, os.path.dirname(composer_py))
spec = importlib.util.spec_from_file_location("aixml2vi", composer_py)
a2v = importlib.util.module_from_spec(spec)
sys.modules["aixml2vi"] = a2v
spec.loader.exec_module(a2v)

_add_fp = a2v.Composer.add_fp
_build_ddo = a2v.Composer.build_ddo
_keys = a2v.Composer._keys


def add_fp(self, el, row):
    if el.get("style") != "Listbox":
        return _add_fp(self, el, row)
    if el.get("type") != "int32":
        raise a2v.Unsupported("style Listbox needs type int32 (the part's value type)")
    el.attrib.pop("style")
    self._listbox_next = True
    try:
        return _add_fp(self, el, row)
    finally:
        self._listbox_next = False
        el.set("style", "Listbox")


def build_ddo(self, tree, is_ind, prefix="fpdco", tag="ddo", in_array=False, force_class=None):
    if getattr(self, "_listbox_next", False) and prefix == "fpdco" and force_class is None:
        self._listbox_next = False
        force_class = "listbox"
    out = _build_ddo(self, tree, is_ind, prefix, tag, in_array, force_class)
    if force_class == "listbox":
        # A part cut from a VI where a Property Node refers to the listbox says so in its annex
        # (hGrowNodeListLength 1). Here no node does, and LabVIEW reports that dangling list as a
        # FATAL insanity (Insane Annex / CrossList in FPHP) and aborts - measured on the
        # Exporting VIs.vi part.
        for annex in out[0].iter("SL__arrayElement"):
            if annex.get("class") == "annex":
                for e in annex.findall("hGrowNodeListLength"):
                    annex.remove(e)
    return out


def keys(self, prefix):
    found = _keys(self, prefix)
    if prefix == "fpdco/listbox/":
        found = [k for k in found if k != "fpdco/listbox/ctl/NumInt32"]
    return found


a2v.Composer.add_fp = add_fp
a2v.Composer.build_ddo = build_ddo
a2v.Composer._keys = keys
sys.exit(a2v.main(sys.argv[2:]))
