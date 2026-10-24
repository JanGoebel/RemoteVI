# Testing

| Layer | Tool | What |
|---|---|---|
| Pure G VIs | vector-driven checks, Caraya suite planned (`tests/caraya/`) | Protocol, Dirty Rects and Translate Input against `tests/vectors/*.json` |
| Live G checks | spike VIs in `spikes/` | capture timing, PNG compression, input injection on `spikes/Injection Fixture.vi` through the production input chain |
| Server acceptance | `node tools/check-server.mjs --url http://127.0.0.1:8080 [--click x,y] [--png out.png]` | black-box checks of a running server, the LabVIEW one or the reference one: HTTP surface, first frame pixel coverage, flow control, input, robustness |
| Client and reference | `node:test` (`npm test`, Node 22+, no install) | WebSocket and HTTP parsers, end-to-end against the reference server, client file is pure ASCII and self-contained |

## Shared test vectors

`tests/vectors/` holds language-neutral JSON produced by `tools/gen-vectors.mjs`. `npm test` fails if the committed vectors drift from the generator.

| File | For VI | Contents |
|---|---|---|
| `websocket.json` | WS Encode Server Frame, WS Decode Client Frame | RFC 6455 accept keys, valid, invalid and incomplete client frames with close codes, server frames |
| `http.json` | – (IG HTTP parses requests) | request heads and expected status, used by the JS parser tests |
| `rects.json` | Dirty Rects | first capture, identical, single pixel, row merging, clipped edge tiles |
| `frame.json` | Frame Encode | complete FRAME messages |
| `input.json` | Parse Input | valid and malformed client messages |
| `translate.json` | Translate Input, Track Modifiers | client/screen coordinate rules with and without mouse capture, wheel, WM_CHAR wrapping, allow list; `modifiers`: modifier keys held after a message |

Bytes are lowercase hex. Pixels are `0x00RRGGBB` integers, row-major.

## Manual acceptance

1. Open and run `spikes/RemoteVI Demo.vi`.
2. Browse to `http://127.0.0.1:8080/`.
3. Operate every control. Type into the string, drag the slide, watch the chart update.
4. Repeat from another machine and from a phone.
5. Stop the demo. The browser shows "Disconnected" and port 8080 is freed.
