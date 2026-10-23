// Reference for Input/Translate Input.vi: turns one parsed client input message
// into the Win32 messages the server posts to the panel window. The rules come
// from spikes/Spike Input Injection.vi (LabVIEW 2025, posted messages):
//
//  * Mouse messages carry CLIENT coordinates in lParam - except while a button
//    is held ("tracking": from a button-down until the matching button-up),
//    when LabVIEW reads the moves and the button-up as SCREEN coordinates.
//  * WM_MOUSEWHEEL always carries screen coordinates (Windows' definition).
//  * A bare posted WM_CHAR right after a non-character key is dropped, and a
//    WM_KEYDOWN of the character's own key makes LabVIEW's message loop
//    produce a second character. So each WM_CHAR is wrapped in key-down/up of
//    VK 0xE8, a key that produces no character.
//  * While a LabVIEW popup (ring/enum menu, right-click menu, graph palette
//    popup ...) is open, LabVIEW reads the REAL cursor position. So every mouse
//    message gets screen coordinates and the server first moves the host cursor
//    there (`cursor` in the result). The popup's own picture comes from a
//    screen capture, see docs/architecture.md.

import { ALLOWED_MESSAGES, mouseLParam } from './protocol.mjs';

export const VK_NOCHAR = 0xe8;
export const KEYUP_LPARAM = 0xc0000001;

const BUTTON_DOWN = new Set([0x201, 0x203, 0x204, 0x206, 0x207, 0x209]);
const BUTTON_UP = new Set([0x202, 0x205, 0x208]);

/**
 * @param {{kind:string,msg:number,x?:number,y?:number,wParam:number,lParam?:number}} input from parseInput()
 * @param {{panelX:number,panelY:number,clientX:number,clientY:number}} geo
 *        panel origin and client-area origin, both in screen coordinates
 * @param {boolean} tracking a button is held (state kept per client by the server)
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
