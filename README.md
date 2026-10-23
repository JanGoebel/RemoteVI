# RemoteVI

**Operate a LabVIEW front panel from any web browser: pixel-accurate, written in G, no NI Web Server.**

RemoteVI replaces LabVIEW *Remote Panels*. The browser shows the panel exactly as LabVIEW draws it, including subpanels, splitters, tabs, graphs, XControls and custom controls. Mouse and keyboard input goes back to LabVIEW as native window messages, so the VI behaves as if someone were at the machine: event structures fire, and latched buttons latch.

## Use it

```
RemoteVI Start.vi   (VI: unwired = this VI, port, fps)  ──►  URL
... your application ...
RemoteVI Stop.vi    (port)
```

Then browse to `http://<machine>:<port>/`. The server also stops by itself when the published VI stops. Try `spikes/RemoteVI Demo.vi` (port 8088).

> On many NI machines port 8080 is taken by NI's Application Web Server. Pick another port.

## How it works

* **Out:** `FP.Get Image` → diff in 64 px tiles → changed bands as PNG (NI's `LV Image to PNG Data.vi`, zlib level 1) → WebSocket → canvas.
* **In:** the browser sends Win32 messages (`WM_LBUTTONDOWN`, `WM_MOUSEMOVE`, `WM_CHAR`, …) with panel coordinates. The server maps them to the panel's window and calls `PostMessageW`.
* **HTTP:** IG HTTP Utils / IG WebSocket Stream handle the request and the upgrade. The client is one embedded HTML file.

Details: [docs/architecture.md](docs/architecture.md), [docs/protocol.md](docs/protocol.md), [docs/security.md](docs/security.md).

## Status

| Part | State |
|---|---|
| Capture, diff, PNG (`source/Capture`) | ✅ verified (vectors, timings) |
| Protocol, WebSocket framing (`source/Protocol`) | ✅ all vectors pass |
| Input (`source/Input`, `source/Win32`) | ✅ click, drag, typing, latched Stop on a live panel, also when the window is covered |
| Server loop, Start/Stop (`source/Server`, `source/API`) | ✅ `tools/check-server.mjs` passes against LabVIEW, about 16–18 fps, about 1–2 % of one core |
| Browser client (`web/index.html`) | ✅ |
| **Popup menus** (ring/enum dropdowns, right-click menus) | ❌ they open on the host, are invisible remotely, and block the UI thread until dismissed. See "Known issues". |
| Splitter dragging | ❓ didn't move in NI's example (possibly locked splitters). Untested on an unlocked one. |
| Access token, bind address | planned |
| `.lvlib`, palette, VI package | planned |

## Known issues

* Clicking a ring, enum or combo box, or right-clicking, opens a LabVIEW popup window (`LVMenuWnd`) on the host. It isn't part of `FP.Get Image`, posted clicks and keys don't select in it, and while it is open the UI thread is busy, so streaming stops. It closes when the host's LabVIEW loses activation.
* Only one server per LabVIEW instance (the Server Loop isn't reentrant).
* A TCP connection that sends nothing stalls the loop for up to 1 s (head read timeout).

## Development

```bash
npm test                                   # JS reference, vectors, end-to-end against the reference server
npm run mock                               # reference server with a simulated panel
node tools/check-server.mjs --url http://127.0.0.1:8088 --click 50,228   # black-box check of a running server
```

The G code was generated with labview-mcp on LabVIEW 2025. The AIXML sources are in `tools/aixml/`. `scripts/Build Win32 Wrappers.vi` regenerates the Call Library wrappers, and `scripts/gen-index-html-vi.mjs` regenerates the embedded client.
