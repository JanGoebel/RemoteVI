# Security model

RemoteVI lets a browser operate a running VI with mouse and keyboard. That is remote control of whatever the VI controls, so treat a published panel like an unlocked keyboard at the machine.

## What v1 of the G toolkit does

| Aspect | Behaviour |
|---|---|
| Listener | all interfaces on the chosen port. Use the Windows firewall, or a reverse proxy on a localhost-bound setup (below), to limit who can connect. A *bind address* option is planned. |
| Authentication | none yet. Anyone who can reach the port can view and operate the panel. A per-start access token (URL fragment, compared in constant time) is planned. |
| Cross-site WebSocket hijacking | refused: a WebSocket upgrade whose `Origin` host differs from `Host` gets `403`. So a page in the operator's browser on another site cannot drive the panel. |
| Clients | at most 8 at a time; more get `503`. |
| Input | only the window messages in protocol §4.3 (mouse buttons, moves, wheel, key down/up, characters) are posted to the panel window. `WM_CLOSE`, `WM_COMMAND`, `WM_SYSCOMMAND` and anything else are dropped, so a client cannot close or reconfigure the window. Input only reaches the published panel's own window. |
| Malformed input | ignored. Invalid WebSocket framing closes the session (`1002`/`1008`/`1009`). |

## HTTP surface

The HTTP side is deliberately tiny, so writing it on IG HTTP Utils plus our own WebSocket framing is reasonable:

* `GET /` returns one constant string (the embedded client). No file system access, so no path traversal is possible.
* `GET /ws` performs the upgrade. Everything else is `404`.
* One request per connection, and no request bodies are used.
* IG HTTP Utils parses the request head.

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
