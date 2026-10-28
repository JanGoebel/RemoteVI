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
  Tools Menu/RemoteVI       the Tools menu entry (the VIPM package installs it into <LabVIEW>/project)

and four build specifications (builds/ is git-ignored, nothing built is committed):

  RemoteVI Server           builds/RemoteVI Server/RemoteVI Server.exe - App/RemoteVI Server.vi
  RemoteVI Demo             builds/RemoteVI Demo/RemoteVI Demo.exe - examples/RemoteVI Demo.vi
  RemoteVI Fixture          builds/RemoteVI Fixture/RemoteVI Fixture.exe - the test fixture in its own process
  RemoteVI Complex Fixture  builds/RemoteVI Complex Fixture/... - the complex fixture in its own process

Both include the whole RemoteVI library ("Always Included"): the Server Loop, the Landing Server
and the Status Panel are opened by path at run time, so no static call pulls them in.

Run it after adding or removing a VI outside source/:   python scripts/gen-lvproj.py
"""
import subprocess
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
    ('Tools Menu/RemoteVI', 'tools-menu/RemoteVI', False),
]


def guid(name):
    """A stable {GUID} per build spec and purpose, so regenerating the project changes nothing."""
    import uuid
    return '{%s}' % str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/JanGoebel/RemoteVI/' + name)).upper()


# (spec name, exe name, top-level VI as a project path, description)
EXES = [
    ('RemoteVI Server', 'RemoteVI Server.exe', '/My Computer/RemoteVI.lvlib/App/RemoteVI Server.vi',
     'RemoteVI Server - share any window in a web browser'),
    ('RemoteVI Demo', 'RemoteVI Demo.exe', '/My Computer/Examples/RemoteVI Demo.vi',
     'RemoteVI Demo - a built application that shares its own panel'),
    ('RemoteVI Fixture', 'RemoteVI Fixture.exe', '/My Computer/Tests/Fixture/RemoteVI Fixture.vi',
     'RemoteVI Fixture - the integration-test fixture in a process of its own (cross-process tests, docs/testing.md)'),
    ('RemoteVI Complex Fixture', 'RemoteVI Complex Fixture.exe', '/My Computer/Tests/Fixture/RemoteVI Complex Fixture.vi',
     'RemoteVI Complex Fixture - the complex-UI fixture in a process of its own (cross-process tests)',
     ['/My Computer/Tests/Fixture/RemoteVI Complex View A.vi', '/My Computer/Tests/Fixture/RemoteVI Complex View B.vi',
      '/My Computer/Tests/Fixture/RemoteVI Complex Inspector.vi']),
]


DYNAMIC = ['Server/RemoteVI Server Loop.vi', 'App/RemoteVI Landing Server.vi', 'API/RemoteVI Status Panel.vi']


def build_spec(name, exe, top, desc, extra=(), indent='\t\t\t'):
    dest = '../builds/%s' % name
    props = [
        ('App_copyErrors', 'Bool', 'true'),
        ('App_INI_aliasGUID', 'Str', guid(name + '/ini-alias')),
        ('App_INI_GUID', 'Str', guid(name + '/ini')),
        ('App_serverConfig.httpPort', 'Int', '8002'),
        ('App_serverType', 'Int', '0'),
        ('Bld_autoIncrement', 'Bool', 'false'),
        ('Bld_buildCacheID', 'Str', guid(name + '/cache')),
        ('Bld_buildSpecName', 'Str', name),
        ('Bld_excludeInlineSubVIs', 'Bool', 'true'),
        ('Bld_excludeLibraryItems', 'Bool', 'false'),
        ('Bld_excludePolymorphicVIs', 'Bool', 'true'),
        ('Bld_localDestDir', 'Path', dest),
        ('Bld_localDestDirType', 'Str', 'relativeToProject'),
        ('Bld_modifyLibraryFile', 'Bool', 'true'),
        ('Bld_previewCacheID', 'Str', guid(name + '/preview')),
        ('Bld_version.build', 'Int', '0'),
        ('Bld_version.major', 'Int', '1'),
        ('Destination[0].destName', 'Str', exe),
        ('Destination[0].path', 'Path', '%s/%s' % (dest, exe)),
        ('Destination[0].path.type', 'Str', 'relativeToProject'),
        ('Destination[0].preserveHierarchy', 'Bool', 'true'),
        ('Destination[0].type', 'Str', 'App'),
        ('Destination[1].destName', 'Str', 'Support Directory'),
        ('Destination[1].path', 'Path', dest + '/data'),
        ('Destination[1].path.type', 'Str', 'relativeToProject'),
        ('DestinationCount', 'Int', '2'),
        ('Source[0].itemID', 'Str', guid(name + '/container')),
        ('Source[0].type', 'Str', 'Container'),
        ('Source[1].destinationIndex', 'Int', '0'),
        ('Source[1].itemID', 'Ref', top),
        ('Source[1].sourceInclusion', 'Str', 'TopLevel'),
        ('Source[1].type', 'Str', 'VI'),
        ('Source[2].Library.allowMissingMembers', 'Bool', 'true'),
        ('Source[2].destinationIndex', 'Int', '0'),
        ('Source[2].itemID', 'Ref', '/My Computer/RemoteVI.lvlib'),
        ('Source[2].sourceInclusion', 'Str', 'Include'),
        ('Source[2].type', 'Str', 'Library'),
    ]
    # opened by path at run time (no static caller): always included
    dyn = ['/My Computer/RemoteVI.lvlib/' + vi for vi in DYNAMIC] + list(extra)
    for i, ref in enumerate(dyn, start=3):
        props += [('Source[%d].destinationIndex' % i, 'Int', '0'),
                  ('Source[%d].itemID' % i, 'Ref', ref),
                  ('Source[%d].sourceInclusion' % i, 'Str', 'Include'),
                  ('Source[%d].type' % i, 'Str', 'VI')]
    props += [
        ('SourceCount', 'Int', str(3 + len(dyn))),
        ('TgtF_companyName', 'Str', 'Jan Goebel'),
        ('TgtF_enableDebugging', 'Bool', 'false'),
        ('TgtF_fileDescription', 'Str', desc),
        ('TgtF_internalName', 'Str', name),
        ('TgtF_legalCopyright', 'Str', 'Copyright (c) 2026 Jan Goebel, MIT license'),
        ('TgtF_productName', 'Str', name),
        ('TgtF_targetfileGUID', 'Str', guid(name + '/target')),
        ('TgtF_targetfileName', 'Str', exe),
        ('TgtF_versionIndependent', 'Bool', 'false'),
    ]
    out = ['%s<Item Name="%s" Type="EXE">' % (indent, escape(name))]
    for k, t, v in props:
        out.append('%s\t<Property Name="%s" Type="%s">%s</Property>' % (indent, k, t, escape(v)))
    out.append('%s</Item>' % indent)
    return out


def item(path, indent):
    p = path.relative_to(ROOT).as_posix()
    kind = {'.lvlib': 'Library', '.lvclass': 'LVClass', '.ctl': 'VI'}.get(path.suffix, 'VI')
    return f'{indent}<Item Name="{escape(path.name, {chr(34): "&quot;"})}" Type="{kind}" URL="../{escape(p, {chr(34): "&quot;"})}"/>'


def ignored(path):
    """True for a git-ignored file (build intermediates such as tests/fixtures/build/Complex Panel.vi)."""
    r = subprocess.run(['git', 'check-ignore', '-q', str(path)], cwd=ROOT)
    return r.returncode == 0


def files(directory, recurse):
    d = ROOT / directory
    if not d.is_dir():
        return [], []
    direct = sorted(f for f in d.iterdir() if f.is_file() and f.suffix.lower() in LV_EXT and not ignored(f))
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
        '\t\t<Item Name="Build Specifications" Type="Build">',
        *[line for spec in EXES for line in build_spec(*spec)],
        '\t\t</Item>',
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
