# RemoteVI

**Operate a LabVIEW front panel from any web browser: pixel-accurate, written in G, no NI Web Server.**

RemoteVI replaces LabVIEW *Remote Panels*. The browser shows the panel exactly as LabVIEW draws it, including subpanels, splitters, tabs, graphs, XControls and custom controls. Mouse and keyboard input goes back to LabVIEW as native window messages, so the VI behaves as if someone were at the machine: event structures fire, and latched buttons latch.

## Quick start: three ways

Every share gets a link with a random access token, `http://127.0.0.1:<port>/?t=<token>`. It works on this computer only unless you choose *whole network* for that share; then the link names the computer's IP address. Give the link only to who should operate the panel ([docs/security.md](docs/security.md)).

**1. Built into your application** (palette RemoteVI, or `source/API`):

```
RemoteVI Start.vi   (VI: unwired = this VI, port = 8088, whole network? = F, token = random, view only? = F)  ──►  URL
... your application ...
RemoteVI Stop.vi    (port)
```

The share also stops by itself when the VI stops. Several shares can run side by side, one per port. `RemoteVI Start Window.vi` shares a window of any process by its handle instead. `RemoteVI Status.vi` tells what is shared, with the links, clients, frame and data rate; `RemoteVI Show Status.vi` opens a status window, and `RemoteVI Status Panel.vi` fits into a subpanel of your UI. Try `examples/RemoteVI Demo.vi` (port 8088; its URL indicator shows the link). It works the same in a built application (build specification `RemoteVI Demo` in `RemoteVI.lvproj`).

**2. From the Tools menu**, no code: **Tools » RemoteVI » Share in Browser** (installed by the VI package into `<LabVIEW>\project\RemoteVI`; from the repository, run `tools-menu/RemoteVI/Share in Browser.vi` or `source/App/RemoteVI Server.vi`). Pick a window on the left - LabVIEW's own first, then LabVIEW-built applications, then other programs - choose port, *Whole network* and *View only*, press **Share selected window**. On the right the shares with their clients, live; select one for Stop sharing, Copy link or Open in browser. Closing the window keeps the shares running; open it again to stop them.

**3. RemoteVI Server.exe**, a standalone application (build specification `RemoteVI Server`, LabVIEW 2025 run-time engine): the same window, plus a landing page that links every share (default port 8088, the next free port when that one is in use; its link with its own token is shown at the bottom). Closing the window stops every share. Command line (after `--`):

```
"RemoteVI Server.exe" -- --share "My Panel.vi" --port 8100 --token secret --whole-network --view-only --landing-port 8088
```

`--share` shares the window with that title at start; `--landing-port 0` runs no landing page.

> Ports: 8088 for the demo and the landing page, 8100 and up for RemoteVI Server's shares. Not 8080: on many NI machines port 8080 is taken by NI's Application Web Server.

## In the browser

* **Scaling:** `1:1` (actual pixels), `Fit` (whole window in view), `Width` (fit the width, scroll vertically), zoom `−` / `+` or Ctrl+wheel. The choice is remembered per browser. Keys when the panel doesn't have focus: `1`, `F`, `W`, `+`, `−`.
* **Fullscreen** button.
* **Touch:** one finger is the mouse (tap = click, slide = drag), a long press is a right-click, two fingers pinch-zoom and pan. The keyboard button opens the on-screen keyboard. Phones start in `Width` mode.

## How it works

* **Out:** the whole front panel window below its title bar - menu bar (also a custom run-time menu), toolbar, panel, scrollbars - copied from the window's composited surface (`GetDC` + `BitBlt`, also while it is covered) → diff in 64 px tiles → changed bands as PNG (NI's `LV Image to PNG Data.vi`, zlib level 1) → WebSocket → canvas.
* **In:** the browser sends Win32 messages (`WM_LBUTTONDOWN`, `WM_MOUSEMOVE`, `WM_CHAR`, …) with coordinates in that window picture. The server maps them to the panel's window and calls `PostMessageW`; menu bar, toolbar and scrollbars are operated like the panel.
* **HTTP:** IG HTTP Utils / IG WebSocket Stream handle the request and the upgrade. The client is one embedded HTML file.

Details: [docs/architecture.md](docs/architecture.md), [docs/protocol.md](docs/protocol.md), [docs/security.md](docs/security.md).

## Status

| Part | State |
|---|---|
| Capture, diff, PNG (`source/Capture`) | ✅ vectors and benchmarks |
| Protocol, WebSocket framing (`source/Protocol`) | ✅ all vectors pass |
| Input (`source/Input`, `source/Win32`) | ✅ clicks, drags, double clicks, wheel, typing, Shift/Ctrl/Alt, hover enter/leave; host cursor and keyboard never touched |
| Whole window: menu bar (also custom run-time menus with submenus), toolbar, scrollbars | ✅ streamed as the window shows them; menu bar menus driven like the other menus, scrollbar arrows and thumbs scroll the panel; the client learns where the panel starts (`origin`) |
| Popups: ring/enum menus, right-click menus with submenus, graph palette; tip strips as text | ✅ streamed as an overlay at their real place (may extend past the panel), hover highlight, submenus beside their parent, invisible on the host when opened remotely, panel keeps updating underneath |
| Other windows: LabVIEW dialogs, native file dialogs, subVI panels and floating windows opened by the application | ✅ listed (`windows` message: caption, place, modal, active, closable) and streamed as WINDOW FRAMEs, shown as floating windows in the browser; clicks go to the window under the pointer, keys to the modal window, Enter/Escape answer dialogs as locally, the panel behind a modal dialog takes no input, close box closes; tracked with Win32 calls only, so nothing blocks while a dialog holds LabVIEW's UI thread |
| Several shares per LabVIEW, window targets (`Start Window.vi`) | ✅ reentrant Server Loop clones, one per port; a window of another LabVIEW, a built application or any program is shared through Win32 only (see Known limits) |
| Access token, bind address, view only | ✅ random token per share in the link (`?t=`), `403` without it; this computer only unless *whole network*; view only ignores input |
| Status API (`Status.vi`, `Status Panel.vi`, `Show Status.vi`) | ✅ per share: link, target, reach, clients (address, connected, idle), fps, kB/s, frames, input-to-frame latency, last error |
| RemoteVI Server (`source/App`), Tools menu entry, RemoteVI Server.exe | ✅ window list grouped LabVIEW first, share/stop/copy/open, landing page, command line; tested in LabVIEW and as the built application |
| Server loop, Start/Stop (`source/Server`, `source/API`) | ✅ frames copied from the window's composited surface (2-5 ms), every 16 ms right after a click or key; click-to-photon about 60 ms on the demo with LabVIEW in the background (`tools/perf.mjs`); idle connections don't stall it; Start reports errors |
| Browser client (`web/index.html`) | ✅ |
| Tests | ✅ `npm test` (22), LabVIEW integration suites `tests/lv`: the fixture (24 of 24), a complex application UI (20 of 20, 1 skipped; see Known limits), two shares at once (3 of 3); the same suites against the fixtures built as executables and shared as windows from another process (20 of 24, 15 of 20: the differences are listed in docs/testing.md); LabVIEW in the background |
| Caraya unit tests | ✅ 161 assertions over 20 suites pass (`tests/caraya/RemoteVI Caraya Runner.vi`, JUnit report); Caraya installed for LabVIEW 2025 |
| Complex panels: splitter panes, tab pages, clusters, subpanels (also swapped at run time), tree, table, slide, knob, graph cursors, path browse dialog, scrolling panes, floating windows | ✅ operated like locally (`tests/lv/complex.test.mjs`); tip strips of controls on tab pages, in clusters and in subpanel VIs |
| Splitter dragging | ✅ the browser drags the bar itself and the server sets the splitter position through VI Server (`splitters` message, `s <id> <pos>`) |
| Library `source/RemoteVI.lvlib` | ✅ every VI under `source/`, virtual folders mirror the disk, all members public (entry points: `API/`) |
| Palette, VI package (`build/RemoteVI.vipb`) | ✅ palette RemoteVI with the API VIs; Tools menu entry; the package itself was not built in this environment |

## Known limits

* **Menus are driven with keys.** The highlight follows the remote pointer and a submenu opens after 400 ms on its entry, but through arrow keys posted to LabVIEW, so a menu that takes no keys (colour picker, line width popup) shows no hover highlight remotely; it is clicked by moving just that window under the host cursor for the click. While such a popup is open its parent menus react to clicks only by closing.
* **Tip strips are shown by the browser.** LabVIEW shows tip strips only while it is the foreground application, so the server sends the texts and bounds of the panel's top-level controls (`tips` message) and the browser shows them after a 500 ms hover. Covered are the controls of every pane, of the selected tab page, cluster elements (two levels deep) and the controls of a VI shown in a subpanel; deeper nesting (a cluster in a cluster on a tab page) and arrays' elements are not. A LabVIEW tip strip the remote pointer raises while LabVIEW is in front still shows on the host for a moment before it is hidden.
* **Ctrl+letter.** Ctrl+A sent as a character reaches LabVIEW, but the letter produces no Key Down event of its own.
* **One share per port.** A port this LabVIEW shares already returns error 5001, a port another program uses the listener's error (60). The shares of one LabVIEW take turns in their shared subVIs, and only one splitter move waits at a time.
* **Window targets (another process) work through Win32 only.** No tip strips, no splitter dragging, no panel origin, and a non-modal panel the other application opens (FP.Open) is listed only when the shared window owns it or is disabled. Shift, Ctrl and Alt reach another process only in the mouse messages' flags, which LabVIEW ignores: a Shift-click or Ctrl+key arrives without the modifier. Attaching to the other process's input queue (`AttachThreadInput`) would carry them, but could not be shown to leave the host's keyboard state alone, so it is not done.
* **The token is in the URL.** It can end up in browser history and, over plain HTTP, on the network; use a TLS reverse proxy beyond a trusted network (docs/security.md).
* **RemoteVI Server's look.** AIXML cannot draw a panel, so the window is laid out at run time from the generic controls the composer has (round push buttons). Window titles with characters outside the system code page show `?`.
* **Modifiers are shared.** Several clients holding Shift/Ctrl at the same time share LabVIEW's single key state.
* **Other windows are found by ownership and timing.** Listed are native dialogs, windows owned by the panel or a listed window, and every window that appears while the panel is disabled (a modal dialog is up). A window that appears while the panel stays enabled and is owned by no listed window (LabVIEW makes a subVI panel opened with FP.Open an `LVDChild` owned by its hidden frame window, like every IDE window) is listed when it is the open front panel of a running VI (VI Server: `Execution:State`, `OS Window`) - an application's floating window yes, Project Explorer, block diagrams and panels of VIs being edited no. A panel opened while a modal window is up is checked after it closes. A window without a caption (LabVIEW's Two Button Dialog) shows its owner's caption, `LabVIEW`. Mouse input to a native dialog goes to the child control under the pointer in its client coordinates; the mouse wheel there is not exact.
* **Splitter bars are dragged by the browser.** LabVIEW moves a splitter bar only while it tracks the real mouse, and the host cursor is never moved, so the browser shows a line while a bar is dragged and the server sets the splitter's Position when it is dropped (no live resizing while dragging; not while a popup or a modal window is open - then the move waits).
* **.NET and ActiveX containers are untested.** Their content is a child window inside the panel window. Input is followed down to the child window under the pointer (`ChildWindowFromPointEx`) only in listed windows such as native dialogs; on the panel it goes to the panel window, and whether LabVIEW passes it on to the container is unmeasured: no fixture has one, as LabVIEW 2025 ships no VI with such a container that could be copied into a fixture and the composer cannot make one.
* **Combo boxes are untested** in the complex fixture for the same reason (the composer's slide and knob parts made LabVIEW crash on load, so the fixture's controls come from NI VIs, none of them a combo box). Ring and enum menus, which work the same way (a popup window), are tested.
* **Remotely opened menus flash on the host for about 70-120 ms.** LabVIEW fades a new menu in, which undoes the hiding until the next listing (docs/architecture.md, Popups). An empty window region hides it completely, but then LabVIEW no longer drives the menu with keys, which remote menus need, so it is not used.
* **Windows only** (input injection is Win32).

## Testing

```bash
npm test                                         # JS reference, vectors, end-to-end against the reference server
RVI_LV=1 RVI_URL='<link>' npm run test:lv        # LabVIEW integration suite; run tests/fixtures/RemoteVI Fixture.vi first (port 8089)
RVI_LV_COMPLEX=1 RVI_URL='<link>' node --test tests/lv/complex.test.mjs   # complex UI suite (RemoteVI Complex Fixture.vi, port 8089)
node tools/check-server.mjs --url '<link>' --click 50,228   # black-box check of a running server
```

`<link>` is the share's link with its token (RemoteVI Status.vi lists them).

Details: [docs/testing.md](docs/testing.md).

## Development

```bash
npm run mock                               # reference server with a simulated panel on http://127.0.0.1:8090/ (no LabVIEW needed)
```

The G code was generated with labview-mcp on LabVIEW 2025. The AIXML sources are in `tools/aixml/`; `python scripts/gen-lvproj.py` regenerates `RemoteVI.lvproj` (virtual folders, build specifications for RemoteVI Server.exe, the demo and the fixtures; build output goes to `builds/`, which is not committed). `scripts/Build Win32 Wrappers.vi` regenerates the Call Library wrappers, and `scripts/gen-index-html-vi.mjs` regenerates the embedded client.
