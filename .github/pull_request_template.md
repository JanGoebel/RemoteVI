## What and why

<!-- What changes for the user of RemoteVI, and why. Link the issue if there is one. -->

## Changes

<!-- One line per commit or logical step. -->

## Tested

<!-- Tick what ran, and say what was not tested and why. -->

- [ ] `npm test`, `npm run vectors:check`, `python tests/caraya/build.py --check`
- [ ] `python tools/dev/lv_versions.py --expect 20.0` (every VI saved for LabVIEW 2020)
- [ ] Caraya (`scripts/run-caraya.ps1`)
- [ ] Fixture suites (`RVI_LV=1 npm run test:lv`, `RVI_LV_COMPLEX=1 node --test tests/lv/complex.test.mjs`)
- [ ] End to end: `examples/RemoteVI Demo.vi` in the browser, LabVIEW in the background
- [ ] Opened in LabVIEW 2020 (`tools/dev/Remote Exec State.vi`), when VIs, libraries or the project changed

## Notes for the review

<!-- Anything to look at closely: risky spots, open questions, follow-ups. -->
