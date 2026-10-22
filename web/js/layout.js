// Pure helpers over the `layout` message (no DOM), so they are unit-testable.

/** Control kinds the browser edits locally with an HTML overlay. */
export const OVERLAY_KINDS = new Set(['numeric', 'string', 'path', 'enum', 'ring']);

const inRect = ([x, y, w, h], px, py) => px >= x && py >= y && px < x + w && py < y + h;

/**
 * Topmost visible control at panel coordinates (px, py).
 * Controls are listed back-to-front (LabVIEW z-order), so search from the end.
 */
export function hitTest(controls, px, py) {
  for (let i = controls.length - 1; i >= 0; i--) {
    const c = controls[i];
    if (c.visible !== false && inRect(c.bounds, px, py)) return c;
  }
  return null;
}

/** Whether a click on this control should open a local overlay editor. */
export function wantsOverlay(control) {
  return !!control && !control.readonly && control.disabled !== true && OVERLAY_KINDS.has(control.kind);
}

/** Rectangle used for the overlay editor: the text part if known, else the whole control. */
export function overlayRect(control) {
  return control.edit ?? control.bounds;
}

/** Convert an overlay's text to the JSON value sent in a `set` message, or throw. */
export function parseOverlayValue(control, text) {
  switch (control.kind) {
    case 'numeric': {
      const v = Number(text.trim().replace(',', '.'));
      if (text.trim() === '' || !Number.isFinite(v)) throw new RangeError('not a number');
      return v;
    }
    case 'enum':
    case 'ring': {
      const v = Number(text);
      if (!Number.isInteger(v) || v < 0 || v >= (control.items?.length ?? 0)) throw new RangeError('no such item');
      return v;
    }
    default:
      return text;
  }
}

/** Map client coordinates to panel pixel coordinates given the canvas's on-screen rect. */
export function toPanelCoords(rect, panelW, panelH, clientX, clientY) {
  const x = Math.floor(((clientX - rect.left) * panelW) / rect.width);
  const y = Math.floor(((clientY - rect.top) * panelH) / rect.height);
  return { x: Math.max(0, Math.min(panelW - 1, x)), y: Math.max(0, Math.min(panelH - 1, y)) };
}

/** Modifier bitmask: 1 shift, 2 ctrl, 4 alt, 8 meta. */
export function modifiers(e) {
  return (e.shiftKey ? 1 : 0) | (e.ctrlKey ? 2 : 0) | (e.altKey ? 4 : 0) | (e.metaKey ? 8 : 0);
}
