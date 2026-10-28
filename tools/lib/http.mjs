// Reference implementation of the minimal, hardened HTTP front end.
// Mirrors Transport/HTTP_ParseRequestHead.vi; the limits are part of the spec
// (docs/security.md) and are covered by tests/vectors/http.json.

export const LIMITS = Object.freeze({
  maxHeadBytes: 8192,
  maxHeaders: 32,
  maxPathBytes: 1024,
});

export class HttpError extends Error {
  constructor(status, message) {
    super(message);
    this.name = 'HttpError';
    this.status = status;
  }
}

const TOKEN = /^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$/;

/**
 * Find the end of the request head (\r\n\r\n).
 * Returns the index just after it, -1 if more data is needed, or throws 431
 * when the head exceeds maxHeadBytes.
 */
export function findHeadEnd(buf, limits = LIMITS) {
  const i = buf.indexOf('\r\n\r\n');
  if (i >= 0) {
    if (i + 4 > limits.maxHeadBytes) throw new HttpError(431, 'request head too large');
    return i + 4;
  }
  if (buf.length >= limits.maxHeadBytes) throw new HttpError(431, 'request head too large');
  return -1;
}

/**
 * Parse a complete request head (latin1 string ending in \r\n\r\n).
 * Only GET is supported; header names are lower-cased; duplicate headers are rejected.
 */
export function parseRequestHead(head, limits = LIMITS) {
  const lines = head.split('\r\n');
  // Drop the two empty strings produced by the terminating \r\n\r\n.
  lines.length -= 2;
  const [method, target, version, ...extra] = lines[0].split(' ');
  if (extra.length || !method || !target || !version) throw new HttpError(400, 'malformed request line');
  if (version !== 'HTTP/1.1' && version !== 'HTTP/1.0') throw new HttpError(505, 'unsupported HTTP version');
  if (method !== 'GET') throw new HttpError(405, 'method not allowed');
  if (target.length > limits.maxPathBytes) throw new HttpError(414, 'URI too long');
  if (target[0] !== '/') throw new HttpError(400, 'target must be origin-form');

  const headerLines = lines.slice(1);
  if (headerLines.length > limits.maxHeaders) throw new HttpError(431, 'too many headers');
  const headers = Object.create(null);
  for (const line of headerLines) {
    const colon = line.indexOf(':');
    if (colon <= 0) throw new HttpError(400, 'malformed header');
    const name = line.slice(0, colon).toLowerCase();
    if (!TOKEN.test(name)) throw new HttpError(400, 'malformed header name');
    if (name in headers) throw new HttpError(400, `duplicate header ${name}`);
    headers[name] = line.slice(colon + 1).trim();
  }

  const q = target.indexOf('?');
  const path = q < 0 ? target : target.slice(0, q);
  const query = Object.create(null);
  if (q >= 0) {
    for (const pair of target.slice(q + 1).split('&')) {
      if (!pair) continue;
      const eq = pair.indexOf('=');
      const k = eq < 0 ? pair : pair.slice(0, eq);
      const v = eq < 0 ? '' : pair.slice(eq + 1);
      query[decodeURIComponentSafe(k)] = decodeURIComponentSafe(v);
    }
  }
  return { method, path, query, version, headers };
}

function decodeURIComponentSafe(s) {
  try {
    return decodeURIComponent(s.replace(/\+/g, ' '));
  } catch {
    throw new HttpError(400, 'bad percent-encoding');
  }
}

/** True if the request asks for a WebSocket upgrade (RFC 6455 section 4.2.1). */
export function isWebSocketUpgrade(req) {
  const upgrade = (req.headers['upgrade'] ?? '').toLowerCase();
  const connection = (req.headers['connection'] ?? '').toLowerCase().split(',').map((s) => s.trim());
  return upgrade === 'websocket' && connection.includes('upgrade') && req.headers['sec-websocket-version'] === '13'
    && typeof req.headers['sec-websocket-key'] === 'string';
}

const REASONS = {
  101: 'Switching Protocols', 200: 'OK', 304: 'Not Modified', 400: 'Bad Request', 401: 'Unauthorized',
  403: 'Forbidden', 404: 'Not Found', 405: 'Method Not Allowed', 408: 'Request Timeout',
  414: 'URI Too Long', 426: 'Upgrade Required', 431: 'Request Header Fields Too Large',
  503: 'Service Unavailable', 505: 'HTTP Version Not Supported',
};

/** Serialise a response head. Every response closes the connection unless it is a 101. */
export function buildResponseHead(status, headers = {}) {
  let s = `HTTP/1.1 ${status} ${REASONS[status] ?? 'Unknown'}\r\n`;
  const all = { ...headers };
  if (status !== 101) all['Connection'] = 'close';
  for (const [k, v] of Object.entries(all)) s += `${k}: ${v}\r\n`;
  return s + '\r\n';
}

/**
 * Security headers added to every static response. The client is one self-contained
 * file, so inline script and style are allowed; nothing may be loaded from anywhere
 * else, and only this origin may be connected to.
 */
export const SECURITY_HEADERS = Object.freeze({
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'Referrer-Policy': 'no-referrer',
  'Cache-Control': 'no-store',
  'Content-Security-Policy': "default-src 'none'; connect-src 'self'; img-src blob:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; frame-ancestors 'none'",
});

/**
 * Access token check (docs/security.md): the query string of the request target must carry
 * t=<token>. Every `?` counts as a parameter separator like `&` (the server may get the query
 * with or without its leading `?`); the first `t` parameter is compared with the share's token
 * in constant time. An empty token never matches (fail closed). Server/RemoteVI Token Check.vi,
 * vectors tests/vectors/http.json -> tokens.
 */
export function tokenOk(query, token) {
  if (!token) return false;
  const q = `&${query.replace(/\?/g, '&')}`;
  const at = q.indexOf('&t=');
  if (at < 0) return false;
  let v = q.slice(at + 3);
  const end = v.indexOf('&');
  if (end >= 0) v = v.slice(0, end);
  if (v.length !== token.length) return false;
  let d = 0;
  for (let i = 0; i < v.length; i++) d |= v.charCodeAt(i) ^ token.charCodeAt(i);
  return d === 0;
}
