# Security model

RemoteVI lets a browser operate a running VI with mouse and keyboard. That is remote control of whatever the VI controls, so treat a published panel like an unlocked keyboard at the machine.

## What the G toolkit does

| Aspect | Behaviour |
|---|---|
| Listener | **this computer only by default**: a share listens on `127.0.0.1`. `whole network? = TRUE` (RemoteVI Start.vi, Start Window.vi; the *Whole network* button of RemoteVI Server; `--whole-network`) listens on every interface, and the link then names this computer's IP address. Choose it per share, and keep the Windows firewall in front of it. |
| Authentication | a random **access token per share** (32 hex digits from `BCryptGenRandom`, or one the caller passes). Every request needs it as `?t=<token>` - the page, the WebSocket upgrade and the landing page; without it, or with a wrong one, the answer is `403`. It is compared in constant time. The link with the token is the key: give it only to who should operate the panel, and stop the share (or start it again for a new token) to revoke it. The token travels in the URL, so it can end up in a browser's history and, over plain HTTP, be read on the network (below). |
| View only | `view only? = TRUE` shows the panel and ignores every input of the browsers (the client is told with `viewonly 1`). |
| Landing page | RemoteVI Server.exe lists its running shares, with their links, on a page of its own (default port 8088, the next free port when that one is in use; `--landing-port`, 0 = none). It has its own token and binds like the shares (this computer only unless `--whole-network`). In LabVIEW (Tools menu) no landing page runs. |
| What can be shared | RemoteVI Start.vi shares a VI's panel. RemoteVI Start Window.vi and RemoteVI Server share any window of any program of the logged-in user - also a browser or a mail program. Share only what the people with the link may see and operate. |
| Host input | the host's cursor and keyboard are never moved or pressed: input is posted to the shared window as window messages (no `SendInput`, `SetCursorPos`, `keybd_event`, `mouse_event`). Shift, Ctrl and Alt held in the browser are set in LabVIEW's own key state (`SetKeyboardState` in LabVIEW's UI thread, put back after the message) - for a panel in the same LabVIEW, and for a LabVIEW-built application reached over VI Server, where the same VI runs inside that application (below). Any other process gets them only in the mouse messages' flags; RemoteVI does not attach to another process's input queue (`AttachThreadInput`). |
| Cross-site WebSocket hijacking | refused: a WebSocket upgrade whose `Origin` host differs from `Host` gets `403`. So a page in the operator's browser on another site cannot drive the panel. |
| Clients | at most 8 at a time; more get `503`. |
| Input | only the window messages in protocol §4.3 (mouse buttons, moves, wheel, key down/up, characters) are posted to the panel window. `WM_CLOSE`, `WM_COMMAND`, `WM_SYSCOMMAND` and anything else are dropped, so a client cannot close or reconfigure the window. Input only reaches the published panel's own window. |
| Malformed input | ignored. Invalid WebSocket framing closes the session (`1002`/`1008`/`1009`). |

## VI Server for full features with a built application

A window of another LabVIEW process is shared with full features (Shift, Ctrl and Alt, tip strips, splitter bars) when that application runs VI Server: RemoteVI then opens an application reference to it and runs `RemoteVI Remote Hooks.vi` inside it (docs/architecture.md, Window targets). To enable it, the application's INI file (`<application>.ini` next to the executable, in the section named like the executable) needs:

```
server.tcp.enabled=True
server.tcp.port=3363
```

and the machine access list should allow this computer only: in the project, **My Computer » Properties » VI Server » Machine Access**, entry `127.0.0.1` allowed, and remove `*`; the build specification writes it into the INI file as `server.tcp.acl` (an encoded list - LabVIEW 2025 no longer reads `server.tcp.access`). Also keep **Exported VIs** at its default or allow `*`, and `server.vi.callsEnabled`/`server.vi.propertiesEnabled` on (the defaults of a build).

What this exposes: VI Server is remote control of the whole application instance - whoever can connect to its port can open, run, abort and change any VI of the application, read and write front panel values, and load VIs from disk into it (that is how RemoteVI loads its hooks). LabVIEW's VI Server has no authentication beyond the machine access list, and it listens on **every** interface (measured: `0.0.0.0:<port>`), not only on 127.0.0.1. So: restrict the machine access list to 127.0.0.1, block the port in the Windows firewall for other computers, and enable VI Server only in applications you intend to share this way. RemoteVI itself only ever connects to 127.0.0.1 unless given another `host:port`. Without VI Server the share still works, window only.

## HTTP surface

The HTTP side is deliberately tiny, so writing it on IG HTTP Utils plus our own WebSocket framing is reasonable:

* `GET /` returns one constant string (the embedded client). No file system access, so no path traversal is possible.
* `GET /ws` performs the upgrade. Everything else is `404`.
* One request per connection, and no request bodies are used.
* IG HTTP Utils parses the request head. The head is read without blocking the server loop (zero-timeout reads, one per loop iteration); a head over 16 KiB is closed unanswered, and a connection that has not sent a complete head within 5 s is closed. So idle connections, such as a browser's speculative preconnects, cannot stall the server.

## Response headers

`GET /` sends:

```
Content-Security-Policy: default-src 'none'; connect-src 'self'; img-src blob:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; frame-ancestors 'none'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: no-referrer
Cache-Control: no-store
```

Inline script and style are allowed because the client is a single self-contained file. `img-src blob:` lets the client show popups, which arrive as PNG blobs. Nothing can be loaded from elsewhere, the page can only connect back to its own origin, and it cannot be framed (no clickjacking).

## Encryption and exposure beyond a lab network

Plain `ws://` is fine on a trusted network. For anything else, put RemoteVI behind a TLS-terminating, authenticating reverse proxy (Caddy, nginx, IIS) and firewall the RemoteVI port itself. The client switches to `wss://` automatically when the page is served over HTTPS.
