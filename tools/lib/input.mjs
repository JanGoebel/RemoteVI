// Reference for Input/Translate Input.vi: turns one parsed client input message
// into the Win32 messages the server posts to the panel window. The rules come
// from spikes/Spike Input Injection.vi (LabVIEW 2025, posted messages):
//
//  * Mouse messages carry CLIENT coordinates in lParam - except while LabVIEW
//    TRACKS a press ("tracking"), when it reads the moves and the button-up as
//    SCREEN coordinates. LabVIEW tracks (and then holds the mouse capture) for
//    latched buttons, sliders, text selection, graph drags ... but not for a
//    switch-when-pressed boolean, which takes its button-up in client
//    coordinates (measured: in screen coordinates the up was lost and LabVIEW
//    thought the button was still held). So the server passes as `tracking`
//    whether LabVIEW's UI thread holds the mouse capture right now
//    (GetGUIThreadInfo -> hwndCapture), read after LabVIEW has handled the
//    button-down. The `tracking` this function returns (button-down until
//    button-up) is only bookkeeping.
//  * WM_MOUSEWHEEL always carries screen coordinates (Windows' definition).
//  * A bare posted WM_CHAR right after a non-character key is dropped, and a
//    WM_KEYDOWN of the character's own key makes LabVIEW's message loop
//    produce a second character. So each WM_CHAR is wrapped in key-down/up of
//    VK 0xE8, a key that produces no character.
//  * While a LabVIEW popup (ring/enum menu, right-click menu, graph palette
//    popup ...) is open, LabVIEW hit-tests clicks with the REAL cursor position
//    against the popup window's REAL position. The host cursor is never moved:
//    the server moves the (invisible) popup windows so that the point the
//    remote user clicked (`cursor` in the result, the popup's logical screen
//    point) lies under wherever the host cursor is, then posts the click with
//    the real cursor position in lParam. Moves and wheel are dropped: LabVIEW
//    only updates the hover highlight on real cursor motion, so there is none;
//    a submenu opens on the second click on its entry. A click outside every
//    popup is not posted; the server closes the popups with WM_CANCELMODE.
//    Popups travel as OVERLAY messages at their logical position, see
//    docs/protocol.md.
//
// Two rules live in the server rather than here, because they are timing and
// thread state, not translation:
//  * Each message is posted only after LabVIEW has handled the one before
//    (two WM_NULL sent to the panel window): LabVIEW drops and reorders key
//    messages that arrive in a burst.
//  * LabVIEW reads Shift/Ctrl/Alt with GetKeyState, which posted messages do
//    not update. The server keeps the modifiers the remote user holds
//    (trackModifiers() below) and writes them into the key state of LabVIEW's
//    UI thread (SetKeyboardState, called in that thread) before posting.

import { ALLOWED_MESSAGES, mouseLParam } from './protocol.mjs';

export const VK_NOCHAR = 0xe8;
export const KEYUP_LPARAM = 0xc0000001;

const BUTTON_DOWN = new Set([0x201, 0x203, 0x204, 0x206, 0x207, 0x209]);
const BUTTON_UP = new Set([0x202, 0x205, 0x208]);

/**
 * @param {{kind:string,msg:number,x?:number,y?:number,wParam:number,lParam?:number}} input from parseInput()
 * @param {{panelX:number,panelY:number,clientX:number,clientY:number}} geo
 *        panel origin and client-area origin, both in screen coordinates
 * @param {boolean} tracking LabVIEW tracks a press, i.e. holds the mouse capture (the server asks Windows)
 * @param {boolean} [popup] a LabVIEW popup window is open
 * @returns {{posts:{msg:number,wParam:number,lParam:number}[], tracking:boolean, cursor:{x:number,y:number}|null}}
 */
export function translateInput(input, geo, tracking, popup = false) {
  if (input.kind !== 'mouse' && input.kind !== 'key') return { posts: [], tracking, cursor: null };
  if (!ALLOWED_MESSAGES.has(input.msg)) return { posts: [], tracking, cursor: null };

  if (input.kind === 'key') {
    if (input.msg === 0x102) {
      return {
        tracking,
        cursor: null,
        posts: [
          { msg: 0x100, wParam: VK_NOCHAR, lParam: 1 },
          { msg: 0x102, wParam: input.wParam, lParam: 1 },
          { msg: 0x101, wParam: VK_NOCHAR, lParam: KEYUP_LPARAM },
        ],
      };
    }
    return { tracking, cursor: null, posts: [{ msg: input.msg, wParam: input.wParam, lParam: input.lParam }] };
  }

  const sx = geo.panelX + input.x;
  const sy = geo.panelY + input.y;
  const screen = mouseLParam(sx, sy);
  const client = mouseLParam(sx - geo.clientX, sy - geo.clientY);
  let lParam;
  let next = tracking;
  if (popup) {
    // The popup tracks the real cursor; button state still comes from the messages.
    if (BUTTON_DOWN.has(input.msg)) next = true;
    else if (BUTTON_UP.has(input.msg)) next = false;
    else return { tracking, cursor: null, posts: [] }; // moves and wheel: dropped
    return { tracking: next, cursor: { x: sx, y: sy }, posts: [{ msg: input.msg, wParam: input.wParam, lParam: screen }] };
  }
  if (input.msg === 0x20a) {
    lParam = screen;
  } else if (BUTTON_DOWN.has(input.msg)) {
    lParam = client;
    next = true;
  } else if (BUTTON_UP.has(input.msg)) {
    lParam = tracking ? screen : client;
    next = false;
  } else {
    lParam = tracking ? screen : client; // WM_MOUSEMOVE
  }
  return { tracking: next, cursor: null, posts: [{ msg: input.msg, wParam: input.wParam, lParam }] };
}

export const MOD_SHIFT = 1;
export const MOD_CTRL = 2;
export const MOD_ALT = 4;

const MODIFIER_KEYS = new Map([
  [0x10, MOD_SHIFT], [0xa0, MOD_SHIFT], [0xa1, MOD_SHIFT],
  [0x11, MOD_CTRL], [0xa2, MOD_CTRL], [0xa3, MOD_CTRL],
  [0x12, MOD_ALT], [0xa4, MOD_ALT], [0xa5, MOD_ALT],
]);

/**
 * Reference for Input/RemoteVI Track Modifiers.vi: the modifier keys the remote
 * user holds after `input`, as a bit set (1 Shift, 2 Ctrl, 4 Alt). A WM_KEYDOWN /
 * WM_KEYUP of a Shift, Ctrl or Alt key (generic, left or right VK) sets / clears its
 * bit; an allowed mouse message carries Shift and Ctrl in wParam (MK_SHIFT 4,
 * MK_CONTROL 8) and keeps Alt; anything else changes nothing.
 * @param {{kind:string,msg:number,wParam:number}} input from parseInput()
 * @param {number} mods held before
 * @returns {number} held after
 */
export function trackModifiers(input, mods) {
  if (input.kind === 'key' && (input.msg === 0x100 || input.msg === 0x101)) {
    const bit = MODIFIER_KEYS.get(input.wParam) ?? 0;
    return input.msg === 0x100 ? mods | bit : mods & ~bit & 0xff;
  }
  if (input.kind === 'mouse' && input.msg >= 0x200 && ALLOWED_MESSAGES.has(input.msg)) {
    return (mods & MOD_ALT) | (input.wParam & 4 ? MOD_SHIFT : 0) | (input.wParam & 8 ? MOD_CTRL : 0);
  }
  return mods;
}
