# tests/caraya/

The Caraya unit and integration tests for the G code. The structure and conventions are in [docs/testing.md](../../docs/testing.md#caraya-unit-tests).

Every unit test is generated from `../vectors/*.json` by `build.py`; rerun it after a vector changes. Those are the same vectors the JS tests use, so the G and JS implementations can't drift apart.
