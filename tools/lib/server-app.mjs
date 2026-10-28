// RemoteVI Server app reference (docs/architecture.md, RemoteVI Server): which windows the app offers
// to share, and the landing page that lists the shares. Mirrors App/RemoteVI Window Rows.vi and
// App/RemoteVI Landing Page.vi; vectors in tests/vectors/server-app.json.

export const WS_EX_TOOLWINDOW = 0x80;
export const WS_EX_NOACTIVATE = 0x08000000;
/** Shell and system windows that are visible to Win32 but not real program windows. */
export const EXCLUDED_CLASSES = ['Windows.UI.Core.CoreWindow', 'Windows.Internal.Shell.TabProxyWindow', 'Progman', 'LockScreenBackstopFrame'];
export const MIN_W = 100;
export const MIN_H = 50;
export const GROUPS = ['LabVIEW', 'LabVIEW application', 'Other programs'];

/** The file name of a program path, `C:\a\LabVIEW.exe` -> `LabVIEW.exe`. */
export function programName(path) {
  const i = Math.max(path.lastIndexOf('\\'), path.lastIndexOf('/'));
  return path.slice(i + 1);
}

/**
 * The shareable windows, grouped and sorted. raw: top-level windows as Win32 lists them
 * {hWnd, pid, path (program path), cls, title, visible, owned, exStyle, w, h}.
 * Kept: visible, at least MIN_W x MIN_H, with a caption, no tool window (WS_EX_TOOLWINDOW) and no window that
 * cannot be activated (WS_EX_NOACTIVATE), not one of EXCLUDED_CLASSES; a window of LabVIEW (class LVDChild)
 * also when it is owned (LabVIEW's panels are owned by its hidden frame), others only unowned;
 * not a LabVIEW window whose caption names a Block Diagram or Project Explorer; not the window `skip` (the app's own).
 * group 0: LabVIEW (the development environment, LabVIEW.exe), 1: a LabVIEW-built application
 * (an LVDChild window of another program), 2: other programs. labviewOnly keeps groups 0 and 1.
 * Sorted by group, then program name (case-insensitive), then title.
 */
export function windowRows(raw, { labviewOnly = false, skip = 0 } = {}) {
  const rows = [];
  for (const w of raw) {
    if (!w.visible || w.w < MIN_W || w.h < MIN_H || !w.title || (w.exStyle & (WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE))
        || EXCLUDED_CLASSES.includes(w.cls) || w.hWnd === skip) continue;
    const lv = w.cls === 'LVDChild';
    if (w.owned && !lv) continue;
    if (lv && (w.title.includes('Block Diagram') || w.title.includes('Project Explorer'))) continue;
    const program = programName(w.path);
    const group = lv ? (program.toLowerCase() === 'labview.exe' ? 0 : 1) : 2;
    if (labviewOnly && group === 2) continue;
    rows.push({ group, program, title: w.title, pid: w.pid, hWnd: w.hWnd });
  }
  const key = (r) => [r.group, r.program.toLowerCase(), r.title];
  rows.sort((a, b) => {
    const ka = key(a), kb = key(b);
    for (let i = 0; i < 3; i++) if (ka[i] !== kb[i]) return ka[i] < kb[i] ? -1 : 1;
    return 0;
  });
  return rows;
}

/** One row as the vectors render it. */
export function renderRow(r) {
  return `${r.group}|${r.program}|${r.title}|${r.pid}|${r.hWnd}`;
}

/** HTML text: & < > " escaped. */
export function htmlEscape(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/**
 * The landing page (RemoteVI Server's own port): every RUNNING share of status (RemoteVI Status.vi)
 * as a link with its token. The page itself is only served with the landing page's own token.
 */
export function landingPage(status) {
  const items = status.filter((s) => s.running).map((s) => `<li><a href="${htmlEscape(s.url)}">${htmlEscape(s.target)}</a>`
    + `<span>${s.kind} - port ${s.port}${s.wholeNetwork ? ', whole network' : ''}${s.viewOnly ? ', view only' : ''}</span></li>`);
  return '<!doctype html><html><head><meta charset="windows-1252"><meta name="viewport" content="width=device-width">'
    + '<title>RemoteVI Server</title><style>body{font:15px Segoe UI,Arial,sans-serif;margin:32px;color:#222}'
    + 'h1{font-size:22px}ul{list-style:none;padding:0}li{margin:10px 0;padding:12px 16px;border:1px solid #ccd;border-radius:8px}'
    + 'a{font-weight:600;color:#0b57d0;text-decoration:none}span{display:block;color:#666;font-size:13px}</style></head>'
    + `<body><h1>RemoteVI Server</h1>${items.length ? `<ul>${items.join('')}</ul>` : '<p>Nothing is shared right now.</p>'}</body></html>`;
}

/** The first port from `start` up that no share in `used` has (RemoteVI Server suggests it for the next share). */
export function nextFreePort(used, start = 8100) {
  let p = start;
  while (used.includes(p) && p < 65535) p++;
  return p;
}

/**
 * RemoteVI Server.exe's command line (the arguments after `--`, as LabVIEW passes them):
 * --share <window title> shares that window at start; --port N its port (default 8100);
 * --token T its token (default random); --whole-network and --view-only as the check boxes;
 * --landing-port P the landing page's port (default 8088, 0 = no landing page).
 * Unknown arguments and a flag without its value are ignored; a bad number keeps the default.
 */
export function parseArgs(args) {
  const out = { share: '', port: 8100, token: '', wholeNetwork: false, viewOnly: false, landingPort: 8088 };
  const num = (s, d) => (/^\d+$/.test(s) && +s <= 65535 ? +s : d);
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    const v = i + 1 < args.length ? args[i + 1] : null;
    if (a === '--whole-network') out.wholeNetwork = true;
    else if (a === '--view-only') out.viewOnly = true;
    else if (v === null) continue;
    else if (a === '--share') { out.share = v; i++; }
    else if (a === '--port') { out.port = num(v, out.port); i++; }
    else if (a === '--token') { out.token = v; i++; }
    else if (a === '--landing-port') { out.landingPort = num(v, out.landingPort); i++; }
  }
  return out;
}
