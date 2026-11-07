"""Generates tools/dev/aixml/style_panel.xml, the source of tools/dev/Style Panel.vi.

Style Panel.vi restyles a composed VI's front panel in place (build tool of the examples):
the composer only makes generic controls, so each row names a control by label and gives the
Silver .ctl to Replace it with (wires and data type stay), the tab page or splitter pane to move
it into, where it goes, its size, boolean text, tip strip, label visibility and visibility.

usage: python tools/dev/aixml/gen_style_panel.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ERR = 'cluster{bool.status,int32.code,string.source}'
E = '[false,0,]'
ROW = ('cluster{string.Label,string.Ctl,string.Tab,int32.Page,int32.Pane,int32.Left,int32.Top,'
       'int32.Width,int32.Height,string.Text,string.Tip,bool.Show Label,bool.Visible}')
TAB = 'cluster{string.Tab,array{string}.Pages,int32.Tab Width,int32.Width,int32.Height}'
FIND = 'RemoteVI Complex Fixture Find Controls.vi'

o = []
w = o.append


class Case:
    """A Case Structure: every input passes into every frame; out_nets name the output tunnels."""

    def __init__(self, uid, parent, sel, ins, outs, ind):
        self.uid, self.parent, self.sel, self.ins, self.outs, self.ind = uid, parent, sel, ins, outs, ind
        self.frames = []

    def frame(self, label, selector, used, body, results):
        """used: indexes of inputs read in this frame; body(lines, inner): lines to append, inner(k) the
        frame's net of input k; results: the frame's net per output tunnel."""
        self.frames.append((label, selector, used, body, results))

    def emit(self):
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
            body(lines, lambda k, f=f: '%s_t%d.value' % (f, k + 1), f)
            for line in lines:
                w('%s    %s' % (p, line))
            for k, net in enumerate(results(lambda k, f=f: '%s_t%d.value' % (f, k + 1))):
                w('%s    <Tunnel _id="Out%d" inputs="value:%s" uid="%s_o%d" uid_parent="%s"/>' % (p, k + 1, net, f, k + 1, f))
            w('%s  </CaseFrame>' % p)
        for k, net in enumerate(self.outs):
            w('%s  <Tunnel _id="Out%d" outputs="value:%s" uid="%s_O%d" uid_parent="%s"/>' % (p, k + 1, net, self.uid, k + 1, self.uid))
        w('%s</Structure>' % p)


def find_one(lines, uid, parent, panel, label_net, err):
    """Find Controls with one label; returns (ref net, error net)."""
    lines.append('<Node _name="Build Array" inputs="element:%s" outputs="appended array:%s_l.appended array" uid="%s_l" uid_parent="%s"/>' % (label_net, uid, uid, parent))
    lines.append('<Call target="%s" inputs="Panel:%s,labels:%s_l.appended array,error in:%s" outputs="Controls:%s_f.Controls,error out:%s_f.error out" uid="%s_f" uid_parent="%s"/>' % (FIND, panel, uid, err, uid, uid, uid, parent))
    lines.append('<Constant outputs="value:%s_z.value" type="int32" uid="%s_z" uid_parent="%s" value="0"/>' % (uid, uid, parent))
    lines.append('<Node _name="Index Array" inputs="array:%s_f.Controls,index:%s_z.value" outputs="element:%s_e.element" uid="%s_e" uid_parent="%s"/>' % (uid, uid, uid, uid, parent))
    return '%s_e.element' % uid, '%s_f.error out' % uid


w('<VI _name="Style Panel.vi" description="Build tool of the RemoteVI examples (source\\3A tools\\5Cdev\\5Caixml\\5Cgen_style_panel.py). Restyles the front panel of a composed VI in place and saves it\\3A the composer only makes generic controls. Run it once on a freshly composed VI (or on one whose controls are all still top-level)\\2C with the VI idle. Steps\\3A (1) every row with a Ctl is Replaced by that .ctl under Silver (a path relative to vi.lib\\5Csilver_ctls\\2C e.g. Numeric\\5CKnob NI_Silver.ctl)\\3B wires\\2C data type\\2C enum items and default value stay. (2) Tabs\\3A each tab control gets as many pages as Pages names (Add Page)\\2C the page labels\\2C and fixed tabs of Tab Width\\3B with Width above 0 the control - also one that is no tab control\\2C such as a subpanel - is sized through its own pane (Set Scaling Scale Single Object\\2C the window grown by the difference\\2C scaling off again). (3) every row\\3A moved onto page Page of the tab control Tab (Left/Top relative to the tab control) or\\2C with Tab empty and Pane 0 or more\\2C into that pane of the panel (Left/Top in pane coordinates)\\2C otherwise placed at Left/Top\\3B Width/Height (0\\3A keep) set the size of a string\\2C button\\2C numeric\\2C the visible area of a multicolumn listbox and the plot area of a graph\\3B Text sets a boolean\\27s text (and centres it)\\3B Tip the tip strip\\3B Show Label and Visible. (4) Window sets the panel bounds and the origin to 0\\2C0. Controls are found anywhere on the panel by label (Find Controls). problems lists every row whose steps returned an error\\2C with the code\\3B the run goes on.">')
w('  <FreeLabel comment="Replace\\2C tabs\\2C place\\2C window\\2C save" uid="lbl" uid_parent="root"/>')
w('  <Control _name="VI" conIdx="0" connection="required" description="The VI to restyle. Saved in place." outputs="value:vi.value" type="path" uid="vi" uid_parent="root" value=""/>')
w('  <Control _name="Silver" conIdx="1" connection="required" description="The folder vi.lib\\5Csilver_ctls of the LabVIEW running this." outputs="value:sv.value" type="path" uid="sv" uid_parent="root" value=""/>')
WIN = 'cluster{int32.Left,int32.Top,int32.Right,int32.Bottom}'
w('  <Control _name="Spec" conIdx="2" connection="required" description="LabVIEW XML file of a cluster spec{Rows\\2C Tabs\\2C Window} - written by tools\\5Caixml\\5Cstyle_rows.py. Rows\\3A one per control. Tabs\\3A pages and size of each tab control. Window\\3A panel bounds in screen coordinates\\2C all zero keeps them." outputs="value:spf.value" type="path" uid="spf" uid_parent="root" value=""/>')
w('  <Node _name="Read from Text File" inputs="file (use dialog):spf.value,error in:ei.value" outputs="refnum out:,text:rd.text,cancelled:,error out:rd.error out" uid="rd" uid_parent="root"/>')
w('  <Constant _name="spec type" outputs="value:spt.value" type="cluster{array{%s}.Rows,array{%s}.Tabs,%s.Window,array{int32}.Splitters}" uid="spt" uid_parent="root" value="[[],[],[0,0,0,0],[]]"/>' % (ROW, TAB, WIN))
w('  <Node _name="Unflatten From XML" inputs="xml string:rd.text,type:spt.value,error in (no error):rd.error out" outputs="value:ux.value,error out:ux.error out" uid="ux" uid_parent="root"/>')
w('  <Node _name="Unbundle By Name" fields="Rows,Tabs,Window,Splitters" inputs="input cluster:ux.value" outputs="Rows:spec.Rows,Tabs:spec.Tabs,Window:spec.Window,Splitters:spec.Splitters" uid="spec" uid_parent="root"/>')
w('  <Control _name="error in" conIdx="8" connection="recommended" description="Error chain in." outputs="value:ei.value" type="%s" uid="ei" uid_parent="root" value="%s"/>' % (ERR, E))
w('  <Node _name="Open VI Reference" inputs="vi path:vi.value,error in (no error):ux.error out" outputs="vi reference:ov.vi reference,error out:ov.error out" uid="ov" uid_parent="root"/>')
w('  <Node _name="Property Node" fields="read+Front Panel" inputs="reference:ov.vi reference,error in (no error):ov.error out" outputs="reference out:,error out:fp.error out,Front Panel:fp.fp" type="{LV.VI}" uid="fp" uid_parent="root"/>')
w('  <Node _name="Property Node" fields="read+Panes[]" inputs="reference:fp.fp,error in (no error):fp.error out" outputs="reference out:,error out:pp.error out,Panes[]:pp.panes" type="{LV.Panel}" uid="pp" uid_parent="root"/>')
# ---- (0) Splitters: the bars of a splitter panel to their positions, in the order of Splitters[] (errors ignored)
w('  <Node _name="Property Node" fields="read+Splitters[]" inputs="reference:fp.fp,error in (no error):pp.error out" outputs="reference out:,error out:,Splitters[]:sps.s" type="{LV.Panel}" uid="sps" uid_parent="root"/>')
w('  <Structure _name="For Loop" count="" label="Each splitter bar to its position" maxin="" maxout="" uid="spl" uid_parent="root">')
w('    <Tunnel _id="In1" inputs="value:sps.s" mode="index" outputs="value:spl_s.value" uid="spl_s" uid_parent="spl"/>')
w('    <Tunnel _id="In2" inputs="value:spec.Splitters" mode="index" outputs="value:spl_p.value" uid="spl_p" uid_parent="spl"/>')
w('    <Node _name="Property Node" fields="write+Position" inputs="reference:spl_s.value,Position:spl_p.value" outputs="reference out:,error out:" type="{LV.Splitter}" uid="spl_w" uid_parent="spl"/>')
w('  </Structure>')
w('  <Constant _name="no duplicate" outputs="value:nd.value" type="bool" uid="nd" uid_parent="root" value="false"/>')
w('  <Constant _name="true" outputs="value:tru.value" type="bool" uid="tru" uid_parent="root" value="true"/>')
w('  <Constant _name="false" outputs="value:fal.value" type="bool" uid="fal" uid_parent="root" value="false"/>')

# ---- (1) Replace ------------------------------------------------------------------------------
w('  <Structure _name="For Loop" count="" label="Replace each control that has a Ctl" maxin="" maxout="" uid="rl" uid_parent="root">')
w('    <Tunnel _id="In1" inputs="value:spec.Rows" mode="index" outputs="value:r_row.value" uid="r_row" uid_parent="rl"/>')
w('    <Tunnel _id="In2" inputs="value:fp.fp" outputs="value:r_fp.value" uid="r_fp" uid_parent="rl"/>')
w('    <Tunnel _id="In3" inputs="value:sv.value" outputs="value:r_sv.value" uid="r_sv" uid_parent="rl"/>')
w('    <ShiftReg uid="r_sr" uid_parent="rl">')
w('      <Left inputs="value:pp.error out" outputs="value:r_e.value" uid="r_srl" uid_parent="r_sr"/>')
w('      <Right inputs="value:r_ce.error out" outputs="value:r_end.value" uid="r_srr" uid_parent="r_sr"/>')
w('    </ShiftReg>')
w('    <Node _name="Unbundle By Name" fields="Label,Ctl" inputs="input cluster:r_row.value" outputs="Label:r_u.Label,Ctl:r_u.Ctl" uid="r_u" uid_parent="rl"/>')
w('    <Node _name="Empty String/Path?" inputs="string/path:r_u.Ctl" outputs="empty?:r_em.empty?" uid="r_em" uid_parent="rl"/>')
c = Case('r_cs', 'rl', 'r_em.empty?', ['r_u.Label', 'r_u.Ctl', 'r_fp.value', 'r_sv.value', 'r_e.value'], ['r_cs.err'], 4)
c.frame('No Ctl\\3A keep', 'True', [4], lambda L, t, f: None, lambda t: [t(4)])


def replace_body(L, t, f):
    ref, err = find_one(L, f + 'fd', f, t(2), t(0), t(4))
    L.append('<Node _name="Build Path" inputs="base path:%s,name or relative path:%s" outputs="appended path:%sbp.appended path" uid="%sbp" uid_parent="%s"/>' % (t(3), t(1), f, f, f))
    # Replace drops the control's value (a table comes back empty): read it before, write it to the new control
    L.append('<Node _name="Property Node" fields="read+Value" inputs="reference:%s" outputs="reference out:,error out:,Value:%sv.value" type="{LV.Control}" uid="%sv" uid_parent="%s"/>' % (ref, f, f, f))
    L.append('<Node _name="Invoke Node" target="Replace" type="{LV.Control}" inputs="reference:%s,error in (no error):%s,Path:%sbp.appended path" outputs="reference out:,error out:%srp.error out" uid="%srp" uid_parent="%s"/>' % (ref, err, f, f, f, f))
    ref2, err2 = find_one(L, f + 'fn', f, t(2), t(0), f + 'rp.error out')
    L.append('<Node _name="Property Node" fields="write+Value" inputs="reference:%s,Value:%sv.value" outputs="reference out:,error out:" type="{LV.Control}" uid="%svw" uid_parent="%s"/>' % (ref2, f, f, f))


c.frame('Replace with the .ctl', 'False', [0, 1, 2, 3, 4], replace_body, lambda t: ['r_cs_f1fn_f.error out'])
c.emit()
w('    <Node _name="Unbundle By Name" fields="code,source" inputs="input cluster:r_cs.err" outputs="code:r_code.code,source:r_code.source" uid="r_code" uid_parent="rl"/>')
w('    <Constant outputs="value:r_fmt.value" type="string" uid="r_fmt" uid_parent="rl" value="%s Replace %d %s"/>')
w('    <Node _name="Format Into String" inputs="format string:r_fmt.value,input 1:r_u.Label,input 2:r_code.code,input 3:r_code.source" outputs="resulting string:r_msg.resulting string" uid="r_msg" uid_parent="rl"/>')
w('    <Tunnel _id="Out1" inputs="value:r_msg.resulting string" mode="index" outputs="value:r_probs.value" uid="r_probs" uid_parent="rl"/>')
w('    <Call target="Clear Errors.vi" inputs="error in (no error):r_cs.err" outputs="error out:r_ce.error out" uid="r_ce" uid_parent="rl"/>')
w('  </Structure>')

# ---- (2) Tabs ---------------------------------------------------------------------------------
w('  <Constant _name="tab class" outputs="value:tcl.value" type="ref{LV.TabControl}" uid="tcl" uid_parent="root" value=""/>')
w('  <Constant _name="fixed tabs" outputs="value:tfx.value" type="int32" uid="tfx" uid_parent="root" value="2"/>')
w('  <Structure _name="For Loop" count="" label="Pages of each tab control" maxin="" maxout="" uid="tl" uid_parent="root">')
w('    <Tunnel _id="In1" inputs="value:spec.Tabs" mode="index" outputs="value:t_row.value" uid="t_row" uid_parent="tl"/>')
w('    <Tunnel _id="In2" inputs="value:fp.fp" outputs="value:t_fp.value" uid="t_fp" uid_parent="tl"/>')
w('    <Tunnel _id="In3" inputs="value:tcl.value" outputs="value:t_cl.value" uid="t_cl" uid_parent="tl"/>')
w('    <Tunnel _id="In4" inputs="value:tfx.value" outputs="value:t_fx.value" uid="t_fx" uid_parent="tl"/>')
w('    <Tunnel _id="In5" inputs="value:ov.vi reference" outputs="value:t_vi.value" uid="t_vi" uid_parent="tl"/>')
w('    <Tunnel _id="In6" inputs="value:pp.panes" outputs="value:t_ps.value" uid="t_ps" uid_parent="tl"/>')
w('    <ShiftReg uid="t_sr" uid_parent="tl">')
w('      <Left inputs="value:r_end.value" outputs="value:t_e.value" uid="t_srl" uid_parent="t_sr"/>')
w('      <Right inputs="value:t_ce.error out" outputs="value:t_end.value" uid="t_srr" uid_parent="t_sr"/>')
w('    </ShiftReg>')
w('    <Node _name="Unbundle By Name" fields="Tab,Pages,Tab Width,Width,Height" inputs="input cluster:t_row.value" outputs="Tab:t_u.Tab,Pages:t_u.Pages,Tab Width:t_u.w,Width:t_u.W,Height:t_u.H" uid="t_u" uid_parent="tl"/>')
L = []
ref, err = find_one(L, 't_fd', 'tl', 't_fp.value', 't_u.Tab', 't_e.value')
for line in L:
    w('    ' + line)
w('    <Node _name="To More Specific Class" inputs="target class:t_cl.value,reference:%s,error in:%s" outputs="specific class reference:t_tab.ref,error out:t_tab.error out" uid="t_tab" uid_parent="tl"/>' % (ref, err))
w('    <Constant outputs="value:t_h.value" type="int32" uid="t_h" uid_parent="tl" value="24"/>')
w('    <Constant outputs="value:t_dim0.value" type="cluster{int32.Width,int32.Height}" uid="t_dim0" uid_parent="tl" value="[110,24]"/>')
w('    <Node _name="Bundle By Name" fields="Width,Height" inputs="input cluster:t_dim0.value,Width:t_u.w,Height:t_h.value" outputs="output cluster:t_dim.output cluster" uid="t_dim" uid_parent="tl"/>')
w('    <Node _name="Property Node" fields="write+Tab Size,write+Fixed Tab Dimension,read+Pages" inputs="reference:t_tab.ref,error in (no error):t_tab.error out,Tab Size:t_fx.value,Fixed Tab Dimension:t_dim.output cluster" outputs="reference out:,error out:t_p0.error out,Pages:t_p0.pages" type="{LV.TabControl}" uid="t_p0" uid_parent="tl"/>')
w('    <Node _name="Array Size" inputs="array:t_u.Pages" outputs="size(s):t_nw.size" uid="t_nw" uid_parent="tl"/>')
w('    <Node _name="Array Size" inputs="array:t_p0.pages" outputs="size(s):t_nh.size" uid="t_nh" uid_parent="tl"/>')
w('    <Node _name="Subtract" inputs="x:t_nw.size,y:t_nh.size" outputs="x-y:t_add.x-y" uid="t_add" uid_parent="tl"/>')
w('    <Structure _name="For Loop" count="" label="Add the missing pages" maxin="t_add.x-y" maxout="" uid="ta" uid_parent="tl">')
w('      <Tunnel _id="In1" inputs="value:t_tab.ref" outputs="value:ta_r.value" uid="ta_r" uid_parent="ta"/>')
w('      <ShiftReg uid="ta_sr" uid_parent="ta">')
w('        <Left inputs="value:t_p0.error out" outputs="value:ta_e.value" uid="ta_srl" uid_parent="ta_sr"/>')
w('        <Right inputs="value:ta_ap.error out" outputs="value:ta_end.value" uid="ta_srr" uid_parent="ta_sr"/>')
w('      </ShiftReg>')
w('      <Constant outputs="value:ta_k.value" type="int32" uid="ta_k" uid_parent="ta" value="0"/>')
w('      <Constant outputs="value:ta_a.value" type="bool" uid="ta_a" uid_parent="ta" value="true"/>')
w('      <Node _name="Invoke Node" target="Add Page" type="{LV.TabControl}" inputs="reference:ta_r.value,error in (no error):ta_e.value,Page:ta_k.value,After:ta_a.value" outputs="reference out:,error out:ta_ap.error out" uid="ta_ap" uid_parent="ta"/>')
w('    </Structure>')
w('    <Node _name="Property Node" fields="read+Pages" inputs="reference:t_tab.ref,error in (no error):ta_end.value" outputs="reference out:,error out:t_p1.error out,Pages:t_p1.pages" type="{LV.TabControl}" uid="t_p1" uid_parent="tl"/>')
w('    <Structure _name="For Loop" count="" label="Name each page" maxin="" maxout="" uid="tn" uid_parent="tl">')
w('      <Tunnel _id="In1" inputs="value:t_p1.pages" mode="index" outputs="value:tn_p.value" uid="tn_p" uid_parent="tn"/>')
w('      <Tunnel _id="In2" inputs="value:t_u.Pages" mode="index" outputs="value:tn_n.value" uid="tn_n" uid_parent="tn"/>')
w('      <ShiftReg uid="tn_sr" uid_parent="tn">')
w('        <Left inputs="value:t_p1.error out" outputs="value:tn_e.value" uid="tn_srl" uid_parent="tn_sr"/>')
w('        <Right inputs="value:tn_pw.error out" outputs="value:tn_end.value" uid="tn_srr" uid_parent="tn_sr"/>')
w('      </ShiftReg>')
w('      <Node _name="Property Node" fields="write+Page Label" inputs="reference:tn_p.value,error in (no error):tn_e.value,Page Label:tn_n.value" outputs="reference out:,error out:tn_pw.error out" type="{LV.Page}" uid="tn_pw" uid_parent="tn"/>')
# a page added by Add Page has no caption to write (1077); the caption of a donor page is set, errors ignored
w('      <Node _name="Property Node" fields="write+Tab Caption" inputs="reference:tn_p.value,Tab Caption:tn_n.value" outputs="reference out:,error out:" type="{LV.Page}" uid="tn_pc" uid_parent="tn"/>')
w('    </Structure>')
# size of the tab control: it has no writable size, so it is scaled with the pane once (Scale Single Object),
# the window grown by the missing width and height, and scaling switched off again
w('    <Node _name="Greater Than 0?" inputs="x:t_u.W" outputs="x &gt; 0?:t_hs.x &gt; 0?" uid="t_hs" uid_parent="tl"/>')
# any control can be sized this way (a subpanel has no writable size either): the size step works on the
# control found by label, with its own error chain, so a row that is no tab control still gets its size
w('    <Call target="Clear Errors.vi" inputs="error in (no error):tn_end.value" outputs="error out:t_clr.error out" uid="t_clr" uid_parent="tl"/>')
c = Case('t_sz', 'tl', 't_hs.x &gt; 0?', [ref, 't_vi.value', 't_ps.value', 't_u.W', 't_u.H', 't_clr.error out'], ['t_sz.err'], 4)
c.frame('Keep the size', 'False', [5], lambda L, t, f: None, lambda t: [t(5)])


def tab_size(L, t, f):
    # the pane the control is in (a splitter panel has several)
    L.append('<Node _name="Property Node" fields="read+OwningPane" inputs="reference:%s,error in (no error):%s" outputs="OwningPane:%sp.element,reference out:,error out:%sop.error out" type="{LV.Control}" uid="%sop" uid_parent="%s"/>' % (t(0), t(5), f, f, f, f))
    L.append('<Constant outputs="value:%sm2.value" type="uint16{No Scaling,Scale All Objects,Scale Single Object}" uid="%sm2" uid_parent="%s" value="2"/>' % (f, f, f))
    L.append('<Constant outputs="value:%sm0.value" type="uint16{No Scaling,Scale All Objects,Scale Single Object}" uid="%sm0" uid_parent="%s" value="0"/>' % (f, f, f))
    L.append('<Node _name="Invoke Node" target="Set Scaling" type="{LV.Pane}" inputs="reference:%sp.element,error in (no error):%s,ScalingMode:%sm2.value,ScalableObj:%s" outputs="reference out:,error out:%ss1.error out" uid="%ss1" uid_parent="%s"/>' % (f, f + 'op.error out', f, t(0), f, f, f))
    L.append('<Node _name="Property Node" fields="read+Bounds" inputs="reference:%s,error in (no error):%ss1.error out" outputs="reference out:,error out:%sb.error out,Bounds:%sb.b" type="{LV.Control}" uid="%sb" uid_parent="%s"/>' % (t(0), f, f, f, f, f))
    L.append('<Node _name="Unbundle By Name" fields="Width,Height" inputs="input cluster:%sb.b" outputs="Width:%sbu.w,Height:%sbu.h" uid="%sbu" uid_parent="%s"/>' % (f, f, f, f, f))
    L.append('<Node _name="Property Node" fields="read+Front Panel Window\\3APanel Bounds" inputs="reference:%s,error in (no error):%sb.error out" outputs="reference out:,error out:%swr.error out,Front Panel Window\\3APanel Bounds:%swr.pb" type="{LV.VI}" uid="%swr" uid_parent="%s"/>' % (t(1), f, f, f, f, f))
    # the window grows by the missing width and height; it is moved to the top left of the screen
    # (0, 40) first, as Windows clamps a window that would reach past the bottom of the screen
    L.append('<Node _name="Unbundle By Name" fields="left,top,right,bottom" inputs="input cluster:%swr.pb" outputs="left:%swu.l,top:%swu.t,right:%swu.r,bottom:%swu.b" uid="%swu" uid_parent="%s"/>' % (f, f, f, f, f, f, f))
    L.append('<Node _name="Subtract" inputs="x:%s,y:%sbu.w" outputs="x-y:%sdw.x-y" uid="%sdw" uid_parent="%s"/>' % (t(3), f, f, f, f))
    L.append('<Node _name="Subtract" inputs="x:%s,y:%sbu.h" outputs="x-y:%sdh.x-y" uid="%sdh" uid_parent="%s"/>' % (t(4), f, f, f, f))
    L.append('<Node _name="Subtract" inputs="x:%swu.r,y:%swu.l" outputs="x-y:%sow.x-y" uid="%sow" uid_parent="%s"/>' % (f, f, f, f, f))
    L.append('<Node _name="Subtract" inputs="x:%swu.b,y:%swu.t" outputs="x-y:%soh.x-y" uid="%soh" uid_parent="%s"/>' % (f, f, f, f, f))
    L.append('<Node _name="Add" inputs="x:%sow.x-y,y:%sdw.x-y" outputs="x+y:%snr.x+y" uid="%snr" uid_parent="%s"/>' % (f, f, f, f, f))
    L.append('<Constant outputs="value:%sy0.value" type="int32" uid="%sy0" uid_parent="%s" value="40"/>' % (f, f, f))
    L.append('<Constant outputs="value:%sx0.value" type="int32" uid="%sx0" uid_parent="%s" value="0"/>' % (f, f, f))
    L.append('<Node _name="Add" inputs="x:%soh.x-y,y:%sdh.x-y" outputs="x+y:%snh.x+y" uid="%snh" uid_parent="%s"/>' % (f, f, f, f, f))
    L.append('<Node _name="Add" inputs="x:%snh.x+y,y:%sy0.value" outputs="x+y:%snb.x+y" uid="%snb" uid_parent="%s"/>' % (f, f, f, f, f))
    L.append('<Node _name="Bundle By Name" fields="left,top,right,bottom" inputs="input cluster:%swr.pb,left:%sx0.value,top:%sy0.value,right:%snr.x+y,bottom:%snb.x+y" outputs="output cluster:%snw.output cluster" uid="%snw" uid_parent="%s"/>' % (f, f, f, f, f, f, f, f))
    L.append('<Node _name="Property Node" fields="write+Front Panel Window\\3APanel Bounds" inputs="reference:%s,error in (no error):%swr.error out,Front Panel Window\\3APanel Bounds:%snw.output cluster" outputs="reference out:,error out:%sww.error out" type="{LV.VI}" uid="%sww" uid_parent="%s"/>' % (t(1), f, f, f, f, f))
    L.append('<Node _name="Invoke Node" target="Set Scaling" type="{LV.Pane}" inputs="reference:%sp.element,error in (no error):%sww.error out,ScalingMode:%sm0.value,ScalableObj:%s" outputs="reference out:,error out:%ss0.error out" uid="%ss0" uid_parent="%s"/>' % (f, f, f, t(0), f, f, f))


c.frame('Scale the tab control with the pane once', 'True', [0, 1, 2, 3, 4, 5], tab_size, lambda t: ['t_sz_f1s0.error out'])
mark = len(o)
c.o = o
c.emit()
w('    <Node _name="Merge Errors" inputs="error in:t_sz.err,error in:tn_end.value" outputs="error out:t_mg.error out" uid="t_mg" uid_parent="tl"/>')
w('    <Node _name="Unbundle By Name" fields="code,source" inputs="input cluster:t_mg.error out" outputs="code:t_code.code,source:t_code.source" uid="t_code" uid_parent="tl"/>')
w('    <Constant outputs="value:t_fmt.value" type="string" uid="t_fmt" uid_parent="tl" value="%s Tabs %d %s"/>')
w('    <Node _name="Format Into String" inputs="format string:t_fmt.value,input 1:t_u.Tab,input 2:t_code.code,input 3:t_code.source" outputs="resulting string:t_msg.resulting string" uid="t_msg" uid_parent="tl"/>')
w('    <Tunnel _id="Out1" inputs="value:t_msg.resulting string" mode="index" outputs="value:t_probs.value" uid="t_probs" uid_parent="tl"/>')
w('    <Call target="Clear Errors.vi" inputs="error in (no error):t_mg.error out" outputs="error out:t_ce.error out" uid="t_ce" uid_parent="tl"/>')
w('  </Structure>')

# ---- (3) Place --------------------------------------------------------------------------------
w('  <Constant _name="string class" outputs="value:scl.value" type="ref{LV.String}" uid="scl" uid_parent="root" value=""/>')
w('  <Constant _name="graph class" outputs="value:gcl.value" type="ref{LV.WaveformGraph}" uid="gcl" uid_parent="root" value=""/>')
w('  <Constant _name="boolean class" outputs="value:bcl.value" type="ref{LV.Boolean}" uid="bcl" uid_parent="root" value=""/>')
w('  <Structure _name="For Loop" count="" label="Move and set each control" maxin="" maxout="" uid="pl" uid_parent="root">')
ins = [('spec.Rows', 'index', 'p_row'), ('fp.fp', None, 'p_fp'), ('pp.panes', None, 'p_ps'), ('tcl.value', None, 'p_tcl'),
       ('nd.value', None, 'p_nd'), ('scl.value', None, 'p_scl'), ('gcl.value', None, 'p_gcl'), ('bcl.value', None, 'p_bcl'),
       ('tru.value', None, 'p_tru'), ('fal.value', None, 'p_fal')]
for k, (src, mode, u) in enumerate(ins):
    w('    <Tunnel _id="In%d" inputs="value:%s"%s outputs="value:%s.value" uid="%s" uid_parent="pl"/>' % (k + 1, src, ' mode="index"' if mode else '', u, u))
w('    <ShiftReg uid="p_sr" uid_parent="pl">')
w('      <Left inputs="value:wc.err" outputs="value:p_e.value" uid="p_srl" uid_parent="p_sr"/>')
w('      <Right inputs="value:p_ce.error out" outputs="value:p_end.value" uid="p_srr" uid_parent="p_sr"/>')
w('    </ShiftReg>')
w('    <Node _name="Unbundle By Name" fields="Label,Tab,Page,Pane,Left,Top,Width,Height,Text,Tip,Show Label,Visible" inputs="input cluster:p_row.value" outputs="Label:p_u.Label,Tab:p_u.Tab,Page:p_u.Page,Pane:p_u.Pane,Left:p_u.Left,Top:p_u.Top,Width:p_u.Width,Height:p_u.Height,Text:p_u.Text,Tip:p_u.Tip,Show Label:p_u.ShowLabel,Visible:p_u.Visible" uid="p_u" uid_parent="pl"/>')
L = []
ref, err = find_one(L, 'p_fd', 'pl', 'p_fp.value', 'p_u.Label', 'p_e.value')
for line in L:
    w('    ' + line)
w('    <Constant outputs="value:p_pos0.value" type="cluster{int32.Left,int32.Top}" uid="p_pos0" uid_parent="pl" value="[0,0]"/>')
w('    <Node _name="Bundle By Name" fields="Left,Top" inputs="input cluster:p_pos0.value,Left:p_u.Left,Top:p_u.Top" outputs="output cluster:p_pos.output cluster" uid="p_pos" uid_parent="pl"/>')
w('    <Node _name="Empty String/Path?" inputs="string/path:p_u.Tab" outputs="empty?:p_nt.empty?" uid="p_nt" uid_parent="pl"/>')
# inputs of the placement case: 0 ctl, 1 err, 2 pos, 3 Tab, 4 Page, 5 Pane, 6 panes, 7 fp, 8 tab class, 9 no dup
c = Case('p_cs', 'pl', 'p_nt.empty?', [ref, err, 'p_pos.output cluster', 'p_u.Tab', 'p_u.Page', 'p_u.Pane', 'p_ps.value', 'p_fp.value', 'p_tcl.value', 'p_nd.value'], ['p_cs.err'], 4)


def onto_page(L, t, f):
    tref, terr = find_one(L, f + 'fd', f, t(7), t(3), t(1))
    L.append('<Node _name="To More Specific Class" inputs="target class:%s,reference:%s,error in:%s" outputs="specific class reference:%stc.ref,error out:%stc.error out" uid="%stc" uid_parent="%s"/>' % (t(8), tref, terr, f, f, f, f))
    L.append('<Node _name="Property Node" fields="read+Pages,read+Position" inputs="reference:%stc.ref,error in (no error):%stc.error out" outputs="reference out:,error out:%stp.error out,Pages:%stp.pages,Position:%stp.pos" type="{LV.TabControl}" uid="%stp" uid_parent="%s"/>' % (f, f, f, f, f, f, f))
    L.append('<Node _name="Index Array" inputs="array:%stp.pages,index:%s" outputs="element:%spg.element" uid="%spg" uid_parent="%s"/>' % (f, t(4), f, f, f))
    L.append('<Node _name="Unbundle By Name" fields="Left,Top" inputs="input cluster:%stp.pos" outputs="Left:%sq.l,Top:%sq.t" uid="%sq" uid_parent="%s"/>' % (f, f, f, f, f))
    L.append('<Node _name="Unbundle By Name" fields="Left,Top" inputs="input cluster:%s" outputs="Left:%sr.l,Top:%sr.t" uid="%sr" uid_parent="%s"/>' % (t(2), f, f, f, f))
    L.append('<Node _name="Add" inputs="x:%sq.l,y:%sr.l" outputs="x+y:%sx.x+y" uid="%sx" uid_parent="%s"/>' % (f, f, f, f, f))
    L.append('<Node _name="Add" inputs="x:%sq.t,y:%sr.t" outputs="x+y:%sy.x+y" uid="%sy" uid_parent="%s"/>' % (f, f, f, f, f))
    L.append('<Node _name="Bundle By Name" fields="Left,Top" inputs="input cluster:%s,Left:%sx.x+y,Top:%sy.x+y" outputs="output cluster:%sb.output cluster" uid="%sb" uid_parent="%s"/>' % (t(2), f, f, f, f, f))
    L.append('<Node _name="Invoke Node" target="Move" type="{LV.Control}" inputs="reference:%s,error in (no error):%stp.error out,position:%sb.output cluster,owner:%spg.element,duplicate:%s" outputs="reference out:,error out:%smv.error out" uid="%smv" uid_parent="%s"/>' % (t(0), f, f, f, t(9), f, f, f))
    L.append('<Node _name="Property Node" fields="write+Position" inputs="reference:%s,error in (no error):%smv.error out,Position:%sb.output cluster" outputs="reference out:,error out:%swp.error out" type="{LV.Control}" uid="%swp" uid_parent="%s"/>' % (t(0), f, f, f, f, f))


def no_tab(L, t, f):
    L.append('<Node _name="Less Than 0?" inputs="x:%s" outputs="x &lt; 0?:%sneg.x &lt; 0?" uid="%sneg" uid_parent="%s"/>' % (t(5), f, f, f))
    # inner case: 0 ctl, 1 err, 2 pos, 3 Pane, 4 panes, 5 no dup
    inner = Case(f + 'pc', f, f + 'neg.x &lt; 0?', [t(0), t(1), t(2), t(5), t(6), t(9)], [f + 'pc.err'], 0)

    def just_place(L2, u, g):
        L2.append('<Node _name="Property Node" fields="write+Position" inputs="reference:%s,error in (no error):%s,Position:%s" outputs="reference out:,error out:%swp.error out" type="{LV.Control}" uid="%swp" uid_parent="%s"/>' % (u(0), u(1), u(2), g, g, g))

    def into_pane(L2, u, g):
        L2.append('<Node _name="Index Array" inputs="array:%s,index:%s" outputs="element:%spn.element" uid="%spn" uid_parent="%s"/>' % (u(4), u(3), g, g, g))
        # Left/Top are relative to the visible top left of the pane: a splitter pane's origin need not be 0,0
        # (NI's splitter example scrolls its main pane), so its Origin is added
        L2.append('<Node _name="Property Node" fields="read+Origin" inputs="reference:%spn.element,error in (no error):%s" outputs="reference out:,error out:%sor.error out,Origin:%sor.o" type="{LV.Pane}" uid="%sor" uid_parent="%s"/>' % (g, u(1), g, g, g, g))
        L2.append('<Node _name="Unbundle By Name" fields="Horizontal,Vertical" inputs="input cluster:%sor.o" outputs="Horizontal:%sou.h,Vertical:%sou.v" uid="%sou" uid_parent="%s"/>' % (g, g, g, g, g))
        L2.append('<Node _name="Unbundle By Name" fields="Left,Top" inputs="input cluster:%s" outputs="Left:%spu.l,Top:%spu.t" uid="%spu" uid_parent="%s"/>' % (u(2), g, g, g, g))
        L2.append('<Node _name="Add" inputs="x:%spu.l,y:%sou.h" outputs="x+y:%sax.x+y" uid="%sax" uid_parent="%s"/>' % (g, g, g, g, g))
        L2.append('<Node _name="Add" inputs="x:%spu.t,y:%sou.v" outputs="x+y:%say.x+y" uid="%say" uid_parent="%s"/>' % (g, g, g, g, g))
        L2.append('<Node _name="Bundle By Name" fields="Left,Top" inputs="input cluster:%s,Left:%sax.x+y,Top:%say.x+y" outputs="output cluster:%sps.output cluster" uid="%sps" uid_parent="%s"/>' % (u(2), g, g, g, g, g))
        L2.append('<Node _name="Invoke Node" target="Move" type="{LV.Control}" inputs="reference:%s,error in (no error):%sor.error out,position:%sps.output cluster,owner:%spn.element,duplicate:%s" outputs="reference out:,error out:%smv.error out" uid="%smv" uid_parent="%s"/>' % (u(0), g, g, g, u(5), g, g, g))
        L2.append('<Node _name="Property Node" fields="write+Position" inputs="reference:%s,error in (no error):%smv.error out,Position:%sps.output cluster" outputs="reference out:,error out:%swp.error out" type="{LV.Control}" uid="%swp" uid_parent="%s"/>' % (u(0), g, g, g, g, g))

    inner.frame('No pane\\3A place', 'True', [0, 1, 2], just_place, lambda u: [inner.uid + '_f0wp.error out'])
    inner.frame('Into the pane', 'False', [0, 1, 2, 3, 4, 5], into_pane, lambda u: [inner.uid + '_f1wp.error out'])
    # emit the inner case into L (Case.emit writes to o; capture)
    mark = len(o)
    inner.emit()
    L.extend(o[mark:])
    del o[mark:]


c.frame('Tab empty\\3A pane or panel', 'True', [0, 1, 2, 5, 6, 9], no_tab, lambda t: ['p_cs_f0pc.err'])
c.frame('Onto a page of Tab', 'False', [0, 1, 2, 3, 4, 7, 8, 9], onto_page, lambda t: ['p_cs_f1wp.error out'])
c.emit()

# size: string Size, graph Plot Area:Size (casts fail quietly for other classes)
w('    <Node _name="Greater Than 0?" inputs="x:p_u.Width" outputs="x &gt; 0?:p_hw.x &gt; 0?" uid="p_hw" uid_parent="pl"/>')
w('    <Constant outputs="value:p_sz0.value" type="cluster{int32.Width,int32.Height}" uid="p_sz0" uid_parent="pl" value="[0,0]"/>')
w('    <Node _name="Bundle By Name" fields="Width,Height" inputs="input cluster:p_sz0.value,Width:p_u.Width,Height:p_u.Height" outputs="output cluster:p_sz.output cluster" uid="p_sz" uid_parent="pl"/>')
c = Case('p_sc', 'pl', 'p_hw.x &gt; 0?', [ref, 'p_sz.output cluster', 'p_scl.value', 'p_gcl.value', 'p_cs.err'], ['p_sc.err'], 4)
c.frame('No size', 'False', [4], lambda L, t, f: None, lambda t: [t(4)])


def sized(L, t, f):
    """Width/Height by class (Bounds is read-only): each cast that fails skips its write; errors ignored."""
    L.append('<Node _name="Unbundle By Name" fields="Width,Height" inputs="input cluster:%s" outputs="Width:%swh.w,Height:%swh.h" uid="%swh" uid_parent="%s"/>' % (t(1), f, f, f, f))
    L.append('<Constant outputs="value:%su0.value" type="cluster{uint32.Width,uint32.Height}" uid="%su0" uid_parent="%s" value="[0,0]"/>' % (f, f, f))
    L.append('<Node _name="Bundle By Name" fields="Width,Height" inputs="input cluster:%su0.value,Width:%swh.w,Height:%swh.h" outputs="output cluster:%su.output cluster" uid="%su" uid_parent="%s"/>' % (f, f, f, f, f, f))
    U = f + 'u.output cluster'
    for k, (cls, prop, val) in enumerate([
            ('LV.Boolean', 'Button Size', U), ('LV.String', 'Size', U), ('LV.Path', 'Size', U),
            ('LV.NumericWithScale', 'Housing Size', U), ('LV.Digital', 'Text Width', f + 'wh.w'),
            ('LV.NamedNumeric', 'Named Numeric Size', U),
            ('LV.WaveformGraph', 'Plot Area\\3ASize', t(1))]):
        g = '%sk%d' % (f, k)
        L.append('<Constant outputs="value:%sc.value" type="ref{%s}" uid="%sc" uid_parent="%s" value=""/>' % (g, cls, g, f))
        L.append('<Node _name="To More Specific Class" inputs="target class:%sc.value,reference:%s" outputs="specific class reference:%sr.ref,error out:%sr.error out" uid="%sr" uid_parent="%s"/>' % (g, t(0), g, g, g, f))
        L.append('<Node _name="Property Node" fields="write+%s" inputs="reference:%sr.ref,error in (no error):%sr.error out,%s:%s" outputs="reference out:,error out:" type="{%s}" uid="%sw" uid_parent="%s"/>' % (prop, g, g, prop, val, cls, g, f))
    # a multicolumn listbox: the size of its visible area
    g = f + 'ml'
    L.append('<Constant outputs="value:%sc.value" type="ref{LV.MulticolumnListbox}" uid="%sc" uid_parent="%s" value=""/>' % (g, g, f))
    L.append('<Node _name="To More Specific Class" inputs="target class:%sc.value,reference:%s" outputs="specific class reference:%sr.ref,error out:%sr.error out" uid="%sr" uid_parent="%s"/>' % (g, t(0), g, g, g, f))
    L.append('<Node _name="Property Node" fields="write+Bounds\\3AArea Width,write+Bounds\\3AArea Height" inputs="reference:%sr.ref,error in (no error):%sr.error out,Bounds\\3AArea Width:%swh.w,Bounds\\3AArea Height:%swh.h" outputs="reference out:,error out:" type="{LV.MulticolumnListbox}" uid="%sp" uid_parent="%s"/>' % (g, g, f, f, g, f))
    # a table: as many visible rows (20 px) and columns (120 px) as fit into Width x Height
    g = f + 'tb'
    L.append('<Constant outputs="value:%sc.value" type="ref{LV.Table}" uid="%sc" uid_parent="%s" value=""/>' % (g, g, f))
    L.append('<Node _name="To More Specific Class" inputs="target class:%sc.value,reference:%s" outputs="specific class reference:%sr.ref,error out:%sr.error out" uid="%sr" uid_parent="%s"/>' % (g, t(0), g, g, g, f))
    L.append('<Constant outputs="value:%srh.value" type="int32" uid="%srh" uid_parent="%s" value="20"/>' % (g, g, f))
    L.append('<Constant outputs="value:%scw.value" type="int32" uid="%scw" uid_parent="%s" value="120"/>' % (g, g, f))
    L.append('<Node _name="Quotient &amp; Remainder" inputs="x:%swh.h,y:%srh.value" outputs="x-y*floor(x/y):,floor(x/y):%sqr.q" uid="%sqr" uid_parent="%s"/>' % (f, g, g, g, f))
    L.append('<Node _name="Quotient &amp; Remainder" inputs="x:%swh.w,y:%scw.value" outputs="x-y*floor(x/y):,floor(x/y):%sqc.q" uid="%sqc" uid_parent="%s"/>' % (f, g, g, g, f))
    L.append('<Node _name="Property Node" fields="write+Number of Rows,write+Number of Columns" inputs="reference:%sr.ref,error in (no error):%sr.error out,Number of Rows:%sqr.q,Number of Columns:%sqc.q" outputs="reference out:,error out:" type="{LV.Table}" uid="%sp" uid_parent="%s"/>' % (g, g, g, g, g, f))
    # a graph also gets a dark plot area (its default plot colours stay readable) with a dim grid, no legend, both scales autoscaling
    g = f + 'gx'
    L.append('<Constant outputs="value:%sc.value" type="ref{LV.WaveformGraph}" uid="%sc" uid_parent="%s" value=""/>' % (g, g, f))
    L.append('<Node _name="To More Specific Class" inputs="target class:%sc.value,reference:%s" outputs="specific class reference:%sr.ref,error out:%sr.error out" uid="%sr" uid_parent="%s"/>' % (g, t(0), g, g, g, f))
    L.append('<Constant outputs="value:%swh.value" type="uint32" uid="%swh" uid_parent="%s" value="2304563"/>' % (g, g, f))
    L.append('<Constant outputs="value:%sgr.value" type="uint32" uid="%sgr" uid_parent="%s" value="3884370"/>' % (g, g, f))
    L.append('<Constant outputs="value:%snl.value" type="bool" uid="%snl" uid_parent="%s" value="false"/>' % (g, g, f))
    L.append('<Node _name="Property Node" fields="write+Plot Area\\3AColors\\3ABG Color,write+Grid Colors\\3AX Color,write+Grid Colors\\3AY Color,write+Legend\\3AVisible,read+X Scale,read+Y Scale" inputs="reference:%sr.ref,error in (no error):%sr.error out,Plot Area\\3AColors\\3ABG Color:%swh.value,Grid Colors\\3AX Color:%sgr.value,Grid Colors\\3AY Color:%sgr.value,Legend\\3AVisible:%snl.value" outputs="reference out:,error out:%sp.error out,X Scale:%sp.xs,Y Scale:%sp.ys" type="{LV.WaveformGraph}" uid="%sp" uid_parent="%s"/>' % (g, g, g, g, g, g, g, g, g, g, f))
    L.append('<Constant outputs="value:%sfit.value" type="uint8" uid="%sfit" uid_parent="%s" value="1"/>' % (g, g, f))
    L.append('<Node _name="Property Node" fields="write+Scale Fit" inputs="reference:%sp.xs,error in (no error):%sp.error out,Scale Fit:%sfit.value" outputs="error out:%spx.error out" type="{LV.GraphScale}" uid="%spx" uid_parent="%s"/>' % (g, g, g, g, g, f))
    L.append('<Node _name="Property Node" fields="write+Scale Fit" inputs="reference:%sp.ys,error in (no error):%spx.error out,Scale Fit:%sfit.value" outputs="error out:" type="{LV.GraphScale}" uid="%spy" uid_parent="%s"/>' % (g, g, g, g, f))


c.frame('Size by class', 'True', [0, 1, 4], sized, lambda t: [t(4)])
c.emit()

# boolean text
w('    <Node _name="Empty String/Path?" inputs="string/path:p_u.Text" outputs="empty?:p_nx.empty?" uid="p_nx" uid_parent="pl"/>')
c = Case('p_bx', 'pl', 'p_nx.empty?', [ref, 'p_u.Text', 'p_bcl.value', 'p_tru.value', 'p_fal.value', 'p_sc.err'], ['p_bx.err'], 4)
c.frame('No text', 'True', [5], lambda L, t, f: None, lambda t: [t(5)])


def btext(L, t, f):
    L.append('<Node _name="To More Specific Class" inputs="target class:%s,reference:%s,error in:%s" outputs="specific class reference:%sb.ref,error out:%sb.error out" uid="%sb" uid_parent="%s"/>' % (t(2), t(0), t(5), f, f, f, f))
    L.append('<Node _name="Property Node" fields="write+Multiple Text String,write+Lock Boolean Text In Center,read+Boolean Text" inputs="reference:%sb.ref,error in (no error):%sb.error out,Multiple Text String:%s,Lock Boolean Text In Center:%s" outputs="reference out:,error out:%sbp.error out,Boolean Text:%sbp.bt" type="{LV.Boolean}" uid="%sbp" uid_parent="%s"/>' % (f, f, t(4), t(3), f, f, f, f))
    L.append('<Node _name="Property Node" fields="write+Text,write+Visible" inputs="reference:%sbp.bt,error in (no error):%sbp.error out,Text:%s,Visible:%s" outputs="reference out:,error out:%sbt.error out" type="{LV.Text}" uid="%sbt" uid_parent="%s"/>' % (f, f, t(1), t(3), f, f, f))
    L.append('<Node _name="Close Reference" inputs="reference:%sbp.bt,error in (no error):%sbt.error out" outputs="error out:%sbc.error out" uid="%sbc" uid_parent="%s"/>' % (f, f, f, f, f))


c.frame('Boolean text', 'False', [0, 1, 2, 3, 4, 5], btext, lambda t: [t(5).replace('_t6.value', 'bc.error out')])
c.emit()
w('    <Node _name="Property Node" fields="write+TipStrip,write+Label.Visible,write+Visible" inputs="reference:%s,error in (no error):p_bx.err,TipStrip:p_u.Tip,Label.Visible:p_u.ShowLabel,Visible:p_u.Visible" outputs="reference out:,error out:p_tip.error out" type="{LV.Control}" uid="p_tip" uid_parent="pl"/>' % ref)
w('    <Node _name="Unbundle By Name" fields="code,source" inputs="input cluster:p_tip.error out" outputs="code:p_code.code,source:p_code.source" uid="p_code" uid_parent="pl"/>')
w('    <Constant outputs="value:p_fmt.value" type="string" uid="p_fmt" uid_parent="pl" value="%s Place %d %s"/>')
w('    <Node _name="Format Into String" inputs="format string:p_fmt.value,input 1:p_u.Label,input 2:p_code.code,input 3:p_code.source" outputs="resulting string:p_msg.resulting string" uid="p_msg" uid_parent="pl"/>')
w('    <Tunnel _id="Out1" inputs="value:p_msg.resulting string" mode="index" outputs="value:p_probs.value" uid="p_probs" uid_parent="pl"/>')
w('    <Call target="Clear Errors.vi" inputs="error in (no error):p_tip.error out" outputs="error out:p_ce.error out" uid="p_ce" uid_parent="pl"/>')
w('  </Structure>')

# ---- (4) Window, save -------------------------------------------------------------------------
w('  <Node _name="Unbundle By Name" fields="Right" inputs="input cluster:spec.Window" outputs="Right:wr.Right" uid="wr" uid_parent="root"/>')
w('  <Node _name="Greater Than 0?" inputs="x:wr.Right" outputs="x &gt; 0?:wg.x &gt; 0?" uid="wg" uid_parent="root"/>')
# (the window step runs between Tabs and Place - wc.err feeds the Place loop: a later window resize
# moved the contents of a splitter pane that were already placed)
c = Case('wc', 'root', 'wg.x &gt; 0?', ['ov.vi reference', 'spec.Window', 't_end.value'], ['wc.err'], 2)
c.frame('Keep the window', 'False', [2], lambda L, t, f: None, lambda t: [t(2)])


def window(L, t, f):
    L.append('<Constant outputs="value:%so.value" type="cluster{int32.Horizontal,int32.Vertical}" uid="%so" uid_parent="%s" value="[0,0]"/>' % (f, f, f))
    L.append('<Constant outputs="value:%sn.value" type="bool" uid="%sn" uid_parent="%s" value="false"/>' % (f, f, f))
    L.append('<Node _name="Property Node" fields="write+Front Panel Window\\3AShow Menu Bar,write+Tool Bar\\3AVisible,write+Front Panel Window\\3AShow Scroll Bars,write+Front Panel Window\\3APanel Bounds,write+Front Panel Window\\3AOrigin" inputs="reference:%s,error in (no error):%s,Front Panel Window\\3AShow Menu Bar:%sn.value,Tool Bar\\3AVisible:%sn.value,Front Panel Window\\3AShow Scroll Bars:%sn.value,Front Panel Window\\3APanel Bounds:%s,Front Panel Window\\3AOrigin:%so.value" outputs="reference out:,error out:%sw.error out" type="{LV.VI}" uid="%sw" uid_parent="%s"/>' % (t(0), t(2), f, f, f, t(1), f, f, f, f))


c.frame('Window bounds\\2C origin 0\\2C0', 'True', [0, 1, 2], window, lambda t: ['wc_f1w.error out'])
c.emit()
w('  <Node _name="Invoke Node" target="Default Vals.Make Curr Default" type="{LV.VI}" inputs="reference:ov.vi reference,error in (no error):p_end.value" outputs="reference out:,error out:mcd.error out" uid="mcd" uid_parent="root"/>')
w('  <Node _name="Invoke Node" target="Save.Instrument" type="{LV.VI}" inputs="reference:ov.vi reference,error in (no error):mcd.error out" outputs="reference out:,error out:svi.error out" uid="svi" uid_parent="root"/>')
w('  <Node _name="Close Reference" inputs="reference:ov.vi reference,error in (no error):svi.error out" outputs="error out:cr.error out" uid="cr" uid_parent="root"/>')
w('  <Node _name="Build Array" concat="true" inputs="array:r_probs.value,array:t_probs.value,array:p_probs.value" outputs="appended array:pa.appended array" uid="pa" uid_parent="root"/>')
w('  <Indicator _name="problems" conIdx="5" connection="recommended" description="Each step\\27s label\\2C step and error code\\3B 0 is fine." inputs="value:pa.appended array" type="array{string}" uid="pr" uid_parent="root" value="[]"/>')
w('  <Indicator _name="error out" conIdx="11" connection="recommended" description="Errors of opening\\2C the window and saving." inputs="value:cr.error out" type="%s" uid="eo" uid_parent="root" value="%s"/>' % (ERR, E))
w('</VI>')

open(os.path.join(HERE, 'style_panel.xml'), 'w', encoding='utf-8', newline='\n').write('\n'.join(o) + '\n')
print('wrote style_panel.xml,', len(o), 'lines')
