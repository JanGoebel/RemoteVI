# Testing

| Layer | Tool | What |
|---|---|---|
| Pure G VIs | Caraya unit tests generated from the vectors (`tests/caraya/`, see below) | Protocol (also Window Frame Encode and the `x <id>` message), Dirty Rects, Translate Input and Track Modifiers against `tests/vectors/*.json` |
| Benchmarks | `spikes/Bench Dirty Rects.vi`, `spikes/Bench Encode PNG.vi` | diff and PNG encode timings; `spikes/Spike Start Errors.vi` checks Start's error reporting |
| Server acceptance | `node tools/check-server.mjs --url http://127.0.0.1:8088 [--click x,y] [--png out.png]` | black-box checks of a running server, the LabVIEW one or the reference one: HTTP surface, first frame pixel coverage, flow control, input, robustness |
| Client and reference | `node:test` (`npm test`, Node 22+, no install) | WebSocket and HTTP parsers, end-to-end against the reference server, client file is pure ASCII and self-contained |
| Input fidelity in LabVIEW | `RVI_LV=1 npm run test:lv` against `tests/fixtures/RemoteVI Fixture.vi` (see below) | clicks, latched buttons, typing, modifiers, hover, ring and right-click menus, tabs, wheel, double click, Shift+arrow, tip strips, run-time shortcut menu with a submenu, hover highlight in menus, submenu beside its parent, the whole window in the stream (menu bar, toolbar, scrollbars; `origin`), run-time menu bar with a submenu, scrollbar arrows, a LabVIEW dialog as a modal window with its own picture (Enter answers it, the panel behind it takes no input, a click on its No button answers it), a native file dialog (Escape cancels it) |

## Shared test vectors

`tests/vectors/` holds language-neutral JSON produced by `tools/gen-vectors.mjs`. `npm test` fails if the committed vectors drift from the generator.

| File | For VI | Contents |
|---|---|---|
| `websocket.json` | WS Encode Server Frame, WS Decode Client Frame | RFC 6455 accept keys, valid, invalid and incomplete client frames with close codes, server frames |
| `http.json` | – (IG HTTP parses requests) | request heads and expected status, used by the JS parser tests |
| `rects.json` | Dirty Rects | first capture, identical, single pixel, row merging, clipped edge tiles |
| `frame.json` | Frame Encode, Overlay Encode, Window Frame Encode | complete FRAME, OVERLAY and WINDOW FRAME messages |
| `input.json` | Parse Input | valid and malformed client messages, also `x <id>` (close a window) |
| `text.json` | JSON String, Tips Message, Splitters Message | ASCII-only JSON string literals of UTF-16 text; complete `tips` messages (empty texts left out) |
| `translate.json` | Translate Input, Track Modifiers | client/screen coordinate rules with and without mouse capture, wheel, double click as a second down, key scan codes, WM_CHAR wrapping, allow list; `modifiers`: modifier keys held after a message |

Bytes are lowercase hex. Pixels are `0x00RRGGBB` integers, row-major.

## Caraya unit tests

`tests/caraya/build.py` generates the G unit tests of the pure VIs from `tests/vectors/` and composes them with the labview-mcp pylabview composer (`tools/aixml/compose.py`). Every vector becomes one assertion, labelled with the vector's name.

| VI under test | Vectors | Test VI |
|---|---|---|
| Protocol/RemoteVI Frame Encode.vi | `frame.json` cases | `unit/Protocol/Test Frame Encode.vi` |
| Protocol/RemoteVI Overlay Encode.vi | `frame.json` overlays | `unit/Protocol/Test Overlay Encode.vi` |
| Protocol/RemoteVI Window Frame Encode.vi | `frame.json` windowFrames | `unit/Protocol/Test Window Frame Encode.vi` |
| Protocol/RemoteVI Parse Input.vi | `input.json` | `unit/Protocol/Test Parse Input.vi` |
| Protocol/RemoteVI WS Encode Server Frame.vi | `websocket.json` serverFrames | `unit/Protocol/Test WS Encode Server Frame.vi` |
| Protocol/RemoteVI WS Decode Client Frame.vi | `websocket.json` clientFrames, incompleteClientFrames | `unit/Protocol/Test WS Decode Client Frame.vi` |
| Capture/RemoteVI Dirty Rects.vi | `rects.json` | `unit/Capture/Test Dirty Rects.vi` |
| Input/RemoteVI Translate Input.vi | `translate.json` cases (input through Parse Input first) | `unit/Input/Test Translate Input.vi` |
| Input/RemoteVI Track Modifiers.vi | `translate.json` modifiers | `unit/Input/Test Track Modifiers.vi` |

Each test has two layers. `support/RemoteVI Check <VI>.vi` calls the VI once per vector and renders expected and actual the same way: bytes as lowercase hex, structured results as short text (`mouse msg=513 x=120 y=45 wParam=1`, `close id=5113012`, `posts=513:1:4325386; tracking=T cursor=-`, rects `x,y,w,h;`). It returns `labels`, `expected`, `actual` and `failures`, and needs no test framework, so it can be run on its own in the IDE. `unit/<area>/Test <VI>.vi` is the Caraya test around it: Define Test, then one Assert Equal per vector. `RemoteVI Caraya Runner.vi` runs all of them non-interactively and writes a JUnit report.

The expected values are constants inside the generated VIs, not read from JSON at run time: LabVIEW's Unflatten From JSON fails with error -375006 when an object lacks a cluster element, and the vectors leave fields out on purpose (null results, error-or-payload frames, optional cursor). So after a vector changes:

```
python tests/caraya/build.py           # regenerate AIXML and compose the VIs
python tests/caraya/build.py --check   # CI: exit 1 when the generated AIXML is stale
```

Comparisons follow the VI's pane types: a vector value that does not fit the output type is wrapped into it as the VI documents (`k 256 -2147483648 0` gives wParam 18446744071562067968 on the U64 terminal).

Requirements: Caraya (`jki_lib_caraya`) installed for LabVIEW 2025. Without it `build.py` composes only the support and check VIs and skips the Caraya layer with a message; a test VI composed against another LabVIEW's Caraya would link into that installation and be broken.

### Running

Headless, with G-CLI and its Caraya tool (`lvos_lib_caraya_cli_extension`):

```
.\scripts\run-caraya.ps1 [-Build] [-Report .\reports\caraya.xml] [-QuitLabVIEW]
```

It checks that Caraya is installed for the LabVIEW version, optionally regenerates the tests, runs every VI in `tests/caraya/unit`, writes the JUnit report and prints tests and failures per suite. LabVIEW is left running unless `-QuitLabVIEW` is given.

In the IDE: run `tests/caraya/RemoteVI Caraya Runner.vi` (report beside it, or at `Report Path`). Its `error out` is 7002 when an assertion failed; the report names which one. Without Caraya, run a `support/RemoteVI Check <VI>.vi` and read `failures`.

## LabVIEW integration suite

`tests/lv/fixture.test.mjs` drives `tests/fixtures/RemoteVI Fixture.vi` through the real server on port 8089, exactly as the browser does, and reads LabVIEW's side from the fixture's event log (format in `tests/lv/harness.mjs`). Run the fixture (one RemoteVI server per LabVIEW instance: stop any other first), then `RVI_LV=1 npm run test:lv`; stop it with its Stop button. LabVIEW may stay in the background while the suite runs, as in real use: tip strips reach the browser as the `tips` message, which does not depend on LabVIEW being the active application (LabVIEW itself shows tip strips only then). The round-5 tests open a Two Button Dialog (fixture button `Ask`) and the native File Dialog (button `Open`); while one is up LabVIEW does not answer VI Server or ActiveX calls, so a tool that drives LabVIEW over them waits until the dialog is answered.

The fixture is generated: `tests/fixtures/aixml/compose_fixture.py <labview-mcp bin>` composes it (through `listbox_composer.py`, which adds `style="Listbox"` to the composer, and `fix_event_data_nodes.py`, which corrects the Event Data Node indices), then `RemoteVI Fixture Arrange.vi` (Fixture = the fixture, Tab Panel = a VI holding only the tab control, made by `RemoteVI Fixture Prep Tab Panel.vi` from a copy of NI's *Programmatically Manipulate a Tab Control.vi*) pastes the tab control, sets the List rows, the Button tip strip and the layout, and saves. The layout puts error out at the bottom right, ending just inside the 900 x 600 window, which gives the panel a scroll range of about 6 px each way: both scrollbars work, and a test click still hits its control when the mouse wheel over Number has scrolled the panel (it does, as locally). Ask opens the Two Button Dialog Proceed? (Yes / No) and logs `dialog TRUE|FALSE`; Open opens the native File Dialog and logs `file <path>` or `file CANCELLED` (both latched buttons, below Stop). At run time the fixture adds a menu Fixture in front of LabVIEW's default run-time menus (Say Hello, and More > Deep Bar; replacing the default menus with Delete Menu Items stopped LabVIEW from showing tip strips, measured), logs `menubar` and `scroll` lines, and scrolls the panel back to 0,0 1.5 s after the last scroll, so a second run finds the controls where the layout lines say. Run Arrange once per compose: it pastes the tab again on a second run.

### Complex application UI

`tests/lv/complex.test.mjs` does the same against `tests/fixtures/RemoteVI Complex Fixture.vi` (also port 8089, so stop the other fixture first): run it, then `RVI_LV_COMPLEX=1 node --test tests/lv/complex.test.mjs`. The fixture is NI's *Resizable Panel with Splitter Bars.vi* with its panes filled: a toolbar pane (ring View, Inspector, Stop, Status), a left pane with a tree, a table, an array of clusters and a vertical scrollbar, and a main pane whose tab control scales with the pane (Scale Single Object) and holds a cluster, a slide, a knob and a path with browse button (page Acquisition), a graph with cursors (Display) and a subpanel (Viewer) showing one of two running VIs, swapped with the ring View. Inspector opens a separate non-modal window (FP.Open). It logs to `RemoteVI Complex Fixture.log` in the temp directory: the harness's lines plus `pane` (the visible part of each pane), `vlayout` (controls of the VI in the subpanel), `ilayout` and `iorigin` (the inspector window's controls), written again whenever they change.

21 tests: tab pages, typing into and toggling cluster elements, table cell editing, tree selection, slide and knob drags, a graph cursor drag (found by its yellow line in the frame), the native file dialog of the browse button, the subpanel VI and its swap, tip strips of nested and subpanel controls, wheel scrolling of the left pane, the floating inspector window (listed, operated, closed). The splitter tests check that the `splitters` message matches the bars in the frame and drag both bars the way the browser does (`s <id> <pos>`, `dragSplitter()` in the harness), then drag them back; the .NET container test is skipped (no container in the fixture).

The fixture is built from AIXML in `tests/fixtures/aixml` with the composer patched by `tools/aixml/pane_parts.py` (Pane and Splitter VI Server classes); `compose_complex.py` documents the steps: compose the helpers, graft the scaffold diagram onto a copy of NI's VI, paste the controls (from NI VIs, as the composer's slide and knob parts crash LabVIEW on load), then run `RemoteVI Complex Fixture Arrange.vi`, which places every control at fixed panel-area coordinates, sets pages, tip strips, scaling and the left pane's scrollbar, and saves.

## Performance

`tools/perf.mjs` measures a running server the way a browser uses it (it decodes every frame into a framebuffer and acks each frame right after decoding it):

```
node tools/perf.mjs --url http://127.0.0.1:8088 --seconds 5 \
  --click 48,275 --roi 26,265,52,22 --repeat 20 \
  --type 60,336 --type-roi 22,326,95,20 --hover 20,60,180,380
```

* **stream**: frames per second, gaps between frames, bytes, rects and pixels per frame. Frames only go out when something changed, so on the demo this is the rate at which the demo redraws its graph, not the server's limit.
* **click** / **type**: input-to-photon - from posting a click (move, down, up) at a point, or one character into a string clicked first, until a FRAME changes a pixel inside the region of interest (the Enable switch and the Message string of the demo above), plus the time to the first frame after the input.
* **hover**: frame gaps while a mouse move is sent every 16 ms, against the idle gaps of the stream phase.

Demo (`examples/RemoteVI Demo.vi`, port 8088), LabVIEW in the background, a second browser connected, medians (p90):

| Build | click-to-photon | key-to-photon | stream gaps | hover fps |
|---|---|---|---|---|
| 4e157a5 (panel only, `FP.Get Image`) | 67 ms (103) | 57 ms (88) | 58 ms | 14.8 |
| 3be4bfd (whole window, `PrintWindow`) | 88 ms (137) | 74 ms (99) | 59 ms | 14.7 |
| 11aaf70 / 97d6ceb (window tracking, full Z-order walks) | 87-117 ms (112-238) | 102-121 ms (137-375) | 64-67 ms | 11.2-11.4 |
| 8dda8cc (before this work) | 93-185 ms (165-249) | 53-204 ms (91-233) | 56-127 ms | 6.8-15.2 |
| now (BitBlt capture, frames every 16 ms after input, no wait after hover moves) | 59 ms (90) | 35 ms (74) | 71 ms* | 13.2 |

\* the demo now draws a 6x larger sine; its own loop (50 ms wait plus the graph) sets the frame rate. The remaining latency is mostly LabVIEW's UI thread, which handles a posted click 0-50 ms late while the demo redraws its graph (measured by posting a click and polling the window's surface). Per call on the demo: `PrintWindow` capture of the 817 x 543 window 40-50 ms, `BitBlt` copy 2-5 ms, PNG of an 817 x 128 band 5 ms, Find Popups 0.3 ms and List Windows 0.6 ms with LVFrame at Z position ~120 of 613 windows.

## Manual acceptance

1. Open and run `examples/RemoteVI Demo.vi`.
2. Browse to `http://127.0.0.1:8088/`.
3. Operate every control. Type into the string, drag the slide, watch the chart update.
4. Repeat from another machine and from a phone.
5. Stop the demo. The browser shows "Disconnected" and port 8088 is freed.
