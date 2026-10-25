#!/usr/bin/env python3
"""Regenerates RemoteVI.lvproj with VIRTUAL folders only (no auto-populating folders).

Auto-populating folders pull in every file under a directory (AIXML, scripts, test data) and
fight with the library, which already owns the toolkit VIs: they caused the "item already
exists" / "conflict" errors when VIs were re-added to RemoteVI.lvlib. So the project lists:

  RemoteVI.lvlib            the toolkit (its own virtual folders mirror source/)
  Examples/                 examples/*.vi
  Tests/Fixture, Tests/Caraya/...   test VIs (outside the library)
  Scripts/...               build scripts and Win32 wrapper templates
  Spikes/                   benchmarks

Run it after adding or removing a VI outside source/:   python scripts/gen-lvproj.py
"""
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / 'RemoteVI.lvproj'
LV_EXT = {'.vi', '.ctl', '.vit', '.lvclass', '.lvlib'}

# (virtual folder path, disk directory, recurse into subdirectories as subfolders)
FOLDERS = [
    ('Examples', 'examples', False),
    ('Tests/Fixture', 'tests/fixtures', False),
    ('Tests/Fixture/build', 'tests/fixtures/build', False),
    ('Tests/Caraya', 'tests/caraya', False),
    ('Tests/Caraya/support', 'tests/caraya/support', False),
    ('Tests/Caraya/unit', 'tests/caraya/unit', True),
    ('Scripts', 'scripts', False),
    ('Scripts/Win32 Wrapper Builder', 'scripts/Win32 Wrapper Builder', False),
    ('Scripts/Win32 Wrapper Templates', 'scripts/Win32 Wrapper Templates', False),
    ('Spikes', 'spikes', False),
]


def item(path, indent):
    p = path.relative_to(ROOT).as_posix()
    kind = {'.lvlib': 'Library', '.lvclass': 'LVClass', '.ctl': 'VI'}.get(path.suffix, 'VI')
    return f'{indent}<Item Name="{escape(path.name, {chr(34): "&quot;"})}" Type="{kind}" URL="../{escape(p, {chr(34): "&quot;"})}"/>'


def files(directory, recurse):
    d = ROOT / directory
    if not d.is_dir():
        return [], []
    direct = sorted(f for f in d.iterdir() if f.is_file() and f.suffix.lower() in LV_EXT)
    subs = sorted(s for s in d.iterdir() if s.is_dir() and recurse)
    return direct, subs


def build_tree():
    tree = {}
    for vpath, directory, recurse in FOLDERS:
        direct, subs = files(directory, recurse)
        node = tree
        for part in vpath.split('/'):
            node = node.setdefault(part, {})
        node.setdefault('__files__', []).extend(direct)
        for s in subs:
            sub_direct, _ = files(s.relative_to(ROOT).as_posix(), False)
            node.setdefault(s.name, {}).setdefault('__files__', []).extend(sub_direct)
    return tree


def render(node, indent):
    out = []
    for name in sorted(k for k in node if k != '__files__'):
        child = node[name]
        if not any_files(child):
            continue
        out.append(f'{indent}<Item Name="{escape(name)}" Type="Folder">')
        out.extend(render(child, indent + '\t'))
        out.append(f'{indent}</Item>')
    for f in node.get('__files__', []):
        out.append(item(f, indent))
    return out


def any_files(node):
    return bool(node.get('__files__')) or any(any_files(v) for k, v in node.items() if k != '__files__')


def main():
    body = render(build_tree(), '\t\t')
    text = '\n'.join([
        "<?xml version='1.0' encoding='UTF-8'?>",
        '<Project Type="Project" LVVersion="25008000">',
        '\t<Property Name="NI.LV.All.SourceOnly" Type="Bool">true</Property>',
        '\t<Property Name="NI.Project.Description" Type="Str">RemoteVI - publish a LabVIEW front panel to a web browser, pixel-accurate and interactive.</Property>',
        '\t<Item Name="My Computer" Type="My Computer">',
        '\t\t<Property Name="server.app.propertiesEnabled" Type="Bool">true</Property>',
        '\t\t<Property Name="server.control.propertiesEnabled" Type="Bool">true</Property>',
        '\t\t<Property Name="server.tcp.enabled" Type="Bool">false</Property>',
        '\t\t<Property Name="server.tcp.port" Type="Int">0</Property>',
        '\t\t<Property Name="server.tcp.serviceName" Type="Str">My Computer/VI Server</Property>',
        '\t\t<Property Name="server.tcp.serviceName.default" Type="Str">My Computer/VI Server</Property>',
        '\t\t<Property Name="server.vi.callsEnabled" Type="Bool">true</Property>',
        '\t\t<Property Name="server.vi.propertiesEnabled" Type="Bool">true</Property>',
        '\t\t<Property Name="specify.custom.address" Type="Bool">false</Property>',
        '\t\t<Item Name="RemoteVI.lvlib" Type="Library" URL="../source/RemoteVI.lvlib"/>',
        *body,
        '\t\t<Item Name="Dependencies" Type="Dependencies"/>',
        '\t\t<Item Name="Build Specifications" Type="Build"/>',
        '\t</Item>',
        '</Project>',
        '',
    ])
    PROJECT.write_text(text, encoding='utf-8')
    folders = sum(1 for line in body if 'Type="Folder"' in line)
    items = sum(1 for line in body if 'URL=' in line)
    print(f'wrote {PROJECT.name}: {folders} virtual folders, {items} items + RemoteVI.lvlib')


if __name__ == '__main__':
    main()
