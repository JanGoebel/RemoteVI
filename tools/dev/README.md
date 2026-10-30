# Developer helpers

These are small VIs and scripts for working on RemoteVI with labview-mcp and LabVIEW 2020 or newer (64-bit); the repository is saved for 2020. They are not part of the toolkit. Each VI's AIXML source is in `aixml/`.

| Helper | Inputs | Purpose |
|---|---|---|
| `Launch Detached.vi` | path | Runs a VI detached (Run VI, no wait, auto-dispose). Use it for servers and demos, because `lvai_run_vi_as_top_level` aborts long runs at its timeout. |
| `Abort Path.vi` | path | Aborts a running VI by path. |
| `FP Close Path.vi` | path | Closes a VI's front panel so the VI leaves memory. |
| `Mem.vi` | text | Lists the VIs in memory whose name contains the text, e.g. "RemoteVI". |
| `Notify Stop.vi` | port | Stops a RemoteVI server by port without waiting. |
| `Build Spec.vi` | project, spec | Builds a build specification through vi.lib/AppBuilder. |
| `Add To Library Files.vi` | library path, items file, callers file | Adds VIs to `RemoteVI.lvlib` and saves their callers. |
| `mk_lists.py` | (none) | Writes `items.txt` (source VIs that lost library membership) and `callers.txt`, and drops their stale lvlib entries. |
| `fixlib.py` | (none) | Restores the lvlib folder layout after AddItem. |
| `start-labview.ps1` | `-Version` (default 2020) | Starts that LabVIEW outside the calling shell's job and waits for it; another version may run beside it. |
| `Save For Previous.vi` | items file, version (20.0) | Saves every VI listed (one path per line) for an older LabVIEW, in place, and returns code and warnings per VI. Run it after generating or recomposing VIs on a newer LabVIEW. |
| `lv_versions.py` | [root] [--expect 20.0] | Prints the version each VI was saved in; with `--expect`, lists and fails on every other one. |
| `lvlib_version.py` | [--major 20] lvlib ... | Marks `.lvlib` files as saved by LabVIEW 2020: `LVVersion`, `NI.Lib.SourceVersion` and the version header of the flattened library icon. A newer header makes LabVIEW 2020 refuse the library (error 122) and break every member. |
| `Remote Run.vi` | machine, port, vi path, inputs, result | Runs a VI in another LabVIEW over VI Server (LabVIEW 2020 on 3365 next to 2026), inputs as LabVIEW XML in `LvVariant`, and returns one control as XML. Use `Launch Detached.vi` as the VI to start something there with its panel open. |
| `Remote Exec State.vi` | machine, port, items file | Loads every VI listed in another LabVIEW and returns open code, execution state (0 broken, 1 runnable) and linker errors per VI - the check that the repository loads in LabVIEW 2020. |

## Library re-add after recomposing VIs
Close everything from RemoteVI first: `Mem.vi` with text "RemoteVI" must return nothing. Then:

```
python tools/dev/mk_lists.py
# run Add To Library Files.vi with source/RemoteVI.lvlib, tools/dev/items.txt, tools/dev/callers.txt
python tools/dev/fixlib.py
```

Repeat until `mk_lists.py` reports 0 items. `mk_lists.py` reads VIs with labview-mcp's bundled pylabview (`%USERPROFILE%\.claude\plugins\cache\zuehlke-labview\labview-mcp\<version>`). If labview-mcp is installed elsewhere, adjust the path at the top of the script.
