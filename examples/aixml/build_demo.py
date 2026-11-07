"""Build steps of examples/RemoteVI Demo.vi (the data logger) and the style table of its panel.

  1. python examples/aixml/gen_remotevi_demo.py
  2. <labview-mcp>\\bin\\pylabview\\python.exe tools/aixml/compose.py examples/aixml/remotevi_demo.xml
       "examples/RemoteVI Demo.vi" source/API source/Server source/Win32
  3. tests/fixtures/RemoteVI Complex Fixture Paste.vi: Fixture = the demo, Donors = [tests/fixtures/build/
     Fixture Tab Panel.vi], Donor Labels = [Tab], Labels = [Configuration], Pane = [0]
     (AIXML cannot create a tab control; this pastes an empty one)
  4. python examples/aixml/build_demo.py  -> writes remotevi_demo.spec.xml (the style table below) and
     prints the inputs of tools/dev/Style Panel.vi; run Style Panel.vi with them
     (lvai_run_vi_and_read_values inputsJson). Every line of problems must end in 0.
  5. save for LabVIEW 2020 (CLAUDE.md, Save version).

usage: python examples/aixml/build_demo.py ["C:\\Program Files\\National Instruments\\LabVIEW 2026\\vi.lib\\silver_ctls"]
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
BTN = r'Boolean\Push Button NI_Silver.ctl'    # a toggle: its lamp shows the state
ACT = r'Boolean\OK Button NI_Silver.ctl'      # a one-shot action
STR = r'String\String Control NI_Silver.ctl'
STRI = r'String\String Indicator NI_Silver.ctl'
T = 'Configuration'

ROWS = [
    # the tab control first: its pages' controls are placed relative to it
    row('Configuration', '', '', 0, -1, left=16, top=16, width=540, height=380, show_label=False),
    # page 0: Acquisition
    row('Device', r'String\Combo Box NI_Silver.ctl', T, 0, left=24, top=72, width=250, tip='The acquisition device (simulated).'),
    row('Sample Rate (Hz)', NUM, T, 0, left=24, top=132, width=110, tip='Samples per second and channel.'),
    row('Samples per Read', NUM, T, 0, left=200, top=132, width=110, tip='Samples per channel in each 50 ms loop, 10 to 500.'),
    row('Acquisition Mode', ENUM, T, 0, left=24, top=192, width=150, tip='Continuous, finite or triggered.'),
    row('Duration (s)', NUM, T, 0, left=200, top=192, width=110, tip='Length of a finite acquisition.'),
    row('Add Noise', BTN, T, 0, left=24, top=252, width=150, height=34, text='Add noise', show_label=False,
        tip='Adds random noise to the simulated signals.'),
    # page 1: Channels
    row('Channels', r'ListTableTree\Table NI_Silver.ctl', T, 1, left=24, top=72, width=500, height=120,
        tip='Name, unit and scale of each channel. Click a cell to edit it.'),
    row('CH0', BTN, T, 1, left=24, top=232, width=100, height=30, text='AI0', show_label=False, tip='Show channel AI0 on the graph.'),
    row('CH1', BTN, T, 1, left=134, top=232, width=100, height=30, text='AI1', show_label=False, tip='Show channel AI1 on the graph.'),
    row('CH2', BTN, T, 1, left=244, top=232, width=100, height=30, text='AI2', show_label=False, tip='Show channel AI2 on the graph.'),
    row('CH3', BTN, T, 1, left=354, top=232, width=100, height=30, text='AI3', show_label=False, tip='Show channel AI3 on the graph.'),
    row('Input Range', ENUM, T, 1, left=24, top=302, width=120, tip='Input range of all channels.'),
    # page 2: Trigger
    row('Trigger Source', r'RingEnum\Text Ring NI_Silver.ctl', T, 2, left=24, top=72, width=150, tip='What starts a triggered acquisition.'),
    row('Trigger Slope', ENUM, T, 2, left=220, top=72, width=110, tip='Edge of the analog trigger.'),
    row('Trigger Level (V)', r'Numeric\Horizontal Pointer Slide NI_Silver.ctl', T, 2, left=24, top=142, width=300,
        tip='Level of the analog edge trigger. Drag the pointer.'),
    row('Filter Cutoff (Hz)', r'Numeric\Knob NI_Silver.ctl', T, 2, left=370, top=112, width=120, height=120,
        tip='Cutoff of the anti-aliasing filter. Drag the knob.'),
    # page 3: Logging
    row('Log Folder', r'String\File Path Control NI_Silver.ctl', T, 3, left=24, top=72, width=470,
        tip='Where log files would be written. The button opens the folder dialog.'),
    row('File Prefix', STR, T, 3, left=24, top=132, width=200, tip='Start of each log file name.'),
    row('File Format', ENUM, T, 3, left=260, top=132, width=110, tip='Format of the log files.'),
    row('Split Every (min)', NUM, T, 3, left=24, top=192, width=110, tip='Starts a new log file after this many minutes.'),
    row('Scheduled Start', r'Numeric\Time Stamp Control NI_Silver.ctl', T, 3, left=260, top=192, width=230,
        tip='When a scheduled acquisition starts. The button opens the calendar.'),
    row('Comment', STR, T, 3, left=24, top=252, width=470, height=60, tip='Stored in the header of every log file.'),
    # the tab control itself, the buttons below it
    row('Acquire', BTN, left=16, top=416, width=126, height=38, text='Acquire', show_label=False,
        tip='Starts and stops the simulated acquisition.'),
    row('Apply', ACT, left=154, top=416, width=126, height=38, text='Apply', show_label=False,
        tip='Applies the configuration - asks first in a LabVIEW dialog.'),
    row('Load Configuration', ACT, left=292, top=416, width=126, height=38, text='Load...', show_label=False,
        tip='Opens a configuration file in the native file dialog.'),
    row('Quit', r'Boolean\Stop Button NI_Silver.ctl', left=430, top=416, width=126, height=38, text='Quit', show_label=False,
        tip='Stops the logger and the remote share.'),
    # right: graph and status
    row('Live Data', r'Graph\Waveform Graph NI_Silver.ctl', left=590, top=34, width=560, height=220,
        tip='The last 1000 samples of every enabled channel.'),
    row('Acquiring', r'Boolean\LED NI_Silver.ctl', left=600, top=370, tip='Lit while the channels are acquired.'),
    row('Samples Acquired', NUMI, left=680, top=370, width=110, tip='Samples per channel since the start.'),
    row('Buffer Usage (%)', r'Numeric\Horizontal Progress Bar NI_Silver.ctl', left=820, top=370, width=150,
        tip='How full the 1000-sample display buffer is.'),
    row('AI0 RMS (V)', r'Numeric\Gauge NI_Silver.ctl', left=1000, top=350, width=100, height=100, tip='RMS value of channel AI0.'),
    row('Board (degC)', r'Numeric\Thermometer NI_Silver.ctl', left=1130, top=340, height=110,
        tip='Temperature of the acquisition board (simulated).'),
    row('Status', STRI, left=16, top=496, width=540, tip='What the logger did last.'),
    row('Remote Link', STRI, left=590, top=496, width=560, tip='Open this link in a browser to operate the panel (RemoteVI).'),
    row('error out', '', left=16, top=600, visible=False),
]
TABS = [('Configuration', ['Acquisition', 'Channels', 'Trigger', 'Logging'], 120, 540, 380)]
WINDOW = (80, 60, 80 + 1250, 60 + 560)

if __name__ == '__main__':
    silver = sys.argv[1] if len(sys.argv) > 1 else r'C:\Program Files\National Instruments\LabVIEW 2026\vi.lib\silver_ctls'
    spec = os.path.join(HERE, 'remotevi_demo.spec.xml')
    write_spec(spec, ROWS, TABS, WINDOW)
    print(inputs_json(os.path.join(REPO, 'examples', 'RemoteVI Demo.vi'), silver, spec))
