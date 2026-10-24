# Testing

| Layer | Tool | What |
|---|---|---|
| Pure G VIs | Caraya unit tests generated from the vectors (`tests/caraya/`, see below) | Protocol, Dirty Rects, Translate Input and Track Modifiers against `tests/vectors/*.json` |
| Live G checks | spike VIs in `spikes/` | capture timing, PNG compression, input injection on `spikes/Injection Fixture.vi` through the production input chain |
| Server acceptance | `node tools/check-server.mjs --url http://127.0.0.1:8088 [--click x,y] [--png out.png]` | black-box checks of a running server, the LabVIEW one or the reference one: HTTP surface, first frame pixel coverage, flow control, input, robustness |
| Client and reference | `node:test` (`npm test`, Node 22+, no install) | WebSocket and HTTP parsers, end-to-end against the reference server, client file is pure ASCII and self-contained |
| Input fidelity in LabVIEW | `RVI_LV=1 npm run test:lv` against `tests/fixtures/RemoteVI Fixture.vi` (see below) | clicks, latched buttons, typing, modifiers, hover, ring and right-click menus, tabs, wheel, double click, Shift+arrow, tip strips, run-time shortcut menu with a submenu |

## Shared test vectors

`tests/vectors/` holds language-neutral JSON produced by `tools/gen-vectors.mjs`. `npm test` fails if the committed vectors drift from the generator.

| File | For VI | Contents |
|---|---|---|
| `websocket.json` | WS Encode Server Frame, WS Decode Client Frame | RFC 6455 accept keys, valid, invalid and incomplete client frames with close codes, server frames |
| `http.json` | – (IG HTTP parses requests) | request heads and expected status, used by the JS parser tests |
| `rects.json` | Dirty Rects | first capture, identical, single pixel, row merging, clipped edge tiles |
| `frame.json` | Frame Encode | complete FRAME messages |
| `input.json` | Parse Input | valid and malformed client messages |
| `translate.json` | Translate Input, Track Modifiers | client/screen coordinate rules with and without mouse capture, wheel, double click as a second down, key scan codes, WM_CHAR wrapping, allow list; `modifiers`: modifier keys held after a message |

Bytes are lowercase hex. Pixels are `0x00RRGGBB` integers, row-major.

## Caraya unit tests

`tests/caraya/build.py` generates the G unit tests of the pure VIs from `tests/vectors/` and composes them with the labview-mcp pylabview composer (`tools/aixml/compose.py`). Every vector becomes one assertion, labelled with the vector's name.

| VI under test | Vectors | Test VI |
|---|---|---|
| Protocol/RemoteVI Frame Encode.vi | `frame.json` cases | `unit/Protocol/Test Frame Encode.vi` |
| Protocol/RemoteVI Overlay Encode.vi | `frame.json` overlays | `unit/Protocol/Test Overlay Encode.vi` |
| Protocol/RemoteVI Parse Input.vi | `input.json` | `unit/Protocol/Test Parse Input.vi` |
| Protocol/RemoteVI WS Encode Server Frame.vi | `websocket.json` serverFrames | `unit/Protocol/Test WS Encode Server Frame.vi` |
| Protocol/RemoteVI WS Decode Client Frame.vi | `websocket.json` clientFrames, incompleteClientFrames | `unit/Protocol/Test WS Decode Client Frame.vi` |
| Capture/RemoteVI Dirty Rects.vi | `rects.json` | `unit/Capture/Test Dirty Rects.vi` |
| Input/RemoteVI Translate Input.vi | `translate.json` cases (input through Parse Input first) | `unit/Input/Test Translate Input.vi` |
| Input/RemoteVI Track Modifiers.vi | `translate.json` modifiers | `unit/Input/Test Track Modifiers.vi` |

Each test has two layers. `support/RemoteVI Check <VI>.vi` calls the VI once per vector and renders expected and actual the same way: bytes as lowercase hex, structured results as short text (`mouse msg=513 x=120 y=45 wParam=1`, `posts=513:1:4325386; tracking=T cursor=-`, rects `x,y,w,h;`). It returns `labels`, `expected`, `actual` and `failures`, and needs no test framework, so it can be run on its own in the IDE. `unit/<area>/Test <VI>.vi` is the Caraya test around it: Define Test, then one Assert Equal per vector. `RemoteVI Caraya Runner.vi` runs all of them non-interactively and writes a JUnit report.

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

`tests/lv/fixture.test.mjs` drives `tests/fixtures/RemoteVI Fixture.vi` through the real server on port 8089, exactly as the browser does, and reads LabVIEW's side from the fixture's event log (format in `tests/lv/harness.mjs`). Run the fixture (one RemoteVI server per LabVIEW instance: stop any other first), then `RVI_LV=1 npm run test:lv`; stop it with its Stop button.

The fixture is generated: `tests/fixtures/aixml/compose_fixture.py <labview-mcp bin>` composes it (through `listbox_composer.py`, which adds `style="Listbox"` to the composer, and `fix_event_data_nodes.py`, which corrects the Event Data Node indices), then `RemoteVI Fixture Arrange.vi` (Fixture = the fixture, Tab Panel = a VI holding only the tab control, made by `RemoteVI Fixture Prep Tab Panel.vi` from a copy of NI's *Programmatically Manipulate a Tab Control.vi*) pastes the tab control, sets the List rows, the Button tip strip and the layout, and saves. Run Arrange once per compose: it pastes the tab again on a second run.

## Manual acceptance

1. Open and run `spikes/RemoteVI Demo.vi`.
2. Browse to `http://127.0.0.1:8088/`.
3. Operate every control. Type into the string, drag the slide, watch the chart update.
4. Repeat from another machine and from a phone.
5. Stop the demo. The browser shows "Disconnected" and port 8088 is freed.
