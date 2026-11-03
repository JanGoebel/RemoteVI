# CI and releases

## Workflow

* `main` is the protected default branch. Work happens on feature branches; each feature is a pull request whose commits stay visible (merge commits, no squash).
* **CI** (`.github/workflows/ci.yml`) runs on every pull request and on `main`:
  * `reference` on `ubuntu-latest`: vector freshness, Caraya tests in sync with the vectors (`tests/caraya/build.py --check`), and `npm test` (reference server, web client, end-to-end).
  * `labview` on the self-hosted Windows runner: Caraya (`scripts/run-caraya.ps1`) and the LabVIEW integration suite (`scripts/run-lv-integration.ps1`). It runs only when the repository variable `LABVIEW_RUNNER` is `true`.
  * `package` on the self-hosted Windows runner, for every pull request and every push to `main`: builds the VI package `jgoebel_lib_remotevi-X.Y.Z.N.vip` (X.Y.Z from `vipm.toml`, N the workflow run number) and keeps it as the artifact `vi-package` for 30 days, to install and test before a release. Also only with `LABVIEW_RUNNER`.
* **Package** (`.github/workflows/package.yml`, reusable): `vipm install` (the packages of `vipm.toml` for LabVIEW 2020 64-bit), then `scripts/build-package.ps1` (below).
* **Release** (`.github/workflows/release.yml`): set `version = "X.Y.Z"` in `vipm.toml` on `main`, commit, then tag that commit:

  ```
  git tag v1.2.3
  git push origin v1.2.3
  ```

  It checks that the tag matches `vipm.toml` and that the LabVIEW runner is configured (a release without its package fails rather than publishing sources only), reruns CI, builds the package on the LabVIEW runner, and publishes a GitHub release named `RemoteVI X.Y.Z` with generated release notes and two files: `jgoebel_lib_remotevi-X.Y.Z.N.vip` and `RemoteVI-vX.Y.Z-source.zip`. Versions `0.x` are marked as pre-releases.

## The VI package

`build/RemoteVI.vipb` (VI Package Builder, saved for LabVIEW 2020 64-bit) installs:

| What | Where |
|---|---|
| `source/` (RemoteVI.lvlib) | `<vi.lib>\jgoebel\RemoteVI` |
| Functions palette **RemoteVI**: Start, Stop, Start Window, Status, Status Panel, Show Status, Open Server | `<menus>\Categories` |
| Tools » RemoteVI » Share in Browser (`tools-menu/`) | `<LabVIEW>\project\RemoteVI` |
| `examples/RemoteVI Demo.vi`, `examples/Executables/` | `<LabVIEW>\examples\RemoteVI` |

`examples/Executables/` holds the batch files and README of the example applications; the applications themselves (`RemoteVI Demo.exe`, `RemoteVI Server.exe` with their INI files) are copied there from `builds/` by the build script and are not committed. They are built by LabVIEW 2020 and need the LabVIEW 2020 Run-Time Engine (64-bit). The package requires 64-bit LabVIEW: only that is tested.

Build it locally (LabVIEW 2020 64-bit with Application Builder, VIPM 2026 or newer, `vipm install` done once):

```
.\scripts\build-package.ps1                       # version from vipm.toml, build number 0
.\scripts\build-package.ps1 -Version 1.2.3 -BuildNumber 7
.\scripts\build-package.ps1 -SkipExecutables      # reuse the executables in builds\
```

The script builds the build specifications `RemoteVI Demo` and `RemoteVI Server` with LabVIEW 2020 (`tools/dev/Build Spec.vi` over LabVIEW's ActiveX server; it refuses another LabVIEW version), stages them, runs `vipm build`, and checks the package: the API VIs, the palette, the Tools menu VI, the example and both executables must be in it, and none of the repository's development files (tests, tools, docs, project, AIXML). The package lands in `builds/`. Install it for testing with VIPM (double-click the `.vip`), preferably in a LabVIEW where this repository is not open: the installed `RemoteVI.lvlib` and the repository's would cross-link.

VIPM writes icons as flattened data; an icon element must hold data (`00000000` for none), as an empty element makes `vipm build` fail with error 74 in *Flattened String To Variant*.

## The self-hosted LabVIEW runner

GitHub's hosted runners have no LabVIEW, and NI's LabVIEW containers are Linux-only, while RemoteVI injects input through Win32. So the LabVIEW jobs need a Windows machine with:

* LabVIEW 2020 (64-bit), activated, with Application Builder and VI Server enabled (default) - the repository and the package are saved for 2020. It must be LabVIEW's registered ActiveX server (the last LabVIEW installed or started once as administrator), because the build script reaches it as `LabVIEW.Application`; a newer LabVIEW may be installed beside it for the other jobs,
* VIPM 2026 or newer with its CLI `vipm` on PATH, the port VIPM uses for LabVIEW 2020 matching that LabVIEW's VI Server port; `vipm install` in the repository root installs IG HTTP Utils, IG WebSocket Stream, IG Stream Base, Caraya, G-CLI and the Caraya CLI extension, as listed in `vipm.toml` (the package workflow runs it on every build),
* Node.js 22 and Python 3.10+,
* a GitHub Actions runner registered for this repository with the labels `self-hosted, windows, labview-2020`, running **in an interactive user session** (not as a Windows service in session 0): RemoteVI captures and drives real windows, which need a desktop. Use the runner's `run.cmd` in a logged-in session, or auto-logon plus a scheduled task.

Then set the repository variable `LABVIEW_RUNNER` to `true` (Settings → Secrets and variables → Actions → Variables).

The VIPM Community Edition builds packages for public repositories, which this one is.
