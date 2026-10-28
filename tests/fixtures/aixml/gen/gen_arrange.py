# Generates tests/fixtures/aixml/RemoteVI Complex Fixture Arrange.xml
import os
AX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERR = 'cluster{bool.status,int32.code,string.source}'
E = '[false,0,]'
POS = 'cluster{int32.Left,int32.Top}'

# label, pane, page (-1: the pane itself), x, y  (pane rows: where the control's top-left lands in the frame minus the
# origin message, the coordinates of the layout lines; page rows: from Settings, in pane coordinates)
ROWS = [
    ('View', 1, -1, 300, 6), ('Status', 1, -1, 420, 7),
    ('Inspector', 0, -1, 14, 28), ('Stop', 0, -1, 120, 28),
    ('Nav', 0, -1, 14, 84), ('Results', 0, -1, 14, 310), ('Steps', 0, -1, 14, 600),
    ('Log Path', 0, -1, 14, 860), ('error out', 0, -1, 14, 900),
    ('Settings', 2, -1, 300, 52),
    ('Channel', 2, 0, 20, 50), ('Rate', 2, 0, 230, 40), ('Level', 2, 0, 390, 40), ('Data File', 2, 0, 20, 220),
    ('Scope', 2, 1, 10, 40),
    ('Viewer', 2, 2, 20, 50),
]
lit = lambda xs: '[%s]' % ','.join(str(x) for x in xs)

o = []
w = o.append
w('<VI _name="RemoteVI Complex Fixture Arrange.vi" description="Build tool of RemoteVI Complex Fixture.vi\\3A run it after RemoteVI Complex Fixture Paste.vi\\2C with the fixture idle\\3B it can be run again (every step sets\\2C nothing is added). Lays the panel out\\3A each control is moved (GObject Move) into its pane (0 left\\2C 1 toolbar\\2C 2 main) or into a page of the tab control Settings and placed at fixed panel-area coordinates (the pane coordinates are the wanted point minus where the pane\'s 0\\2C0 lands: CvtPaneToPanelCoords\\2C CvtPanelToScreenCoords\\2C minus Panel Bounds - placing relative to the pane\'s Position drifted from run to run) or relative to Settings. The toolbar holds Inspector\\2C View\\2C Stop and Status\\2C the left pane Nav\\2C Results and Steps (taller than the pane\\2C so it scrolls) and the hidden Log Path and error out\\2C the main pane Settings\\3B page Acquisition holds Channel\\2C Rate\\2C Level and Data File\\2C page Display holds Scope\\2C page Viewer (added with Add Page when the tab has two) the subpanel Viewer. Then\\3A pages named Acquisition\\2C Display and Viewer with fixed 110 px tabs\\2C Stop and Inspector switch when released\\2C Data File with its browse button\\2C Results with column headers and three rows\\2C Steps three elements high\\2C tip strips on Rate\\2C on Gain inside Channel and on Nav\\2C the main pane scaling Settings with the pane (Pane Set Scaling\\2C Scale Single Object)\\2C the left pane\'s vertical scrollbar always on\\2C the window 1180 x 760\\3B in View A\\2C View B and the inspector (Views) the Quit switches hidden and tip strips set. Saves the fixture and the views. problems lists every row or step that returned an error\\2C with its code\\3B the run goes on.">')
w('  <FreeLabel comment="Lay the panel out\\2C then save" uid="lbl" uid_parent="root"/>')
w('  <Control _name="Fixture" conIdx="0" connection="required" description="Path of RemoteVI Complex Fixture.vi. Saved in place." outputs="value:fx.value" type="path" uid="fx" uid_parent="root" value=""/>')
w('  <Control _name="error in" conIdx="11" connection="recommended" description="Error chain in." outputs="value:ei.value" type="%s" uid="ei" uid_parent="root" value="%s"/>' % (ERR, E))
w('  <Node _name="Open VI Reference" inputs="vi path:fx.value,error in (no error):ei.value" outputs="vi reference:of.vi reference,error out:of.error out" uid="of" uid_parent="root"/>')
w('  <Node _name="Property Node" fields="read+Front Panel" inputs="reference:of.vi reference,error in (no error):of.error out" outputs="reference out:,error out:fpf.error out,Front Panel:fpf.fp" type="{LV.VI}" uid="fpf" uid_parent="root"/>')
w('  <Node _name="Property Node" fields="read+Panes[]" inputs="reference:fpf.fp,error in (no error):fpf.error out" outputs="reference out:,error out:pp.error out,Panes[]:pp.panes" type="{LV.Panel}" uid="pp" uid_parent="root"/>')
# the window first, so the panes have their final size
w('  <Constant _name="window" outputs="value:wb.value" type="cluster{int32.Left,int32.Top,int32.Right,int32.Bottom}" uid="wb" uid_parent="root" value="[80,80,1260,840]"/>')
w('  <Node _name="Property Node" fields="write+Front Panel Window\\3APanel Bounds" inputs="reference:of.vi reference,error in (no error):pp.error out,Front Panel Window\\3APanel Bounds:wb.value" outputs="reference out:,error out:wn.error out" type="{LV.VI}" uid="wn" uid_parent="root"/>')
# Settings: its pages
w('  <Constant _name="settings" outputs="value:lst.value" type="array{string}" uid="lst" uid_parent="root" value="[Settings,Gain]"/>')
w('  <Call target="RemoteVI Complex Fixture Find Controls.vi" inputs="Panel:fpf.fp,labels:lst.value,error in:wn.error out" outputs="Controls:fst.Controls,error out:fst.error out" uid="fst" uid_parent="root"/>')
w('  <Constant _name="zero" outputs="value:i0.value" type="int32" uid="i0" uid_parent="root" value="0"/>')
w('  <Constant _name="one" outputs="value:i1.value" type="int32" uid="i1" uid_parent="root" value="1"/>')
w('  <Node _name="Index Array" inputs="array:fst.Controls,index:i0.value" outputs="element:ist.element" uid="ist" uid_parent="root"/>')
w('  <Constant _name="tab class" outputs="value:cta.value" type="ref{LV.TabControl}" uid="cta" uid_parent="root" value=""/>')
w('  <Node _name="To More Specific Class" inputs="target class:cta.value,reference:ist.element,error in:fst.error out" outputs="specific class reference:tab.ref,error out:tab.error out" uid="tab" uid_parent="root"/>')
w('  <Constant _name="fixed tab size" outputs="value:tsz.value" type="int32" uid="tsz" uid_parent="root" value="2"/>')
w('  <Constant _name="tab dimension" outputs="value:tdm.value" type="cluster{int32.Width,int32.Height}" uid="tdm" uid_parent="root" value="[110,23]"/>')
w('  <Node _name="Property Node" fields="write+Tab Size,write+Fixed Tab Dimension,read+Pages" inputs="reference:tab.ref,error in (no error):tab.error out,Tab Size:tsz.value,Fixed Tab Dimension:tdm.value" outputs="reference out:,error out:tp.error out,Pages:tp.pages" type="{LV.TabControl}" uid="tp" uid_parent="root"/>')
w('  <Node _name="Array Size" inputs="array:tp.pages" outputs="size(s):tpn.size" uid="tpn" uid_parent="root"/>')
w('  <Constant _name="three" outputs="value:i3.value" type="int32" uid="i3" uid_parent="root" value="3"/>')
w('  <Node _name="Less?" inputs="x:tpn.size,y:i3.value" outputs="x &lt; y?:tpl.x &lt; y?" uid="tpl" uid_parent="root"/>')
w('  <Structure _name="Case Structure" selectin="tpl.x &lt; y?" uid="cap" uid_parent="root">')
w('    <Tunnel _id="In1" inputs="value:tab.ref" uid="capi1" uid_parent="cap"/>')
w('    <Tunnel _id="In2" inputs="value:tp.error out" uid="capi2" uid_parent="cap"/>')
w('    <Tunnel _id="In3" inputs="value:tp.pages" uid="capi3" uid_parent="cap"/>')
w('    <CaseFrame label="Two pages\\3A add the third (Viewer)" selector="True" selectout="" uid="capT" uid_parent="cap">')
w('      <Tunnel _id="In1" outputs="value:apt1.value" uid="apt1" uid_parent="capT"/>')
w('      <Tunnel _id="In2" outputs="value:apt2.value" uid="apt2" uid_parent="capT"/>')
w('      <Tunnel _id="In3" outputs="value:" uid="apt3" uid_parent="capT"/>')
w('      <Constant _name="after page 1" outputs="value:apk.value" type="int32" uid="apk" uid_parent="capT" value="1"/>')
w('      <Constant _name="after" outputs="value:apa.value" type="bool" uid="apa" uid_parent="capT" value="true"/>')
w('      <Node _name="Invoke Node" target="Add Page" type="{LV.TabControl}" inputs="reference:apt1.value,error in (no error):apt2.value,Page:apk.value,After:apa.value" outputs="reference out:,error out:apn.error out" uid="apn" uid_parent="capT"/>')
w('      <Node _name="Property Node" fields="read+Pages" inputs="reference:apt1.value,error in (no error):apn.error out" outputs="reference out:,error out:apr.error out,Pages:apr.pages" type="{LV.TabControl}" uid="apr" uid_parent="capT"/>')
w('      <Tunnel _id="Out1" inputs="value:apr.pages" uid="apto1" uid_parent="capT"/>')
w('      <Tunnel _id="Out2" inputs="value:apr.error out" uid="apto2" uid_parent="capT"/>')
w('    </CaseFrame>')
w('    <CaseFrame selector="False" selectout="" uid="capF" uid_parent="cap">')
w('      <Tunnel _id="In1" outputs="value:" uid="apf1" uid_parent="capF"/>')
w('      <Tunnel _id="In2" outputs="value:apf2.value" uid="apf2" uid_parent="capF"/>')
w('      <Tunnel _id="In3" outputs="value:apf3.value" uid="apf3" uid_parent="capF"/>')
w('      <Tunnel _id="Out1" inputs="value:apf3.value" uid="apfo1" uid_parent="capF"/>')
w('      <Tunnel _id="Out2" inputs="value:apf2.value" uid="apfo2" uid_parent="capF"/>')
w('    </CaseFrame>')
w('    <Tunnel _id="Out1" outputs="value:cap.pages" uid="capo1" uid_parent="cap"/>')
w('    <Tunnel _id="Out2" outputs="value:cap.err" uid="capo2" uid_parent="cap"/>')
w('  </Structure>')
w('  <Constant _name="page names" outputs="value:pgn.value" type="array{string}" uid="pgn" uid_parent="root" value="[Acquisition,Display,Viewer]"/>')
w('  <Structure _name="For Loop" count="" label="Name the pages" maxin="" maxout="" uid="fpg" uid_parent="root">')
w('    <Tunnel _id="In1" inputs="value:cap.pages" mode="index" outputs="value:pg.value" uid="pg" uid_parent="fpg"/>')
w('    <Tunnel _id="In2" inputs="value:pgn.value" mode="index" outputs="value:pgl.value" uid="pgl" uid_parent="fpg"/>')
w('    <ShiftReg uid="srp" uid_parent="fpg">')
w('      <Left inputs="value:cap.err" outputs="value:pe.value" uid="srpl" uid_parent="srp"/>')
w('      <Right inputs="value:pw.error out" outputs="value:pageErr.value" uid="srpr" uid_parent="srp"/>')
w('    </ShiftReg>')
w('    <Node _name="Property Node" fields="write+Page Label,write+Tab Caption" inputs="reference:pg.value,error in (no error):pe.value,Page Label:pgl.value,Tab Caption:pgl.value" outputs="reference out:,error out:pw.error out" type="{LV.Page}" uid="pw" uid_parent="fpg"/>')
w('  </Structure>')
w('  <Call target="Clear Errors.vi" inputs="error in (no error):pageErr.value" outputs="error out:ce0.error out" uid="ce0" uid_parent="root"/>')
# rows
w('  <Constant _name="labels" outputs="value:rl.value" type="array{string}" uid="rl" uid_parent="root" value="%s"/>' % lit(r[0] for r in ROWS))
w('  <Constant _name="panes" outputs="value:rp.value" type="array{int32}" uid="rp" uid_parent="root" value="%s"/>' % lit(r[1] for r in ROWS))
w('  <Constant _name="pages" outputs="value:rg.value" type="array{int32}" uid="rg" uid_parent="root" value="%s"/>' % lit(r[2] for r in ROWS))
w('  <Constant _name="offsets" outputs="value:ro.value" type="array{%s}" uid="ro" uid_parent="root" value="%s"/>' % (POS, lit('[%d,%d]' % (r[3], r[4]) for r in ROWS)))
w('  <Constant _name="no duplicate" outputs="value:nd.value" type="bool" uid="nd" uid_parent="root" value="false"/>')
w('  <Node _name="Property Node" fields="read+Front Panel Window\\3APanel Bounds" inputs="reference:of.vi reference,error in (no error):" outputs="Front Panel Window\\3APanel Bounds:fpb.pb,reference out:,error out:" type="{LV.VI}" uid="fpb" uid_parent="root"/>')
w('  <Node _name="Unbundle By Name" fields="left,top" inputs="input cluster:fpb.pb" outputs="left:fpbu.l,top:fpbu.t" uid="fpbu" uid_parent="root"/>')
w('  <Structure _name="For Loop" count="" label="Move each control into its pane or page and place it" maxin="" maxout="" uid="fl" uid_parent="root">')
for i, (src, nm) in enumerate((('rl.value', 'lL'), ('rp.value', 'lP'), ('rg.value', 'lG'), ('ro.value', 'lO')), 1):
    w('    <Tunnel _id="In%d" inputs="value:%s" mode="index" outputs="value:%s.value" uid="%s" uid_parent="fl"/>' % (i, src, nm, nm))
for i, (src, nm) in enumerate((('fpf.fp', 'lF'), ('pp.panes', 'lPs'), ('tab.ref', 'lT'), ('nd.value', 'lD'), ('ce0.error out', 'lE'), ('fpbu.l', 'lBl'), ('fpbu.t', 'lBt')), 5):
    w('    <Tunnel _id="In%d" inputs="value:%s" outputs="value:%s.value" uid="%s" uid_parent="fl"/>' % (i, src, nm, nm))
w('    <Node _name="Build Array" inputs="element:lL.value" outputs="appended array:l1.appended array" uid="l1" uid_parent="fl"/>')
w('    <Call target="RemoteVI Complex Fixture Find Controls.vi" inputs="Panel:lF.value,labels:l1.appended array,error in:lE.value" outputs="Controls:fc.Controls,error out:fc.error out" uid="fc" uid_parent="fl"/>')
w('    <Constant _name="zero" outputs="value:z.value" type="int32" uid="z" uid_parent="fl" value="0"/>')
w('    <Node _name="Index Array" inputs="array:fc.Controls,index:z.value" outputs="element:ctl.element" uid="ctl" uid_parent="fl"/>')
w('    <Node _name="Index Array" inputs="array:lPs.value,index:lP.value" outputs="element:pane.element" uid="pane" uid_parent="fl"/>')
w('    <Node _name="Property Node" fields="read+Position" inputs="reference:pane.element,error in (no error):fc.error out" outputs="reference out:,error out:pnp.error out,Position:pnp.pos" type="{LV.GObject}" uid="pnp" uid_parent="fl"/>')
w('    <Node _name="Less Than 0?" inputs="x:lG.value" outputs="x &lt; 0?:np.x &lt; 0?" uid="np" uid_parent="fl"/>')
w('    <Node _name="Unbundle By Name" fields="Left,Top" inputs="input cluster:lO.value" outputs="Left:uo.l,Top:uo.t" uid="uo" uid_parent="fl"/>')
w('    <Structure _name="Case Structure" selectin="np.x &lt; 0?" uid="cs" uid_parent="fl">')
for i, src in enumerate(('ctl.element', 'pane.element', 'pnp.pos', 'lT.value', 'lG.value', 'uo.l', 'uo.t', 'lD.value', 'pnp.error out', 'lF.value', 'lBl.value', 'lBt.value'), 1):
    w('      <Tunnel _id="In%d" inputs="value:%s" uid="csi%d" uid_parent="cs"/>' % (i, src, i))
# pane row: owner = the pane, position = pane origin + offset
w('      <CaseFrame label="Into the pane" selector="True" selectout="" uid="cT" uid_parent="cs">')
for i in range(1, 13):
    w('        <Tunnel _id="In%d" outputs="value:%s" uid="t%d" uid_parent="cT"/>' % (i, ('t%d.value' % i) if i not in (3, 4, 5) else '', i))
w('        <Constant _name="pane origin" outputs="value:t0p.value" type="cluster{int32.Horizontal,int32.Vertical}" uid="t0p" uid_parent="cT" value="[0,0]"/>')
w('        <Node _name="Invoke Node" target="CvtPaneToPanelCoords" type="{LV.Pane}" inputs="reference:t2.value,error in (no error):t9.value,PaneCoords:t0p.value" outputs="reference out:,error out:tcv.error out,PanelCoords:tcv.pc" uid="tcv" uid_parent="cT"/>')
w('        <Node _name="Invoke Node" target="CvtPanelToScreenCoords" type="{LV.Panel}" inputs="reference:t10.value,error in (no error):tcv.error out,PanelCoords:tcv.pc" outputs="reference out:,error out:tcs.error out,ScreenCoords:tcs.sc" uid="tcs" uid_parent="cT"/>')
w('        <Node _name="Unbundle By Name" fields="Horizontal,Vertical" inputs="input cluster:tcs.sc" outputs="Horizontal:tq.l,Vertical:tq.t" uid="tq" uid_parent="cT"/>')
w('        <Node _name="Subtract" inputs="x:tq.l,y:t11.value" outputs="x-y:tbx.x-y" uid="tbx" uid_parent="cT"/>')
w('        <Node _name="Subtract" inputs="x:tq.t,y:t12.value" outputs="x-y:tby.x-y" uid="tby" uid_parent="cT"/>')
w('        <Node _name="Subtract" inputs="x:t6.value,y:tbx.x-y" outputs="x-y:tx.x+y" uid="tx" uid_parent="cT"/>')
w('        <Node _name="Subtract" inputs="x:t7.value,y:tby.x-y" outputs="x-y:ty.x+y" uid="ty" uid_parent="cT"/>')
w('        <Constant _name="position" outputs="value:tp0.value" type="cluster{int32.Left,int32.Top}" uid="tp0" uid_parent="cT" value="[0,0]"/>')
w('        <Node _name="Bundle By Name" fields="Left,Top" inputs="input cluster:tp0.value,Left:tx.x+y,Top:ty.x+y" outputs="output cluster:tb.output cluster" uid="tb" uid_parent="cT"/>')
w('        <Node _name="Invoke Node" target="Move" type="{LV.Control}" inputs="reference:t1.value,error in (no error):tcs.error out,position:tb.output cluster,owner:t2.value,duplicate:t8.value" outputs="reference out:,error out:tm.error out" uid="tm" uid_parent="cT"/>')
w('        <Node _name="Property Node" fields="write+Position" inputs="reference:t1.value,error in (no error):tm.error out,Position:tb.output cluster" outputs="reference out:,error out:tw.error out" type="{LV.Control}" uid="tw" uid_parent="cT"/>')
w('        <Tunnel _id="Out1" inputs="value:tw.error out" uid="tO1" uid_parent="cT"/>')
w('      </CaseFrame>')
# page row: owner = the page of Settings, position = Settings position + offset
w('      <CaseFrame label="Onto a page of Settings" selector="False" selectout="" uid="cF" uid_parent="cs">')
for i in range(1, 13):
    w('        <Tunnel _id="In%d" outputs="value:%s" uid="f%d" uid_parent="cF"/>' % (i, ('f%d.value' % i) if i not in (2, 3, 10, 11, 12) else '', i))
w('        <Node _name="Property Node" fields="read+Pages" inputs="reference:f4.value,error in (no error):f9.value" outputs="reference out:,error out:fpq.error out,Pages:fpq.pages" type="{LV.TabControl}" uid="fpq" uid_parent="cF"/>')
w('        <Node _name="Index Array" inputs="array:fpq.pages,index:f5.value" outputs="element:fpe.element" uid="fpe" uid_parent="cF"/>')
w('        <Node _name="Property Node" fields="read+Position" inputs="reference:f4.value,error in (no error):fpq.error out" outputs="reference out:,error out:ftp.error out,Position:ftp.pos" type="{LV.Control}" uid="ftp" uid_parent="cF"/>')
w('        <Node _name="Unbundle By Name" fields="Left,Top" inputs="input cluster:ftp.pos" outputs="Left:fq.l,Top:fq.t" uid="fq" uid_parent="cF"/>')
w('        <Node _name="Add" inputs="x:fq.l,y:f6.value" outputs="x+y:fxa.x+y" uid="fxa" uid_parent="cF"/>')
w('        <Node _name="Add" inputs="x:fq.t,y:f7.value" outputs="x+y:fy.x+y" uid="fy" uid_parent="cF"/>')
w('        <Node _name="Bundle By Name" fields="Left,Top" inputs="input cluster:ftp.pos,Left:fxa.x+y,Top:fy.x+y" outputs="output cluster:fb.output cluster" uid="fb" uid_parent="cF"/>')
w('        <Node _name="Invoke Node" target="Move" type="{LV.Control}" inputs="reference:f1.value,error in (no error):ftp.error out,position:fb.output cluster,owner:fpe.element,duplicate:f8.value" outputs="reference out:,error out:fm.error out" uid="fm" uid_parent="cF"/>')
w('        <Node _name="Property Node" fields="write+Position" inputs="reference:f1.value,error in (no error):fm.error out,Position:fb.output cluster" outputs="reference out:,error out:fw.error out" type="{LV.Control}" uid="fw" uid_parent="cF"/>')
w('        <Tunnel _id="Out1" inputs="value:fw.error out" uid="fO1" uid_parent="cF"/>')
w('      </CaseFrame>')
w('      <Tunnel _id="Out1" outputs="value:cs.err" uid="csO1" uid_parent="cs"/>')
w('    </Structure>')
w('    <Node _name="Unbundle By Name" fields="code" inputs="input cluster:cs.err" outputs="code:ue.code" uid="ue" uid_parent="fl"/>')
w('    <Constant _name="fmt" outputs="value:pf.value" type="string" uid="pf" uid_parent="fl" value="%s %d"/>')
w('    <Node _name="Format Into String" inputs="format string:pf.value,input 1:lL.value,input 2:ue.code" outputs="resulting string:ps.resulting string" uid="ps" uid_parent="fl"/>')
w('    <Tunnel _id="Out1" inputs="value:ps.resulting string" mode="index" outputs="value:rowProblems.value" uid="rowProblems" uid_parent="fl"/>')
w('    <Tunnel _id="Out2" inputs="value:cs.err" outputs="value:lastErr.value" uid="lastErr" uid_parent="fl"/>')
w('  </Structure>')

# property steps: (label, class, fields, input values) - each its own error, collected as text
STEPS = [
    ('Stop', 'LV.Boolean', 'Mechanical Action', 'uint32', '1'),
    ('Inspector', 'LV.Boolean', 'Mechanical Action', 'uint32', '1'),
    ('Log Path', 'LV.Control', 'Visible', 'bool', 'false'),
    ('error out', 'LV.Control', 'Visible', 'bool', 'false'),
    ('Data File', 'LV.Path', 'Browse Button\\3AVisible', 'bool', 'true'),
    ('Results', 'LV.Table', 'Visible Items\\3AColumn Headers Visible', 'bool', 'true'),
    ('Results', 'LV.Table', 'Column Header Strings[]', 'array{string}', '[Step,Value]'),
    ('Results', 'LV.Table', 'Value', 'array.2{string}', '[[Init,1],[Run,2],[Stop,3]]'),
    ('Steps', 'LV.Array', 'Number of Rows', 'uint32', '3'),
    ('Rate', 'LV.Control', 'TipStrip', 'string', 'Sample rate'),
    ('Gain', 'LV.Control', 'TipStrip', 'string', 'Channel gain'),
    ('Nav', 'LV.Control', 'TipStrip', 'string', 'Pick a section'),
    ('View', 'LV.Control', 'Label.Visible', 'bool', 'false'),
    ('Status', 'LV.Control', 'Label.Visible', 'bool', 'false'),
]
w('  <Call target="Clear Errors.vi" inputs="error in (no error):lastErr.value" outputs="error out:ce1.error out" uid="ce1" uid_parent="root"/>')
prev = None
for k, (label, cls, field, typ, val) in enumerate(STEPS):
    u = 's%d' % k
    w('  <Constant _name="%s" outputs="value:%sl.value" type="array{string}" uid="%sl" uid_parent="root" value="[%s]"/>' % (label, u, u, label))
    w('  <Call target="RemoteVI Complex Fixture Find Controls.vi" inputs="Panel:fpf.fp,labels:%sl.value,error in:%s" outputs="Controls:%sf.Controls,error out:%sf.error out" uid="%sf" uid_parent="root"/>' % (u, prev or 'ce1.error out', u, u, u))
    w('  <Node _name="Index Array" inputs="array:%sf.Controls,index:i0.value" outputs="element:%si.element" uid="%si" uid_parent="root"/>' % (u, u, u))
    if cls != 'LV.Control':
        w('  <Constant _name="class" outputs="value:%sc.value" type="ref{%s}" uid="%sc" uid_parent="root" value=""/>' % (u, cls, u))
        w('  <Node _name="To More Specific Class" inputs="target class:%sc.value,reference:%si.element,error in:%sf.error out" outputs="specific class reference:%st.ref,error out:%st.error out" uid="%st" uid_parent="root"/>' % (u, u, u, u, u, u))
        ref, err = '%st.ref' % u, '%st.error out' % u
    else:
        ref, err = '%si.element' % u, '%sf.error out' % u
    w('  <Constant _name="value" outputs="value:%sv.value" type="%s" uid="%sv" uid_parent="root" value="%s"/>' % (u, typ, u, val))
    w('  <Node _name="Property Node" fields="write+%s" inputs="reference:%s,error in (no error):%s,%s:%sv.value" outputs="reference out:,error out:%sp.error out" type="{%s}" uid="%sp" uid_parent="root"/>' % (field, ref, err, field, u, u, cls, u))
    w('  <Node _name="Unbundle By Name" fields="code" inputs="input cluster:%sp.error out" outputs="code:%se.code" uid="%se" uid_parent="root"/>' % (u, u, u))
    w('  <Call target="Clear Errors.vi" inputs="error in (no error):%sp.error out" outputs="error out:%sx.error out" uid="%sx" uid_parent="root"/>' % (u, u, u))
    prev = '%sx.error out' % u
    w('  <Constant _name="fmt" outputs="value:%sm.value" type="string" uid="%sm" uid_parent="root" value="%s %s %%d"/>' % (u, u, label, field.replace('\\3A', ':')))
    w('  <Node _name="Format Into String" inputs="format string:%sm.value,input 1:%se.code" outputs="resulting string:%ss.resulting string" uid="%ss" uid_parent="root"/>' % (u, u, u, u))
# pane scaling of the main pane: Settings scales with it
w('  <Constant _name="two" outputs="value:i2.value" type="int32" uid="i2" uid_parent="root" value="2"/>')
w('  <Node _name="Index Array" inputs="array:pp.panes,index:i2.value" outputs="element:mp.element" uid="mp" uid_parent="root"/>')
w('  <Constant _name="scale single object" outputs="value:ssm.value" type="uint16{No Scaling,Scale All Objects,Scale Single Object}" uid="ssm" uid_parent="root" value="2"/>')
w('  <Node _name="Invoke Node" target="Set Scaling" type="{LV.Pane}" inputs="reference:mp.element,error in (no error):%s,ScalingMode:ssm.value,ScalableObj:ist.element" outputs="reference out:,error out:sc.error out" uid="sc" uid_parent="root"/>' % prev)
w('  <Node _name="Unbundle By Name" fields="code" inputs="input cluster:sc.error out" outputs="code:sce.code" uid="sce" uid_parent="root"/>')
w('  <Constant _name="fmt" outputs="value:scm.value" type="string" uid="scm" uid_parent="root" value="Set Scaling %d"/>')
w('  <Node _name="Format Into String" inputs="format string:scm.value,input 1:sce.code" outputs="resulting string:scs.resulting string" uid="scs" uid_parent="root"/>')
# the left pane gets a vertical scrollbar (NI's donor panel has them off while running), so it scrolls
w('  <Node _name="Index Array" inputs="array:pp.panes,index:i0.value" outputs="element:lp0.element" uid="lp0" uid_parent="root"/>')
w('  <Constant _name="always on" outputs="value:vsb.value" type="uint16{Always On,Always Off,Off While Running}" uid="vsb" uid_parent="root" value="0"/>')
w('  <Node _name="Property Node" fields="write+VertScrollbarVisibility" inputs="reference:lp0.element,error in (no error):sc.error out,VertScrollbarVisibility:vsb.value" outputs="reference out:,error out:sb.error out" type="{LV.Pane}" uid="sb" uid_parent="root"/>')
w('  <Node _name="Unbundle By Name" fields="code" inputs="input cluster:sb.error out" outputs="code:sbe.code" uid="sbe" uid_parent="root"/>')
w('  <Constant _name="fmt" outputs="value:sbm.value" type="string" uid="sbm" uid_parent="root" value="VertScrollbarVisibility %d"/>')
w('  <Node _name="Format Into String" inputs="format string:sbm.value,input 1:sbe.code" outputs="resulting string:sbs.resulting string" uid="sbs" uid_parent="root"/>')

# the views and the inspector window: hide the Quit switches (set with Value (Signaling) at stop), tip strip on A Apply
w('  <Control _name="Views" conIdx="1" connection="recommended" description="Paths of RemoteVI Complex View A.vi\\2C View B.vi and Inspector.vi\\3B each is edited and saved." outputs="value:vws.value" type="array{path}" uid="vws" uid_parent="root" value="[]"/>')
w('  <Constant _name="quit labels" outputs="value:vql.value" type="array{string}" uid="vql" uid_parent="root" value="[A Quit,B Quit,Inspector Quit]"/>')
w('  <Constant _name="tip labels" outputs="value:vtl.value" type="array{string}" uid="vtl" uid_parent="root" value="[A Apply,B Run,Apply]"/>')
w('  <Constant _name="tips" outputs="value:vtt.value" type="array{string}" uid="vtt" uid_parent="root" value="[Apply view A,Run view B,Apply the note]"/>')
w('  <Constant _name="hidden" outputs="value:vhf.value" type="bool" uid="vhf" uid_parent="root" value="false"/>')
w('  <Structure _name="For Loop" count="" label="Each view" maxin="" maxout="" uid="fv" uid_parent="root">')
w('    <Tunnel _id="In1" inputs="value:vws.value" mode="index" outputs="value:vp.value" uid="vp" uid_parent="fv"/>')
w('    <Tunnel _id="In2" inputs="value:vql.value" mode="index" outputs="value:vq.value" uid="vq" uid_parent="fv"/>')
w('    <Tunnel _id="In3" inputs="value:vtl.value" mode="index" outputs="value:vt.value" uid="vt" uid_parent="fv"/>')
w('    <Tunnel _id="In4" inputs="value:vtt.value" mode="index" outputs="value:vx.value" uid="vx" uid_parent="fv"/>')
w('    <Tunnel _id="In5" inputs="value:vhf.value" outputs="value:vh.value" uid="vh" uid_parent="fv"/>')
w('    <Tunnel _id="In6" inputs="value:i0.value" outputs="value:v0.value" uid="v0" uid_parent="fv"/>')
w('    <Tunnel _id="In7" inputs="value:i1.value" outputs="value:v1.value" uid="v1" uid_parent="fv"/>')
w('    <Node _name="Open VI Reference" inputs="vi path:vp.value" outputs="vi reference:vo.vi reference,error out:vo.error out" uid="vo" uid_parent="fv"/>')
w('    <Node _name="Property Node" fields="read+Front Panel" inputs="reference:vo.vi reference,error in (no error):vo.error out" outputs="reference out:,error out:vf.error out,Front Panel:vf.fp" type="{LV.VI}" uid="vf" uid_parent="fv"/>')
w('    <Node _name="Build Array" inputs="element:vq.value,element:vt.value" outputs="appended array:vb.appended array" uid="vb" uid_parent="fv"/>')
w('    <Call target="RemoteVI Complex Fixture Find Controls.vi" inputs="Panel:vf.fp,labels:vb.appended array,error in:vf.error out" outputs="Controls:vc.Controls,error out:vc.error out" uid="vc" uid_parent="fv"/>')
w('    <Node _name="Index Array" inputs="array:vc.Controls,index:v0.value" outputs="element:vqr.element" uid="vqr" uid_parent="fv"/>')
w('    <Node _name="Index Array" inputs="array:vc.Controls,index:v1.value" outputs="element:vtr.element" uid="vtr" uid_parent="fv"/>')
w('    <Node _name="Property Node" fields="write+Visible" inputs="reference:vqr.element,error in (no error):vc.error out,Visible:vh.value" outputs="reference out:,error out:vw1.error out" type="{LV.Control}" uid="vw1" uid_parent="fv"/>')
w('    <Node _name="Property Node" fields="write+TipStrip" inputs="reference:vtr.element,error in (no error):vw1.error out,TipStrip:vx.value" outputs="reference out:,error out:vw2.error out" type="{LV.Control}" uid="vw2" uid_parent="fv"/>')
w('    <Node _name="Invoke Node" target="Save.Instrument" type="{LV.VI}" inputs="reference:vo.vi reference,error in (no error):vw2.error out" outputs="reference out:,error out:vsv.error out" uid="vsv" uid_parent="fv"/>')
w('    <Node _name="Close Reference" inputs="reference:vo.vi reference,error in (no error):vsv.error out" outputs="error out:vcl.error out" uid="vcl" uid_parent="fv"/>')
w('    <Node _name="Unbundle By Name" fields="code" inputs="input cluster:vcl.error out" outputs="code:vce.code" uid="vce" uid_parent="fv"/>')
w('    <Constant _name="fmt" outputs="value:vfm.value" type="string" uid="vfm" uid_parent="fv" value="view %s %d"/>')
w('    <Node _name="Format Into String" inputs="format string:vfm.value,input 1:vq.value,input 2:vce.code" outputs="resulting string:vfs.resulting string" uid="vfs" uid_parent="fv"/>')
w('    <Tunnel _id="Out1" inputs="value:vfs.resulting string" mode="index" outputs="value:viewProblems.value" uid="viewProblems" uid_parent="fv"/>')
w('  </Structure>')
parts = ','.join(['element:rowProblems.value' ] + ['element:s%ds.resulting string' % k for k in range(len(STEPS))] + ['element:scs.resulting string', 'element:sbs.resulting string'])
# Build Array: the rows' array first (concatenated), then one element per step
w('  <Node _name="Build Array" inputs="%s" outputs="appended array:all.appended array" uid="all" uid_parent="root"/>' % ','.join(['array:rowProblems.value'] + ['element:s%ds.resulting string' % k for k in range(len(STEPS))] + ['element:scs.resulting string', 'element:sbs.resulting string', 'array:viewProblems.value']))
w('  <Indicator _name="problems" conIdx="4" connection="recommended" description="One line per row and step\\3A its label and error code (0 = done)." inputs="value:all.appended array" type="array{string}" uid="pr" uid_parent="root" value="[]"/>')
# save after everything: sequence through the last step's error and the scaling
w('  <Node _name="Merge Errors" inputs="error in:s%dp.error out,error in:sb.error out" outputs="error out:mm.error out" uid="mm" uid_parent="root"/>' % (len(STEPS) - 1))
w('  <Call target="Clear Errors.vi" inputs="error in (no error):mm.error out" outputs="error out:ce2.error out" uid="ce2" uid_parent="root"/>')
w('  <Node _name="Invoke Node" target="Save.Instrument" type="{LV.VI}" inputs="reference:of.vi reference,error in (no error):ce2.error out" outputs="reference out:sv.reference out,error out:sv.error out" uid="sv" uid_parent="root"/>')
w('  <Node _name="Close Reference" inputs="reference:sv.reference out,error in (no error):sv.error out" outputs="error out:cr.error out" uid="cr" uid_parent="root"/>')
w('  <Indicator _name="error out" conIdx="15" connection="recommended" description="Errors of opening and saving the fixture (the layout steps report in problems)." inputs="value:cr.error out" type="%s" uid="eo" uid_parent="root" value="%s"/>' % (ERR, E))
w('</VI>')
open(os.path.join(AX, 'RemoteVI Complex Fixture Arrange.xml'), 'w', encoding='utf-8', newline='\n').write('\n'.join(o) + '\n')
print('ok')
