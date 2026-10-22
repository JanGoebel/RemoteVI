# RemoteVI protocol, version 1

This is the normative spec. The reference implementation lives in `web/js/protocol.js` and `tools/lib/*`. Test vectors are in `tests/vectors/`.

## 1. HTTP endpoints

| Path | Purpose |
|---|---|
| `GET /` | `index.html` of the browser client |
| `GET /js/*`, `GET /css/*` | client assets, served from a fixed in-memory table |
| `GET /ws` | WebSocket upgrade (RFC 6455, version 13) |

Every other path returns `404`, every other method `405`, and every response but `101` carries `Connection: close`. Limits are in [security.md](security.md).

## 2. Session lifecycle

```
client                                     server
  │  WebSocket upgrade  ──────────────────►  │  Origin must match Host (if present)
  │  {"t":"hello","v":1,"client":…,"token":…}►│  must arrive within 3 s
  │  ◄──────────────── {"t":"welcome",…}    │
  │  ◄──────────────── {"t":"layout",…}     │
  │  ◄──────────────── FRAME (keyframe)     │
  │  {"t":"ack","seq":1} ─────────────────►  │
  │  ◄──────────────── FRAME (delta) …      │
```

The access token travels in the `hello` message, not the URL. The browser reads it from the page URL's fragment (`http://host:port/#token=…`), and fragments are never sent to servers or proxies.

Close codes, beyond the RFC 6455 ones:

| Code | Meaning | Client behaviour |
|---|---|---|
| 4400 | unsupported protocol version | stop, show error |
| 4401 | no/invalid `hello` (timeout, wrong first message) | stop, show error |
| 4403 | wrong token | stop, show error |
| 1001 | server shutting down or VI unpublished | reconnect with backoff |

## 3. Binary messages (server → client)

All integers are **big-endian**, which is LabVIEW's native `Flatten To String` order.

### FRAME (type `0x10`)

| Offset | Size | Field |
|---|---|---|
| 0 | u8 | type = `0x10` |
| 1 | u8 | flags: bit 0 = keyframe (all tiles present; panel size may have changed) |
| 2 | u32 | seq: starts at 1 per session, +1 per frame |
| 6 | u16 | panel width (px) |
| 8 | u16 | panel height (px) |
| 10 | u16 | tile count N |
| 12 | … | N tiles |

Tile:

| Offset | Size | Field |
|---|---|---|
| 0 | u16 | x |
| 2 | u16 | y |
| 4 | u16 | w |
| 6 | u16 | h |
| 8 | u8 | encoding |
| 9 | u32 | payload length L |
| 13 | L | payload |

Encodings:

| Value | Name | Payload |
|---|---|---|
| `0x00` | SOLID | 4 bytes `00 RR GG BB` (exactly a LabVIEW `U32` colour) |
| `0x01` | QOI | a complete QOI image (header + chunks + end marker), 3 channels, size w×h |
| `0x02` | RAW_RGB | w×h×3 bytes, row-major `RR GG BB` |

Rules:

* Tiles never overlap within a frame and must lie inside the panel.
* A change of panel size is only allowed on a keyframe.
* The server's tile grid is an implementation detail. Clients must accept tiles of any size.

## 4. JSON messages

Every text message is a JSON object with a string field `t`. Unknown `t` values and unknown fields are ignored, which keeps the protocol forward compatible.

### Server → client

| `t` | Fields | Notes |
|---|---|---|
| `welcome` | `v`, `session`, `vi` (VI name), `panel {w,h}`, `mode` (`single`/`everyone`/`view`), `role` (`controller`/`viewer`) | first message after a valid `hello` |
| `layout` | `controls[]` (see below) | sent after `welcome` and whenever the layout changes |
| `value` | `id`, `value` | current value of an overlay-editable control, so overlays open pre-filled |
| `role` | `role`, `owner` (display name or `null`) | ownership changed |
| `pong` | `ts` | echo of `ping.ts` |
| `error` | `code`, `message` | non-fatal. Codes: `not-controller`, `rejected`, `unknown-control` |

Control entry (`layout.controls[]`, ordered back-to-front):

```json
{ "id": "c2", "label": "Setpoint", "kind": "numeric",
  "bounds": [24, 104, 120, 22], "edit": [24, 104, 104, 22],
  "readonly": false, "visible": true, "disabled": false,
  "min": -10, "max": 10, "items": [], "mech": "", "multiline": false, "value": 2.5 }
```

* `bounds` and `edit` are `[x, y, w, h]` in panel pixels.
* `kind` is one of `boolean`, `numeric`, `string`, `path`, `enum`, `ring`, `slider`, `chart`, `graph`, `cluster`, `array`, `other`.
* `mech` is set for booleans: `switch-when-pressed`, `switch-when-released`, `switch-until-released`, `latch-when-pressed`, `latch-when-released`, `latch-until-released`.
* `id` stays stable for the lifetime of a publication. LabVIEW uses the control's VI Server reference number, formatted as a string.
* With `Flatten To JSON`, all fields are always present. Clients treat empty or zero values as "not applicable".

### Client → server

| `t` | Fields | Requires controller |
|---|---|---|
| `hello` | `v`, `client`, `token` | – |
| `ack` | `seq` | – |
| `ping` | `ts` (opaque number) | – |
| `refresh` | – (request a keyframe) | – |
| `control` | `action`: `request` / `release` | – |
| `mouse` | `e`: `down`/`up`/`move`/`wheel`; `x`, `y` (panel px); `b` (button for down/up, button mask for move); `dy` (wheel: ±1); `mods` | yes |
| `key` | `e`: `down`/`up`; `key`, `code` (DOM `KeyboardEvent` values); `mods` | yes |
| `set` | `id`, `value` (JSON number, string or integer index) | yes |

`mods` is a bitmask: 1 = Shift, 2 = Ctrl, 4 = Alt, 8 = Meta.

If a viewer sends one of the "requires controller" messages, the server answers with `error`/`not-controller` and ignores it.

## 5. Input model

1. The client hit-tests a pointer press against `layout.controls`, topmost visible first.
2. If the hit control is overlay-editable (`numeric`, `string`, `path`, `enum`, `ring`, not read-only or disabled), the client opens a local editor at `edit` (or `bounds`) and sends only `set` when the edit is committed.
3. Otherwise it forwards raw `mouse` events. The server hit-tests again, and the control's adapter interprets the gesture (boolean mechanical action, slider drag, wheel increments).
4. `key` events go to the server only while no overlay is open.

## 6. Flow control

The client sends `ack` with a frame's `seq` *after* painting it. The server sends a new frame to a session only while `seq − lastAck < FramesInFlight` (default 2), and only if that session's socket backlog is under 1 MiB. Diffing is done against the last frame *sent to that session*, so skipped captures never lose changes.

## 7. Versioning

`hello.v` / `welcome.v` carry the protocol version. A server closes with 4400 if it can't speak the requested version. New optional fields and new message types don't change the version. Changes to the binary layout or the meaning of existing fields do.
