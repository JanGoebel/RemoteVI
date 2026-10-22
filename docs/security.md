# Security model

RemoteVI lets a browser operate a running VI. That is remote control of equipment, so the defaults are conservative and every limit is tested.

## Defaults

| Setting | Default | Rationale |
|---|---|---|
| Bind address | `127.0.0.1` | Nothing is reachable from the network until you opt in. The Tools dialog has a "Allow access from other computers" checkbox that sets `0.0.0.0`. |
| Access token | random 72 bit, generated per publication | Required in `hello`. Compared in constant time. Shown in the URL fragment and QR code only. |
| Mode | `single` | One controller at a time, the same as Remote Panels. |
| Control allowlist | all controls | `Options.Controls` can mark controls hidden (they are masked in the image) or view-only. |

## Why our own HTTP/WebSocket server is reasonable

The server isn't a general-purpose web server. Its whole attack surface:

* **Static files** come from a fixed, in-memory table built at publish time (or embedded at build time). The request path is used *only* as a lookup key and is never joined into a filesystem path, so path traversal can't happen (it's tested with `/../` and `%2e%2e`).
* **No request bodies**: only `GET`, so there's no body parsing, no chunked encoding and no multipart. `Content-Length` is ignored.
* **No keep-alive**: every non-upgrade response closes the connection, so there's no pipelining or request-smuggling state machine.
* **One WebSocket endpoint**, which accepts small JSON text messages only.

The underlying problems (HTTP framing and RFC 6455 framing) are small, well specified and covered by test vectors.

## Enforced limits

| Limit | Value | Response |
|---|---|---|
| Request head size | 8 KiB | `431` |
| Header count | 32 | `431` |
| Request-target length | 1024 bytes | `414` |
| Time to complete the request head | 5 s | `408` (slowloris protection) |
| Time from upgrade to valid `hello` | 3 s | close `4401` |
| Concurrent connections | 16 (configurable) | `503` |
| Client WebSocket payload | 64 KiB | close `1009` |
| Unmasked client frame, RSV bits, unknown opcode, fragmented or oversized control frame | – | close `1002` |
| Fragmented or binary client data messages | – | close `1008` |
| Malformed JSON / missing `t` | – | close `1008` |
| Cross-origin WebSocket (`Origin` host ≠ `Host`) | – | `403` (stops cross-site WebSocket hijacking from a page the operator happens to visit) |

Duplicate headers, header names that aren't valid tokens, absolute-form targets, and HTTP versions other than 1.0/1.1 are rejected with `400`/`505`.

## Response headers

Static responses send `Content-Security-Policy: default-src 'self'; …; frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` and `Cache-Control: no-store`.

## Input validation

* `set` values are coerced with `Unflatten From JSON` into the control's *own* data type, and an error rejects the message. Numerics are then clamped to the control's data range when *Respond to value outside limits* is set to *Coerce*.
* Indicators, disabled controls and controls outside the allowlist reject all input.
* Input from viewers is ignored.

## Encryption

* **LAN and lab use**: plain `ws://` on a trusted network, protected by the token.
* **Anything else**: put RemoteVI behind a TLS reverse proxy (Caddy, nginx, IIS) and keep RemoteVI bound to `127.0.0.1`. The client switches to `wss://` automatically when the page is served over HTTPS.
* **Planned**: a `TlsWebSocketTransport` built on LabVIEW's native TLS functions (2020+) for direct HTTPS without a proxy.

## Not in scope

User accounts, per-user permissions and audit logs. If you need those, put an authenticating reverse proxy in front.
