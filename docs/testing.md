# Testing

There are three layers. All of them run in CI, and the LabVIEW layers need a self-hosted runner with LabVIEW installed.

| Layer | Tool | What | Where |
|---|---|---|---|
| G unit tests | **Caraya** (JKI) | every pure VI from Milestone 1, checked against `tests/vectors/*.json` | `tests/caraya/unit/` |
| G integration tests | Caraya | publish `tests/caraya/fixtures/Fixture Panel.vi`, connect with a G WebSocket client, assert frames, layout, `set`, roles, limits | `tests/caraya/integration/` |
| Client and reference tests | `node:test` (no npm dependencies) | browser client modules, the reference codec, HTTP and WebSocket parsers, end-to-end against the reference server | `tests/js/` |

## Shared test vectors

`tests/vectors/` holds language-neutral JSON produced by `tools/gen-vectors.mjs`:

| File | Contents | Oracle |
|---|---|---|
| `sha1.json` | inputs straddling the padding boundaries, plus the RFC 6455 handshake input | `node:crypto` |
| `base64.json` | the RFC 4648 §10 examples and binary edge cases | `node:buffer` |
| `websocket.json` | accept keys, valid, invalid and incomplete client frames with the expected close codes, server frames | RFC 6455 §1.3 and §5.7 examples |
| `http.json` | request heads with the expected path or error status | hand-written |
| `qoi.json` | images that exercise every QOI op (RUN > 62, INDEX, DIFF wrap-around, LUMA, RGB) | reference encoder, round-trip tested |
| `tiles.json` | clipped grid, diff with changes in clipped edge tiles, SOLID/QOI/RAW selection | reference implementation |
| `frame.json` | a complete FRAME message with all three encodings | reference implementation |

Bytes are lowercase hex. Pixels are `0x00RRGGBB` integers. `npm test` fails if the committed vectors drift from the generator.

## Caraya conventions

```
tests/caraya/
├── _support/
│   ├── Load Vector.vi        name ("qoi.json") → JSON string (path relative to this VI)
│   ├── Hex To Bytes.vi       hex string → U8[]
│   └── Bytes To Hex.vi       U8[] → hex string
├── unit/
│   ├── Transport/  Test SHA1.vi, Test Base64.vi, Test WS Accept Key.vi,
│   │               Test WS Decode Client Frame.vi, Test WS Decode Incomplete.vi,
│   │               Test WS Encode Server Frame.vi, Test HTTP Parse Request Head.vi,
│   │               Test HTTP Find Head End.vi, Test HTTP Build Response Head.vi
│   ├── Capture/    Test QOI Encode.vi, Test Tile Grid.vi, Test Tile Diff.vi,
│   │               Test Encode Tile.vi, Test Frame Encode.vi
│   └── Panel/      Test Classify Control.vi, Test Build Layout.vi (against the fixture)
├── integration/    Test Publish And Connect.vi, Test Keyframe Pixel Exact.vi,
│                   Test Flow Control.vi, Test Set Value.vi, Test Roles.vi,
│                   Test Token Rejected.vi, Test HTTP Limits.vi
└── fixtures/       Fixture Panel.vi (one control of every supported kind), G WS Client.lvclass
```

* **One test VI per unit under test.** A test VI loops over all cases in its vector file and calls Caraya `Assert Equal` (or `Assert True`) with the case `name` as the message, so a failure pinpoints the vector.
* **Vector parsing**: `Unflatten From JSON` into a typed cluster that mirrors the JSON. Unknown keys are ignored, so a vector file can grow without breaking older tests.
* **Data-driven, no hard-coded bytes in G.** New cases are added in `tools/gen-vectors.mjs`, which updates both test suites at once.
* **Integration tests** bind to `127.0.0.1` on port 0 (an ephemeral port, read back from `Server`), so they can run in parallel.
* The pixel-exact test publishes the fixture with every value fixed. It reconstructs the image from the keyframe with a G QOI *decoder* (test support only) and compares it with `Panel.Get Image`.

## Running

```powershell
# Caraya, headless, JUnit output for CI (check the flags against your installed Caraya CLI version)
g-cli --lv-ver 2020 caraya -- -s "tests\caraya" -x "reports\caraya.xml"

# or use the wrapper
.\scripts\run-caraya.ps1 -LabVIEWVersion 2020
```

```bash
npm test                 # client, reference codec, end-to-end (Node 22+, no install needed)
npm run vectors          # regenerate tests/vectors after changing the generator
npm run mock             # reference server with a simulated panel on http://127.0.0.1:8080
```

In the IDE you can also open Caraya's interactive runner on `tests/caraya`.
