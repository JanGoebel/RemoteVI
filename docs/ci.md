# CI and releases

## Workflow

* `main` is the protected default branch. Work happens on feature branches; each feature is a pull request whose commits stay visible (merge commits, no squash).
* **CI** (`.github/workflows/ci.yml`) runs on every pull request and on `main`:
  * `reference` on `ubuntu-latest`: vector freshness, Caraya tests in sync with the vectors (`tests/caraya/build.py --check`), and `npm test` (reference server, web client, end-to-end).
  * `labview` on the self-hosted Windows runner: Caraya (`scripts/run-caraya.ps1`) and the LabVIEW integration suite (`scripts/run-lv-integration.ps1`). It runs only when the repository variable `LABVIEW_RUNNER` is `true`.
* **Release** (`.github/workflows/release.yml`): push a tag `vX.Y.Z` on `main`.

  ```
  git tag v1.2.3
  git push origin v1.2.3
  ```

  It reruns CI, builds `jgoebel_lib_remotevi-X.Y.Z.vip` from `build/RemoteVI.vipb` on the LabVIEW runner (`vipm build --version-number X.Y.Z`), zips the sources, and publishes a GitHub release with generated release notes. Without a LabVIEW runner the release carries the source archive only.

## The self-hosted LabVIEW runner

GitHub's hosted runners have no LabVIEW, and NI's LabVIEW containers are Linux-only, while RemoteVI injects input through Win32. So the LabVIEW jobs need a Windows machine with:

* LabVIEW 2025 (64-bit), with VI Server enabled (default),
* VIPM, then `vipm install` in the repository root (IG HTTP Utils, IG WebSocket Stream, IG Stream Base, Caraya, G-CLI, Caraya CLI extension, as listed in `vipm.toml`),
* Node.js 22 and Python 3.10+,
* a GitHub Actions runner registered for this repository with the labels `self-hosted, windows, labview-2025`, running **in an interactive user session** (not as a Windows service in session 0): RemoteVI captures and drives real windows, which need a desktop. Use the runner's `run.cmd` in a logged-in session, or auto-logon plus a scheduled task.

Then set the repository variable `LABVIEW_RUNNER` to `true` (Settings → Secrets and variables → Actions → Variables).

The VIPM Community Edition builds packages for public repositories, which this one is.
