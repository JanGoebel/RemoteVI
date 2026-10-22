# RemoteVI

**Control a LabVIEW VI from a web browser: pixel-accurate, low latency, in one click.**

RemoteVI brings back what LabVIEW *Remote Panels* used to do, without the browser plug-in, the Run-Time Engine on the client, or the NI Web Server. Any browser (desktop, tablet, phone) shows the front panel exactly as LabVIEW draws it, and lets you operate it.

* **One click**: *Tools » RemoteVI » Publish Front Panel…* → pick a VI → open the URL or scan the QR code.
* **Any VI, unmodified**: everything goes through VI Server. Remote input arrives through `Value (Signaling)`, so the VI's event structures fire as if someone were at the keyboard.
* **Pixel-accurate**: the panel is streamed as lossless image tiles (QOI), so custom controls, XControls, graphs and decorations all look exactly right.
* **Low latency**: WebSocket, dirty tiles only, ack-based flow control. A slow client skips frames instead of lagging behind.
* **Pure G**: no DLLs, no NI Web Server, no VIPM dependencies. LabVIEW 2020 or newer.
* **Multi-user**: one controller with *Request control* (as in Remote Panels), everyone may control, or view only.
* **Secure defaults**: binds to localhost, needs a per-publication access token, hardened minimal HTTP surface. See [docs/security.md](docs/security.md).

## Using it in an application

```
RemoteVI Publish.vi   (VI ref = This VI, Options) ──► URL
...
RemoteVI Unpublish.vi
```

This works in the IDE and in built EXEs. Real-Time support is planned. See [docs/architecture.md § Targets](docs/architecture.md#targets).

## Status

| Part | State |
|---|---|
| Architecture, protocol v1, security model | ✅ [docs/](docs/) |
| Browser client (`web/`) | ✅ working against the reference server |
| Reference server + simulated panel (`tools/`) | ✅ executable spec for the G side |
| Shared test vectors (`tests/vectors/`) | ✅ SHA-1, Base64, WebSocket, HTTP, QOI, tiles, frames |
| JS test suite | ✅ `npm test` |
| LabVIEW project (`RemoteVI.lvproj`) | ✅ skeleton with auto-populating folders |
| G implementation (`source/`) | ⏳ Milestones 1–4 in [docs/labview-implementation.md](docs/labview-implementation.md) |
| Caraya suite (`tests/caraya/`) | ⏳ planned in [docs/testing.md](docs/testing.md) |
| VI Package | ⏳ Milestone 4 |

## Repository layout

```
RemoteVI.lvproj        LabVIEW 2020 project (source, tests, web, scripts are auto-populating folders)
source/                the toolkit: RemoteVI.lvlib and classes
web/                   browser client, plain ES modules, no build step, served by the toolkit
tests/caraya/          Caraya unit + integration tests for the G code
tests/vectors/         language-neutral test vectors shared by Caraya and JS tests
tests/js/              node:test suites (client, reference codec, end-to-end)
tools/lib/             reference implementation (QOI, tiles, HTTP, WebSocket)
tools/mock-server/     reference server with a simulated front panel
scripts/               run-caraya.ps1 (G-CLI), later: build and embed helpers
docs/                  architecture, protocol, security, implementation guide, testing
```

## Development

The browser client and the protocol can be developed without LabVIEW, using Node.js 22+ and no `npm install`:

```bash
npm run mock    # → open the printed http://127.0.0.1:8080/#token=… URL
npm test
```

The LabVIEW side uses LabVIEW 2020 SP1, [Caraya](https://www.vipm.io/package/jki_lib_caraya/) and [G-CLI](https://www.vipm.io/package/wiresmith_technology_lib_g_cli/):

```powershell
.\scripts\run-caraya.ps1 -LabVIEWVersion 2020
```

Open `RemoteVI.lvproj` in LabVIEW 2020 or newer.
