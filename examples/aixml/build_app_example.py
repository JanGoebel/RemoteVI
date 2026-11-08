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
  7. tools/dev/Fit To Pane.vi on the main VI, once per line of FIT (printed too): the menu and the subpanel fill
     their panes and follow them when the window or a splitter bar moves. control size must equal pane size
     (the menu's height within a row).
  8. tools/dev/Set Columns.vi once per line of COLUMNS (printed too): the lists get their column widths and rows
     (a multicolumn listbox has no writable size); size must be 859 wide.
  9. save for LabVIEW 2020 (CLAUDE.md, Save version).

usage: python examples/aixml/build_app_example.py ["...\\vi.lib\\silver_ctls"]
"""
import json
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
ACT = r'Boolean\Blank Button NI_Silver.ctl'
STR = r'String\String Control NI_Silver.ctl'
STRI = r'String\String Indicator NI_Silver.ctl'
LIST = r'ListTableTree\Multicolumn Listbox NI_Silver.ctl'
GRAPH = r'Graph\Waveform Graph NI_Silver.ctl'
# the size of the subpanel once Fit To Pane made it fill its pane: a screen panel of exactly this size is
# shown as laid out (a smaller one was rescaled when it was inserted - the graph ran past the edge)
SCREEN_W, SCREEN_H = 891, 690
# a graph's Width and Height are its plot area; scales and labels add about 83 x 84 (measured: a plot of
# 859 x 430 had Bounds 942 x 514)

MAIN = [
    # left pane (0): the navigation menu
    row('Menu', LIST, '', 0, 0, left=0, top=0, show_label=False, tip='Choose the screen to show.'),
    # toolbar pane (1): above the main pane, 891 px wide
    row('Page', r'String\String Indicator - Frameless NI_Silver.ctl', '', 0, 1, left=14, top=17, width=170, show_label=False,
        tip='The screen shown.'),
    row('Remote Link', STRI, '', 0, 1, left=196, top=15, width=560, height=26, show_label=False,
        tip='Open this link in a browser to operate the application (RemoteVI).'),
    row('Quit', r'Boolean\Stop Button NI_Silver.ctl', '', 0, 1, left=770, top=10, width=108, height=36, text='Quit', show_label=False,
        tip='Stops the application and the remote share.'),
    # main pane (2): the subpanel; Fit To Pane makes it fill the pane
    row('Screen', '', '', 0, 2, left=0, top=0, show_label=False),
    row('error out', '', '', 0, 0, left=8, top=600, visible=False),
]
# controls without a writable size (the subpanel, multicolumn listboxes) are sized in the Tabs step
MAIN_TABS = []  # the menu and the subpanel have no writable size: Fit To Pane sizes them to their panes
# Fit To Pane.vi: (label, width bar, pane left of bar, height bar, cell width, row height, rows). The menu's pane runs
# the full height of the window beside the bar (no bar sets its height, -1): its 39 rows of 18 px fill it, and the
# column of 171 px plus the frame (29) makes it 200 px wide at run time, the pane's width, when the main VI writes
# its Number of Columns; the subpanel's pane lies right of and below the bars
FIT = [('Menu', 0, True, -1, 171, 20, 39), ('Screen', 0, False, 1, 0, 0, 0)]
MAIN_SPLITTERS = [200, 56]  # the vertical bar (menu width), then the horizontal one (toolbar height)
MAIN_WINDOW = (80, 60, 80 + 1100, 60 + 754)  # the size of NI's splitter panel: a smaller one is refused (error 1)

LIVE = [
    row('Live Data', GRAPH, left=16, top=16, width=776, height=346, tip='The last block of four simulated channels.'),
    row('Statistics', r'ListTableTree\Table NI_Silver.ctl', left=16, top=490, width=420, height=150,
        tip='Maximum and minimum of each channel in the block shown.'),
    row('Pause', r'Boolean\Pause Button NI_Silver.ctl', left=823, top=490, width=52, height=52, show_label=True,
        text=' ', tip='Holds the graph.'),  # a glyph button: the Push Button's text 'Pause' is blanked
]
FILES = [
    row('Log Files', LIST, left=16, top=30, width=859, height=240, tip='Select a file to see its preview.'),
    row('Delete', ACT, left=16, top=284, width=126, height=34, text='Delete...', show_label=False,
        tip='Removes the selected file - asks first in a LabVIEW dialog.'),
    row('Export', ACT, left=154, top=284, width=126, height=34, text='Export...', show_label=False,
        tip='Exports the selected file - choose the target in the native file dialog.'),
    row('Preview', GRAPH, left=16, top=340, width=480, height=200, tip='The first samples of AI0 of the selected file.'),
    row('Details', STRI, left=600, top=370, width=275, height=180, tip='About the selected file.'),
    row('Status', STRI, left=16, top=640, width=859, tip='What the last Delete or Export did.'),
]
ALARMS = [
    row('Alarm', r'Boolean\LED NI_Silver.ctl', left=16, top=24, tip='Lit while an alarm is active.'),
    row('Active Alarms', NUMI, left=80, top=24, width=60, tip='Alarms not acknowledged yet.'),
    row('Alarms', LIST, left=16, top=90, width=859, height=500, tip='Active alarms, oldest first.'),
    row('Acknowledge', ACT, left=16, top=610, width=140, height=34, text='Acknowledge', show_label=False,
        tip='Acknowledges the selected alarm.'),
    row('Acknowledge All', ACT, left=168, top=610, width=140, height=34, text='Acknowledge All', show_label=False,
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
# Set Columns.vi: (screen, listbox, column widths, visible rows); the frame and the scroll bar add 49 px of width
COLUMNS = [('RemoteVI App Log Files.vi', 'Log Files', [320, 190, 150, 150], 9),
           ('RemoteVI App Alarms.vi', 'Alarms', [150, 110, 170, 380], 22)]
VIS = [
    ('main', os.path.join(REPO, 'examples', 'RemoteVI Application Example.vi'), MAIN, MAIN_TABS, MAIN_WINDOW, MAIN_SPLITTERS),
    ('live_data', os.path.join(REPO, 'examples', 'Application Example', 'RemoteVI App Live Data.vi'), LIVE, [], SCREEN_WINDOW, []),
    ('log_files', os.path.join(REPO, 'examples', 'Application Example', 'RemoteVI App Log Files.vi'), FILES, [('Log Files', [], 0, 859, 240)], SCREEN_WINDOW, []),
    ('alarms', os.path.join(REPO, 'examples', 'Application Example', 'RemoteVI App Alarms.vi'), ALARMS, [('Alarms', [], 0, 859, 500)], SCREEN_WINDOW, []),
    ('settings', os.path.join(REPO, 'examples', 'Application Example', 'RemoteVI App Settings.vi'), SETTINGS, [], SCREEN_WINDOW, []),
]

if __name__ == '__main__':
    silver = sys.argv[1] if len(sys.argv) > 1 else r'C:\Program Files\National Instruments\LabVIEW 2026\vi.lib\silver_ctls'
    for name, vi, rows, tabs, window, splitters in VIS:
        spec = os.path.join(HERE, 'app_%s.spec.xml' % name)
        write_spec(spec, rows, tabs, window, splitters)
        print(name, inputs_json(vi, silver, spec))
    for screen, label, widths, rows in COLUMNS:
        print('columns', json.dumps({'VI': os.path.join(REPO, 'examples', 'Application Example', screen), 'Label': label,
                                     'Widths': widths, 'Rows': rows}))
    for label, wbar, left, hbar, cw, rh, rows in FIT:
        print('fit', json.dumps({'VI': VIS[0][1], 'Label': label, 'Width Bar': wbar, 'Pane Left Of Bar': left,
                                 'Height Bar': hbar, 'Cell Width': cw, 'Row Height': rh, 'Rows': rows}))
