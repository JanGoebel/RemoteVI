"""Text icons of RemoteVI's VIs: draws one 32x32 PNG per VI (tools/dev/icon_font.py) and writes the two list files of
tools/dev/Set Icons.vi, which applies them and saves the VIs.

    <labview-mcp>\\bin\\pylabview\\python.exe tools/dev/icons.py [names...]
    then run tools/dev/Set Icons.vi with VIs = builds/icons/vis.txt and Icons = builds/icons/pngs.txt (no project
    open; every code must be 0), and save the VIs for 2020.

Banner: RVI for the library (grey background for the palette VIs of source/API), the DLL for the Win32 wrappers,
DEMO / APP for the examples, DEV for the tools here, W32B for the wrapper builder, TEST / CHECK for the Caraya tests
and their generated support VIs, FIXT for the fixtures, BENCH / SPIKE for tools/bench/. Lines: the name, shortened to 5
characters each. VIs with hand made icons are not listed. With names, only the VIs whose path contains one of them.
tests/caraya/build.py composes the support VIs without icons: run this again after it.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from icon_font import render, GREY, WHITE  # noqa: E402

API = {
    'RemoteVI Start': ('RVI', 'START', ''),
    'RemoteVI Start Window': ('RVI', 'START', 'WNDW'),
    'RemoteVI Status': ('RVI', 'STATS', ''),
    'RemoteVI Status Panel': ('RVI', 'STATS', 'PANEL'),
    'RemoteVI Show Status': ('RVI', 'SHOW', 'STATS'),
    'RemoteVI Open Server': ('RVI', 'OPEN', 'SRVR'),
}
LIB = {
    'App': {
        'Arrange Controls': ('ARRNG', 'CTRLS'), 'Copy Text': ('COPY', 'TEXT'), 'HTML Escape': ('HTML', 'ESC'),
        'Landing Page': ('LAND', 'PAGE'), 'Landing Server': ('LAND', 'SRVR'), 'List Top Windows': ('TOP', 'WNDWS'),
        'Next Free Port': ('FREE', 'PORT'), 'Open URL': ('OPEN', 'URL'), 'Parse Arguments': ('PARSE', 'ARGS'),
        'Process Path': ('PROC', 'PATH'), 'Server Share': ('SRVR', 'SHARE'), 'Server Windows': ('SRVR', 'WNDWS'),
        'Server': ('RVI', 'SRVR'), 'Share Rows': ('SHARE', 'ROWS'), 'Start Landing Page': ('START', 'LAND'),
        'VI Of Window': ('VI OF', 'WNDW'), 'Window Rows': ('WNDW', 'ROWS'),
    },
    'Capture': {'Encode Rect PNG': ('RECT', 'PNG')},
    'Input': {
        'Apply Modifiers': ('APPLY', 'MODS'), 'Close Window': ('CLOSE', 'WNDW'), 'Get Panel Geometry': ('PANEL', 'GEOM'),
        'Hover Menus': ('HOVER', 'MENUS'), 'Post Input': ('POST', 'INPUT'), 'Route Input': ('ROUTE', 'INPUT'),
        'Target Geometry': ('TRGT', 'GEOM'), 'Track Modifiers': ('TRACK', 'MODS'),
        'Translate Input': ('TRANS', 'INPUT'), 'Write Modifiers': ('WRITE', 'MODS'),
    },
    'Protocol': {
        'JSON String': ('JSON', 'STR'), 'Parse Input': ('PARSE', 'INPUT'), 'Splitters Message': ('SPLIT', 'MSG'),
        'Tips Message': ('TIPS', 'MSG'), 'Window Frame Encode': ('WNDW', 'FRAME'), 'Windows Message': ('WNDWS', 'MSG'),
    },
    'Server': {
        'Accept Clients': ('ACCPT', 'CLNTS'), 'Add Client': ('ADD', 'CLNT'), 'Apply Splitter': ('APPLY', 'SPLIT'),
        'Call Hooks': ('CALL', 'HOOKS'), 'Capture And Send': ('CAPT', '+SEND'), 'Capture Frame': ('CAPT', 'FRAME'),
        'Capture Windows': ('CAPT', 'WNDWS'), 'Close Clients': ('CLOSE', 'CLNTS'), 'Connect VI Server': ('CONN', 'VISRV'),
        'Control Children': ('CTRL', 'CHILD'), 'Drop Closed Clients': ('DROP', 'CLNTS'), 'Format Duration': ('FMT', 'DUR'),
        'Greeting': ('GREET', ''), 'Handle Connection': ('HNDL', 'CONN'), 'Handle Text Message': ('HNDL', 'TEXT'),
        'Index HTML': ('INDEX', 'HTML'), 'Launch Server Loop': ('LNCH', 'LOOP'), 'Launch Share': ('LNCH', 'SHARE'),
        'List Popups': ('LIST', 'POPUP'), 'Loop Flags': ('LOOP', 'FLAGS'), 'Loop Greeting': ('LOOP', 'GREET'),
        'Loop Init': ('LOOP', 'INIT'), 'New Token': ('NEW', 'TOKEN'),
        'Open Server Loop': ('OPEN', 'LOOP'), 'Origin Message': ('ORIGN', 'MSG'), 'Other Shares': ('OTHER', 'SHARE'),
        'Panel Controls': ('PANEL', 'CTRLS'), 'Post Client Input': ('POST', 'CLNT'), 'Print Frame': ('PRINT', 'FRAME'),
        'Publish Status': ('PUBL', 'STATS'), 'Read Panel Info': ('PANEL', 'INFO'), 'Read Splitters': ('READ', 'SPLIT'),
        'Read Tips': ('READ', 'TIPS'), 'Refresh Geometry': ('RFRSH', 'GEOM'), 'Remote Target': ('RMT', 'TRGT'),
        'Retrack Popups': ('RTRCK', 'POPUP'), 'Route Request': ('ROUTE', 'REQ'), 'Running Panels': ('RUN', 'PANEL'),
        'Send Client Windows': ('SEND', 'CLWND'), 'Send Frame': ('SEND', 'FRAME'), 'Send Origin': ('SEND', 'ORIGN'),
        'Send Overlay': ('SEND', 'OVRLY'), 'Send Tips': ('SEND', 'TIPS'), 'Send Window Frame': ('SEND', 'WFRM'),
        'Send Windows': ('SEND', 'WNDWS'), 'Serve Clients Step': ('SERVE', 'STEP'),
        'Serve Pending Connection': ('SERVE', 'PEND'), 'Server Loop': ('SRVR', 'LOOP'),
        'Server Setup': ('SRVR', 'SETUP'), 'Service Client': ('SERV', 'CLNT'), 'Service Clients': ('SERV', 'CLNTS'),
        'Set Server Loop Inputs': ('LOOP', 'INPUT'), 'Share Running': ('SHARE', 'RUN'), 'Splitter Request': ('SPLIT', 'REQ'),
        'Status Convert': ('STATS', 'CONV'), 'Status Registry': ('STATS', 'REG'), 'Status Text': ('STATS', 'TEXT'),
        'Target Name': ('TRGT', 'NAME'), 'Target Running': ('TRGT', 'RUN'), 'Token Check': ('TOKEN', 'CHECK'),
        'Track Popups': ('TRACK', 'POPUP'), 'Track Target': ('TRACK', 'TRGT'), 'Track Windows': ('TRACK', 'WNDWS'), 'VI Server Request': ('VISRV', 'REQ'),
        'VI Stopped': ('VI', 'STOP'), 'Write To Clients': ('WRITE', 'CLNTS'),
    },
    'Win32': {
        'Copy Window': ('COPY', 'WNDW'), 'Find Popups': ('FIND', 'POPUP'), 'Frame Rect': ('FRAME', 'RECT'),
        'List Windows': ('LIST', 'WNDWS'), 'Menu Highlight': ('MENU', 'HILIT'), 'Thread Windows': ('THRD', 'WNDWS'),
        'Window Info': ('WNDW', 'INFO'),
    },
}
# Win32 wrappers built by tools/Build Win32 Wrappers.vi: (banner, line 2, line 3)
WRAPPERS = {
    'bcrypt BCryptGenRandom': ('BCRYP', 'GEN', 'RAND'), 'gdi32 BitBlt': ('GDI32', 'BIT', 'BLT'),
    'gdi32 CreateRectRgn': ('GDI32', 'RECT', 'RGN'), 'kernel32 CloseHandle': ('KRNL', 'CLOSE', 'HNDL'),
    'kernel32 GetCurrentThreadId': ('KRNL', 'THRD', 'ID'), 'kernel32 OpenProcess': ('KRNL', 'OPEN', 'PROC'),
    'kernel32 QueryFullProcessImageNameW': ('KRNL', 'PROC', 'IMAGE'),
    'LabVIEW LVImageDataToPNGByteArray': ('LV', 'IMG', 'PNG'), 'user32 AttachThreadInput': ('USER', 'ATTCH', 'INPUT'),
    'user32 GetClientRect': ('USER', 'CLNT', 'RECT'), 'user32 GetSysColor': ('USER', 'SYS', 'COLOR'),
    'user32 IsWindow': ('USER', 'IS', 'WNDW'), 'user32 SetWindowRgn': ('USER', 'WNDW', 'RGN'),
}
OTHER = {
    r'examples\RemoteVI Demo.vi': ('DEMO', 'RVI', ''),
    r'examples\Application Example\RemoteVI App Alarms.vi': ('APP', 'ALARM', ''),
    r'examples\Application Example\RemoteVI App Live Data.vi': ('APP', 'LIVE', 'DATA'),
    r'examples\Application Example\RemoteVI App Log Files.vi': ('APP', 'LOG', 'FILES'),
    r'examples\Application Example\RemoteVI App Settings.vi': ('APP', 'SETNG', ''),
    r'hooks\RemoteVI Remote Hooks.vi': ('RVI', 'RMT', 'HOOKS'),
    r'tools\dev\Add To Library Files.vi': ('DEV', 'ADD', 'LIB'), r'tools\dev\Build Spec.vi': ('DEV', 'BUILD', 'SPEC'),
    r'tools\dev\Fit To Pane.vi': ('DEV', 'FIT', 'PANE'), r'tools\dev\FP Close Path.vi': ('DEV', 'FP', 'CLOSE'),
    r'tools\dev\Launch Detached.vi': ('DEV', 'LNCH', 'DTCH'), r'tools\dev\Mem.vi': ('DEV', 'MEM', ''),
    r'tools\dev\Notify Stop.vi': ('DEV', 'NTFY', 'STOP'), r'tools\dev\Set Columns.vi': ('DEV', 'SET', 'COLS'),
    r'tools\dev\Style Panel.vi': ('DEV', 'STYLE', 'PANEL'), r'tools\dev\Set Icons.vi': ('DEV', 'SET', 'ICONS'),
    r'tools\dev\Relink Save.vi': ('DEV', 'RELNK', 'SAVE'),
    r'tools\dev\Replace In Descriptions.vi': ('DEV', 'DESC', 'REPL'),
    r'tools-menu\RemoteVI\Share in Browser.vi': ('RVI', 'SHARE', 'BRWSR'),
    r'tests\caraya\RemoteVI Caraya Runner.vi': ('TEST', 'RUN', 'ALL'),
    r'tests\caraya\support\RemoteVI Test Bytes To Hex.vi': ('TEST', 'BYTES', 'HEX'),
    r'tests\caraya\support\RemoteVI Test Hex To Bytes.vi': ('TEST', 'HEX', 'BYTES'),
    r'tests\fixtures\RemoteVI Fixture.vi': ('FIXT', 'RVI', ''),
    r'tests\fixtures\RemoteVI Fixture Arrange.vi': ('FIXT', 'ARRNG', ''),
    r'tests\fixtures\RemoteVI Fixture Layout.vi': ('FIXT', 'LAYOT', ''),
    r'tests\fixtures\RemoteVI Complex Fixture All Controls.vi': ('FIXT', 'ALL', 'CTRLS'),
    r'tests\fixtures\RemoteVI Complex Fixture Arrange.vi': ('FIXT', 'CMPLX', 'ARRNG'),
    r'tests\fixtures\RemoteVI Complex Fixture Button Refs.vi': ('FIXT', 'BTN', 'REFS'),
    r'tests\fixtures\RemoteVI Complex Fixture Children.vi': ('FIXT', 'CHILD', ''),
    r'tests\fixtures\RemoteVI Complex Fixture Events.vi': ('FIXT', 'EVNTS', ''),
    r'tests\fixtures\RemoteVI Complex Fixture Find Controls.vi': ('FIXT', 'FIND', 'CTRLS'),
    r'tests\fixtures\RemoteVI Complex Fixture Layout.vi': ('FIXT', 'CMPLX', 'LAYOT'),
    r'tests\fixtures\RemoteVI Complex Fixture Paste.vi': ('FIXT', 'PASTE', ''),
    r'tests\fixtures\RemoteVI Complex Fixture Prep Panel.vi': ('FIXT', 'PREP', 'PANEL'),
    r'tests\fixtures\RemoteVI Complex Fixture Refs.vi': ('FIXT', 'REFS', ''),
    r'tests\fixtures\RemoteVI Complex Fixture Value Text.vi': ('FIXT', 'VALUE', 'TEXT'),
    r'tests\fixtures\RemoteVI Complex Inspector.vi': ('FIXT', 'INSPC', ''),
    r'tests\fixtures\RemoteVI Complex View A.vi': ('FIXT', 'VIEW', 'A'),
    r'tests\fixtures\RemoteVI Complex View B.vi': ('FIXT', 'VIEW', 'B'),
    r'tools\bench\Bench Dirty Rects.vi': ('BENCH', 'DIRTY', 'RECTS'),
    r'tools\bench\Bench Encode PNG.vi': ('BENCH', 'ENC', 'PNG'),
    r'tools\bench\Spike Start Errors.vi': ('SPIKE', 'START', 'ERRS'),
    r'tools\Build Win32 Wrappers.vi': ('W32B', 'BUILD', 'WRAPS'),
    r'tools\dev\Set Reentrant.vi': ('DEV', 'SET', 'REENT'),
    r'tools\Win32 Wrapper Builder\W32B Create CLFN.vi': ('W32B', 'CREAT', 'CLFN'),
    r'tools\Win32 Wrapper Builder\W32B Parse Spec.vi': ('W32B', 'PARSE', 'SPEC'),
}
# Caraya subjects: tests\caraya\unit\<folder>\Test <subject>.vi (banner TEST) and its generated
# tests\caraya\support\RemoteVI Check <subject>.vi (banner CHECK) share the two lines
SUBJECTS = {
    'App': {'Landing Page': ('LAND', 'PAGE'), 'Next Free Port': ('FREE', 'PORT'), 'Parse Arguments': ('PARSE', 'ARGS'),
            'Window Rows': ('WNDW', 'ROWS')},
    'Capture': {'Dirty Rects': ('DIRTY', 'RECTS')},
    'Input': {'Track Modifiers': ('TRACK', 'MODS'), 'Translate Input': ('TRANS', 'INPUT')},
    'Protocol': {'Frame Encode': ('FRAME', 'ENC'), 'JSON String': ('JSON', 'STR'), 'Overlay Encode': ('OVRLY', 'ENC'),
                 'Parse Input': ('PARSE', 'INPUT'), 'Splitters Message': ('SPLIT', 'MSG'),
                 'Tips Message': ('TIPS', 'MSG'), 'WS Decode Client Frame': ('WS', 'DECOD'),
                 'WS Encode Server Frame': ('WS', 'ENCOD'), 'Window Frame Encode': ('WNDW', 'FRAME')},
    'Server': {'Format Duration': ('FMT', 'DUR'), 'Status Convert': ('STATS', 'CONV'), 'Status Text': ('STATS', 'TEXT'),
               'Token Check': ('TOKEN', 'CHECK')},
}


def table():
    """{relative path: (line1, line2, line3, background)}"""
    t = {}
    for name, lines in API.items():
        t[os.path.join('source', 'API', name + '.vi')] = lines + (GREY,)
    for folder, names in LIB.items():
        for name, (l2, l3) in names.items():
            t[os.path.join('source', folder, 'RemoteVI %s.vi' % name)] = ('RVI', l2, l3, WHITE)
    for name, lines in WRAPPERS.items():
        t[os.path.join('source', 'Win32', name + '.vi')] = lines + (WHITE,)
    for path, lines in OTHER.items():
        t[path] = lines + (WHITE,)
    for folder, names in SUBJECTS.items():
        for name, (l2, l3) in names.items():
            t[os.path.join('tests', 'caraya', 'unit', folder, 'Test %s.vi' % name)] = ('TEST', l2, l3, WHITE)
            t[os.path.join('tests', 'caraya', 'support', 'RemoteVI Check %s.vi' % name)] = ('CHECK', l2, l3, WHITE)
    return t


if __name__ == '__main__':
    out = os.path.join(REPO, 'builds', 'icons')
    os.makedirs(out, exist_ok=True)
    items, missing = [], []
    for rel, (l1, l2, l3, bg) in sorted(table().items()):
        if sys.argv[1:] and not any(n.lower() in rel.lower() for n in sys.argv[1:]):
            continue
        vi = os.path.join(REPO, rel)
        if not os.path.exists(vi):
            missing.append(rel)
            continue
        png = os.path.join(out, rel.replace(os.sep, '_')[:-3] + '.png')
        render(l1, l2, l3, bg=bg).save(png)
        items.append((vi, png))
    for name, col in (('vis.txt', 0), ('pngs.txt', 1)):
        with open(os.path.join(out, name), 'w') as f:
            f.write(';'.join(i[col] for i in items))  # no trailing semicolon: it would add an empty path
    print('%d icons -> %s' % (len(items), out))
    for rel in missing:
        print('missing', rel)
    sys.exit(1 if missing else 0)
