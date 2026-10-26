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
  │  ◄──────────────── "origin <x> <y>"    │  text, where the panel starts in the frame
  │  ◄──────────────── FRAME seq 1         │  whole frame
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
| 6 | u16 | frame width in pixels |
| 8 | u16 | frame height in pixels |
| 10 | u16 | rect count *n* |
| 12 | *n* × rect | |

Each rect:

| Offset | Type | Field |
|---|---|---|
| 0 | i16 | x of the top-left corner in the frame |
| 2 | i16 | y |
| 4 | u32 | length *L* of the PNG |
| 8 | *L* bytes | a PNG image; its own header carries width and height |

The client resizes its canvas to the frame size when it changes, then draws each PNG at (x, y). The first frame of a session, and any frame after a size change, covers the whole frame.

**The frame** is the published front panel window below its title bar: its client area, which in LabVIEW holds the menu bar (LabVIEW draws it itself, also a custom run-time menu bar; measured: `GetMenu` is NULL, `GetMenuBarInfo` fails), the toolbar, the panel and the panel's scrollbars, exactly as the window shows them. The panel area starts at `origin` (§3.3) inside it. A minimized window keeps its last frame until it is restored.

**Which rects:** the server splits the frame into a grid of 64 × 64 tiles (edge tiles clipped), compares the capture with the one this client was last sent, and merges the dirty tiles of each tile row into one rect, spanning the first to the last dirty tile of that row. See `dirtyRects()` and `tests/vectors/rects.json`. A client must not depend on this; any set of rects is valid.

### 3.2 OVERLAY (binary message)

The LabVIEW popups that are open over the panel: ring/enum menus, right-click menus and their submenus, combo-box lists, graph-palette popups, tip strips. Each OVERLAY **replaces** the previous one; an empty list clears it. The server sends one whenever the popups or their pixels change, outside flow control (they are small and rare), and sends the current one to a client that connects while a popup is open.

| Offset | Type | Field |
|---|---|---|
| 0 | u8 | magic `0x52` |
| 1 | u8 | message type `2` = OVERLAY |
| 2 | u16 | popup count *n* |
| 4 | *n* × rect | same layout as FRAME rects (§3.1): x, y, length, PNG |

x and y are relative to the frame origin and **may lie outside the frame**, for example a context menu that overflows the right or bottom edge. The client draws the popups over the canvas, unclipped, and sends input on them with the same frame coordinates, which may be negative or beyond the frame size. Popups are listed bottom-most first, so later entries are drawn on top. `encodeOverlay()`, `tests/vectors/frame.json` → `overlays`.

### 3.3 Text messages

One command word, a space, and an argument. Clients ignore commands they don't know.

| Message | Meaning |
|---|---|
| `title <name>` | name of the published VI, for display |
| `viewonly 0` / `viewonly 1` | whether the server ignores this client's input |
| `windows <json>` | the application's other windows (dialogs, native file dialogs, subVI panels): see §7 |
| `origin <x> <y>` | where the panel starts inside the frame. The frame shows the whole front panel window below its title bar (menu bar, toolbar, panel, scrollbars), so the panel usually starts below the menu bar and toolbar. Sent on connect (with the greeting, before the first FRAME) and whenever it changes (the server reads it every 500 ms with the window geometry: `Front Panel Window:Panel Bounds` minus the frame origin). It is information only: all coordinates of the protocol are frame coordinates. |

## 4. Client → server (text messages)

ASCII, single spaces, decimal integers. Anything malformed is **ignored**, not fatal (`parseInput()`, `tests/vectors/input.json`).

| Message | Meaning |
|---|---|
| `a <seq>` | frame `seq` has been painted |
| `m <msg> <x> <y> <wParam>` | mouse message `msg` at frame pixel (x, y) |
| `k <msg> <wParam> <lParam>` | keyboard message `msg` |
| `x <id>` | close window `id` (§7), like its title bar's close button |

`msg`, `wParam` and `lParam` are **Win32 window-message values**. The server posts them to the panel's native window as they are. Only the server translates coordinates.

### 4.1 Mouse

| `msg` | Name | Sent on |
|---|---|---|
| 512 (0x200) | `WM_MOUSEMOVE` | pointer move, at most once per animation frame |
| 513 / 514 | `WM_LBUTTONDOWN` / `UP` | left button |
| 515 | `WM_LBUTTONDBLCLK` | second press of a double click, instead of DOWN (the server posts it as DOWN, see below) |
| 516 / 517 / 518 | `WM_RBUTTON…` | right button, likewise |
| 519 / 520 / 521 | `WM_MBUTTON…` | middle button, likewise |
| 522 (0x20A) | `WM_MOUSEWHEEL` | wheel; high word of `wParam` is the signed delta, ±120 per notch |

`wParam` carries the `MK_*` flags: `MK_LBUTTON 1`, `MK_RBUTTON 2`, `MK_SHIFT 4`, `MK_CONTROL 8`, `MK_MBUTTON 16`.

Server side (`translateInput()` in `tools/lib/input.mjs`, `tests/vectors/translate.json`): screen point = (frame origin on screen) + (x, y), where the frame origin is the top-left of the window's client area (`ScreenToClient(hWnd)` of the screen point 0,0; `geo.panelX/panelY`, the name is historical). Menu bar, toolbar and scrollbars are inside the client area, so a click on any of them is an ordinary client-area click: a click on a menu bar title opens its menu (an `LVMenuWnd` popup, driven like every other menu, see below), a click on a scrollbar arrow or a drag of its thumb scrolls the panel (measured). `lParam = (y << 16) | (x & 0xFFFF)` of either:

* **client** coordinates: hover moves and button-downs;
* **screen** coordinates: moves and the button-up while LabVIEW *tracks* a press. LabVIEW tracks, and then holds the mouse capture, for latched buttons, sliders, text selection, graph drags and the like, and reads posted moves and the button-up as screen coordinates while it does (measured with the input-injection spike, see git history). A switch-when-pressed boolean does not track: its button-up must be in client coordinates, or LabVIEW loses it and behaves as if the button were still held (measured). So the server does not guess from the button state; before translating it asks Windows whether LabVIEW's UI thread holds the mouse capture (`GetGUIThreadInfo` → `hwndCapture`, `RemoteVI Mouse Captured.vi`), which it can, because the previous message has been handled by then (§4.4);
* **screen** coordinates: `WM_MOUSEWHEEL`, as Windows defines it.

**Double clicks** are posted as a second button-down: `WM_LBUTTONDBLCLK`, `WM_RBUTTONDBLCLK` and `WM_MBUTTONDBLCLK` become `WM_LBUTTONDOWN`, `WM_RBUTTONDOWN` and `WM_MBUTTONDOWN`. LabVIEW's panel window class has no `CS_DBLCLKS`, so Windows never sends it the DBLCLK messages; LabVIEW detects the double click itself from two downs, and it ignores a posted DBLCLK (measured: a listbox Double Click event fires for down-up-down-up, never for down-up-DBLCLK-up). The client keeps sending DBLCLK, so a server for a window class that does want it can post it unchanged.

**While a popup is open**, LabVIEW hit-tests clicks with the real cursor position against the popup window's real position and ignores posted coordinates. The server never moves the host cursor, and it no longer moves LabVIEW's menus either: a menu is operated with keys posted to the panel window, which holds the mouse capture while a menu is open (`VK_DOWN`/`VK_UP` move the highlight, `VK_RETURN` chooses the highlighted item or opens its submenu, `VK_RIGHT` opens a submenu, `VK_LEFT` closes one; measured). The server finds the menu under the client's point, moves the highlight onto the row under it - capturing the menu after each key and looking for the Windows highlight colour (`GetSysColor(COLOR_HIGHLIGHT)`) down its middle column - and then acts:

* `WM_MOUSEMOVE` (no longer dropped): the highlight follows the pointer, like local hover; moves are coalesced to the latest position and applied once per server loop iteration. After 400 ms on one item the server presses `VK_RIGHT`, which opens that item's submenu, as a local hover does - but only when the item shows a submenu arrow (the strip at the right end of the highlighted band holds a pixel that is not the highlight colour): in a menu of the panel's menu bar `VK_RIGHT` on an item without a submenu opens the next menu bar menu (measured). On a parent menu while a submenu is open, nothing happens on the item that opened it; on another item the submenu is closed with `VK_LEFT` once the pointer has rested there 300 ms, and the parent's highlight follows.
* Button-down: submenus above the clicked menu are closed with `VK_LEFT`, the highlight is moved onto the row and `VK_RETURN` is pressed (nothing is chosen on a separator or a disabled item). The matching button-up is not posted. A button-up on a menu is never posted, so the release of the click that opened a menu chooses nothing.
* A popup that shows no highlight and takes no keys - the plot legend's colour picker and line width popup (both `LVMenuWnd`), graph palette popups - is clicked with the mouse: only that window is moved by the offset that puts the clicked point under the real cursor, the button message is posted with the real cursor position in `lParam`, and the window is moved back right after; a button-down and its button-up are each handled that way. No probe key is posted into a window without the menu background colour (`COLOR_MENU`): a key spoils the colour picker's next click (measured).
* A click outside every popup is not posted: the server closes all popups (`WM_CANCELMODE`, sent).

Every popup therefore stays where LabVIEW put it, a submenu opens beside its parent exactly as on the host, and OVERLAY positions are the popups' real positions relative to the frame. The wheel is still dropped while a popup is open. Frames keep coming while a popup is open (the window is drawn with `PrintWindow`).

**Tip strips** (window class `LVTipStrip`) are part of the OVERLAY but are not a popup in the sense above: input stays in normal mode while one is shown, so the remote pointer's next move hides it as on the host (measured: a posted move off the control closes it). LabVIEW shows a tip strip for posted hover moves; no real cursor dwell is needed (measured).

### 4.2 Keyboard

| `msg` | Name | Sent for |
|---|---|---|
| 256 / 257 | `WM_KEYDOWN` / `WM_KEYUP` | non-character keys: Enter, Tab, Backspace, Esc, arrows, Home/End, PgUp/PgDn, Insert/Delete, F1–F12, Shift, Ctrl |
| 258 | `WM_CHAR` | printable characters (the character code), and Ctrl+A…Z as codes 1–26 |

Printable characters go as `WM_CHAR` so the result doesn't depend on the host's keyboard layout. `lParam` for key messages is repeat count 1, bit 24 for extended keys, and bits 30–31 set on key-up.

Server side, a `WM_KEYDOWN`/`WM_KEYUP` whose `lParam` has no scan code (bits 16–23 zero, as the client sends it) gets the key's set-1 scan code, as a real keyboard delivers it (`SCAN_CODES` and `keyLParamWithScan()` in `tools/lib/input.mjs`; the listed keys and Shift/Ctrl/Alt have the same scan code in every layout). Measured: with a posted Shift and a posted Right arrow both at scan code 0, LabVIEW lost the arrow; with either scan code set, Shift+Right arrived.

Server side, each `WM_CHAR` is posted as `WM_KEYDOWN(0xE8)`, `WM_CHAR`, `WM_KEYUP(0xE8)`. A bare posted `WM_CHAR` right after a non-character key is dropped by LabVIEW, and a key-down of the character's own key would make LabVIEW's message loop produce the character twice. VK `0xE8` produces no character.

### 4.3 Allowed messages

The server posts only the messages listed in 4.1 and 4.2 (`ALLOWED_MESSAGES`) and drops everything else. A client can never send `WM_CLOSE`, `WM_DESTROY`, `WM_COMMAND` or similar.

### 4.4 Delivery: one message at a time, modifiers in the key state

Two things a posted message does not carry, so the server supplies them (`RemoteVI Post Input.vi`, `RemoteVI Service Client.vi`):

* **Pacing.** LabVIEW drops and reorders key messages that arrive in a burst: twelve posted Backspace key-downs became one, and the character a key-down generates landed behind characters posted after it (measured). So the server posts the next message only after LabVIEW has handled the previous one: after each post it sends `WM_NULL` to the panel window twice (`SendMessageTimeoutW`, 500 ms each, `RemoteVI Wait Input Handled.vi`). A sent message is delivered the next time the thread looks into its queue, before any posted one, so the second round trip returns after the posts have been handled. Sent messages are also handled inside LabVIEW's modal loops, so this cannot deadlock. While a popup is open the same wait follows each key the server posts to a menu.
* **Modifier keys.** LabVIEW reads Shift, Ctrl and Alt of every mouse and key event with `GetKeyState`, and posted messages do not update the key state Windows keeps per thread (measured: a posted Shift-click and a posted Ctrl+A arrived without modifiers, the posted `MK_SHIFT` and `VK_SHIFT` key-down notwithstanding). The server keeps per client which modifiers the remote user holds (`trackModifiers()` in `tools/lib/input.mjs`, `RemoteVI Track Modifiers.vi`, vectors in `translate.json` → `modifiers`): a `WM_KEYDOWN`/`WM_KEYUP` of `VK_SHIFT`/`VK_CONTROL`/`VK_MENU` or their left/right variants sets/clears the bit, a mouse message carries Shift and Ctrl in `MK_SHIFT`/`MK_CONTROL`. Whenever that set changes it is written into the key state of LabVIEW's UI thread before the message is posted: `GetKeyboardState` + `SetKeyboardState`, both called **in LabVIEW's UI thread** (a thread's key state can only be read and written by that thread), bit `0x80` of the generic and the left key, the right key released (`RemoteVI Set Modifier Keys.vi`). This changes nothing outside LabVIEW's UI thread: not the physical keyboard, not `GetAsyncKeyState`, not other programs; the next real input LabVIEW receives replaces it. It is not written while a popup is open (the popup's modal loop holds the UI thread); the change is written with the first message after the popup closes. A client that disconnects with modifiers written releases them.

Mouse-path popup clicks (popups that take no keys) additionally wait until the popup is 350 ms old (since the server first saw it): LabVIEW ignores a click on a ring menu that arrives within about 250 ms of opening it (measured with posted messages: 200 ms ignored, 250 ms chosen). Keys to a menu need no such wait (measured: `VK_DOWN` worked 70 ms after a menu appeared).

## 5. Flow control

A client acks each frame **after painting it**. The server sends a new frame to a client only while that client has fewer than **2** unacknowledged frames. A slow client or network therefore gets fewer, fresher frames, never a backlog. Each client is diffed against what *it* was last sent, so clients of different speeds don't hold each other back.

## 6. Limits

| Limit | Value | Action |
|---|---|---|
| Client WebSocket payload | 64 KiB | close `1009` |
| Unmasked client frame, RSV bits, unknown opcode, fragmented or oversized control frame | – | close `1002` |
| Binary or fragmented client data message | – | close `1008` |
| Concurrent clients | 8 | `503` on upgrade |

## 7. Other windows: dialogs, file dialogs, subVI panels

A VI is more than its front panel. It opens LabVIEW dialogs (One/Two/Three Button Dialog, Prompt User, error dialogs), native Windows dialogs (file and folder selection, message boxes) and front panels of subVIs that open in their own window. A remote user must see and operate them, or the application gets stuck waiting for an answer nobody can give.

**Which windows.** Visible top-level windows of the LabVIEW process that belong to the published application, other than the published panel itself and popups (§3.2): windows owned by the published panel or by another listed window, every window that appears while the published panel is disabled (that is, a modal dialog is up), and native dialogs (`#32770`) of the process. IDE windows (Project Explorer, block diagrams, other VIs being edited) are not listed.

**`windows <json>`** (text message) lists them, front-most first, whenever the set, a title, a position, a size or the state changes. `windows []` means none.

```json
[{"id": 5113012, "title": "Proceed?", "x": 211, "y": 140, "w": 320, "h": 132,
  "modal": true, "active": true, "closable": true}]
```

| Field | Meaning |
|---|---|
| `id` | stable for the window's lifetime (the server uses the HWND) |
| `title` | the window's caption; a window without one is listed with its owner's caption (LabVIEW's Two Button Dialog has none and is owned by LabVIEW's hidden frame window, so it reads `LabVIEW`) |
| `x`, `y` | top-left of the window's **client area** (including its own menu bar), in main-frame coordinates; may be negative or beyond the main frame |
| `w`, `h` | client area size; the same as its WINDOW FRAME size |
| `modal` | the published panel is disabled while this window is up |
| `active` | it has the keyboard; the client draws it as the front window |
| `closable` | the window has a close box; `x <id>` is allowed |

**WINDOW FRAME** (binary message, type 3) carries a window's picture, with the same dirty-rectangle encoding as FRAME:

| Offset | Type | Field |
|---|---|---|
| 0 | u8 | magic `0x52` |
| 1 | u8 | message type `3` = WINDOW FRAME |
| 2 | u32 | window `id` |
| 6 | u32 | `seq`, shared with FRAME: the client acks it with `a <seq>` the same way |
| 10 | u16 | width |
| 12 | u16 | height |
| 14 | u16 | rect count *n* |
| 16 | *n* × rect | as in §3.1 |

The first WINDOW FRAME of a window, and any after a size change, covers it completely.

**Input.** Mouse messages stay in main-frame coordinates; a listed window occupies its `x, y, w, h` there. The server routes a mouse message to the front-most window under the point (popups first, then windows in list order, then the panel) and converts it into that window's client coordinates. A client that lets the user drag a window to another place on screen converts pointer positions back, so the server always receives host-layout coordinates. Keyboard messages go where the host's keyboard would send them: to the front-most `modal` window if one is listed, else to the window that received the last button-down, else to the panel. So Enter or Escape answer a dialog right after it opened, as they would locally. `x <id>` posts `WM_SYSCOMMAND` with `SC_CLOSE` to a listed, closable window - what its title bar's close button sends, so the window closes as it would locally (a native dialog cancels); it is never sent to the published panel. A bare `WM_CLOSE` is not used: posted to LabVIEW's Two Button Dialog it destroyed the window while the dialog function kept waiting for an answer, which hung the calling VI (measured on LabVIEW 2025).

**Client presentation** (`web/index.html`): each window is a floating box above the panel with an HTML title bar (caption, close button when `closable`) and its frame below, scaled like the panel. While a `modal` window is listed, the panel is dimmed and takes no input, as it does on the host. Title bars can be dragged to move a window out of the way on the client only; a window list in the top bar brings a window to the front. On narrow screens windows open centered and fitted to the width.
