"""Small helpers for Python generators of AIXML (used by examples/aixml/gen_*.py).

Case writes a Case Structure whose inputs pass into every frame; each frame names the inputs it
reads and the net it gives each output tunnel, which saves writing the tunnel boilerplate by hand.
"""


class Case:
    def __init__(self, out, uid, parent, sel, ins, outs, ind):
        self.o, self.uid, self.parent, self.sel, self.ins, self.outs, self.ind = out, uid, parent, sel, ins, outs, ind
        self.frames = []

    def frame(self, label, selector, used, body, results):
        """used: indexes of the inputs this frame reads; body(lines, t, f) appends XML lines, t(k) is the
        frame's net of input k and f the frame's uid (prefix new uids with it); results(t) gives the
        frame's net for each output tunnel."""
        self.frames.append((label, selector, used, body, results))
        return self

    def tin(self, n, k):
        return '%s_f%d_t%d.value' % (self.uid, n, k + 1)

    def emit(self):
        w = self.o.append
        p = ' ' * self.ind
        w('%s<Structure _name="Case Structure" selectin="%s" uid="%s" uid_parent="%s">' % (p, self.sel, self.uid, self.parent))
        for k, net in enumerate(self.ins):
            w('%s  <Tunnel _id="In%d" inputs="value:%s" uid="%s_i%d" uid_parent="%s"/>' % (p, k + 1, net, self.uid, k + 1, self.uid))
        for n, (label, selector, used, body, results) in enumerate(self.frames):
            f = '%s_f%d' % (self.uid, n)
            w('%s  <CaseFrame label="%s" selector="%s" selectout="" uid="%s" uid_parent="%s">' % (p, label, selector, f, self.uid))
            for k in range(len(self.ins)):
                t = '%s_t%d' % (f, k + 1)
                w('%s    <Tunnel _id="In%d" outputs="value:%s" uid="%s" uid_parent="%s"/>'
                  % (p, k + 1, (t + '.value') if k in used else '', t, f))
            lines = []
            t = (lambda k, n=n: self.tin(n, k))
            if body:
                body(lines, t, f)
            for line in lines:
                w('%s    %s' % (p, line))
            for k, net in enumerate(results(t) if results else []):
                w('%s    <Tunnel _id="Out%d" inputs="value:%s" uid="%s_o%d" uid_parent="%s"/>' % (p, k + 1, net, f, k + 1, f))
            w('%s  </CaseFrame>' % p)
        for k, net in enumerate(self.outs):
            w('%s  <Tunnel _id="Out%d" outputs="value:%s" uid="%s_O%d" uid_parent="%s"/>' % (p, k + 1, net, self.uid, k + 1, self.uid))
        w('%s</Structure>' % p)
