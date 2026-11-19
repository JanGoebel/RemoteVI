# CI and releases

## Workflow

* `main` is the protected default branch. Work happens on feature branches; each feature is a pull request whose commits stay visible (merge commits, no squash).
* **CI** (`.github/workflows/ci.yml`) runs on every pull request and on `main`:
  * `reference` on `ubuntu-latest`: vector freshness, Caraya tests in sync with the vectors (`tests/caraya/build.py --check`), and `npm test` (reference server, web client, end-to-end).
  * `labview` on the self-hosted Windows runner: Caraya (`tools/run-caraya.ps1`) and the LabVIEW integration suite (`tools/run-lv-integration.ps1`). It runs only when the repository variable `LABVIEW_RUNNER` is `true`.
  * `package` on the self-hosted Windows runner, for every pull request and every push to `main`: builds the VI package `jgoebel_lib_remotevi-X.Y.Z.N.vip` (X.Y.Z from `vipm.toml`, N the workflow run number) and keeps it as the artifact `vi-package` for 30 days, to install and test before a release. Also only with `LABVIEW_RUNNER`.
* **Package** (`.github/workflows/package.yml`, reusable): `vipm install` (the packages of `vipm.toml` for LabVIEW 2020 64-bit), then `tools/build-package.ps1` (below).
* **Release** (`.github/workflows/release.yml`): set `version = "X.Y.Z"` in `vipm.toml` on `main`, commit, then tag that commit:

  ```
  git tag v1.2.3
  git push origin v1.2.3
  ```

  It checks that the tag matches `vipm.toml` and that the LabVIEW runner is configured (a release without its package fails rather than publishing sources only), reruns CI, builds the package on the LabVIEW runner, and publishes a GitHub release named `RemoteVI X.Y.Z` with generated release notes and two files: `jgoebel_lib_remotevi-X.Y.Z.N.vip` and `RemoteVI-vX.Y.Z-source.zip`. Versions `0.x` are marked as pre-releases.

## The VI package

`package/RemoteVI.vipb` (VI Package Builder, saved for LabVIEW 2020 64-bit) installs:

| What | Where |
|---|---|
| `source/` (RemoteVI.lvlib) | `<vi.lib>\jgoebel\RemoteVI` |
| Functions palette **RemoteVI**: Start, Stop, Start Window, Status, Status Panel, Show Status, Open Server | `<menus>\Categories` |
| Tools » RemoteVI » Share in Browser (`source/Tools Menu/`) | `<LabVIEW>\project\RemoteVI` |
| `examples/RemoteVI Demo.vi`, `examples/Executables/` | `<LabVIEW>\examples\RemoteVI` |

`examples/Executables/` holds the batch files and README of the example applications; the applications themselves (`RemoteVI Demo.exe`, `RemoteVI Server.exe` with their INI files) are copied there from `builds/` by the build script and are not committed. They are built by LabVIEW 2020 and need the LabVIEW 2020 Run-Time Engine (64-bit). The package requires 64-bit LabVIEW: only that is tested.

Build it locally (LabVIEW 2020 64-bit with Application Builder, VIPM 2026 or newer, `vipm install` done once):

```
.\tools\build-package.ps1                       # version from vipm.toml, build number 0
.\tools\build-package.ps1 -Version 1.2.3 -BuildNumber 7
.\tools\build-package.ps1 -SkipExecutables      # reuse the executables in builds\
.\tools\build-package.ps1 -CloseLabVIEW         # quit LabVIEW 2020 between the executables and VIPM (CI)
```

Application Builder keeps the built VIs in LabVIEW's memory, and VIPM refuses to build while source VIs are open (error 42, with the list of VIs). So after building the executables, close them (or the project) in LabVIEW 2020, or let the script quit LabVIEW with `-CloseLabVIEW`; VIPM starts it again with nothing loaded. The integration suite closes its fixture for the same reason.

The script builds the build specifications `RemoteVI Demo`, `RemoteVI Application Example` and `RemoteVI Server` with LabVIEW 2020 (`-LabVIEWVersion`), stages them, runs `vipm build`, and checks the package: the API VIs, the palette, the Tools menu VI, the example and both executables must be in it, and none of the repository's development files (tests, tools, docs, project, AIXML). The package lands in `builds/`.

Both this script and the integration suite (`tools/run-lv-integration.ps1`) drive LabVIEW through NI's LabVIEW CLI (`tools/labview-cli.ps1`), which ships with LabVIEW and talks to it over VI Server TCP on the port in that LabVIEW's `LabVIEW.ini` (`server.tcp.port`, default 3363). The CLI starts LabVIEW if it is not running, or uses the running one. Its `RunVI` operation runs `tools/dev/Build Spec CLI.vi` (the build) and `tests/fixtures/Launch Fixture.vi` (starts the fixture and returns its share link). The CLI's own `ExecuteBuildSpec` fails in LabVIEW 2020 with error 1498, because the CLI installed with a newer LabVIEW is newer than 2020. ActiveX (`LabVIEW.Application`) is not used: on the runner it reached no working LabVIEW, not even after LabVIEW was closed and restarted.

Install it for testing with VIPM (double-click the `.vip`), preferably in a LabVIEW where this repository is not open: the installed `RemoteVI.lvlib` and the repository's would cross-link.

The package requires IG HTTP Utils, IG WebSocket Stream and IG Stream Base, so VIPM installs them with it. VIPM takes that list from the configuration `package/RemoteVI.vipc`, which the build spec names: the `External_Dependencies` of the spec alone leave the package without requirements. When a dependency of `vipm.toml` changes, change the spec and the configuration too; the script fails if the built package does not require every dependency of `vipm.toml`.

VIPM writes icons as flattened data; an icon element must hold data (`00000000` for none), as an empty element makes `vipm build` fail with error 74 in *Flattened String To Variant*.

## The self-hosted LabVIEW runner

GitHub's hosted runners have no LabVIEW, and NI's LabVIEW containers are Linux-only, while RemoteVI injects input through Win32. So the LabVIEW jobs need a Windows machine with:

* LabVIEW 2020 (64-bit), activated, with Application Builder - the repository and the package are saved for 2020 - and VI Server TCP/IP enabled (Tools » Options » VI Server; `server.tcp.enabled=True` in its `LabVIEW.ini`), because the LabVIEW CLI, G-CLI and VIPM all reach it there. A newer LabVIEW may be installed beside it on another VI Server port,
* NI's LabVIEW CLI (`LabVIEWCLI.exe` under `Shared\LabVIEW CLI`, installed with LabVIEW 2018 or newer),
* VIPM 2026 or newer with its CLI `vipm` on PATH, the port VIPM uses for LabVIEW 2020 matching that LabVIEW's VI Server port; `vipm install` in the repository root installs IG HTTP Utils, IG WebSocket Stream, IG Stream Base, Caraya, G-CLI and the Caraya CLI extension, as listed in `vipm.toml` (the LabVIEW and package jobs run it on every build),
* Node.js 22 and Python 3.10+; the scripts run in Windows PowerShell 5.1, which Windows includes (PowerShell 7 is not needed),
* a GitHub Actions runner registered for this repository with the labels `self-hosted, windows, labview-2020`, running **in an interactive user session** (not as a Windows service in session 0): RemoteVI captures and drives real windows, which need a desktop. Use the runner's `run.cmd` in a logged-in session, or auto-logon plus a scheduled task.

Then set the repository variable `LABVIEW_RUNNER` to `true` (Settings → Secrets and variables → Actions → Variables).

The VIPM Community Edition builds packages for public repositories, which this one is.
