# Developer helpers

These are small VIs and scripts for working on RemoteVI with LabVIEW 2025 (64-bit) and labview-mcp. They are not part of the toolkit. Each VI's AIXML source is in `aixml/`.

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
| `start-labview.ps1` | (none) | Starts LabVIEW 2025 outside the calling shell's job and waits for it. |

## Library re-add after recomposing VIs
Close everything from RemoteVI first: `Mem.vi` with text "RemoteVI" must return nothing. Then:

```
python tools/dev/mk_lists.py
# run Add To Library Files.vi with source/RemoteVI.lvlib, tools/dev/items.txt, tools/dev/callers.txt
python tools/dev/fixlib.py
```

Repeat until `mk_lists.py` reports 0 items. `mk_lists.py` reads VIs with labview-mcp's bundled pylabview (`%USERPROFILE%\.claude\plugins\cache\zuehlke-labview\labview-mcp\<version>`). If labview-mcp is installed elsewhere, adjust the path at the top of the script.
