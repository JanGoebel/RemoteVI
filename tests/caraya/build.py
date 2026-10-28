"""Generate the RemoteVI Caraya unit tests from the shared test vectors (tests/vectors/*.json).

The vectors are the oracle. This script turns every vector into a constant inside a generated VI,
so a changed or added vector needs `python tests/caraya/build.py` to reach the G tests;
`--check` fails when the AIXML on disk no longer matches the vectors (run it in CI next to
`npm run vectors:check`).

Why the expected values are generated instead of read from JSON at run time: LabVIEW's own
Unflatten From JSON stops with error -375006 ("The cluster element was not found in the JSON
string") as soon as one object lacks a cluster element - measured on input.json, whose results
carry only the fields of their kind - and the vectors are heterogeneous by design (null results,
error-or-payload frames, optional cursor). JSONtext is installed but is a malleable-VI API the
pylabview composer cannot call.

Two layers, so the vector check itself runs without Caraya:

  support/RemoteVI Check <subject>.vi   calls the VI under test once per vector, renders expected
                                         and actual the same way (bytes as lowercase hex) and
                                         returns labels[], expected[], actual[] and failures.
  unit/<area>/Test <subject>.vi          Caraya test: Define Test, then one Assert Equal per vector
                                         with the vector's name as the assertion label.
  RemoteVI Caraya Runner.vi              runs every unit test, JUnit report (.xml) beside it or at
                                         `Report Path`.

The Caraya layer is only composed when Caraya is installed for the LabVIEW the VIs are saved
for (LabVIEW 2025): a test VI composed against another LabVIEW's Caraya stores an absolute link
into that installation and is broken here. `--caraya-dir` overrides the lookup.

Usage (any Python 3.10+; the composer itself runs in labview-mcp's bundled Python):
    python tests/caraya/build.py            generate AIXML and compose every VI
    python tests/caraya/build.py --aixml    generate AIXML only
    python tests/caraya/build.py --check    exit 1 when the AIXML is stale against the vectors
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
VEC = os.path.join(ROOT, "tests", "vectors")
AIXML_DIR = os.path.join(HERE, "aixml")
SUPPORT = os.path.join(HERE, "support")
UNIT = os.path.join(HERE, "unit")
COMPOSE = os.path.join(ROOT, "tools", "aixml", "compose.py")
LV_DIR = r"C:\Program Files\National Instruments\LabVIEW 2025"
CARAYA_REL = r"vi.lib\addons\_JKI Toolkits\Caraya"

HEX2B = "RemoteVI Test Hex To Bytes.vi"
B2HEX = "RemoteVI Test Bytes To Hex.vi"


# --------------------------------------------------------------------------- AIXML writing
def esc(s):
    """AIXML literal: every character that is not a letter or digit as \\XX. Structural
    characters of a literal (, [ ]) and leading/trailing spaces can then never be misread."""
    return "".join(c if c.isascii() and c.isalnum() else "\\%02X" % ord(c) for c in s)


def attr(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def lit(v):
    """Python value -> AIXML literal. str -> escaped, bool -> true/false, list/tuple -> [..]."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return esc(v)
    return "[" + ",".join(lit(x) for x in v) + "]"


class Doc:
    def __init__(self, name, description):
        self.name, self.description, self.lines, self.depth = name, description, [], 1

    def _emit(self, s):
        self.lines.append("  " * self.depth + s)

    def el(self, tag, **a):
        parts = []
        for k, v in a.items():
            if v is None:
                continue
            k = {"name_": "_name", "id_": "_id"}.get(k, k)
            if k == "uid":
                self.uids = getattr(self, "uids", set())
                if v in self.uids:
                    raise ValueError("%s: duplicate uid %r" % (self.name, v))
                self.uids.add(v)
            parts.append('%s="%s"' % (k, attr(v) if k not in ("inputs", "outputs") else v))
        self._emit("<%s %s/>" % (tag, " ".join(parts)))

    def el_uid(self, uid):
        self.uids = getattr(self, "uids", set())
        if uid in self.uids:
            raise ValueError("%s: duplicate uid %r" % (self.name, uid))
        self.uids.add(uid)

    @staticmethod
    def io(pairs):
        return ",".join("%s:%s" % (t, n) for t, n in pairs)

    def const(self, uid, typ, value, parent="root", label=None):
        self.el("Constant", name_=label, outputs="value:%s.v" % uid, type=typ, uid=uid, uid_parent=parent, value=value)
        return "%s.v" % uid

    def node(self, uid, name, ins, outs, parent="root", **extra):
        self.el("Node", name_=name, inputs=self.io(ins), outputs=self.io(outs), uid=uid, uid_parent=parent, **extra)

    def call(self, uid, target, ins, outs, parent="root"):
        self.el("Call", target=target, inputs=self.io(ins), outputs=self.io(outs), uid=uid, uid_parent=parent)

    def control(self, uid, name, typ, con, value, description, connection="required"):
        self.el("Control", name_=name, conIdx=str(con), connection=connection, description=description,
                outputs="value:%s.v" % uid, type=typ, uid=uid, uid_parent="root", value=value)
        return "%s.v" % uid

    def indicator(self, uid, name, typ, con, net, value, description):
        self.el("Indicator", name_=name, conIdx=str(con), connection="recommended", description=description,
                inputs="value:%s" % net, type=typ, uid=uid, uid_parent="root", value=value)

    def label(self, uid, text, parent="root"):
        self.el("FreeLabel", comment=text, uid=uid, uid_parent=parent)

    def loop_open(self, uid, label, parent="root", count="", maxin=""):
        self.el_uid(uid)
        self._emit('<Structure _name="For Loop" count="%s" label="%s" maxin="%s" maxout="" uid="%s" uid_parent="%s">'
                   % (count, attr(label), maxin, uid, parent))
        self.depth += 1
        self.tin, self.tout = getattr(self, "tin", []), getattr(self, "tout", [])
        self.tin.append(0)
        self.tout.append(0)

    def loop_close(self):
        self.depth -= 1
        self.tin.pop()
        self.tout.pop()
        self._emit("</Structure>")

    def tunnel_in(self, uid, loop, net, index=True):
        self.tin[-1] += 1
        self.el("Tunnel", id_="In%d" % self.tin[-1], inputs="value:%s" % net, mode="index" if index else None,
                outputs="value:%s.v" % uid, uid=uid, uid_parent=loop)
        return "%s.v" % uid

    def tunnel_out(self, uid, loop, net):
        self.tout[-1] += 1
        self.el("Tunnel", id_="Out%d" % self.tout[-1], inputs="value:%s" % net, mode="index",
                outputs="value:%s.v" % uid, uid=uid, uid_parent=loop)
        return "%s.v" % uid

    # small rendering helpers -------------------------------------------------------------
    def dec(self, uid, net, parent):
        self.node(uid, "Number To Decimal String", [("number", net)], [("decimal integer string", uid + ".v")], parent)
        return uid + ".v"

    def concat(self, uid, nets, parent):
        self.node(uid, "Concatenate Strings", [("string", n) for n in nets], [("concatenated string", uid + ".v")], parent)
        return uid + ".v"

    def tf(self, uid, net, parent, t="T", f="F"):
        a = self.const(uid + "t", "string", esc(t), parent)
        b = self.const(uid + "f", "string", esc(f), parent)
        self.node(uid, "Select", [("t", a), ("s", net), ("f", b)], [("s? t\\3Af", uid + ".v")], parent)
        return uid + ".v"

    def s(self, uid, text, parent):
        return self.const(uid, "string", esc(text), parent)

    def hex(self, uid, net, parent):
        self.call(uid, B2HEX, [("bytes", net)], [("hex", uid + ".v")], parent)
        return uid + ".v"

    def unhex(self, uid, net, parent):
        self.call(uid, HEX2B, [("hex", net)], [("bytes", uid + ".v")], parent)
        return uid + ".v"

    def text(self):
        return '<VI _name="%s" description="%s">\r\n%s\r\n</VI>\r\n' % (
            attr(self.name), attr(self.description.replace("\\", "\\5C")), "\r\n".join(self.lines))


# --------------------------------------------------------------------------- support VIs
def hex_to_bytes():
    d = Doc(HEX2B, "Test support: decodes a lowercase hex string (as written in tests/vectors) into "
                   "the bytes it stands for. Two hex digits per byte; digits 0-9 and a-f. Pure.")
    hx = d.control("hex", "hex", "string", 0, "", "Lowercase hex, two digits per byte.")
    d.node("sba", "String To Byte Array", [("string", hx)], [("unsigned byte array", "sba.v")])
    d.node("tl", "To Long Integer", [("number", "sba.v")], [("32bit integer", "tl.v")])
    k48 = d.const("k48", "int32", "48")
    k39 = d.const("k39", "int32", "39")
    k16 = d.const("k16", "int32", "16")
    d.node("sub", "Subtract", [("x", "tl.v"), ("y", k48)], [("x-y", "sub.v")])
    d.label("lb", "(c - 48) mod 39: 0-9 and a-f to 0..15")
    d.node("nib", "Quotient & Remainder", [("x", "sub.v"), ("y", k39)],
           [("x-y*floor(x/y)", "nib.v"), ("floor(x/y)", "")])
    d.node("asz", "Array Size", [("array", "nib.v")], [("size(s)", "asz.v")])
    k2 = d.const("k2", "int32", "2")
    d.node("half", "Quotient & Remainder", [("x", "asz.v"), ("y", k2)],
           [("x-y*floor(x/y)", ""), ("floor(x/y)", "half.v")])
    d.node("rs", "Reshape Array", [("array", "nib.v"), ("dimension size", "half.v"), ("dimension size", k2)],
           [("output array", "rs.v")])
    d.loop_open("H", "One byte per digit pair")
    row = d.tunnel_in("tn", "H", "rs.v")
    t16 = d.tunnel_in("t16", "H", k16, index=False)
    k0 = d.const("k0", "int32", "0", "H")
    k1 = d.const("k1", "int32", "1", "H")
    d.node("ix", "Index Array", [("array", row), ("index", k0), ("index", k1)],
           [("element", "ix.hi"), ("element", "ix.lo")], "H")
    d.node("m16", "Multiply", [("x", "ix.hi"), ("y", t16)], [("x*y", "m16.v")], "H")
    d.node("add", "Add", [("x", "m16.v"), ("y", "ix.lo")], [("x+y", "add.v")], "H")
    d.node("u8", "To Unsigned Byte Integer", [("number", "add.v")], [("unsigned 8bit integer", "u8.v")], "H")
    d.tunnel_out("ub", "H", "u8.v")
    d.loop_close()
    d.node("bas", "Byte Array To String", [("unsigned byte array", "ub.v")], [("string", "bas.v")])
    d.indicator("bytes", "bytes", "string", 4, "bas.v", "", "The decoded bytes.")
    return d


def bytes_to_hex():
    d = Doc(B2HEX, "Test support: renders bytes as lowercase hex, two digits per byte, the notation "
                   "of tests/vectors. Pure.")
    by = d.control("bytes", "bytes", "string", 0, "", "Any bytes.")
    d.node("sba", "String To Byte Array", [("string", by)], [("unsigned byte array", "sba.v")])
    k16 = d.const("k16", "uint8", "16")
    k9 = d.const("k9", "uint8", "9")
    k48 = d.const("k48", "uint8", "48")
    k39 = d.const("k39", "uint8", "39")
    d.node("qr", "Quotient & Remainder", [("x", "sba.v"), ("y", k16)],
           [("x-y*floor(x/y)", "qr.lo"), ("floor(x/y)", "qr.hi")])
    for n in ("hi", "lo"):
        d.node("g" + n, "Greater?", [("x", "qr." + n), ("y", k9)], [("x > y?", "g%s.v" % n)])
        d.node("b" + n, "Boolean To (0\\2C1)", [("Boolean", "g%s.v" % n)], [("0\\2C 1", "b%s.v" % n)])
        d.node("m" + n, "Multiply", [("x", "b%s.v" % n), ("y", k39)], [("x*y", "m%s.v" % n)])
        d.node("a" + n, "Add", [("x", "qr." + n), ("y", k48)], [("x+y", "a%s.v" % n)])
        d.node("c" + n, "Add", [("x", "a%s.v" % n), ("y", "m%s.v" % n)], [("x+y", "c%s.v" % n)])
        d.node("u" + n, "To Unsigned Byte Integer", [("number", "c%s.v" % n)], [("unsigned 8bit integer", "u%s.v" % n)])
    d.node("il", "Interleave 1D Arrays", [("array", "uhi.v"), ("array", "ulo.v")], [("interleaved array", "il.v")])
    d.node("bas", "Byte Array To String", [("unsigned byte array", "il.v")], [("string", "bas.v")])
    d.indicator("hex", "hex", "string", 4, "bas.v", "", "Lowercase hex, two digits per byte.")
    return d


# --------------------------------------------------------------------------- check VIs
CHECK_OUT_DOC = ("Outputs, one element per vector: labels (the vector's name), expected (rendered "
                 "from the vector), actual (the VI's result rendered the same way), and failures, "
                 "the number of vectors whose expected and actual differ.")


def check_doc(subject, vecfile, what):
    return Doc("RemoteVI Check %s.vi" % subject,
               "Test support, generated by tests/caraya/build.py from tests/vectors/%s - do not edit. "
               "Calls RemoteVI %s.vi once per vector: %s %s" % (vecfile, subject, what, CHECK_OUT_DOC))


def finish_check(d, labels, expected, actual):
    """labels/expected/actual are array nets at top level. Adds failures and the indicators."""
    d.node("neq", "Not Equal?", [("x", expected), ("y", actual)], [("x != y?", "neq.v")])
    d.node("n01", "Boolean To (0\\2C1)", [("Boolean", "neq.v")], [("0\\2C 1", "n01.v")])
    d.node("nsum", "Add Array Elements", [("numeric array", "n01.v")], [("sum", "nsum.v")])
    d.indicator("o_lab", "labels", "array{string}", 4, labels, "[]", "Vector names, one per vector.")
    d.indicator("o_exp", "expected", "array{string}", 6, expected, "[]", "Expected result per vector, rendered as text.")
    d.indicator("o_act", "actual", "array{string}", 8, actual, "[]", "Actual result per vector, rendered the same way.")
    d.indicator("o_fail", "failures", "int32", 10, "nsum.v", "0", "Number of vectors whose expected and actual differ.")


def cases_loop(d, ctype, cases, fields, label):
    """Constant array of case clusters, loop indexing it, Unbundle By Name. Returns dict field->net."""
    d.const("cases", "array{cluster{%s}}" % ctype, lit(cases), label="vectors")
    d.loop_open("L", label)
    c = d.tunnel_in("tc", "L", "cases.v")
    d.node("ub", "Unbundle By Name", [("input cluster", c)], [(f, "ub." + f) for f in fields], "L", fields=",".join(fields))
    return {f: "ub." + f for f in fields}


def close_cases(d, label_net, expect_net, actual_net):
    d.tunnel_out("lab", "L", label_net)
    d.tunnel_out("exp", "L", expect_net)
    d.tunnel_out("act", "L", actual_net)
    d.loop_close()
    return "lab.v", "exp.v", "act.v"


def check_frame_like(subject, vecfile, key, input_name):
    vec = json.load(open(os.path.join(VEC, vecfile)))
    cases = []
    for c in vec[key]:
        items = c["popups"] if key == "overlays" else c["rects"]
        rects = [(r["x"], r["y"], r["png"]) for r in items]
        if key == "cases":
            cases.append((c["name"], c["seq"], c["width"], c["height"], rects, c["message"]))
        elif key == "windowFrames":
            cases.append((c["name"], c["id"], c["seq"], c["width"], c["height"], rects, c["message"]))
        else:
            cases.append((c["name"], rects, c["message"]))
    rtype = "array{cluster{int16.x,int16.y,string.png}}.%s" % input_name
    if key == "cases":
        ctype = "string.name,uint32.seq,uint16.width,uint16.height,%s,string.message" % rtype
        fields = ["name", "seq", "width", "height", input_name, "message"]
    elif key == "windowFrames":
        ctype = "string.name,uint32.id,uint32.seq,uint16.width,uint16.height,%s,string.message" % rtype
        fields = ["name", "id", "seq", "width", "height", input_name, "message"]
    else:
        ctype = "string.name,%s,string.message" % rtype
        fields = ["name", input_name, "message"]
    d = check_doc(subject, vecfile, "the png fields are hex in the vector and decoded to bytes before "
                  "the call; the message is compared as lowercase hex.")
    f = cases_loop(d, ctype, cases, fields, "One vector")
    d.loop_open("R", "Decode png hex", "L")
    r = d.tunnel_in("tr", "R", f[input_name])
    d.node("ubr", "Unbundle By Name", [("input cluster", r)], [("png", "ubr.png")], "R", fields="png")
    png = d.unhex("uh", "ubr.png", "R")
    d.node("bn", "Bundle By Name", [("input cluster", r), ("png", png)], [("output cluster", "bn.v")], "R", fields="png")
    rr = d.tunnel_out("rr", "R", "bn.v")
    d.loop_close()
    if key == "cases":
        d.call("sut", "RemoteVI %s.vi" % subject,
               [("seq", f["seq"]), ("width", f["width"]), ("height", f["height"]), ("rects", rr)],
               [("message", "sut.v")], "L")
    elif key == "windowFrames":
        d.call("sut", "RemoteVI %s.vi" % subject,
               [("id", f["id"]), ("seq", f["seq"]), ("width", f["width"]), ("height", f["height"]), ("rects", rr)],
               [("message", "sut.v")], "L")
    else:
        d.call("sut", "RemoteVI %s.vi" % subject, [("popups", rr)], [("message", "sut.v")], "L")
    act = d.hex("hx", "sut.v", "L")
    finish_check(d, *close_cases(d, f["name"], f["message"], act))
    return d


def check_parse():
    vec = json.load(open(os.path.join(VEC, "input.json")))
    cases = [("Parse '%s'" % c["text"], c["text"], render_parse(c["result"])) for c in vec["cases"]]
    d = check_doc("Parse Input", "input.json", "a null result is kind invalid; the other outputs are "
                  "compared only where the vector's result names them (mouse: msg x y wParam, key: msg "
                  "wParam lParam, ack: seq, close: id, splitter: id and x as pos).")
    f = cases_loop(d, "string.name,string.text,string.expect", cases, ["name", "text", "expect"], "One vector")
    o = render_parse_g(d, f["text"], "L")
    finish_check(d, *close_cases(d, f["name"], f["expect"], o))
    return d


def render_parse(r):
    if r is None:
        return "invalid"
    if r["kind"] == "mouse":
        return "mouse msg=%d x=%d y=%d wParam=%d" % (r["msg"], r["x"], r["y"], r["wParam"] % 2**64)
    if r["kind"] == "key":   # wParam is U64 on the pane: a negative vector value wraps (0xFFFFFFFF80000000)
        return "key msg=%d wParam=%d lParam=%d" % (r["msg"], r["wParam"] % 2**64, r["lParam"])
    if r["kind"] == "ack":
        return "ack seq=%d" % r["seq"]
    if r["kind"] == "close":
        return "close id=%d" % r["id"]
    if r["kind"] == "splitter":
        return "splitter id=%d pos=%d" % (r["id"], r["pos"])
    raise ValueError(r)


def parse_call(d, text_net, parent):
    d.call("pi", "RemoteVI Parse Input.vi", [("text", text_net)],
           [("kind", "pi.kind"), ("msg", "pi.msg"), ("x", "pi.x"), ("y", "pi.y"),
            ("wParam", "pi.wParam"), ("lParam", "pi.lParam"), ("seq", "pi.seq"), ("id", "pi.id")], parent)


def render_parse_g(d, text_net, parent):
    parse_call(d, text_net, parent)
    n = {k: d.dec("d" + k, "pi." + k, parent) for k in ("msg", "x", "y", "wParam", "lParam", "seq", "id")}
    mouse = d.concat("cm", [d.s("sm1", "mouse msg=", parent), n["msg"], d.s("sm2", " x=", parent), n["x"],
                            d.s("sm3", " y=", parent), n["y"], d.s("sm4", " wParam=", parent), n["wParam"]], parent)
    key = d.concat("ck", [d.s("sk1", "key msg=", parent), n["msg"], d.s("sk2", " wParam=", parent), n["wParam"],
                          d.s("sk3", " lParam=", parent), n["lParam"]], parent)
    ack = d.concat("ca", [d.s("sa1", "ack seq=", parent), n["seq"]], parent)
    close = d.concat("cx", [d.s("sx1", "close id=", parent), n["id"]], parent)
    split = d.concat("cq", [d.s("sq1", "splitter id=", parent), n["id"], d.s("sq2", " pos=", parent), n["x"]], parent)
    inv = d.s("si", "invalid", parent)
    d.node("ba", "Build Array", [("element", inv), ("element", mouse), ("element", key), ("element", ack), ("element", close),
                                 ("element", split)],
           [("appended array", "ba.v")], parent)
    d.node("ki", "To Long Integer", [("number", "pi.kind")], [("32bit integer", "ki.v")], parent)
    d.node("ix", "Index Array", [("array", "ba.v"), ("index", "ki.v")], [("element", "ix.v")], parent)
    return "ix.v"


def check_ws_encode():
    vec = json.load(open(os.path.join(VEC, "websocket.json")))
    cases = []
    for c in vec["serverFrames"]:
        if "payloadLength" in c:   # payload of payloadLength zero bytes, only the header is given
            cases.append((c["name"], c["opcode"], "", c["payloadLength"], c["header"], len(c["header"])))
        else:
            cases.append((c["name"], c["opcode"], c["payload"], -1, c["frame"], -1))
    d = check_doc("WS Encode Server Frame", "websocket.json (serverFrames)",
                  "payload is the vector's hex, or payloadLength zero bytes where the vector gives only "
                  "the header; the frame is compared as lowercase hex, only its first bytes where the "
                  "vector gives a header.")
    f = cases_loop(d, "string.name,uint8.opcode,string.payload,int32.zeros,string.expect,int32.cmp",
                   cases, ["name", "opcode", "payload", "zeros", "expect", "cmp"], "One vector")
    pl = d.unhex("uh", f["payload"], "L")
    z = d.const("z8", "uint8", "0", "L")
    d.node("ia", "Initialize Array", [("element", z), ("dimension size", f["zeros"])], [("initialized array", "ia.v")], "L")
    d.node("zs", "Byte Array To String", [("unsigned byte array", "ia.v")], [("string", "zs.v")], "L")
    zero = d.const("z0", "int32", "0", "L")
    d.node("hz", "Less?", [("x", f["zeros"]), ("y", zero)], [("x &lt; y?", "hz.v")], "L")
    d.node("sp", "Select", [("t", pl), ("s", "hz.v"), ("f", "zs.v")], [("s? t\\3Af", "sp.v")], "L")
    d.call("sut", "RemoteVI WS Encode Server Frame.vi", [("opcode", f["opcode"]), ("payload", "sp.v")],
           [("frame", "sut.v")], "L")
    hx = d.hex("hx", "sut.v", "L")
    d.node("sl", "String Length", [("string", hx)], [("length", "sl.v")], "L")
    d.node("hc", "Less?", [("x", f["cmp"]), ("y", zero)], [("x &lt; y?", "hc.v")], "L")
    d.node("ln", "Select", [("t", "sl.v"), ("s", "hc.v"), ("f", f["cmp"])], [("s? t\\3Af", "ln.v")], "L")
    d.node("ss", "String Subset", [("string", hx), ("offset (0)", zero), ("length (rest)", "ln.v")],
           [("substring", "ss.v")], "L")
    finish_check(d, *close_cases(d, f["name"], f["expect"], "ss.v"))
    return d


def check_ws_decode():
    vec = json.load(open(os.path.join(VEC, "websocket.json")))
    cases = []
    for c in vec["clientFrames"]:
        if "error" in c:
            cases.append((c["name"], c["frame"], False, "complete=F close=%d" % c["error"]))
        else:
            cases.append((c["name"], c["frame"], True, "complete=T fin=%s opcode=%d payload=%s consumed=%d close=0" % (
                "T" if c["fin"] else "F", c["opcode"], c["payload"], len(c["frame"]) // 2)))
    for h in vec["incompleteClientFrames"]:
        cases.append(("incomplete prefix '%s'" % h, h, False, "complete=F close=0"))
    d = check_doc("WS Decode Client Frame", "websocket.json (clientFrames, incompleteClientFrames)",
                  "a valid frame must decode completely with its fin, opcode and payload, bytes consumed = "
                  "the frame length (as the JS tests assert) and close code 0; an invalid frame must give "
                  "complete? FALSE and the vector's close code; an incomplete prefix complete? FALSE and close "
                  "code 0. max payload keeps its default (65536, the JS limit).")
    f = cases_loop(d, "string.name,string.frame,bool.full,string.expect", cases,
                   ["name", "frame", "full", "expect"], "One vector")
    buf = d.unhex("uh", f["frame"], "L")
    d.call("sut", "RemoteVI WS Decode Client Frame.vi", [("buffer", buf), ("max payload", "")],
           [("complete?", "sut.cmp"), ("fin", "sut.fin"), ("opcode", "sut.op"), ("payload", "sut.pl"),
            ("bytes consumed", "sut.n"), ("close code", "sut.cc")], "L")
    cmp_ = d.tf("tcm", "sut.cmp", "L")
    fin = d.tf("tf", "sut.fin", "L")
    cc = d.dec("dcc", "sut.cc", "L")
    full = d.concat("cf", [d.s("f1", "complete=", "L"), cmp_, d.s("f2", " fin=", "L"), fin,
                           d.s("f3", " opcode=", "L"), d.dec("dop", "sut.op", "L"),
                           d.s("f4", " payload=", "L"), d.hex("hp", "sut.pl", "L"),
                           d.s("f5", " consumed=", "L"), d.dec("dn", "sut.n", "L"),
                           d.s("f6", " close=", "L"), cc], "L")
    short = d.concat("cs", [d.s("s1", "complete=", "L"), cmp_, d.s("s2", " close=", "L"), cc], "L")
    d.node("sel", "Select", [("t", full), ("s", f["full"]), ("f", short)], [("s? t\\3Af", "sel.v")], "L")
    finish_check(d, *close_cases(d, f["name"], f["expect"], "sel.v"))
    return d


def render_rects(rects):
    return "".join("%d,%d,%d,%d;" % (r["x"], r["y"], r["w"], r["h"]) for r in rects)


def check_dirty_rects():
    vec = json.load(open(os.path.join(VEC, "rects.json")))
    cases = [(c["name"], c["hasPrev"], c["cur"], render_rects(c["rects"])) for c in vec["cases"]]
    d = check_doc("Dirty Rects", "rects.json", "the vector's row-major pixels are reshaped to "
                  "[height][width]; no previous capture is an empty previous array; rects are rendered "
                  "x,y,w,h; in output order.")
    W, H = d.const("w", "int32", str(vec["width"]), label="width"), d.const("h", "int32", str(vec["height"]), label="height")
    ts = d.const("ts", "int32", str(vec["tileSize"]), label="tile size")
    prev = d.const("prev", "array{uint32}", lit(vec["prev"]), label="prev")
    d.node("rp", "Reshape Array", [("array", prev), ("dimension size", H), ("dimension size", W)], [("output array", "rp.v")])
    empty = d.const("e2", "array.2{uint32}", "[]", label="no previous capture")
    f = cases_loop(d, "string.name,bool.hasPrev,array{uint32}.cur,string.expect", cases,
                   ["name", "hasPrev", "cur", "expect"], "One vector")
    tp = d.tunnel_in("tp", "L", "rp.v", index=False)
    te = d.tunnel_in("te", "L", empty, index=False)
    tw = d.tunnel_in("tw", "L", W, index=False)
    th = d.tunnel_in("th", "L", H, index=False)
    tt = d.tunnel_in("tt", "L", ts, index=False)
    d.node("rc", "Reshape Array", [("array", f["cur"]), ("dimension size", th), ("dimension size", tw)],
           [("output array", "rc.v")], "L")
    d.node("sp", "Select", [("t", tp), ("s", f["hasPrev"]), ("f", te)], [("s? t\\3Af", "sp.v")], "L")
    d.call("sut", "RemoteVI Dirty Rects.vi", [("previous", "sp.v"), ("current", "rc.v"), ("tile size", tt)],
           [("rects", "sut.v")], "L")
    d.loop_open("R", "One rect", "L")
    r = d.tunnel_in("tr", "R", "sut.v")
    d.node("ubr", "Unbundle By Name", [("input cluster", r)],
           [("x", "ubr.x"), ("y", "ubr.y"), ("w", "ubr.w"), ("h", "ubr.h")], "R", fields="x,y,w,h")
    comma = d.s("cm", ",", "R")
    rs = d.concat("rs", [d.dec("dx", "ubr.x", "R"), comma, d.dec("dy", "ubr.y", "R"), comma,
                         d.dec("dw", "ubr.w", "R"), comma, d.dec("dh", "ubr.h", "R"), d.s("sc", ";", "R")], "R")
    d.tunnel_out("ro", "R", rs)
    d.loop_close()
    act = d.concat("all", ["ro.v"], "L")
    finish_check(d, *close_cases(d, f["name"], f["expect"], act))
    return d


def render_translate(c):
    posts = "".join("%d:%d:%d;" % (p["msg"], p["wParam"], p["lParam"]) for p in c["posts"])
    cur = "-" if c["cursor"] is None else "%d,%d" % (c["cursor"]["x"], c["cursor"]["y"])
    return "posts=%s tracking=%s cursor=%s" % (posts, "T" if c["trackingAfter"] else "F", cur)


def check_translate():
    vec = json.load(open(os.path.join(VEC, "translate.json")))
    g = vec["geo"]
    cases = [(c["name"], c["input"], c["popup"], c["trackingBefore"], render_translate(c)) for c in vec["cases"]]
    d = check_doc("Translate Input", "translate.json (cases)", "the vector's input text goes through "
                  "RemoteVI Parse Input.vi first, geo is the vector's geo, tracking in is trackingBefore; "
                  "posts are rendered msg:wParam:lParam; each, cursor as x,y or - when the vector's cursor "
                  "is null (move? FALSE).")
    geo = d.const("geo", "cluster{int32.panelX,int32.panelY,int32.clientX,int32.clientY}",
                  lit([g["panelX"], g["panelY"], g["clientX"], g["clientY"]]), label="geo")
    f = cases_loop(d, "string.name,string.input,bool.popup,bool.trackingBefore,string.expect", cases,
                   ["name", "input", "popup", "trackingBefore", "expect"], "One vector")
    tg = d.tunnel_in("tg", "L", geo, index=False)
    parse_call(d, f["input"], "L")
    d.call("sut", "RemoteVI Translate Input.vi",
           [("kind", "pi.kind"), ("msg", "pi.msg"), ("x", "pi.x"), ("y", "pi.y"), ("wParam", "pi.wParam"),
            ("lParam", "pi.lParam"), ("geo", tg), ("popup", f["popup"]), ("tracking in", f["trackingBefore"])],
           [("posts", "sut.posts"), ("tracking out", "sut.tr"), ("cursor", "sut.cur")], "L")
    d.loop_open("R", "One post", "L")
    p = d.tunnel_in("tp", "R", "sut.posts")
    d.node("ubp", "Unbundle By Name", [("input cluster", p)],
           [("msg", "ubp.msg"), ("wParam", "ubp.wParam"), ("lParam", "ubp.lParam")], "R", fields="msg,wParam,lParam")
    colon = d.s("co", ":", "R")
    ps = d.concat("ps", [d.dec("pm", "ubp.msg", "R"), colon, d.dec("pw", "ubp.wParam", "R"), colon,
                         d.dec("pl", "ubp.lParam", "R"), d.s("sc", ";", "R")], "R")
    d.tunnel_out("po", "R", ps)
    d.loop_close()
    posts = d.concat("pall", ["po.v"], "L")
    d.node("ubc", "Unbundle By Name", [("input cluster", "sut.cur")],
           [("move?", "ubc.mv"), ("x", "ubc.x"), ("y", "ubc.y")], "L", fields="move?,x,y")
    xy = d.concat("cxy", [d.dec("cx", "ubc.x", "L"), d.s("cc", ",", "L"), d.dec("cy", "ubc.y", "L")], "L")
    d.node("csel", "Select", [("t", xy), ("s", "ubc.mv"), ("f", d.s("cd", "-", "L"))], [("s? t\\3Af", "csel.v")], "L")
    act = d.concat("actv", [d.s("a1", "posts=", "L"), posts, d.s("a2", " tracking=", "L"), d.tf("ttr", "sut.tr", "L"),
                           d.s("a3", " cursor=", "L"), "csel.v"], "L")
    finish_check(d, *close_cases(d, f["name"], f["expect"], act))
    return d


def check_track_modifiers():
    vec = json.load(open(os.path.join(VEC, "translate.json")))
    cases = [(c["name"], c["input"], c["modsBefore"], str(c["modsAfter"])) for c in vec["modifiers"]]
    d = check_doc("Track Modifiers", "translate.json (modifiers)", "the vector's input text goes through "
                  "RemoteVI Parse Input.vi first, mods in is modsBefore, mods out is compared with modsAfter.")
    f = cases_loop(d, "string.name,string.input,uint8.modsBefore,string.expect", cases,
                   ["name", "input", "modsBefore", "expect"], "One vector")
    parse_call(d, f["input"], "L")
    d.call("sut", "RemoteVI Track Modifiers.vi",
           [("kind", "pi.kind"), ("msg", "pi.msg"), ("wParam", "pi.wParam"), ("mods in", f["modsBefore"])],
           [("mods out", "sut.v")], "L")
    act = d.dec("dm", "sut.v", "L")
    finish_check(d, *close_cases(d, f["name"], f["expect"], act))
    return d


def check_string_out(subject, vecfile, what, ctype, cases, inputs, output="message"):
    """A pure VI whose result is a string: cases are (name, *inputs, expect); inputs names the
    case fields in the order of the cluster after name and before expect, each wired to the
    subject's terminal of that name. Expected and actual are compared as the strings they are."""
    d = check_doc(subject, vecfile, what)
    fields = ["name"] + inputs + ["expect"]
    f = cases_loop(d, "string.name,%s,string.expect" % ctype, cases, fields, "One vector")
    d.call("sut", "RemoteVI %s.vi" % subject, [(i, f[i]) for i in inputs], [(output, "sut.v")], "L")
    finish_check(d, *close_cases(d, f["name"], f["expect"], "sut.v"))
    return d


def check_json_string():
    vec = json.load(open(os.path.join(VEC, "text.json")))
    cases = [(c["name"], c["text"], c["json"]) for c in vec["jsonStrings"]]
    return check_string_out("JSON String", "text.json (jsonStrings)", "text is the vector's UTF-16 code units, "
                            "json is compared as the string literal it is.", "array{uint16}.text", cases, ["text"], "json")


def check_tips_message():
    vec = json.load(open(os.path.join(VEC, "text.json")))
    # The VI widens each byte of a tip text to one code unit: the vectors' texts are all below 0x100.
    cases = [(c["name"], [(t["x"], t["y"], t["w"], t["h"], "".join(chr(u) for u in t["text"])) for t in c["tips"]],
              c["message"]) for c in vec["tips"]]
    return check_string_out("Tips Message", "text.json (tips)", "each tip's text is the vector's code units as "
                            "bytes (all below 0x100); the message is compared as the string it is.",
                            "array{cluster{int32.x,int32.y,int32.w,int32.h,string.text}}.tips", cases, ["tips"])


def check_splitters_message():
    vec = json.load(open(os.path.join(VEC, "text.json")))
    cases = [(c["name"], [(b["x"], b["y"], b["w"], b["h"], b["vertical"], b["min"], b["max"]) for b in c["bars"]],
              c["message"]) for c in vec["splitters"]]
    return check_string_out("Splitters Message", "text.json (splitters)", "the message is compared as the string it is.",
                            "array{cluster{int32.x,int32.y,int32.w,int32.h,bool.vertical,int32.min,int32.max}}.bars",
                            cases, ["bars"])


def check_token_check():
    vec = json.load(open(os.path.join(VEC, "http.json")))
    cases = [(c["name"], c["query"], "" if c.get("emptyToken") else vec["token"], "T" if c["ok"] else "F")
             for c in vec["tokens"]]
    d = check_doc("Token Check", "http.json (tokens)", "query and token as in the vector (the vector's token, or "
                  "empty for emptyToken); ok? is rendered T or F.")
    f = cases_loop(d, "string.name,string.query,string.token,string.expect", cases, ["name", "query", "token", "expect"],
                   "One vector")
    d.call("sut", "RemoteVI Token Check.vi", [("query", f["query"]), ("token", f["token"])], [("ok?", "sut.v")], "L")
    act = d.tf("tok", "sut.v", "L")
    finish_check(d, *close_cases(d, f["name"], f["expect"], act))
    return d


def check_format_duration():
    vec = json.load(open(os.path.join(VEC, "status.json")))
    cases = [("%s s" % c["seconds"], float(c["seconds"]), c["text"]) for c in vec["durations"]]
    return check_string_out("Format Duration", "status.json (durations)", "the text is compared as the string it is.",
                            "double.seconds", cases, ["seconds"], "text")


OUT_FIELDS = ("port", "url", "target", "kind", "wholeNetwork", "running", "uptime", "clients", "fps", "kBps",
              "frames", "latencyMs", "viewOnly", "lastError", "hWnd")
OUT_TYPE = ("array{cluster{uint16.port,string.url,string.target,string.kind,bool.whole network,bool.running,"
            "double.uptime s,array{cluster{string.address,double.connected s,double.idle s}}.clients,double.fps,"
            "double.kB per s,uint32.frames,double.latency ms,bool.view only,string.last error,uint64.hWnd}}")
RAW_TYPE = ("array{cluster{uint16.port,string.url,string.target,string.kind,bool.whole network,double.started,"
            "double.updated,array{cluster{string.address,double.since,double.last input}}.clients,double.fps,"
            "double.bytes per s,uint32.frames,double.latency ms,bool.view only,string.last error,uint64.hWnd}}")


def out_tuple(s):
    return tuple([(c["address"], float(c["connected"]), float(c["idle"])) for c in s["clients"]]
                 if k == "clients" else float(s[k]) if isinstance(s[k], float) else s[k] for k in OUT_FIELDS)


def check_status_text():
    vec = json.load(open(os.path.join(VEC, "status.json")))
    cases = [(c["name"], [out_tuple(s) for s in c["status"]], c["text"]) for c in vec["texts"]]
    return check_string_out("Status Text", "status.json (texts)", "the text is compared as the string it is (lines "
                            "joined with a line feed).", OUT_TYPE + ".status", cases, ["status"], "text")


def check_status_convert():
    vec = json.load(open(os.path.join(VEC, "status.json")))
    cv = vec["convert"]
    raw = [tuple([(c["address"], float(c["since"]), float(c["lastInput"])) for c in r["clients"]] if k == "clients"
                 else float(r[k]) if k in ("started", "updated", "fps", "bytesPerS", "latencyMs") else r[k]
                 for k in ("port", "url", "target", "kind", "wholeNetwork", "started", "updated", "clients", "fps",
                           "bytesPerS", "frames", "latencyMs", "viewOnly", "lastError", "hWnd")) for r in cv["raw"]]
    # Rendered through RemoteVI Status Text.vi: the vector's converted status gives the expected text.
    import subprocess as _sp
    expect = _sp.run(["node", "-e", "import('./tools/lib/status.mjs').then(m=>process.stdout.write("
                      "m.statusText(%s)))" % json.dumps(cv["status"])], capture_output=True, text=True, cwd=ROOT).stdout
    d = check_doc("Status Convert", "status.json (convert)", "raw and now as in the vector; the status is "
                  "rendered with RemoteVI Status Text.vi and compared with the text of the vector's status.")
    f = cases_loop(d, "string.name,%s.raw,double.now,string.expect" % RAW_TYPE, [("convert", raw, float(cv["now"]), expect)],
                   ["name", "raw", "now", "expect"], "One vector")
    d.call("sut", "RemoteVI Status Convert.vi", [("raw", f["raw"]), ("now", f["now"])], [("status", "sut.v")], "L")
    d.call("txt", "RemoteVI Status Text.vi", [("status", "sut.v")], [("text", "txt.v")], "L")
    finish_check(d, *close_cases(d, f["name"], f["expect"], "txt.v"))
    return d


RAW_WIN_TYPE = ("array{cluster{uint64.hWnd,uint32.pid,string.path,string.class,string.title,bool.visible,bool.owned,"
                "uint32.ex style,int32.w,int32.h}}")


def check_window_rows():
    vec = json.load(open(os.path.join(VEC, "server-app.json")))
    raw = [(w["hWnd"], w["pid"], w["path"], w["cls"], w["title"], w["visible"], w["owned"], w["exStyle"], w["w"], w["h"])
           for w in vec["raw"]]
    cases = [(c["name"], raw, c["labviewOnly"], c["skip"], "".join(r + "\n" for r in c["rows"])) for c in vec["windowRows"]]
    d = check_doc("Window Rows", "server-app.json (windowRows)", "raw, labview only? and skip as in the vector; "
                  "each row is rendered group|program|title|pid|hWnd with a line feed after it.")
    f = cases_loop(d, "string.name,%s.raw,bool.lvo,uint64.skip,string.expect" % RAW_WIN_TYPE, cases,
                   ["name", "raw", "lvo", "skip", "expect"], "One vector")
    d.call("sut", "RemoteVI Window Rows.vi", [("raw", f["raw"]), ("labview only?", f["lvo"]), ("skip", f["skip"])],
           [("rows", "sut.v")], "L")
    d.const("rf", "string", esc("%d|%s|%s|%d|%d\n"), "L")
    d.loop_open("R", "One line per row", parent="L")
    r = d.tunnel_in("tr", "R", "sut.v")
    rf = d.tunnel_in("trf", "R", "rf.v", index=False)
    d.node("ru", "Unbundle By Name", [("input cluster", r)], [(k, "ru." + k.replace(" ", "")) for k in
           ("group", "program", "title", "pid", "hWnd")], "R", fields="group,program,title,pid,hWnd")
    d.node("rl", "Format Into String", [("format string", rf), ("input 1", "ru.group"), ("input 2", "ru.program"),
           ("input 3", "ru.title"), ("input 4", "ru.pid"), ("input 5", "ru.hWnd")], [("resulting string", "rl.v")], "R")
    d.tunnel_out("lines", "R", "rl.v")
    d.loop_close()
    act = d.concat("all", ["lines.v"], "L")
    finish_check(d, *close_cases(d, f["name"], f["expect"], act))
    return d


def check_landing_page():
    vec = json.load(open(os.path.join(VEC, "server-app.json")))
    cases = [(c["name"], [out_tuple(st) for st in c["status"]], c["html"]) for c in vec["landing"]]
    return check_string_out("Landing Page", "server-app.json (landing)", "the page is compared as the string it is.",
                            OUT_TYPE + ".status", cases, ["status"], "html")


def check_next_free_port():
    vec = json.load(open(os.path.join(VEC, "server-app.json")))
    cases = [("%s from %d" % (c["used"], c["start"]), c["used"], c["start"], str(c["port"])) for c in vec["nextFreePort"]]
    d = check_doc("Next Free Port", "server-app.json (nextFreePort)", "used and start as in the vector; the port "
                  "is rendered as a decimal number.")
    f = cases_loop(d, "string.name,array{uint16}.used,uint16.start,string.expect", cases,
                   ["name", "used", "start", "expect"], "One vector")
    d.call("sut", "RemoteVI Next Free Port.vi", [("used", f["used"]), ("start", f["start"])], [("port", "sut.v")], "L")
    act = d.dec("pd", "sut.v", "L")
    finish_check(d, *close_cases(d, f["name"], f["expect"], act))
    return d


def check_parse_arguments():
    vec = json.load(open(os.path.join(VEC, "server-app.json")))
    tf = lambda b: "T" if b else "F"
    cases = [(" ".join(c["args"]) or "(none)", c["args"],
              "%s|%d|%s|%s|%s|%d" % (c["share"], c["port"], c["token"], tf(c["wholeNetwork"]), tf(c["viewOnly"]),
                                     c["landingPort"])) for c in vec["parseArgs"]]
    d = check_doc("Parse Arguments", "server-app.json (parseArgs)", "args as in the vector; the options are "
                  "rendered share|port|token|whole network|view only|landing port with T or F.")
    f = cases_loop(d, "string.name,array{string}.args,string.expect", cases, ["name", "args", "expect"], "One vector")
    d.call("sut", "RemoteVI Parse Arguments.vi", [("args", f["args"])], [("options", "sut.v")], "L")
    d.node("ou", "Unbundle By Name", [("input cluster", "sut.v")], [("share", "ou.share"), ("port", "ou.port"),
           ("token", "ou.token"), ("whole network", "ou.wn"), ("view only", "ou.vo"), ("landing port", "ou.lp")], "L",
           fields="share,port,token,whole network,view only,landing port")
    wn = d.tf("twn", "ou.wn", "L")
    vo = d.tf("tvo", "ou.vo", "L")
    d.const("of", "string", esc("%s|%d|%s|%s|%s|%d"), "L")
    d.node("ol", "Format Into String", [("format string", "of.v"), ("input 1", "ou.share"), ("input 2", "ou.port"),
           ("input 3", "ou.token"), ("input 4", wn), ("input 5", vo), ("input 6", "ou.lp")],
           [("resulting string", "ol.v")], "L")
    finish_check(d, *close_cases(d, f["name"], f["expect"], "ol.v"))
    return d


# --------------------------------------------------------------------------- Caraya layer
SUBJECTS = [  # (subject, area, vector source for the description)
    ("Frame Encode", "Protocol", "frame.json cases"),
    ("Overlay Encode", "Protocol", "frame.json overlays"),
    ("Window Frame Encode", "Protocol", "frame.json windowFrames"),
    ("Parse Input", "Protocol", "input.json"),
    ("WS Encode Server Frame", "Protocol", "websocket.json serverFrames"),
    ("WS Decode Client Frame", "Protocol", "websocket.json clientFrames and incompleteClientFrames"),
    ("Dirty Rects", "Capture", "rects.json"),
    ("Translate Input", "Input", "translate.json cases"),
    ("Track Modifiers", "Input", "translate.json modifiers"),
    ("JSON String", "Protocol", "text.json jsonStrings"),
    ("Tips Message", "Protocol", "text.json tips"),
    ("Splitters Message", "Protocol", "text.json splitters"),
    ("Token Check", "Server", "http.json tokens"),
    ("Format Duration", "Server", "status.json durations"),
    ("Status Text", "Server", "status.json texts"),
    ("Status Convert", "Server", "status.json convert"),
    ("Window Rows", "App", "server-app.json windowRows"),
    ("Landing Page", "App", "server-app.json landing"),
    ("Next Free Port", "App", "server-app.json nextFreePort"),
    ("Parse Arguments", "App", "server-app.json parseArgs"),
]


def caraya_test(subject, source):
    d = Doc("Test %s.vi" % subject,
            "Caraya unit test of RemoteVI %s.vi against tests/vectors (%s), generated by "
            "tests/caraya/build.py - do not edit. One Assert Equal per vector, labelled with the vector's "
            "name; expected and actual are rendered as text by support/RemoteVI Check %s.vi (bytes as "
            "lowercase hex), so a failure shows both in the vector's own notation." % (subject, source, subject))
    d.call("dt", "Caraya.lvlib\\3ATest.lvclass\\3ADefine Test.vi",
           [("error in (no error)", ""), ("Label (VI Title)", ""), ("register caller level (0)", "")],
           [("error out", "dt.err"), ("Properties.Test", "")])
    d.call("chk", "RemoteVI Check %s.vi" % subject, [],
           [("labels", "chk.lab"), ("expected", "chk.exp"), ("actual", "chk.act"), ("failures", "")])
    d.loop_open("L", "One assertion per vector")
    lab = d.tunnel_in("tl", "L", "chk.lab")
    exp = d.tunnel_in("te", "L", "chk.exp")
    act = d.tunnel_in("ta", "L", "chk.act")
    err = d.tunnel_in("tr", "L", "dt.err", index=False)
    d.node("ve", "To Variant", [("anything", exp)], [("Variant", "ve.v")], "L")
    d.node("va", "To Variant", [("anything", act)], [("Variant", "va.v")], "L")
    d.call("as", "Caraya.lvlib\\3AAssert.lvclass\\3AAssert Equal Value_Variant.vi",
           [("Label", lab), ("error in (no error)", err), ("Expected", "ve.v"), ("Actual", "va.v"),
            ("Assert Only? (F)", ""), ("Execution time (s)", "")],
           [("error out", ""), ("Properties.Assert", "")], "L")
    d.loop_close()
    return d


def runner(tests_rel):
    d = Doc("RemoteVI Caraya Runner.vi",
            "Runs every RemoteVI Caraya unit test (generated by tests/caraya/build.py) with Caraya's "
            "Run Tests (Array Path), non-interactive, and writes a JUnit report. Test paths are relative "
            "to this VI, so the folder can move. Report Path empty: RemoteVI Caraya Report.xml beside this "
            "VI. Caraya answers 7002 in error out when a test failed - read the report for which one.")
    rp = d.control("rp", "Report Path", "path", 0, "", "JUnit report file, must end in .xml. Empty: "
                   "RemoteVI Caraya Report.xml beside this VI.", connection="recommended")
    d.node("cp", "Current VI's Path", [], [("path", "cp.v")])
    d.node("sp", "Strip Path", [("path", "cp.v")], [("stripped path", "sp.v"), ("name", "")])
    nets = []
    for i, rel in enumerate(tests_rel):
        k = d.const("p%d" % i, "path", esc(rel))
        d.node("bp%d" % i, "Build Path", [("base path", "sp.v"), ("name or relative path", k)],
               [("appended path", "bp%d.v" % i)])
        nets.append("bp%d.v" % i)
    d.node("ba", "Build Array", [("element", n) for n in nets], [("appended array", "ba.v")])
    dn = d.const("dn", "string", esc("RemoteVI Caraya Report.xml"))
    d.node("bd", "Build Path", [("base path", "sp.v"), ("name or relative path", dn)], [("appended path", "bd.v")])
    d.node("ep", "Empty String/Path?", [("string/path", rp)], [("empty?", "ep.v")])
    d.node("sel", "Select", [("t", "bd.v"), ("s", "ep.v"), ("f", rp)], [("s? t\\3Af", "sel.v")])
    f = d.const("fi", "bool", "false", label="Interactive (T)")
    d.el("Call", adapt="true", instance="Caraya.lvlib\\3ARun Test (Array Path).vi", target="Caraya.lvlib\\3ARun Tests.vi",
         inputs=Doc.io([("timeout (2000 ms)", ""), ("Test Report", ""), ("Verbose", ""), ("Report Path", "sel.v"),
                        ("error in", ""), ("Inspect Recursively (T)", ""), ("Paths", "ba.v"), ("Interactive (T)", f)]),
         outputs=Doc.io([("error out", "run.err"), ("Test Results", "")]), uid="run", uid_parent="root")
    d.indicator("o_rp", "Report Path used", "path", 4, "sel.v", "", "The JUnit report this run wrote.")
    d.indicator("o_err", "error out", "cluster{bool.status,int32.code,string.source}", 15, "run.err", "[false,0,]",
                "Caraya's error: 7002 when a test failed. Not a fault - read the report.")
    return d


# --------------------------------------------------------------------------- driver
def all_docs():
    """(aixml file name, Doc, target vi path, needs Caraya)"""
    out = [("hex_to_bytes.xml", hex_to_bytes(), os.path.join(SUPPORT, HEX2B), False),
           ("bytes_to_hex.xml", bytes_to_hex(), os.path.join(SUPPORT, B2HEX), False)]
    checks = {
        "Frame Encode": lambda: check_frame_like("Frame Encode", "frame.json", "cases", "rects"),
        "Overlay Encode": lambda: check_frame_like("Overlay Encode", "frame.json", "overlays", "popups"),
        "Window Frame Encode": lambda: check_frame_like("Window Frame Encode", "frame.json", "windowFrames", "rects"),
        "Parse Input": check_parse,
        "WS Encode Server Frame": check_ws_encode,
        "WS Decode Client Frame": check_ws_decode,
        "Dirty Rects": check_dirty_rects,
        "Translate Input": check_translate,
        "Track Modifiers": check_track_modifiers,
        "JSON String": check_json_string,
        "Tips Message": check_tips_message,
        "Splitters Message": check_splitters_message,
        "Token Check": check_token_check,
        "Format Duration": check_format_duration,
        "Status Text": check_status_text,
        "Status Convert": check_status_convert,
        "Window Rows": check_window_rows,
        "Landing Page": check_landing_page,
        "Next Free Port": check_next_free_port,
        "Parse Arguments": check_parse_arguments,
    }
    rel = []
    for subject, area, source in SUBJECTS:
        slug = subject.lower().replace(" ", "_")
        out.append(("check_%s.xml" % slug, checks[subject](),
                    os.path.join(SUPPORT, "RemoteVI Check %s.vi" % subject), False))
        out.append(("test_%s.xml" % slug, caraya_test(subject, source),
                    os.path.join(UNIT, area, "Test %s.vi" % subject), True))
        rel.append("unit\\%s\\Test %s.vi" % (area, subject))
    out.append(("runner.xml", runner(rel), os.path.join(HERE, "RemoteVI Caraya Runner.vi"), True))
    return out


def caraya_dir(arg):
    d = arg or os.path.join(LV_DIR, CARAYA_REL)
    return d if os.path.isfile(os.path.join(d, "Caraya.lvlib")) else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--aixml", action="store_true", help="write the AIXML only, compose nothing")
    ap.add_argument("--check", action="store_true", help="exit 1 when the AIXML on disk is stale")
    ap.add_argument("--caraya-dir", help="Caraya folder to compose the test VIs against "
                    "(default: LabVIEW 2025's vi.lib\\addons\\_JKI Toolkits\\Caraya)")
    ap.add_argument("--only", help="compose only VIs whose file name contains this text")
    a = ap.parse_args()

    docs = all_docs()
    stale = []
    os.makedirs(AIXML_DIR, exist_ok=True)
    for fname, d, _, _ in docs:
        p = os.path.join(AIXML_DIR, fname)
        text = d.text()
        old = open(p, encoding="utf-8", newline="").read() if os.path.exists(p) else None
        if old != text:
            stale.append(fname)
            if not a.check:
                with open(p, "w", encoding="utf-8", newline="") as fh:
                    fh.write(text)
    if a.check:
        print("stale: %s" % ", ".join(stale) if stale else "AIXML matches the vectors")
        return 1 if stale else 0
    if a.aixml:
        print("AIXML written to %s (%d changed)" % (AIXML_DIR, len(stale)))
        return 0

    car = caraya_dir(a.caraya_dir)
    search = [os.path.join(ROOT, "source", s) for s in ("Protocol", "Capture", "Input", "Server", "App")] + [SUPPORT]
    rc = 0
    for fname, d, vi, needs_caraya in docs:
        if a.only and a.only.lower() not in os.path.basename(vi).lower():
            continue
        if needs_caraya and not car:
            print("SKIP %s: Caraya is not installed for LabVIEW 2025 (%s) - pass --caraya-dir"
                  % (os.path.basename(vi), os.path.join(LV_DIR, CARAYA_REL)))
            continue
        os.makedirs(os.path.dirname(vi), exist_ok=True)
        args = [sys.executable, COMPOSE, os.path.join(AIXML_DIR, fname), vi] + search + ([car] if needs_caraya else [])
        r = subprocess.run(args, capture_output=True, text=True)
        tail = (r.stdout + r.stderr).strip().splitlines()
        print(("OK   " if r.returncode == 0 else "FAIL ") + os.path.relpath(vi, ROOT))
        if r.returncode != 0:
            print("\n".join("     " + t for t in tail[-6:]))
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
