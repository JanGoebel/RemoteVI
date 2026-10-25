# RemoteVI

**Operate a LabVIEW front panel from any web browser: pixel-accurate, written in G, no NI Web Server.**

RemoteVI replaces LabVIEW *Remote Panels*. The browser shows the panel exactly as LabVIEW draws it, including subpanels, splitters, tabs, graphs, XControls and custom controls. Mouse and keyboard input goes back to LabVIEW as native window messages, so the VI behaves as if someone were at the machine: event structures fire, and latched buttons latch.

## Use it

```
RemoteVI Start.vi   (VI: unwired = this VI, port = 8088, fps)  ──►  URL
... your application ...
RemoteVI Stop.vi    (port = 8088)
```

Then browse to `http://<machine>:<port>/`. The server also stops by itself when the published VI stops. Try `examples/RemoteVI Demo.vi` (port 8088).

> The default port is 8088, not 8080: on many NI machines port 8080 is taken by NI's Application Web Server.

## In the browser

* **Scaling:** `1:1` (actual pixels), `Fit` (whole window in view), `Width` (fit the width, scroll vertically), zoom `−` / `+` or Ctrl+wheel. The choice is remembered per browser. Keys when the panel doesn't have focus: `1`, `F`, `W`, `+`, `−`.
* **Fullscreen** button.
* **Touch:** one finger is the mouse (tap = click, slide = drag), a long press is a right-click, two fingers pinch-zoom and pan. The keyboard button opens the on-screen keyboard. Phones start in `Width` mode.

## How it works

* **Out:** `FP.Get Image` → diff in 64 px tiles → changed bands as PNG (NI's `LV Image to PNG Data.vi`, zlib level 1) → WebSocket → canvas.
* **In:** the browser sends Win32 messages (`WM_LBUTTONDOWN`, `WM_MOUSEMOVE`, `WM_CHAR`, …) with panel coordinates. The server maps them to the panel's window and calls `PostMessageW`.
* **HTTP:** IG HTTP Utils / IG WebSocket Stream handle the request and the upgrade. The client is one embedded HTML file.

Details: [docs/architecture.md](docs/architecture.md), [docs/protocol.md](docs/protocol.md), [docs/security.md](docs/security.md).

## Status

| Part | State |
|---|---|
| Capture, diff, PNG (`source/Capture`) | ✅ vectors and benchmarks |
| Protocol, WebSocket framing (`source/Protocol`) | ✅ all vectors pass |
| Input (`source/Input`, `source/Win32`) | ✅ clicks, drags, double clicks, wheel, typing, Shift/Ctrl/Alt, hover enter/leave; host cursor and keyboard never touched |
| Popups: ring/enum menus, right-click menus with submenus, graph palette, tip strips | ✅ streamed as an overlay at their real place (may extend past the panel), hover highlight, submenus beside their parent, invisible on the host when opened remotely, panel keeps updating underneath |
| Server loop, Start/Stop (`source/Server`, `source/API`) | ✅ about 16 fps, about 1–2 % of one core; idle connections don't stall it; Start reports errors |
| Browser client (`web/index.html`) | ✅ |
| Tests | ✅ `npm test` (18), unit-test check VIs (96 vectors), LabVIEW integration suite `tests/lv` (16) |
| Caraya unit tests | ✅ 96 assertions over 8 suites pass (`tests/caraya/RemoteVI Caraya Runner.vi`, JUnit report); Caraya installed for LabVIEW 2025 |
| Splitter dragging | ❓ untested on a panel with an unlocked splitter |
| Library `source/RemoteVI.lvlib` | ✅ every VI under `source/`, virtual folders mirror the disk, all members public (entry points: `API/`) |
| Access token, bind address, palette, VI package | planned |

## Known limits

* **Menus are driven with keys.** The highlight follows the remote pointer and a submenu opens after 400 ms on its entry, but through arrow keys posted to LabVIEW, so a menu that takes no keys (colour picker, line width popup) shows no hover highlight remotely; it is clicked by moving just that window under the host cursor for the click. While such a popup is open its parent menus react to clicks only by closing.
* **Remote tip strips can flash on the host.** One triggered remotely shows on the host for 20–90 ms before it is hidden, or stays visible if the host cursor is over the panel.
* **Ctrl+letter.** Ctrl+A sent as a character reaches LabVIEW, but the letter produces no Key Down event of its own.
* **One server per LabVIEW instance.** The Server Loop isn't reentrant. A second `RemoteVI Start.vi` returns error 5001, and a port in use returns the listener's error (60).
* **Modifiers are shared.** Several clients holding Shift/Ctrl at the same time share LabVIEW's single key state.
* **Windows only** (input injection is Win32).

## Testing

```bash
npm test                                         # JS reference, vectors, end-to-end against the reference server
RVI_LV=1 npm run test:lv                         # LabVIEW integration suite; run tests/fixtures/RemoteVI Fixture.vi first (port 8089)
node tools/check-server.mjs --click 50,228       # black-box check of a running server (default http://127.0.0.1:8088)
```

Details: [docs/testing.md](docs/testing.md).

## Development

```bash
npm run mock                               # reference server with a simulated panel, for client work without LabVIEW
```

The G code was generated with labview-mcp on LabVIEW 2025. The AIXML sources are in `tools/aixml/`. `scripts/Build Win32 Wrappers.vi` regenerates the Call Library wrappers, and `scripts/gen-index-html-vi.mjs` regenerates the embedded client.
