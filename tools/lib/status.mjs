// Status API reference (docs/architecture.md, Status): what RemoteVI Status.vi returns for the
// shares of one LabVIEW application instance, and its text form. Mirrors Server/RemoteVI Status
// Convert.vi, Server/RemoteVI Format Duration.vi and Server/RemoteVI Status Text.vi; vectors in
// tests/vectors/status.json.

/** A share counts as running while its server loop published within this many seconds. */
export const ALIVE_S = 2;

/**
 * Raw entries (what each server loop publishes every 500 ms, times in seconds since the LabVIEW
 * epoch) -> the status the API returns, for the time `now`.
 */
export function statusConvert(raw, now) {
  return raw.map((r) => ({
    port: r.port, url: r.url, target: r.target, kind: r.kind, wholeNetwork: r.wholeNetwork,
    running: now - r.updated < ALIVE_S,
    uptime: now - r.started,
    clients: r.clients.map((c) => ({
      address: c.address, connected: now - c.since, idle: c.lastInput > 0 ? now - c.lastInput : -1,
    })),
    fps: r.fps, kBps: r.bytesPerS / 1024, frames: r.frames, latencyMs: r.latencyMs, viewOnly: r.viewOnly,
    lastError: r.lastError,
  }));
}

/** Whole seconds as `12 s`, `3 min 5 s` or `2 h 7 min`. */
export function formatDuration(seconds) {
  const s = Math.max(0, Math.floor(seconds));
  if (s < 60) return `${s} s`;
  if (s < 3600) return `${Math.floor(s / 60)} min ${s % 60} s`;
  return `${Math.floor(s / 3600)} h ${Math.floor(s / 60) % 60} min`;
}

/** The text form of the status, one block per share, lines joined with LF. */
export function statusText(servers) {
  if (!servers.length) return 'No RemoteVI share is running.';
  const lines = [];
  for (const s of servers) {
    lines.push(`Port ${s.port}: ${s.target} (${s.kind}), ${s.running ? `running for ${formatDuration(s.uptime)}` : 'stopped'}, `
      + `${s.wholeNetwork ? 'whole network' : 'this computer only'}${s.viewOnly ? ', view only' : ''}`);
    lines.push(`  ${s.url}`);
    lines.push(`  ${s.clients.length} ${s.clients.length === 1 ? 'client' : 'clients'}, ${s.fps.toFixed(1)} fps, `
      + `${s.kBps.toFixed(0)} kB/s, ${s.frames} frames, input to frame ${s.latencyMs.toFixed(0)} ms`);
    for (const c of s.clients) {
      lines.push(`  ${c.address}, connected ${formatDuration(c.connected)}, `
        + `${c.idle < 0 ? 'no input yet' : `last input ${formatDuration(c.idle)} ago`}`);
    }
    if (s.lastError) lines.push(`  last error: ${s.lastError}`);
  }
  return lines.join('\n');
}
