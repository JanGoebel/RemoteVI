// RemoteVI Server app reference (docs/architecture.md, RemoteVI Server): which windows the app offers
// to share, and the landing page that lists the shares. Mirrors App/RemoteVI Window Rows.vi and
// App/RemoteVI Landing Page.vi; vectors in tests/vectors/server-app.json.

export const WS_EX_TOOLWINDOW = 0x80;
export const GROUPS = ['LabVIEW', 'LabVIEW application', 'Other programs'];

/** The file name of a program path, `C:\a\LabVIEW.exe` -> `LabVIEW.exe`. */
export function programName(path) {
  const i = Math.max(path.lastIndexOf('\\'), path.lastIndexOf('/'));
  return path.slice(i + 1);
}

/**
 * The shareable windows, grouped and sorted. raw: top-level windows as Win32 lists them
 * {hWnd, pid, path (program path), cls, title, visible, owned, exStyle, w, h}.
 * Kept: visible, with a size and a caption, no tool window; a window of LabVIEW (class LVDChild)
 * also when it is owned (LabVIEW's panels are owned by its hidden frame), others only unowned;
 * not a LabVIEW window whose caption names a Block Diagram or Project Explorer; not the window `skip` (the app's own).
 * group 0: LabVIEW (the development environment, LabVIEW.exe), 1: a LabVIEW-built application
 * (an LVDChild window of another program), 2: other programs. labviewOnly keeps groups 0 and 1.
 * Sorted by group, then program name (case-insensitive), then title.
 */
export function windowRows(raw, { labviewOnly = false, skip = 0 } = {}) {
  const rows = [];
  for (const w of raw) {
    if (!w.visible || w.w <= 0 || w.h <= 0 || !w.title || (w.exStyle & WS_EX_TOOLWINDOW) || w.hWnd === skip) continue;
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
