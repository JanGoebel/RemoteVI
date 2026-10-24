# RemoteVI protocol, version 2

This is the normative spec. The reference implementation is `tools/lib/protocol.mjs` (with `rects.mjs`, `websocket.mjs`, `http.mjs`), the reference server is `tools/mock-server/server.mjs`, and the browser side is `web/index.html`. Test vectors are in `tests/vectors/`.

Version 2 replaces version 1's per-control model (layout, `set`, overlays, QOI tiles). The panel is a picture going one way and raw mouse and keyboard events going the other. Everything LabVIEW draws is shown as drawn, and everything a local user can click can be clicked remotely.

## 1. HTTP endpoints

| Request | Response |
|---|---|
| `GET /` or `GET /index.html` | the browser client, one self-contained HTML file |
| `GET /ws` with a WebSocket upgrade (RFC 6455, version 13) | `101`, then the session below |
| `GET /ws` without an upgrade | `426` |
| a WebSocket upgrade whose `Origin` host differs from `Host` | `403` |
| any other path | `404` |

Static responses carry the headers in [security.md](security.md#response-headers) and close the connection.

## 2. Session

```
client                                   server
  │  WebSocket upgrade  ────────────────►  │
  │  ◄──────────────── "title <VI name>"   │  text
  │  ◄──────────────── "viewonly 0|1"      │  text
  │  ◄──────────────── FRAME seq 1         │  whole panel
  │  "a 1" ────────────────────────────►   │  ack after painting
  │  "m 513 120 45 1" ─────────────────►   │  input, any time
  │  ◄──────────────── FRAME seq 2 …       │  only what changed
```

There is no handshake beyond the WebSocket upgrade. A client may send input as soon as the socket is open.

## 3. Server → client

### 3.1 FRAME (binary message)

All integers are big-endian.

| Offset | Type | Field |
|---|---|---|
| 0 | u8 | magic `0x52` (`R`) |
| 1 | u8 | message type `1` = FRAME |
| 2 | u32 | `seq`, 1 for the first frame of a session, then +1 per frame |
| 6 | u16 | panel width in pixels |
| 8 | u16 | panel height in pixels |
| 10 | u16 | rect count *n* |
| 12 | *n* × rect | |

Each rect:

| Offset | Type | Field |
|---|---|---|
| 0 | i16 | x of the top-left corner on the panel |
| 2 | i16 | y |
| 4 | u32 | length *L* of the PNG |
| 8 | *L* bytes | a PNG image; its own header carries width and height |

The client resizes its canvas to the panel size when it changes, then draws each PNG at (x, y). The first frame of a session, and any frame after a size change, covers the whole panel.

**Which rects:** the server splits the panel into a grid of 64 × 64 tiles (edge tiles clipped), compares the capture with the one this client was last sent, and merges the dirty tiles of each tile row into one rect, spanning the first to the last dirty tile of that row. See `dirtyRects()` and `tests/vectors/rects.json`. A client must not depend on this; any set of rects is valid.

### 3.2 OVERLAY (binary message)

The LabVIEW popups that are open over the panel: ring/enum menus, right-click menus, combo-box lists, graph-palette popups. Each OVERLAY **replaces** the previous one; an empty list clears it. The server sends one whenever the popups or their pixels change, outside flow control (they are small and rare), and sends the current one to a client that connects while a popup is open.

| Offset | Type | Field |
|---|---|---|
| 0 | u8 | magic `0x52` |
| 1 | u8 | message type `2` = OVERLAY |
| 2 | u16 | popup count *n* |
| 4 | *n* × rect | same layout as FRAME rects (§3.1): x, y, length, PNG |

x and y are relative to the panel origin and **may lie outside the panel**, for example a context menu that overflows the right or bottom edge. The client draws the popups over the canvas, unclipped, and sends input on them with the same panel coordinates, which may be negative or beyond the panel size. Popups are listed bottom-most first, so later entries are drawn on top. `encodeOverlay()`, `tests/vectors/frame.json` → `overlays`.

### 3.3 Text messages

One command word, a space, and an argument. Clients ignore commands they don't know.

| Message | Meaning |
|---|---|
| `title <name>` | name of the published VI, for display |
| `viewonly 0` / `viewonly 1` | whether the server ignores this client's input |

## 4. Client → server (text messages)

ASCII, single spaces, decimal integers. Anything malformed is **ignored**, not fatal (`parseInput()`, `tests/vectors/input.json`).

| Message | Meaning |
|---|---|
| `a <seq>` | frame `seq` has been painted |
| `m <msg> <x> <y> <wParam>` | mouse message `msg` at panel pixel (x, y) |
| `k <msg> <wParam> <lParam>` | keyboard message `msg` |

`msg`, `wParam` and `lParam` are **Win32 window-message values**. The server posts them to the panel's native window as they are. Only the server translates coordinates.

### 4.1 Mouse

| `msg` | Name | Sent on |
|---|---|---|
| 512 (0x200) | `WM_MOUSEMOVE` | pointer move, at most once per animation frame |
| 513 / 514 | `WM_LBUTTONDOWN` / `UP` | left button |
| 515 | `WM_LBUTTONDBLCLK` | second press of a double click, instead of DOWN |
| 516 / 517 / 518 | `WM_RBUTTON…` | right button, likewise |
| 519 / 520 / 521 | `WM_MBUTTON…` | middle button, likewise |
| 522 (0x20A) | `WM_MOUSEWHEEL` | wheel; high word of `wParam` is the signed delta, ±120 per notch |

`wParam` carries the `MK_*` flags: `MK_LBUTTON 1`, `MK_RBUTTON 2`, `MK_SHIFT 4`, `MK_CONTROL 8`, `MK_MBUTTON 16`.

Server side (`translateInput()` in `tools/lib/input.mjs`, `tests/vectors/translate.json`): screen point = (panel origin on screen) + (x, y), where the panel origin is the top-left of `Front Panel Window:Panel Bounds`. The client-area origin comes from `ScreenToClient(hWnd)`; in the IDE the toolbar is inside the client area. `lParam = (y << 16) | (x & 0xFFFF)` of either:

* **client** coordinates: hover moves and button-downs;
* **screen** coordinates: moves and the button-up while LabVIEW *tracks* a press. LabVIEW tracks, and then holds the mouse capture, for latched buttons, sliders, text selection, graph drags and the like, and reads posted moves and the button-up as screen coordinates while it does (measured in `spikes/Spike Input Injection.vi`). A switch-when-pressed boolean does not track: its button-up must be in client coordinates, or LabVIEW loses it and behaves as if the button were still held (measured). So the server does not guess from the button state; before translating it asks Windows whether LabVIEW's UI thread holds the mouse capture (`GetGUIThreadInfo` → `hwndCapture`, `RemoteVI Mouse Captured.vi`), which it can, because the previous message has been handled by then (§4.4);
* **screen** coordinates: `WM_MOUSEWHEEL`, as Windows defines it.

**While a popup is open**, LabVIEW hit-tests clicks with the real cursor position against the popup window's real position. The server never moves the host cursor. It moves the popup windows (invisible on the host) by the offset that puts the clicked point under the real cursor, then posts the button message with the real cursor position in `lParam`. Moves and wheel are dropped, because LabVIEW updates the hover highlight only on real cursor motion. A click outside every popup is not posted: the server closes all popups (`WM_CANCELMODE`, sent). A submenu opens on the second click on its entry; entries inside a submenu cannot be chosen remotely. Frames keep coming while a popup is open (the panel is drawn with `PrintWindow`). OVERLAY positions stay the popups' logical positions (real position minus that offset).

### 4.2 Keyboard

| `msg` | Name | Sent for |
|---|---|---|
| 256 / 257 | `WM_KEYDOWN` / `WM_KEYUP` | non-character keys: Enter, Tab, Backspace, Esc, arrows, Home/End, PgUp/PgDn, Insert/Delete, F1–F12, Shift, Ctrl |
| 258 | `WM_CHAR` | printable characters (the character code), and Ctrl+A…Z as codes 1–26 |

Printable characters go as `WM_CHAR` so the result doesn't depend on the host's keyboard layout. `lParam` for key messages is repeat count 1, bit 24 for extended keys, and bits 30–31 set on key-up.

Server side, each `WM_CHAR` is posted as `WM_KEYDOWN(0xE8)`, `WM_CHAR`, `WM_KEYUP(0xE8)`. A bare posted `WM_CHAR` right after a non-character key is dropped by LabVIEW, and a key-down of the character's own key would make LabVIEW's message loop produce the character twice. VK `0xE8` produces no character.

### 4.3 Allowed messages

The server posts only the messages listed in 4.1 and 4.2 (`ALLOWED_MESSAGES`) and drops everything else. A client can never send `WM_CLOSE`, `WM_DESTROY`, `WM_COMMAND` or similar.

### 4.4 Delivery: one message at a time, modifiers in the key state

Two things a posted message does not carry, so the server supplies them (`RemoteVI Post Input.vi`, `RemoteVI Service Client.vi`):

* **Pacing.** LabVIEW drops and reorders key messages that arrive in a burst: twelve posted Backspace key-downs became one, and the character a key-down generates landed behind characters posted after it (measured). So the server posts the next message only after LabVIEW has handled the previous one: after each post it sends `WM_NULL` to the panel window twice (`SendMessageTimeoutW`, 500 ms each, `RemoteVI Wait Input Handled.vi`). A sent message is delivered the next time the thread looks into its queue, before any posted one, so the second round trip returns after the posts have been handled. Sent messages are also handled inside LabVIEW's modal loops, so this cannot deadlock. Not done while a popup is open; that path waits for the popups to change instead.
* **Modifier keys.** LabVIEW reads Shift, Ctrl and Alt of every mouse and key event with `GetKeyState`, and posted messages do not update the key state Windows keeps per thread (measured: a posted Shift-click and a posted Ctrl+A arrived without modifiers, the posted `MK_SHIFT` and `VK_SHIFT` key-down notwithstanding). The server keeps per client which modifiers the remote user holds (`trackModifiers()` in `tools/lib/input.mjs`, `RemoteVI Track Modifiers.vi`, vectors in `translate.json` → `modifiers`): a `WM_KEYDOWN`/`WM_KEYUP` of `VK_SHIFT`/`VK_CONTROL`/`VK_MENU` or their left/right variants sets/clears the bit, a mouse message carries Shift and Ctrl in `MK_SHIFT`/`MK_CONTROL`. Whenever that set changes it is written into the key state of LabVIEW's UI thread before the message is posted: `GetKeyboardState` + `SetKeyboardState`, both called **in LabVIEW's UI thread** (a thread's key state can only be read and written by that thread), bit `0x80` of the generic and the left key, the right key released (`RemoteVI Set Modifier Keys.vi`). This changes nothing outside LabVIEW's UI thread: not the physical keyboard, not `GetAsyncKeyState`, not other programs; the next real input LabVIEW receives replaces it. It is not written while a popup is open (the popup's modal loop holds the UI thread); the change is written with the first message after the popup closes. A client that disconnects with modifiers written releases them.

Popup clicks additionally wait until the popup is 350 ms old (since the server first saw it): LabVIEW ignores a click on a ring menu that arrives within about 250 ms of opening it (measured with posted messages: 200 ms ignored, 250 ms chosen).

## 5. Flow control

A client acks each frame **after painting it**. The server sends a new frame to a client only while that client has fewer than **2** unacknowledged frames. A slow client or network therefore gets fewer, fresher frames, never a backlog. Each client is diffed against what *it* was last sent, so clients of different speeds don't hold each other back.

## 6. Limits

| Limit | Value | Action |
|---|---|---|
| Client WebSocket payload | 64 KiB | close `1009` |
| Unmasked client frame, RSV bits, unknown opcode, fragmented or oversized control frame | – | close `1002` |
| Binary or fragmented client data message | – | close `1008` |
| Concurrent clients | 8 | `503` on upgrade |
