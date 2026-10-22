# RemoteVI architecture

RemoteVI publishes a running VI's front panel to a web browser: you see it pixel for pixel and can interact with it. It takes one click from the Tools menu, or one VI call in an application. It brings back what LabVIEW Remote Panels used to do, without the browser plug-in and without the NI Web Server.

## Goals and constraints

| Goal | Consequence |
|---|---|
| Pixel-accurate view | The panel is streamed **as an image**, not re-implemented in HTML. Whatever LabVIEW draws (XControls, custom controls, graphs, decorations) shows up exactly. |
| Low latency | WebSocket, `TCP_NODELAY`, only dirty tiles, lossless codec that is cheap to encode, ack-based flow control so frames never queue up. |
| LabVIEW-only | Pure G. No DLLs, no NI Web Server, no VIPM dependencies. The browser client is static HTML/JS that the toolkit serves itself, with no build step. |
| LabVIEW 2020+ | Only features available in 2020: VI Server, TCP primitives, `Flatten To JSON`/`Unflatten From JSON`, LVOOP, Async Call By Reference. |
| One click | Tools menu → pick VI → URL + QR code. The target VI is **not modified**. |
| IDE first, then EXE, then RT | See [Targets](#targets). |

## Overview

```
 ┌──────────────── LabVIEW (IDE or EXE) ──────────────────────────────────────────┐
 │                                                                                │
 │  Target VI ◄── VI Server refs ──┐                                              │
 │  (unmodified)                   │                                              │
 │                    ┌────────────┴─────────┐     ┌──────────────────────────┐   │
 │                    │ Capture loop         │     │ PanelModel               │   │
 │                    │ Get Panel Image      │     │ walks Panel.Controls[]   │   │
 │                    │ → U32 pixmap         │     │ bounds, kind, value      │   │
 │                    └────────────┬─────────┘     └────────────┬─────────────┘   │
 │                                 │ pixmap                     │ layout JSON     │
 │                    ┌────────────▼────────────────────────────▼─────────────┐   │
 │                    │ Server  (one per published VI)                        │   │
 │                    │  ├─ Transport (abstract): TCP+HTTP+WebSocket [default]│   │
 │                    │  ├─ Session × N: per-client diff state, flow control  │   │
 │                    │  └─ InputDispatcher → ControlAdapter (per kind)       │   │
 │                    └────────────┬──────────────────────────────────────────┘   │
 └─────────────────────────────────┼──────────────────────────────────────────────┘
                                   │ ws://host:port/ws    (binary frames + JSON)
                     ┌─────────────▼─────────────┐
                     │ Browser: canvas renderer, │
                     │ input capture, overlays   │
                     └───────────────────────────┘
```

### 1. Capture: pixel-exact frames

* `Panel.Get Image` (or `VI.Get Panel Image` as a fallback) → `Unflatten Pixmap` → 2D `U32` array of `0x00RRGGBB`.
* The loop runs only while at least one session is connected. The rate is adaptive: up to `MaxFPS` (default 30) while something changes, and it backs off when nothing has changed for a while.
* **Tile diff**: the panel is split into a grid of 64×64 tiles. Each session keeps the last pixmap *it* was sent, so a slow client never forces a fast client to wait, and every client gets a consistent picture. Only tiles that differ are sent.
* **Per-tile encoding**, all lossless:
  * `SOLID`: the tile is a single colour (typical for panel background), 4 bytes.
  * `QOI`: [Quite OK Image](https://qoiformat.org) format. It compresses about as well as PNG on UI graphics, takes O(n) to encode with a 64-entry hash, and is around 150 lines of G. We picked it over PNG because LabVIEW 2020 has no in-memory PNG encoder, and deflate in pure G is far too slow for 30 fps.
  * `RAW_RGB`: used when QOI would be larger (noise, photos).
* Encoded tiles are cached per capture, so N clients cost one encode.

### 2. Layout and interaction

The bitmap shows *what* the panel looks like. To make it *interactive*, the server also sends a **layout**: one entry per control with id, label, kind, bounds, an optional editable sub-rectangle, range, enum items and read-only flag. `PanelModel` builds it through VI Server (`Panel.Controls[]`, recursing into clusters, tabs and sub-panels' pane controls). It's resent when bounds or visibility change, checked at about 2 Hz.

Input is handled in one of three ways, picked per control kind (see [protocol.md](protocol.md#input-model)):

| Control | Browser | LabVIEW side |
|---|---|---|
| Boolean | sends `mouse down/up` | `BooleanAdapter` applies the mechanical action (switch vs. latch, when-pressed vs. when-released) and writes `Value (Signaling)` |
| Slider, knob, dial, scrollbar | sends `mouse down/move/up` | adapter maps the pointer to a value using scale range and housing geometry |
| Numeric, string, path | opens an HTML `<input>` **overlay** at the control's text rectangle, sends `set` on Enter | adapter validates and coerces the JSON value via `Unflatten From JSON` with the control's own data type, then writes `Value (Signaling)` |
| Enum, ring, combo box | opens an HTML `<select>` overlay with the items | same as above |
| Anything else (graphs, XControls, tables…) | view-only in v1 | `FallbackAdapter` rejects the input |

Using `Value (Signaling)` means the target VI's own event structures fire exactly as if a local user had operated the control. That's the property that makes "publish any VI unmodified" work.

Overlays give native text editing (IME, clipboard, mobile keyboards) with no round trip per keystroke. The pixel stream shows the committed value a frame later.

### 3. Transport

* An abstract `Transport` class, with the default implementation `TcpWebSocketTransport` on the native TCP primitives. A TLS variant (LabVIEW 2020's TLS functions) or an adapter around a third-party server (for example IG HTTP Server) can be added without touching anything else.
* The HTTP surface is deliberately tiny: `GET` static files from a fixed table, plus `GET /ws` upgrade. See [security.md](security.md) for why this is safe to write ourselves and which limits are enforced.
* Server → client: binary `FRAME` messages and JSON text messages. Client → server: JSON text messages only.
* **Flow control**: the client acks every frame after painting it. A session never has more than `FramesInFlight` (default 2) unacknowledged frames. When the network or the browser is slow, the client skips intermediate states instead of watching an ever-growing backlog. This is what keeps latency low under load.

### 4. Sessions and control ownership

The modes match Remote Panels' semantics:

* `single` (default): one controller, everyone else views. The first client gets control, and others can *Request control*, which takes it over (as in Remote Panels). The host can always reclaim control.
* `everyone`: all clients may operate the panel.
* `view`: nobody may operate the panel, and input is ignored.

### 5. LabVIEW code organisation (LVOOP, no framework dependency)

```
source/RemoteVI.lvlib
├── API/                       public, documented, on the palette
│   ├── RemoteVI Publish.vi         VI ref + Options → Server, URL
│   ├── RemoteVI Unpublish.vi
│   ├── RemoteVI Get URL.vi
│   └── RemoteVI Options.ctl        port, bind address, token, mode, max fps, tile size, control allowlist
├── Server/Server.lvclass      owns listener, capture loop, session list (DVR-protected)
├── Session/Session.lvclass    per-client state: lastSent pixmap, seq/ack, role
├── Transport/
│   ├── Transport.lvclass           abstract
│   ├── TcpWebSocketTransport.lvclass
│   ├── HTTP_*.vi                   head parsing, response building, static table
│   └── WS_*.vi, SHA1.vi, Base64.vi frame codec, handshake
├── Capture/                   PanelCapture.vi, TileGrid.vi, TileDiff.vi, EncodeTile.vi, QOI_Encode.vi, FrameEncode.vi
├── Panel/PanelModel.lvclass   VI Server walk → layout cluster → JSON
├── Input/
│   ├── InputDispatcher.vi
│   └── ControlAdapter.lvclass  + BooleanAdapter, NumericAdapter, StringAdapter, PathAdapter,
│                                 ListAdapter (enum/ring/combo), SliderAdapter, FallbackAdapter
└── Web/                       the browser client (web/), copied into the package; embedded for EXE builds
source/Tools/                  installs to <LabVIEW>/project/RemoteVI/ → Tools » RemoteVI » Publish Front Panel…
```

Concurrency: each `Server` runs three loops, started with *Async Call By Reference*: Listener, Capture, and one Reader per session. Shared state (the session list and the current owner) sits behind a DVR. Writes to a socket happen only from the capture loop and from that session's reader, under a per-session semaphore, so frames and JSON messages never interleave mid-message.

Every pure function (parsers, codecs, diff, encoders, hit tests) is a stateless subVI with no I/O. Those are exactly what the Caraya unit tests cover, using the shared vectors in `tests/vectors/`.

## The reference implementation

`tools/` holds a JavaScript reference implementation of the server side (codec, tiles, HTTP, WebSocket), plus a mock server that renders a simulated panel. It serves two purposes:

1. The browser client can be developed and tested without LabVIEW.
2. It's an executable specification: the G code is ported function by function from `tools/lib/*.mjs`. The vectors in `tests/vectors/` are generated from it, and the Caraya tests assert the G code produces the same bytes.

## Targets

| Target | Status | Notes |
|---|---|---|
| LabVIEW IDE (Windows, Linux, macOS) | v1 | Full feature set. |
| Built EXE | v1 | Same code path. The panel must be open, but it may be minimised or off-screen (spike S1 checks hidden panels). The web client is embedded as a string constant, so the build needs no support files. |
| LabVIEW Real-Time | v2 (planned) | RT targets have **no UI thread to render panels**, so `Get Panel Image` isn't available. Plan: at deploy time in the IDE, RemoteVI captures a *panel skin*: the background with the controls hidden, plus per-control state images such as boolean true/false and the slider housing. On the target only values are streamed, and the browser composites the skin with values drawn into the edit rectangles. That's near-pixel-accurate for standard controls and keeps RT CPU load tiny. The transport, session and protocol code is shared unchanged (pure TCP, works on NI Linux RT). |

## Risks to retire first (spikes)

| # | Question | Why it matters | Fallback |
|---|---|---|---|
| S1 | How fast is `Get Panel Image` for a 1920×1080 panel in the IDE and in an EXE? Does it work for a hidden or minimised panel? | Sets the achievable frame rate. | Capture per control with `Control.Get Image` and only for controls whose value changed. Capture less often when idle. |
| S2 | How fast is G QOI encoding and tile diffing on a 1080p U32 array, in-place? | CPU budget. | Bigger tiles, compare rows with `Equal?` on subarrays, encode in parallel for-loops. |
| S3 | Latched booleans can't be written through `Value`/`Value (Signaling)` (error 1193). | Stop buttons are usually latched. | Temporarily switch the mechanical action to the equivalent switch, write, restore. Or emit the value change through a RemoteVI user event that a VI can opt into. |
| S4 | Getting the slider, knob and housing geometry from VI Server. | Accurate drag mapping. | Map against the control bounds with an empirically measured inset. |
| S5 | Dynamic Value Change event registration on arbitrary control refs, for change-driven capture. | Lower idle CPU. | Polling at a low rate when idle. |
