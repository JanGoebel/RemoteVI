# LabVIEW implementation guide

This document specifies every VI in `source/RemoteVI.lvlib`, in the order they should be built. Each pure VI has a JavaScript reference function: port it one to one and check it against the shared vectors (see [testing.md](testing.md)).

Conventions:

* **LabVIEW 2020 SP1**, saved with *Separate compiled code from source* (the project sets this by default).
* Error in/out on every VI that can fail. Pure VIs are reentrant (*preallocated clone*) and have no front-panel I/O.
* Connector pane 4-2-2-4. Error cluster bottom left/right, primary input/output top left/right.
* Byte strings are LabVIEW strings (U8 arrays where noted). All multi-byte integers are big-endian: use `Flatten To String` with the default byte order and *prepend size* = False.
* Pixmaps are `2D U32` arrays `[row, column]` of `0x00RRGGBB`, exactly what `Unflatten Pixmap` (24-bit) returns.

## Milestone 1: pure building blocks (no I/O, 100 % Caraya-covered)

| VI | Inputs → Outputs | Reference | Vectors |
|---|---|---|---|
| `Transport/SHA1.vi` | U8[] data → U8[20] digest | `node:crypto` | `sha1.json` |
| `Transport/Base64 Encode.vi` | U8[] → string | `Buffer.toString('base64')` | `base64.json` |
| `Transport/WS Accept Key.vi` | key string → accept string | `acceptKey()` in `tools/lib/websocket.mjs` | `websocket.json → accept` |
| `Transport/WS Decode Client Frame.vi` | U8[] buffer, max payload (U32, default 65536) → complete? (bool), fin, opcode (U8), payload (U8[]), bytes consumed (U32), close code (U16; 0 = OK) | `decodeClientFrame()` | `websocket.json → clientFrames, incompleteClientFrames` |
| `Transport/WS Encode Server Frame.vi` | opcode (U8), payload (string) → frame (string) | `encodeServerFrame()` | `websocket.json → serverFrames` |
| `Transport/HTTP Find Head End.vi` | buffer string → index (I32, −1 = need more), error status (U16) | `findHeadEnd()` | – |
| `Transport/HTTP Parse Request Head.vi` | head string → Request cluster {method, path, query (keys[]/values[]), version, header names[] (lower case), header values[]}, status (U16; 0 = OK) | `parseRequestHead()` | `http.json` |
| `Transport/HTTP Is WebSocket Upgrade.vi` | Request → bool | `isWebSocketUpgrade()` | `http.json` |
| `Transport/HTTP Build Response Head.vi` | status (U16), header names[], values[] → string | `buildResponseHead()` | – |
| `Capture/QOI Encode.vi` | 2D U32 pixmap, rect {x,y,w,h} → U8[] | `encodeQoi()` in `tools/lib/qoi-encode.mjs` | `qoi.json` |
| `Capture/Tile Grid.vi` | width, height, tile size → rect[] | `tileGrid()` | `tiles.json → grid` |
| `Capture/Tile Diff.vi` | prev pixmap, cur pixmap, tile size → dirty rect[] (all tiles if the sizes differ or prev is empty) | `diffTiles()` | `tiles.json → diff` |
| `Capture/Encode Tile.vi` | pixmap, rect → Tile {rect, encoding (U8), data (U8[])} | `encodeTile()` | `tiles.json → encodeTile` |
| `Capture/Frame Encode.vi` | flags, seq (U32), width, height, Tile[] → message string | `encodeFrame()` in `web/js/protocol.js` | `frame.json` |

Implementation notes:

* **SHA-1**: work on `U32`. Rotate with two `Logical Shift`s OR-ed together, `(x << n) | (x >> (32 − n))`, not with `Rotate Left With Carry`. Pad to 64-byte blocks. The vectors deliberately include 55, 56, 63, 64 and 65 byte inputs.
* **QOI**: keep the 64-entry index as a `U32[64]` shift register initialised to an impossible value (`0xFFFFFFFF`, since pixels are 24-bit). Hash = `(r·3 + g·5 + b·7 + 255·11) mod 64`. Compute differences as `I8` wrap-around: `(cur − prev + 384) AND 0xFF − 128`. Preallocate the output at `14 + w·h·4 + 8` bytes, write with `Replace Array Subset`, and trim at the end. Never build the array in a loop.
* **Tile Diff**: compare row slices with `Array Subset` + `Equal?` (compare aggregates) instead of per-pixel loops. Run the loop over tiles with *parallel for-loop* enabled.

## Milestone 2: capture, layout and input against a fixture VI

| VI / class | Responsibility |
|---|---|
| `Capture/Panel Capture.vi` | VI ref → pixmap (`Panel.Get Image`, 24-bit, visible area only) → `Unflatten Pixmap` |
| `Panel/PanelModel.lvclass` | `Build Layout.vi`: VI ref → Control[] (id = refnum as string, label, kind, bounds, edit rect, readonly, visible, disabled, min/max, items, mech). Recurses into `Cluster.Controls[]` and `Tab.Pages[].Controls[]`. Controls are ordered back-to-front. `Layout Changed?.vi` compares bounds and visibility. |
| `Panel/Classify Control.vi` | control ref → kind enum, using `Class Name`. Unknown classes → `other`. |
| `Input/ControlAdapter.lvclass` | dynamic dispatch `Apply Mouse.vi`, `Apply Set.vi` (JSON string → value), `Current Value JSON.vi` |
| `BooleanAdapter`, `NumericAdapter`, `StringAdapter`, `PathAdapter`, `ListAdapter`, `SliderAdapter`, `FallbackAdapter` | per-kind behaviour; see `tools/mock-server/panel.mjs` (`set()`, `mouse()`) for the reference semantics |
| `Input/Input Dispatcher.vi` | JSON message → adapter lookup by id or hit test → apply → changed values |

`Apply Set.vi` must use `Unflatten From JSON` with the control's own `Value` data type, taken from the property node's variant. Write with `Value (Signaling)`. For latched booleans see spike S3 in [architecture.md](architecture.md#risks-to-retire-first-spikes).

## Milestone 3: server, sessions, API

| VI / class | Responsibility |
|---|---|
| `Transport/Transport.lvclass` | abstract: `Listen`, `Accept`, `Read`, `Write`, `Close` |
| `Transport/TcpWebSocketTransport.lvclass` | TCP primitives. Sets `TCP_NODELAY`: on Windows through the `TCP Get Raw Net Object` + `setsockopt` pattern, guarded by a conditional disable structure so non-Windows targets compile. Enforces the timeouts in security.md. |
| `Web/Static Files.vi` | returns the fixed table {path → MIME type, body}. Development builds read `web/` once at publish time. EXE builds use a string constant generated by `scripts/Embed Web Client.vi`. |
| `Session/Session.lvclass` | lastSent pixmap, seq, lastAck, role, per-session write semaphore. `Push Frame.vi` mirrors `Session.pushFrame()` in `tools/mock-server/server.mjs`. |
| `Server/Server.lvclass` | Listener loop, Capture loop and Reader loops (Async Call By Reference, *0x80 fire and forget* + *0x100 reentrant*). Shared state sits in a DVR. Stops on `Unpublish` or when the target VI goes idle. |
| `API/RemoteVI Publish.vi` | **the one VI a user needs**: VI ref (default: caller) + Options → Server + URL. |
| `API/RemoteVI Unpublish.vi`, `API/RemoteVI Get URL.vi` | – |

Behavioural reference: `tools/mock-server/server.mjs`. The integration tests in `tests/js/server.test.mjs` describe what the LabVIEW server must do, and the Caraya integration suite repeats them with a G WebSocket client.

## Milestone 4: one-click tooling and packaging

* `source/Tools/Publish Front Panel.vi` → installed to `<LabVIEW>/project/RemoteVI/` so it appears under **Tools » RemoteVI**. It shows a dialog listing all VIs in memory that have an open front panel. It has these options: port, LAN access, mode. Clicking *Publish* opens the browser and shows the URL and a QR code (`Capture/QR Encode.vi`, pure G, byte mode, ECC level M).
* Quick Drop shortcut `Ctrl+Space, Ctrl+W`: publish the front-most VI.
* `build/RemoteVI.vipb`: VI Package. Installs the library to `<vi.lib>/RemoteVI`, the palette menu under *Addons » RemoteVI*, and the Tools menu entry. Minimum LabVIEW version 20.0.
