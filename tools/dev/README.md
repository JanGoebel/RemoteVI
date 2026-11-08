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
| `Style Panel.vi` | VI, Silver (vi.lib\silver_ctls), Spec | Restyles a composed VI's panel and saves it (the composer only makes generic controls). In order: puts the splitter bars of a splitter panel to their positions; Replaces controls with Silver .ctl files (wires, type and value stay); sets tab pages and sizes controls that have no writable size (tab controls, subpanels, multicolumn listboxes) through their own pane's scaling; sets the window (menu bar, tool bar and scroll bars hidden, panel bounds); then moves controls onto tab pages or into splitter panes (relative to the pane's visible top left, its Origin) and places them, sizes them by class, sets boolean text, tip strips, label visibility and the graph look. The Spec file is written by `tools/aixml/style_rows.py` (see `examples/aixml/build_demo.py` and `build_app_example.py`); `problems` lists each step with its error code (a 1057 in the Tabs step of a control that is no tab control is expected). Source: `aixml/gen_style_panel.py`. |
| `Fit To Pane.vi` | VI, Label, Width Bar, Pane Left Of Bar, Height Bar, Cell Width, Row Height, Rows | Makes a control of a splitter panel fill its pane and follow it (what Fit Control to Pane does by hand), also a subpanel or a multicolumn listbox, which have no writable size: scrolls the pane to 0,0, moves the control there, shrinks the pane to the control by moving its splitter bars with scaling off, switches Scale Single Object on and puts the bars back; saves the VI. `control size` must equal `pane size`. Cell Width > 0 first sizes a multicolumn listbox (one column, rows, no headers or scroll bar). Used by `examples/aixml/build_app_example.py`. Source: `aixml/fit_to_pane.xml`. |
| `Set Columns.vi` | VI, Label, Widths, Rows | Sizes a multicolumn listbox by its columns: the width of each column, then the number of visible columns and rows; saves the VI. A VI that writes Number of Columns at run time keeps the widths. Source: `aixml/set_columns.xml`. |
| `icons.py` | [names...] | The text icon of every VI without a hand-made one (banner RVI for the library, grey for the palette VIs; the DLL for Win32 wrappers; DEMO, APP, DEV elsewhere): draws them as 32x32 PNGs into `builds/icons/` and writes `vis.txt` and `pngs.txt` for `Set Icons.vi`. Add a row for each new VI. Run with labview-mcp's pylabview python (it has Pillow). With names, only the VIs whose path contains one. |
| `icon_font.py` | | Draws those icons: frame, 006699 banner and two lines in the 5x7 font of labview-mcp's `lvai_set_vi_icon`, pixel for pixel, so icons from either match. |
| `Set Icons.vi` | VIs, Icons | Sets the icon of each VI from its PNG (both files list paths separated by semicolons), saves the VI and returns one error code per VI. Run with no project open, then save the VIs for 2020. Source: `aixml/set_icons.xml`. |
| `Remote Exec State.vi` | machine, port, items file | Loads every VI listed in another LabVIEW and returns open code, execution state (0 broken, 1 runnable) and linker errors per VI - the check that the repository loads in LabVIEW 2020. |

## Library re-add after recomposing VIs
Close everything from RemoteVI first: `Mem.vi` with text "RemoteVI" must return nothing. Then:

```
python tools/dev/mk_lists.py
# run Add To Library Files.vi with source/RemoteVI.lvlib, tools/dev/items.txt, tools/dev/callers.txt
python tools/dev/fixlib.py
```

Repeat until `mk_lists.py` reports 0 items. `mk_lists.py` reads VIs with labview-mcp's bundled pylabview (`%USERPROFILE%\.claude\plugins\cache\zuehlke-labview\labview-mcp\<version>`). If labview-mcp is installed elsewhere, adjust the path at the top of the script.
