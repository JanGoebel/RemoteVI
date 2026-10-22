# tests/caraya/

The Caraya unit and integration tests for the G code. The structure and conventions are in [docs/testing.md](../../docs/testing.md#caraya-conventions).

Every unit test is data-driven from `../vectors/*.json`. Those are the same vectors the JS tests use, so the G and JS implementations can't drift apart.
