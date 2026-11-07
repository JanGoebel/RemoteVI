"""Build steps of examples/RemoteVI Application Example.vi and its screens, and the style tables of their panels.

  1. python examples/aixml/gen_app_example.py
  2. compose the screens (multicolumn listboxes need --listbox):
       <labview-mcp>\\bin\\pylabview\\python.exe tools/aixml/compose.py --listbox examples/aixml/app_<screen>.xml
         "examples/Application Example/RemoteVI App <Screen>.vi"
     and the main VI's scaffold:
       ... compose.py --listbox examples/aixml/app_main.xml "builds/app/App Scaffold.vi" source/API source/Server source/Win32
  3. copy <LabVIEW>\\examples\\Controls and Indicators\\Containers\\Resizable Panel with Splitter Bars.vi to
     builds/app/App Panel.vi and run tests/fixtures/RemoteVI Complex Fixture Prep Panel.vi on it (path)
  4. lvai_graft_diagram panel=builds/app/App Panel.vi scaffold=builds/app/App Scaffold.vi
     output=examples/RemoteVI Application Example.vi allowNewControls replaceDiagram (any empty project active)
  5. tests/fixtures/RemoteVI Complex Fixture Paste.vi: Fixture = the example, Donors = [<LabVIEW>\\examples\\
     Controls and Indicators\\Containers\\Multiple VIs in a Subpanel.vi], Donor Labels = [Subpanel],
     Labels = [Screen], Pane = [2]
  6. python examples/aixml/build_app_example.py  -> writes app_<name>.spec.xml and prints the inputs of
     tools/dev/Style Panel.vi for each VI; run it once per VI. Every line of problems must end in 0.
  7. save for LabVIEW 2020 (CLAUDE.md, Save version).

usage: python examples/aixml/build_app_example.py ["...\\vi.lib\\silver_ctls"]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'aixml'))
from style_rows import row, inputs_json, write_spec  # noqa: E402

NUM = r'Numeric\Numeric Control NI_Silver.ctl'
NUMI = r'Numeric\Numeric Indicator NI_Silver.ctl'
ENUM = r'RingEnum\Enum NI_Silver.ctl'
BTN = r'Boolean\Push Button NI_Silver.ctl'
ACT = r'Boolean\OK Button NI_Silver.ctl'
STR = r'String\String Control NI_Silver.ctl'
STRI = r'String\String Indicator NI_Silver.ctl'
LIST = r'ListTableTree\Multicolumn Listbox NI_Silver.ctl'
GRAPH = r'Graph\Waveform Graph NI_Silver.ctl'
SCREEN_W, SCREEN_H = 880, 560

MAIN = [
    # left pane (0): the navigation menu
    row('Menu', LIST, '', 0, 0, left=8, top=8, width=176, height=420, show_label=False,
        tip='Choose the screen to show.'),
    # toolbar pane (1)
    row('Page', r'String\String Indicator - Frameless NI_Silver.ctl', '', 0, 1, left=12, top=14, width=200, show_label=False,
        tip='The screen shown.'),
    row('Remote Link', STRI, '', 0, 1, left=230, top=14, width=520, show_label=False,
        tip='Open this link in a browser to operate the application (RemoteVI).'),
    row('Quit', r'Boolean\Stop Button NI_Silver.ctl', '', 0, 1, left=770, top=10, width=110, height=34, text='Quit', show_label=False,
        tip='Stops the application and the remote share.'),
    # main pane (2): the subpanel, sized in the Tabs step
    row('Screen', '', '', 0, 2, left=8, top=10, show_label=False),
    row('error out', '', '', 0, 0, left=8, top=600, visible=False),
]
# controls without a writable size (the subpanel, multicolumn listboxes) are sized in the Tabs step
MAIN_TABS = [('Screen', [], 0, SCREEN_W, SCREEN_H), ('Menu', [], 0, 184, 420)]
MAIN_SPLITTERS = [200, 56]  # the vertical bar (menu width), then the horizontal one (toolbar height)
MAIN_WINDOW = (80, 60, 80 + 1100, 60 + 680)

LIVE = [
    row('Live Data', GRAPH, left=16, top=16, width=760, height=340, tip='The last block of four simulated channels.'),
    row('Statistics', r'ListTableTree\Table NI_Silver.ctl', left=16, top=420, width=380, height=100,
        tip='Maximum and minimum of each channel in the block shown.'),
    row('Pause', BTN, left=720, top=440, width=126, height=38, text='Pause', show_label=False, tip='Holds the graph.'),
]
FILES = [
    row('Log Files', LIST, left=16, top=30, width=848, height=170, tip='Select a file to see its preview.'),
    row('Delete', ACT, left=16, top=212, width=126, height=34, text='Delete...', show_label=False,
        tip='Removes the selected file - asks first in a LabVIEW dialog.'),
    row('Export', ACT, left=154, top=212, width=126, height=34, text='Export...', show_label=False,
        tip='Exports the selected file - choose the target in the native file dialog.'),
    row('Preview', GRAPH, left=16, top=270, width=520, height=190, tip='The first samples of AI0 of the selected file.'),
    row('Details', STRI, left=620, top=290, width=224, height=120, tip='About the selected file.'),
    row('Status', STRI, left=16, top=520, width=848, tip='What the last Delete or Export did.'),
]
ALARMS = [
    row('Alarm', r'Boolean\LED NI_Silver.ctl', left=16, top=24, tip='Lit while an alarm is active.'),
    row('Active Alarms', NUMI, left=80, top=24, width=60, tip='Alarms not acknowledged yet.'),
    row('Alarms', LIST, left=16, top=90, width=848, height=360, tip='Active alarms, oldest first.'),
    row('Acknowledge', ACT, left=16, top=470, width=140, height=34, text='Acknowledge', show_label=False,
        tip='Acknowledges the selected alarm.'),
    row('Acknowledge All', ACT, left=168, top=470, width=140, height=34, text='Acknowledge All', show_label=False,
        tip='Acknowledges every alarm.'),
]
SETTINGS = [
    row('Station Name', STR, left=16, top=30, width=300, tip='Shown in the log file headers.'),
    row('Operator', STR, left=16, top=90, width=300, tip='Who runs the station.'),
    row('Units', ENUM, left=16, top=150, width=180, tip='Units of the displays and the log files.'),
    row('Sample Interval (ms)', NUM, left=16, top=210, width=110, tip='How often the station samples its channels.'),
    row('Keep Logs (days)', NUM, left=200, top=210, width=110, tip='Log files older than this are removed.'),
    row('Export Automatically', BTN, left=16, top=270, width=220, height=32, text='Export automatically', show_label=False,
        tip='Exports every log file when it is closed.'),
    row('Export Folder', r'String\File Path Control NI_Silver.ctl', left=16, top=330, width=500, tip='Where exports go.'),
    row('Save', ACT, left=16, top=400, width=126, height=38, text='Save', show_label=False, tip='Saves the settings (simulated).'),
    row('Status', STRI, left=16, top=470, width=500, tip='When the settings were saved last.'),
]
SCREEN_WINDOW = (100, 100, 100 + SCREEN_W, 100 + SCREEN_H)
VIS = [
    ('main', os.path.join(REPO, 'examples', 'RemoteVI Application Example.vi'), MAIN, MAIN_TABS, MAIN_WINDOW, MAIN_SPLITTERS),
    ('live_data', os.path.join(REPO, 'examples', 'Application Example', 'RemoteVI App Live Data.vi'), LIVE, [], SCREEN_WINDOW, []),
    ('log_files', os.path.join(REPO, 'examples', 'Application Example', 'RemoteVI App Log Files.vi'), FILES, [('Log Files', [], 0, 848, 170)], SCREEN_WINDOW, []),
    ('alarms', os.path.join(REPO, 'examples', 'Application Example', 'RemoteVI App Alarms.vi'), ALARMS, [('Alarms', [], 0, 848, 360)], SCREEN_WINDOW, []),
    ('settings', os.path.join(REPO, 'examples', 'Application Example', 'RemoteVI App Settings.vi'), SETTINGS, [], SCREEN_WINDOW, []),
]

if __name__ == '__main__':
    silver = sys.argv[1] if len(sys.argv) > 1 else r'C:\Program Files\National Instruments\LabVIEW 2026\vi.lib\silver_ctls'
    for name, vi, rows, tabs, window, splitters in VIS:
        spec = os.path.join(HERE, 'app_%s.spec.xml' % name)
        write_spec(spec, rows, tabs, window, splitters)
        print(name, inputs_json(vi, silver, spec))
