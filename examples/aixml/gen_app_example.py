"""Generates the AIXML of the RemoteVI application example (examples/RemoteVI Application Example.vi).

The example is what a LabVIEW application with a professional UI looks like when RemoteVI shares it:
NI's splitter panel - a toolbar pane on top, a navigation menu on the left that a splitter bar splits
off, and a main pane with a subpanel. The menu loads one of four screens into the subpanel:

  RemoteVI App Live Data.vi   four simulated channels on a graph, statistics, pause
  RemoteVI App Log Files.vi   simulated log files: preview, delete (LabVIEW dialog), export (file dialog)
  RemoteVI App Alarms.vi      simulated alarms arriving, acknowledge one or all
  RemoteVI App Settings.vi    station settings, save (LabVIEW dialog)

Every screen is a VI of its own with its own loop; the main VI runs all four (Run VI, no wait) and
swaps the one shown in the subpanel. They stop when the main VI sends on the named notifier
"RemoteVI Application Example". Nothing is written to disk: the data are simulated.

Written files (examples/aixml/):
  app_main.xml        the main VI's diagram and controls, composed to a scaffold that is grafted into
                      NI's splitter panel (build_app_example.py has the steps)
  app_live_data.xml, app_log_files.xml, app_alarms.xml, app_settings.xml   the screens

usage: python examples/aixml/gen_app_example.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools', 'aixml'))
from aixml_case import Case  # noqa: E402

ERR = 'cluster{bool.status,int32.code,string.source}'
NOTIFIER = 'RemoteVI Application Example'
PERIOD_MS = 100
o = []


def w(line):
    o.append(line)


def const(uid, typ, value, parent='root', name='', ind=2):
    nm = ' _name="%s"' % name if name else ''
    w('%s<Constant%s outputs="value:%s.value" type="%s" uid="%s" uid_parent="%s" value="%s"/>' % (' ' * ind, nm, uid, typ, uid, parent, value))
    return uid + '.value'


def node(name, ins, outs, uid, parent='root', extra='', ind=2):
    w('%s<Node _name="%s" inputs="%s" outputs="%s" uid="%s" uid_parent="%s"%s/>' % (' ' * ind, name, ins, outs, uid, parent, extra))


def ctl(name, typ, value, uid, parent='sl', desc='', extra='', ind=4):
    w('%s<Control _name="%s" description="%s" outputs="value:%s.value" type="%s" uid="%s" uid_parent="%s" value="%s"%s/>'
      % (' ' * ind, name, desc, uid, typ, uid, parent, value, extra))
    return uid + '.value'


def ind_(name, typ, net, uid, parent='sl', desc='', extra='', value='', ind=4):
    w('%s<Indicator _name="%s" description="%s" inputs="value:%s" type="%s" uid="%s" uid_parent="%s" value="%s"%s/>'
      % (' ' * ind, name, desc, net, typ, uid, parent, value, extra))


def L_const(L, uid, typ, value, parent):
    L.append('<Constant outputs="value:%s.value" type="%s" uid="%s" uid_parent="%s" value="%s"/>' % (uid, typ, uid, parent, value))
    return uid + '.value'


def L_node(L, name, ins, outs, uid, parent, extra=''):
    L.append('<Node _name="%s" inputs="%s" outputs="%s" uid="%s" uid_parent="%s"%s/>' % (name, ins, outs, uid, parent, extra))


def strs(items):
    """An AIXML array literal of strings."""
    return '[' + ','.join(items) + ']'


def strs2(rows):
    return '[' + ','.join(strs(r) for r in rows) + ']'


def save(name):
    open(os.path.join(HERE, name), 'w', encoding='utf-8', newline='\n').write('\n'.join(o) + '\n')
    print('wrote', name, len(o), 'lines')
    del o[:]


# ---------------------------------------------------------------- screens: a loop until the notifier fires
def screen_begin(vi, desc, regs):
    """regs: (uid, initial net, right net) per shift register; left nets are <uid>.value. The initial
    constants, written while the arguments were evaluated, move behind the VI line."""
    pre = o[:]
    del o[:]
    w('<VI _name="%s" description="%s">' % (vi, desc))
    o.extend(pre)
    w('  <FreeLabel comment="A screen of RemoteVI Application Example.vi\\3A runs until the notifier %s fires" uid="lbl" uid_parent="root"/>' % NOTIFIER)
    const('nn', 'string', NOTIFIER, name='notifier name')
    const('nt', 'bool', 'false', name='notification type')
    node('Obtain Notifier', 'name (unnamed):nn.value,notification data type:nt.value', 'notifier out:on.notifier out,created new?:,error out:on.error out', 'on')
    w('  <Structure _name="While Loop" count="" label="Screen loop\\2C every %d ms" uid="sl" uid_parent="root">' % PERIOD_MS)
    w('    <Tunnel _id="In1" inputs="value:on.notifier out" outputs="value:l_n.value" uid="l_n" uid_parent="sl"/>')
    for uid, init, right in regs:
        w('    <ShiftReg uid="%s_sr" uid_parent="sl">' % uid)
        w('      <Left inputs="value:%s" outputs="value:%s.value" uid="%s" uid_parent="%s_sr"/>' % (init, uid, uid, uid))
        w('      <Right inputs="value:%s" outputs="value:" uid="%s_r" uid_parent="%s_sr"/>' % (right, uid, uid))
        w('    </ShiftReg>')


def screen_end():
    const('tmo', 'int32', str(PERIOD_MS), 'sl', ind=4)
    node('Wait on Notification', 'notifier:l_n.value,timeout in ms (-1):tmo.value',
         'notifier out:won.notifier out,notification:,timed out?:won.timed out?,error out:won.error out', 'won', 'sl', ind=4)
    node('Not', 'x:won.timed out?', '.not. x?:wnt..not. x?', 'wnt', 'sl', ind=4)
    # stop on the notification (not timed out) and on an error: a notifier that is gone (the main VI ended)
    # returns at once with error 1 and timed out? TRUE (measured), so without the error the loop would spin
    w('    <Node _name="Unbundle By Name" fields="status" inputs="input cluster:won.error out" outputs="status:wer.status" uid="wer" uid_parent="sl"/>')
    node('Or', 'x:wnt..not. x?,y:wer.status', 'x .or. y?:wst.x .or. y?', 'wst', 'sl', ind=4)
    # the notifier leaves the loop through a tunnel, so Release Notifier runs after the loop. Taken from Obtain
    # Notifier directly it ran first: every wait then failed at once with error 1 and the loop never waited -
    # four screens spinning used 85 % of a 4-core machine (measured)
    w('    <Tunnel _id="Out1" inputs="value:won.notifier out" outputs="value:l_no.value" uid="l_no" uid_parent="sl"/>')
    w('    <Condition inputs="value:wst.x .or. y?" uid="slc" uid_parent="sl" value="stop"/>')
    w('  </Structure>')
    node('Release Notifier', 'notifier:l_no.value', 'notifier name:,last notification:,error out:', 'rn')
    w('</VI>')


def listbox_columns(label, headers, uid, parent='root', ind=2):
    """Columns and headers of a multicolumn listbox (style Listbox), once before the loop."""
    const(uid + 'n', 'int32', str(len(headers)), parent, ind=ind)
    const(uid + 'h', 'array{string}', strs(headers), parent, ind=ind)
    const(uid + 't', 'bool', 'true', parent, ind=ind)
    w('%s<Node _name="Property Node" fields="write+Number of Columns,write+Column Header Strings[],write+Visible Items\\3AColumn Headers Visible" link="%s" '
      'inputs="error in (no error):,Number of Columns:%sn.value,Column Header Strings[]:%sh.value,Visible Items\\3AColumn Headers Visible:%st.value" outputs="error out:" '
      'type="{LV.MulticolumnListbox}" uid="%s" uid_parent="%s"/>' % (' ' * ind, label, uid, uid, uid, uid, parent))


def items_case(uid, label, arrays, dirty_net, ind=4):
    """When dirty: Item Names of the listbox = the rows built from the column arrays; out: dirty false."""
    n = len(arrays)
    const(uid + '_ff', 'bool', 'false', 'sl', ind=ind)
    c = Case(o, uid, 'sl', dirty_net, arrays + [uid + '_ff.value'], [uid + '.dirty'], ind)
    c.frame('Rows unchanged', 'False', [n], None, lambda t: [t(n)])

    def body(L, t, f):
        L.append('<Structure _name="For Loop" count="" label="One row per file" maxin="" maxout="" uid="%sr" uid_parent="%s">' % (f, f))
        for k in range(len(arrays)):
            L.append('  <Tunnel _id="In%d" inputs="value:%s" mode="index" outputs="value:%sr%d.value" uid="%sr%d" uid_parent="%sr"/>' % (k + 1, t(k), f, k, f, k, f))
        L.append('  <Node _name="Build Array" inputs="%s" outputs="appended array:%sra.appended array" uid="%sra" uid_parent="%sr"/>'
                 % (','.join('element:%sr%d.value' % (f, k) for k in range(len(arrays))), f, f, f))
        L.append('  <Tunnel _id="Out1" inputs="value:%sra.appended array" mode="index" outputs="value:%sitems.value" uid="%sitems" uid_parent="%sr"/>' % (f, f, f, f))
        L.append('</Structure>')
        L.append('<Node _name="Property Node" fields="write+Item Names" link="%s" inputs="error in (no error):,Item Names:%sitems.value" outputs="error out:" type="{LV.MulticolumnListbox}" uid="%sin" uid_parent="%s"/>' % (label, f, f, f))
    c.frame('Show the rows', 'True', list(range(n + 1)), body, lambda t: [t(n)])
    c.emit()


# ================================================================ Live Data
screen_begin('RemoteVI App Live Data.vi',
             'Screen Live Data of RemoteVI Application Example.vi\\3A four simulated channels on the graph Live Data (500 samples each\\2C a new block every 100 ms)\\2C their maximum and minimum in Statistics. Pause holds the picture. Runs until the notifier RemoteVI Application Example fires (the main VI quits).',
             [('ph', const('ph0', 'double', '0', name='start phase'), 'pc.phase'),
              ('dat', const('dat0', 'array.2{double}', '[]', name='no data'), 'pc.data'),
              ('sts', const('sts0', 'array.2{string}', '[]', name='no statistics'), 'pc.stats')])
pause = ctl('Pause', 'bool', 'false', 'pause', desc='Holds the graph. Press again to continue.')
c = Case(o, 'pc', 'sl', pause, ['ph.value', 'dat.value', 'sts.value'], ['pc.phase', 'pc.data', 'pc.stats'], 4)


def live(L, t, f):
    step = L_const(L, f + 'st', 'double', '0.15', f)
    L_node(L, 'Add', 'x:%s,y:%s' % (t(0), step), 'x+y:%sph.x+y' % f, f + 'ph', f)
    n4 = L_const(L, f + 'n4', 'int32', '4', f)
    ch = f + 'ch'
    L.append('<Structure _name="For Loop" count="%s.value" label="Each channel" maxin="%s" maxout="" uid="%s" uid_parent="%s">' % (ch, n4, ch, f))
    L.append('  <Tunnel _id="In1" inputs="value:%sph.x+y" outputs="value:%sp.value" uid="%sp" uid_parent="%s"/>' % (f, ch, ch, ch))
    L.append('  <Node _name="To Double Precision Float" inputs="number:%s.value" outputs="double precision float:%scd.double precision float" uid="%scd" uid_parent="%s"/>' % (ch, ch, ch, ch))
    L.append('  <Constant outputs="value:%sq.value" type="double" uid="%sq" uid_parent="%s" value="0.25"/>' % (ch, ch, ch))
    L.append('  <Node _name="Multiply" inputs="x:%scd.double precision float,y:%sq.value" outputs="x*y:%sa0.x*y" uid="%sa0" uid_parent="%s"/>' % (ch, ch, ch, ch, ch))
    L.append('  <Constant outputs="value:%sone.value" type="double" uid="%sone" uid_parent="%s" value="1"/>' % (ch, ch, ch))
    L.append('  <Node _name="Add" inputs="x:%sa0.x*y,y:%sone.value" outputs="x+y:%samp.x+y" uid="%samp" uid_parent="%s"/>' % (ch, ch, ch, ch, ch))
    L.append('  <Node _name="Add" inputs="x:%scd.double precision float,y:%sone.value" outputs="x+y:%sk.x+y" uid="%sk" uid_parent="%s"/>' % (ch, ch, ch, ch, ch))
    L.append('  <Node _name="Add" inputs="x:%sp.value,y:%scd.double precision float" outputs="x+y:%soff.x+y" uid="%soff" uid_parent="%s"/>' % (ch, ch, ch, ch, ch))
    L.append('  <Constant outputs="value:%sn.value" type="int32" uid="%sn" uid_parent="%s" value="500"/>' % (ch, ch, ch))
    s = ch + 's'
    L.append('  <Structure _name="For Loop" count="%s.value" label="Each sample" maxin="%sn.value" maxout="" uid="%s" uid_parent="%s">' % (s, ch, s, ch))
    for k, (src, nm) in enumerate([(ch + 'amp.x+y', 'a'), (ch + 'k.x+y', 'k'), (ch + 'off.x+y', 'o')]):
        L.append('    <Tunnel _id="In%d" inputs="value:%s" outputs="value:%s%s.value" uid="%s%s" uid_parent="%s"/>' % (k + 1, src, s, nm, s, nm, s))
    L.append('    <Node _name="To Double Precision Float" inputs="number:%s.value" outputs="double precision float:%sj.double precision float" uid="%sj" uid_parent="%s"/>' % (s, s, s, s))
    L.append('    <Constant outputs="value:%sw.value" type="double" uid="%sw" uid_parent="%s" value="0.0251327412"/>' % (s, s, s))
    L.append('    <Node _name="Multiply" inputs="x:%sj.double precision float,y:%sw.value" outputs="x*y:%st.x*y" uid="%st" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('    <Node _name="Multiply" inputs="x:%st.x*y,y:%sk.value" outputs="x*y:%stk.x*y" uid="%stk" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('    <Node _name="Add" inputs="x:%stk.x*y,y:%so.value" outputs="x+y:%sx.x+y" uid="%sx" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('    <Node _name="Sine" inputs="x:%sx.x+y" outputs="sin(x):%ssn.sin(x)" uid="%ssn" uid_parent="%s"/>' % (s, s, s, s))
    L.append('    <Node _name="Multiply" inputs="x:%ssn.sin(x),y:%sa.value" outputs="x*y:%sy.x*y" uid="%sy" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('    <Node _name="Random Number (0-1)" inputs="" outputs="number\\3A 0 to 1:%srn.number\\3A 0 to 1" uid="%srn" uid_parent="%s"/>' % (s, s, s))
    L.append('    <Constant outputs="value:%sh.value" type="double" uid="%sh" uid_parent="%s" value="0.5"/>' % (s, s, s))
    L.append('    <Node _name="Subtract" inputs="x:%srn.number\\3A 0 to 1,y:%sh.value" outputs="x-y:%sr0.x-y" uid="%sr0" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('    <Constant outputs="value:%snz.value" type="double" uid="%snz" uid_parent="%s" value="0.06"/>' % (s, s, s))
    L.append('    <Node _name="Multiply" inputs="x:%sr0.x-y,y:%snz.value" outputs="x*y:%sr1.x*y" uid="%sr1" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('    <Node _name="Add" inputs="x:%sy.x*y,y:%sr1.x*y" outputs="x+y:%sv.x+y" uid="%sv" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('    <Tunnel _id="Out1" inputs="value:%sv.x+y" mode="index" outputs="value:%srow.value" uid="%srow" uid_parent="%s"/>' % (s, s, s, s))
    L.append('  </Structure>')
    L.append('  <Node _name="Array Max &amp; Min" inputs="array:%srow.value" outputs="max value:%smm.max,max index (indices):,min value:%smm.min,min index (indices):" uid="%smm" uid_parent="%s"/>' % (s, ch, ch, ch, ch))
    L.append('  <Constant outputs="value:%sfn.value" type="string" uid="%sfn" uid_parent="%s" value="AI%%d"/>' % (ch, ch, ch))
    L.append('  <Node _name="Format Into String" inputs="format string:%sfn.value,input 1:%s.value" outputs="resulting string:%snm.resulting string" uid="%snm" uid_parent="%s"/>' % (ch, ch, ch, ch, ch))
    L.append('  <Constant outputs="value:%sfv.value" type="string" uid="%sfv" uid_parent="%s" value="%%.3f"/>' % (ch, ch, ch))
    L.append('  <Node _name="Format Into String" inputs="format string:%sfv.value,input 1:%smm.max" outputs="resulting string:%smx.resulting string" uid="%smx" uid_parent="%s"/>' % (ch, ch, ch, ch, ch))
    L.append('  <Node _name="Format Into String" inputs="format string:%sfv.value,input 1:%smm.min" outputs="resulting string:%smn.resulting string" uid="%smn" uid_parent="%s"/>' % (ch, ch, ch, ch, ch))
    L.append('  <Node _name="Build Array" inputs="element:%snm.resulting string,element:%smx.resulting string,element:%smn.resulting string" outputs="appended array:%ssr.appended array" uid="%ssr" uid_parent="%s"/>' % (ch, ch, ch, ch, ch, ch))
    L.append('  <Tunnel _id="Out1" inputs="value:%srow.value" mode="index" outputs="value:%sdata.value" uid="%sdata" uid_parent="%s"/>' % (s, ch, ch, ch))
    L.append('  <Tunnel _id="Out2" inputs="value:%ssr.appended array" mode="index" outputs="value:%sstat.value" uid="%sstat" uid_parent="%s"/>' % (ch, ch, ch, ch))
    L.append('</Structure>')
    hdr = L_const(L, f + 'hd', 'array.2{string}', strs2([['Channel', 'Max (V)', 'Min (V)']]), f)
    L_node(L, 'Build Array', 'array:%s,array:%sstat.value' % (hdr, ch), 'appended array:%sst2.appended array' % f, f + 'st2', f, ' concat="true"')


c.frame('Pause\\3A keep the picture', 'True', [0, 1, 2], None, lambda t: [t(0), t(1), t(2)])
c.frame('Next block of four channels', 'False', [0], live, lambda t: ['pc_f1ph.x+y', 'pc_f1chdata.value', 'pc_f1st2.appended array'])
c.emit()
w('    <Indicator _name="Live Data" description="The last block of every channel (simulated)." inputs="value:pc.data" style="graph21703" type="array.2{double}" uid="graph" uid_parent="sl" value="[]"/>')
ind_('Statistics', 'array.2{string}', 'pc.stats', 'stat', desc='Maximum and minimum of each channel in the block shown.', value='[]')
screen_end()
save('app_live_data.xml')

# ================================================================ Log Files
FILES = []  # three weeks of runs: more than the list shows, so it scrolls
for _d in range(1, 22):
    _pump = _d % 4 == 0
    _h = 1 + _d % 3 if _pump else 8 - (_d % 5 == 2)
    FILES.append(('%s_2026-10-%02d_%s.tdms' % ('pump-test' if _pump else 'cooling-loop', _d + 9, '1430' if _pump else '0800'),
                  '2026-10-%02d %s' % (_d + 9, '14:30' if _pump else '08:00'), '%d h %02d min' % (_h, (_d * 7) % 60),
                  '%d MB' % (_h * 51 + _d)))
cols = list(zip(*FILES))
screen_begin('RemoteVI App Log Files.vi',
             'Screen Log Files of RemoteVI Application Example.vi\\3A the log files of the station (simulated - none exists on disk). Selecting a file in Log Files shows its preview and details. Delete asks in a LabVIEW dialog and removes the file from the list\\3B Export asks for a target in the native file dialog. Runs until the notifier RemoteVI Application Example fires (the main VI quits).',
             [('fn', const('fn0', 'array{string}', strs(cols[0]), name='file names'), 'dc.names'),
              ('fs', const('fs0', 'array{string}', strs(cols[1]), name='started'), 'dc.started'),
              ('fd', const('fd0', 'array{string}', strs(cols[2]), name='durations'), 'dc.durations'),
              ('fz', const('fz0', 'array{string}', strs(cols[3]), name='sizes'), 'dc.sizes'),
              ('dty', const('dty0', 'bool', 'true', name='rows to show'), 'dc.dirty'),
              ('psel', const('psel0', 'int32', '-2', name='no selection yet'), 'nsel.s? t\\3Af'),
              ('pv', const('pv0', 'array.2{double}', '[]', name='no preview'), 'oc.preview'),
              ('dt', const('dt0', 'string', 'Select a log file to see its preview.', name='no details'), 'oc.details'),
              ('st', const('st0', 'string', '', name='no status'), 'xc.status')])
lst = ctl('Log Files', 'int32', '-1', 'lst', desc='The log files of the station. Select one to see its preview.', extra=' style="Listbox"')
dl = ctl('Delete', 'bool', 'false', 'del', desc='Removes the selected file (asks first).', extra=' style="latched"')
ex = ctl('Export', 'bool', 'false', 'exp', desc='Exports the selected file (choose the target in the file dialog).', extra=' style="latched"')
items_case('ic', 'Log Files', ['fn.value', 'fs.value', 'fd.value', 'fz.value'], 'dty.value')
node('Array Size', 'array:fn.value', 'size(s):nf.size(s)', 'nf', 'sl', ind=4)
node('Greater Or Equal To 0?', 'x:lst.value', 'x &gt;= 0?:v0.x &gt;= 0?', 'v0', 'sl', ind=4)
node('Less?', 'x:lst.value,y:nf.size(s)', 'x &lt; y?:v1.x &lt; y?', 'v1', 'sl', ind=4)
node('And', 'x:v0.x &gt;= 0?,y:v1.x &lt; y?', 'x .and. y?:val.x .and. y?', 'val', 'sl', ind=4)
node('Not Equal?', 'x:lst.value,y:psel.value', 'x != y?:chg.x != y?', 'chg', 'sl', ind=4)
node('And', 'x:chg.x != y?,y:val.x .and. y?', 'x .and. y?:opn.x .and. y?', 'opn', 'sl', ind=4)
for k, (arr, nm) in enumerate([('fn.value', 'name'), ('fs.value', 'start'), ('fd.value', 'dur'), ('fz.value', 'size')]):
    node('Index Array', 'array:%s,index:lst.value' % arr, 'element:x%s.element' % nm, 'x' + nm, 'sl', ind=4)

# preview and details of a newly selected file
c = Case(o, 'oc', 'sl', 'opn.x .and. y?', ['pv.value', 'dt.value', 'lst.value', 'xname.element', 'xstart.element', 'xdur.element', 'xsize.element', 'val.x .and. y?'],
         ['oc.preview', 'oc.details'], 4)


def no_open(L, t, f):
    # nothing selected any more (deleted): clear the details
    L_const(L, f + 'nd', 'string', 'Select a log file to see its preview.', f)
    L_const(L, f + 'np', 'array.2{double}', '[]', f)
    L_node(L, 'Select', 'f:%snp.value,s:%s,t:%s' % (f, t(7), t(0)), 's? t\\3Af:%sp.s? t\\3Af' % f, f + 'p', f)
    L_node(L, 'Select', 'f:%snd.value,s:%s,t:%s' % (f, t(7), t(1)), 's? t\\3Af:%sd.s? t\\3Af' % f, f + 'd', f)


def do_open(L, t, f):
    L.append('<Node _name="To Double Precision Float" inputs="number:%s" outputs="double precision float:%sk.double precision float" uid="%sk" uid_parent="%s"/>' % (t(2), f, f, f))
    L_const(L, f + 'n', 'int32', '400', f)
    s = f + 's'
    L.append('<Structure _name="For Loop" count="%s.value" label="Preview samples" maxin="%sn.value" maxout="" uid="%s" uid_parent="%s">' % (s, f, s, f))
    L.append('  <Tunnel _id="In1" inputs="value:%sk.double precision float" outputs="value:%sk.value" uid="%sk" uid_parent="%s"/>' % (f, s, s, s))
    L.append('  <Node _name="To Double Precision Float" inputs="number:%s.value" outputs="double precision float:%sj.double precision float" uid="%sj" uid_parent="%s"/>' % (s, s, s, s))
    L.append('  <Constant outputs="value:%sa.value" type="double" uid="%sa" uid_parent="%s" value="0.015"/>' % (s, s, s))
    L.append('  <Constant outputs="value:%sone.value" type="double" uid="%sone" uid_parent="%s" value="1"/>' % (s, s, s))
    L.append('  <Node _name="Add" inputs="x:%sk.value,y:%sone.value" outputs="x+y:%sk1.x+y" uid="%sk1" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('  <Node _name="Multiply" inputs="x:%sj.double precision float,y:%sa.value" outputs="x*y:%st.x*y" uid="%st" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('  <Node _name="Multiply" inputs="x:%st.x*y,y:%sk1.x+y" outputs="x*y:%sx.x*y" uid="%sx" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('  <Node _name="Sine" inputs="x:%sx.x*y" outputs="sin(x):%ss1.sin(x)" uid="%ss1" uid_parent="%s"/>' % (s, s, s, s))
    L.append('  <Constant outputs="value:%sb.value" type="double" uid="%sb" uid_parent="%s" value="0.31"/>' % (s, s, s))
    L.append('  <Node _name="Multiply" inputs="x:%sj.double precision float,y:%sb.value" outputs="x*y:%sx2.x*y" uid="%sx2" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('  <Node _name="Sine" inputs="x:%sx2.x*y" outputs="sin(x):%ss2.sin(x)" uid="%ss2" uid_parent="%s"/>' % (s, s, s, s))
    L.append('  <Constant outputs="value:%sc.value" type="double" uid="%sc" uid_parent="%s" value="0.2"/>' % (s, s, s))
    L.append('  <Node _name="Multiply" inputs="x:%ss2.sin(x),y:%sc.value" outputs="x*y:%sr.x*y" uid="%sr" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('  <Node _name="Add" inputs="x:%ss1.sin(x),y:%sr.x*y" outputs="x+y:%sv.x+y" uid="%sv" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('  <Tunnel _id="Out1" inputs="value:%sv.x+y" mode="index" outputs="value:%srow.value" uid="%srow" uid_parent="%s"/>' % (s, s, s, s))
    L.append('</Structure>')
    L_node(L, 'Build Array', 'element:%srow.value' % s, 'appended array:%sp.appended array' % f, f + 'p', f)
    L_const(L, f + 'fm', 'string', '%s\\0AStarted %s\\2C recorded for %s\\2C %s.\\0A4 channels (AI0 to AI3)\\2C 1 kHz. Simulated - the file does not exist.', f)
    L_node(L, 'Format Into String', 'format string:%sfm.value,input 1:%s,input 2:%s,input 3:%s,input 4:%s' % (f, t(3), t(4), t(5), t(6)),
           'resulting string:%sd.resulting string' % f, f + 'd', f)


c.frame('Selection unchanged', 'False', [0, 1, 7], no_open, lambda t: ['oc_f0p.s? t\\3Af', 'oc_f0d.s? t\\3Af'])
c.frame('Show the selected file', 'True', [2, 3, 4, 5, 6], do_open, lambda t: ['oc_f1p.appended array', 'oc_f1d.resulting string'])
c.emit()

# Delete: ask, then remove the row
const('dc_no', 'bool', 'false', 'sl', ind=4)
c = Case(o, 'dc', 'sl', dl, ['fn.value', 'fs.value', 'fd.value', 'fz.value', 'ic.dirty', 'lst.value', 'xname.element', 'val.x .and. y?', 'st.value', 'dc_no.value'],
         ['dc.names', 'dc.started', 'dc.durations', 'dc.sizes', 'dc.dirty', 'dc.deleted', 'dc.status'], 4)
c.frame('Not pressed', 'False', [0, 1, 2, 3, 4, 8, 9], None, lambda t: [t(0), t(1), t(2), t(3), t(4), t(9), t(8)])


def do_delete(L, t, f):
    inner = Case(L, f + 'v', f, t(7), [t(0), t(1), t(2), t(3), t(4), t(5), t(6)],
                 [f + 'v.n', f + 'v.s', f + 'v.d', f + 'v.z', f + 'v.y', f + 'v.del', f + 'v.st'], 0)

    def none(L2, u, g):
        L_const(L2, g + 'm', 'string', 'Select a log file first.', g)
        L_const(L2, g + 'f', 'bool', 'false', g)

    inner.frame('Nothing selected', 'False', [0, 1, 2, 3, 4], none,
                lambda u: [u(0), u(1), u(2), u(3), u(4), f + 'v_f0f.value', f + 'v_f0m.value'])

    def ask(L2, u, g):
        L_const(L2, g + 'fm', 'string', 'Delete the log file %s?\\0A(Simulated - nothing is deleted on disk.)', g)
        L_node(L2, 'Format Into String', 'format string:%sfm.value,input 1:%s' % (g, u(6)), 'resulting string:%sq.resulting string' % g, g + 'q', g)
        L_const(L2, g + 'yes', 'string', 'Delete', g)
        L_const(L2, g + 'no', 'string', 'Keep', g)
        L_node(L2, 'Two Button Dialog', 'message:%sq.resulting string,T button name (&quot;OK&quot;):%syes.value,F button name (&quot;Cancel&quot;):%sno.value' % (g, g, g),
               'T button?:%sd.T button?' % g, g + 'd', g)
        for k, nm in enumerate(['n', 's', 'd', 'z']):
            L_node(L2, 'Delete From Array', 'array:%s,index:%s' % (u(k), u(5)), 'array w/ subset deleted:%sx%s.v' % (g, nm), g + 'x' + nm, g)
            L_node(L2, 'Select', 't:%sx%s.v,s:%sd.T button?,f:%s' % (g, nm, g, u(k)), 's? t\\3Af:%ss%s.s? t\\3Af' % (g, nm), g + 's' + nm, g)
        L_node(L2, 'Or', 'x:%s,y:%sd.T button?' % (u(4), g), 'x .or. y?:%sdy.x .or. y?' % g, g + 'dy', g)
        L_const(L2, g + 'okm', 'string', 'Deleted %s from the list.', g)
        L_const(L2, g + 'nom', 'string', 'Kept %s.', g)
        L_node(L2, 'Select', 't:%sokm.value,s:%sd.T button?,f:%snom.value' % (g, g, g), 's? t\\3Af:%sfmt.s? t\\3Af' % g, g + 'fmt', g)
        L_node(L2, 'Format Into String', 'format string:%sfmt.s? t\\3Af,input 1:%s' % (g, u(6)), 'resulting string:%sm.resulting string' % g, g + 'm', g)

    inner.frame('Ask the remote user', 'True', [0, 1, 2, 3, 4, 5, 6], ask,
                lambda u: [f + 'v_f1sn.s? t\\3Af', f + 'v_f1ss.s? t\\3Af', f + 'v_f1sd.s? t\\3Af', f + 'v_f1sz.s? t\\3Af',
                           f + 'v_f1dy.x .or. y?', f + 'v_f1d.T button?', f + 'v_f1m.resulting string'])
    inner.emit()


c.frame('Delete the selected file', 'True', [0, 1, 2, 3, 4, 5, 6, 7], do_delete,
        lambda t: ['dc_f1v.n', 'dc_f1v.s', 'dc_f1v.d', 'dc_f1v.z', 'dc_f1v.y', 'dc_f1v.del', 'dc_f1v.st'])
c.emit()
# a deleted row: show the selection again next time
const('nsel0', 'int32', '-2', 'sl', ind=4)
node('Select', 't:nsel0.value,s:dc.deleted,f:lst.value', 's? t\\3Af:nsel.s? t\\3Af', 'nsel', 'sl', ind=4)

# Export: native file dialog
c = Case(o, 'xc', 'sl', ex, ['dc.status', 'xname.element', 'val.x .and. y?'], ['xc.status'], 4)
c.frame('Not pressed', 'False', [0], None, lambda t: [t(0)])


def do_export(L, t, f):
    inner = Case(L, f + 'v', f, t(2), [t(1)], [f + 'v.st'], 0)
    inner.frame('Nothing selected', 'False', [], lambda L2, u, g: L_const(L2, g + 'm', 'string', 'Select a log file first.', g),
                lambda u: [f + 'v_f0m.value'])

    def dlg(L2, u, g):
        L2.append('<Node _name="File Dialog" inputs="" outputs="selected path:%sd.selected path,error out:" uid="%sd" uid_parent="%s"/>' % (g, g, g))
        L_node(L2, 'Not A Number/Path/Refnum?', 'number/path/refnum:%sd.selected path' % g, 'NaN/Path/Refnum?:%sc.NaN/Path/Refnum?' % g, g + 'c', g)
        L_const(L2, g + 'fm', 'string', 'Exported %s to %s (simulated).', g)
        L_node(L2, 'Format Into String', 'format string:%sfm.value,input 1:%s,input 2:%sd.selected path' % (g, u(0), g), 'resulting string:%sm.resulting string' % g, g + 'm', g)
        L_const(L2, g + 'x', 'string', 'Export cancelled.', g)
        L_node(L2, 'Select', 't:%sx.value,s:%sc.NaN/Path/Refnum?,f:%sm.resulting string' % (g, g, g), 's? t\\3Af:%ss.s? t\\3Af' % g, g + 's', g)

    inner.frame('Choose the target', 'True', [0], dlg, lambda u: [f + 'v_f1s.s? t\\3Af'])
    inner.emit()


c.frame('Export the selected file', 'True', [1, 2], do_export, lambda t: ['xc_f1v.st'])
c.emit()
w('    <Indicator _name="Preview" description="The first 400 samples of channel AI0 of the selected file (simulated)." inputs="value:oc.preview" style="graph21703" type="array.2{double}" uid="pvg" uid_parent="sl" value="[]"/>')
ind_('Details', 'string', 'oc.details', 'dti', desc='About the selected file.')
ind_('Status', 'string', 'xc.status', 'sti', desc='What the last Delete or Export did.')
screen_end()


def before_loop(fn):
    """Writes fn's lines in front of the screen loop (the listbox columns are set once)."""
    at = next(i for i, s in enumerate(o) if 'While Loop' in s)
    tail = o[at:]
    del o[at:]
    fn()
    o.extend(tail)


before_loop(lambda: listbox_columns('Log Files', ['File', 'Started', 'Duration', 'Size'], 'lbc'))
save('app_log_files.xml')

# ================================================================ Alarms
TEMPLATES = [
    ('Warning', 'AI0 Supply pressure', 'Pressure above 6.0 bar'),
    ('Alarm', 'AI2 Coolant temperature', 'Temperature above 45 degC'),
    ('Warning', 'Pump P1', 'Motor current high'),
    ('Alarm', 'AI3 Flow', 'Flow below 2 l/min'),
    ('Info', 'Logger', 'Disk space below 10 %'),
]
tcols = list(zip(*TEMPLATES))
screen_begin('RemoteVI App Alarms.vi',
             'Screen Alarms of RemoteVI Application Example.vi\\3A active alarms of the station (simulated\\3A a new one arrives every 6 s while fewer than 10 are active). Acknowledge removes the selected alarm\\2C Acknowledge All every alarm. Runs until the notifier RemoteVI Application Example fires (the main VI quits).',
             [('at', const('at0', 'array{string}', strs(['08:12:04', '08:47:31']), name='times'), 'kc.t'),
              ('av', const('av0', 'array{string}', strs(['Warning', 'Info']), name='severities'), 'kc.v'),
              ('as', const('as0', 'array{string}', strs(['Pump P1', 'Logger']), name='sources'), 'kc.s'),
              ('am', const('am0', 'array{string}', strs(['Motor current high', 'Log file split']), name='messages'), 'kc.m'),
              ('tk', const('tk0', 'int32', '0', name='ticks'), 'tki.x+1'),
              ('nx', const('nx0', 'int32', '0', name='next template'), 'nc.next'),
              ('ady', const('ady0', 'bool', 'true', name='rows to show'), 'ac.dirty')])
alst = ctl('Alarms', 'int32', '-1', 'alst', desc='Active alarms\\2C oldest first. Select one to acknowledge it.', extra=' style="Listbox"')
ack = ctl('Acknowledge', 'bool', 'false', 'ack', desc='Acknowledges the selected alarm.', extra=' style="latched"')
acka = ctl('Acknowledge All', 'bool', 'false', 'acka', desc='Acknowledges every alarm.', extra=' style="latched"')
node('Increment', 'x:tk.value', 'x+1:tki.x+1', 'tki', 'sl', ind=4)
const('six', 'int32', '60', 'sl', ind=4)
node('Quotient &amp; Remainder', 'x:tki.x+1,y:six.value', 'x-y*floor(x/y):tq.r,floor(x/y):', 'tq', 'sl', ind=4)
node('Equal To 0?', 'x:tq.r', 'x = 0?:due.x = 0?', 'due', 'sl', ind=4)
node('Array Size', 'array:at.value', 'size(s):na.size(s)', 'na', 'sl', ind=4)
const('ten', 'int32', '10', 'sl', ind=4)
node('Less?', 'x:na.size(s),y:ten.value', 'x &lt; y?:room.x &lt; y?', 'room', 'sl', ind=4)
node('And', 'x:due.x = 0?,y:room.x &lt; y?', 'x .and. y?:add.x .and. y?', 'add', 'sl', ind=4)
c = Case(o, 'nc', 'sl', 'add.x .and. y?', ['at.value', 'av.value', 'as.value', 'am.value', 'nx.value', 'ady.value'],
         ['nc.t', 'nc.v', 'nc.s', 'nc.m', 'nc.next', 'nc.dirty'], 4)
c.frame('No new alarm', 'False', [0, 1, 2, 3, 4, 5], None, lambda t: [t(0), t(1), t(2), t(3), t(4), t(5)])


def new_alarm(L, t, f):
    L_const(L, f + 'ws', 'bool', 'true', f)
    L.append('<Node _name="Get Date/Time String" inputs="want seconds? (F):%sws.value" outputs="date string:,time string:%sdt.time string" uid="%sdt" uid_parent="%s"/>' % (f, f, f, f))
    for k, (nm, col) in enumerate([('v', tcols[0]), ('s', tcols[1]), ('m', tcols[2])]):
        L_const(L, f + 'k' + nm, 'array{string}', strs(col), f)
        L_node(L, 'Index Array', 'array:%sk%s.value,index:%s' % (f, nm, t(4)), 'element:%se%s.element' % (f, nm), f + 'e' + nm, f)
    L_node(L, 'Build Array', 'array:%s,element:%sdt.time string' % (t(0), f), 'appended array:%sbt.appended array' % f, f + 'bt', f, ' concat="true"')
    for k, nm in enumerate(['v', 's', 'm']):
        L_node(L, 'Build Array', 'array:%s,element:%se%s.element' % (t(k + 1), f, nm), 'appended array:%sb%s.appended array' % (f, nm), f + 'b' + nm, f, ' concat="true"')
    L_node(L, 'Increment', 'x:%s' % t(4), 'x+1:%si.x+1' % f, f + 'i', f)
    L_const(L, f + 'five', 'int32', '5', f)
    L_node(L, 'Quotient &amp; Remainder', 'x:%si.x+1,y:%sfive.value' % (f, f), 'x-y*floor(x/y):%sq.r,floor(x/y):' % f, f + 'q', f)
    L_const(L, f + 'y', 'bool', 'true', f)


c.frame('A new alarm arrives', 'True', [0, 1, 2, 3, 4], new_alarm,
        lambda t: ['nc_f1bt.appended array', 'nc_f1bv.appended array', 'nc_f1bs.appended array', 'nc_f1bm.appended array', 'nc_f1q.r', 'nc_f1y.value'])
c.emit()
node('Greater Or Equal To 0?', 'x:alst.value', 'x &gt;= 0?:a0.x &gt;= 0?', 'a0', 'sl', ind=4)
node('And', 'x:a0.x &gt;= 0?,y:ack.value', 'x .and. y?:ak.x .and. y?', 'ak', 'sl', ind=4)
node('Or', 'x:ak.x .and. y?,y:acka.value', 'x .or. y?:anyk.x .or. y?', 'anyk', 'sl', ind=4)
c = Case(o, 'kc', 'sl', 'anyk.x .or. y?', ['nc.t', 'nc.v', 'nc.s', 'nc.m', 'nc.dirty', 'alst.value', 'acka.value'],
         ['kc.t', 'kc.v', 'kc.s', 'kc.m', 'kc.dirty0'], 4)
c.frame('Nothing to acknowledge', 'False', [0, 1, 2, 3, 4], None, lambda t: [t(0), t(1), t(2), t(3), t(4)])


def acknowledge(L, t, f):
    L_const(L, f + 'e', 'array{string}', '[]', f)
    for k, nm in enumerate(['t', 'v', 's', 'm']):
        L_node(L, 'Delete From Array', 'array:%s,index:%s' % (t(k), t(5)), 'array w/ subset deleted:%sx%s.v' % (f, nm), f + 'x' + nm, f)
        L_node(L, 'Select', 't:%se.value,s:%s,f:%sx%s.v' % (f, t(6), f, nm), 's? t\\3Af:%ss%s.s? t\\3Af' % (f, nm), f + 's' + nm, f)
    L_const(L, f + 'y', 'bool', 'true', f)


c.frame('Acknowledge', 'True', [0, 1, 2, 3, 5, 6], acknowledge,
        lambda t: ['kc_f1st.s? t\\3Af', 'kc_f1sv.s? t\\3Af', 'kc_f1ss.s? t\\3Af', 'kc_f1sm.s? t\\3Af', 'kc_f1y.value'])
c.emit()
items_case('ac', 'Alarms', ['kc.t', 'kc.v', 'kc.s', 'kc.m'], 'kc.dirty0')
node('Array Size', 'array:kc.t', 'size(s):nk.size(s)', 'nk', 'sl', ind=4)
ind_('Active Alarms', 'int32', 'nk.size(s)', 'nai', desc='How many alarms are not acknowledged yet.', value='0')
node('Greater Than 0?', 'x:nk.size(s)', 'x &gt; 0?:lit.x &gt; 0?', 'lit', 'sl', ind=4)
ind_('Alarm', 'bool', 'lit.x &gt; 0?', 'led', desc='Lit while an alarm is active.', value='false')
screen_end()
before_loop(lambda: listbox_columns('Alarms', ['Time', 'Severity', 'Source', 'Message'], 'abc'))
save('app_alarms.xml')

# ================================================================ Settings
screen_begin('RemoteVI App Settings.vi',
             'Screen Settings of RemoteVI Application Example.vi\\3A settings of the station (simulated - nothing is stored). Save confirms in a LabVIEW dialog. Runs until the notifier RemoteVI Application Example fires (the main VI quits).',
             [('st', const('st0', 'string', 'Settings are not saved yet.', name='first status'), 'sc.status')])
stn = ctl('Station Name', 'string', 'Cooling loop test bench', 'stn', desc='Shown in the log file headers.')
ctl('Operator', 'string', 'Shift A', 'opr', desc='Who runs the station.')
ctl('Units', 'uint16{SI (bar\\2C degC),US (psi\\2C degF)}', '0', 'unt', desc='Units of the displays and the log files.')
ctl('Sample Interval (ms)', 'double', '100', 'smp', desc='How often the station samples its channels.')
ctl('Keep Logs (days)', 'double', '30', 'ret', desc='Log files older than this are removed.')
ctl('Export Automatically', 'bool', 'true', 'aex', desc='Exports every log file when it is closed.')
ctl('Export Folder', 'path', 'C\\3A\\5CData\\5CExport', 'efd', desc='Where exports go.')
sv = ctl('Save', 'bool', 'false', 'sav', desc='Saves the settings (simulated).', extra=' style="latched"')
c = Case(o, 'sc', 'sl', sv, ['st.value', stn], ['sc.status'], 4)
c.frame('Not pressed', 'False', [0], None, lambda t: [t(0)])


def do_save(L, t, f):
    L_const(L, f + 'fm', 'string', 'Settings of %s saved (simulated).', f)
    L_node(L, 'Format Into String', 'format string:%sfm.value,input 1:%s' % (f, t(1)), 'resulting string:%sm.resulting string' % f, f + 'm', f)
    L_const(L, f + 'ok', 'string', 'OK', f)
    L_node(L, 'One Button Dialog', 'message:%sm.resulting string,button name (&quot;OK&quot;):%sok.value' % (f, f), 'true:', f + 'd', f)
    L_const(L, f + 'ws', 'bool', 'true', f)
    L.append('<Node _name="Get Date/Time String" inputs="want seconds? (F):%sws.value" outputs="date string:,time string:%sdt.time string" uid="%sdt" uid_parent="%s"/>' % (f, f, f, f))
    L_const(L, f + 'sm', 'string', 'Saved at %s.', f)
    L_node(L, 'Format Into String', 'format string:%ssm.value,input 1:%sdt.time string' % (f, f), 'resulting string:%ss.resulting string' % f, f + 's', f)


c.frame('Save and confirm', 'True', [1], do_save, lambda t: ['sc_f1s.resulting string'])
c.emit()
ind_('Status', 'string', 'sc.status', 'sti', desc='When the settings were saved last.')
screen_end()
save('app_settings.xml')

# ================================================================ main VI (scaffold for the splitter panel)
SCREENS = ['RemoteVI App Live Data.vi', 'RemoteVI App Log Files.vi', 'RemoteVI App Alarms.vi', 'RemoteVI App Settings.vi']
PAGES = ['Live Data', 'Log Files', 'Alarms', 'Settings']
w('<VI _name="RemoteVI Application Example.vi" description="RemoteVI example\\3A a LabVIEW application with a professional UI\\2C operated from a web browser. The panel has three panes - a toolbar on top\\2C the navigation Menu on the left (split off by a splitter bar the remote user can drag) and the main pane with the subpanel Screen. The menu loads one of four screens into the subpanel\\3A Live Data\\2C Log Files\\2C Alarms and Settings (VIs in the folder Application Example\\2C all running from the start\\3B their dialogs and the native file dialog are answered in the browser too). RemoteVI Start.vi shares the panel on port 8087 (this computer only)\\3B Remote Link shows the link with its access token. Quit stops the screens (named notifier RemoteVI Application Example) and RemoteVI Stop.vi ends the share\\3B closing the panel does the same. The data are simulated\\3B nothing is written to disk.">')
w('  <FreeLabel comment="Share the panel\\2C run the screens\\2C show the one the menu selects\\2C stop everything on Quit" uid="lbl" uid_parent="root"/>')
const('port', 'uint16', '8087', name='port')
w('  <Call inputs="port:port.value" outputs="URL:st.URL,error out:st.error out" target="RemoteVI Start.vi" uid="st" uid_parent="root"/>')
w('  <Indicator _name="Remote Link" description="Open this link in a browser to operate the application remotely (RemoteVI)." inputs="value:st.URL" type="string" uid="url" uid_parent="root" value=""/>')
const('nn', 'string', NOTIFIER, name='notifier name')
const('nt', 'bool', 'false', name='notification type')
node('Obtain Notifier', 'name (unnamed):nn.value,notification data type:nt.value,error in (no error):st.error out',
     'notifier out:on.notifier out,created new?:,error out:on.error out', 'on')
# the menu
const('mi', 'array.2{string}', strs2([[p] for p in PAGES]), name='menu items')
const('m1', 'int32', '1', name='one column')
const('mf', 'bool', 'false', name='no headers')
w('  <Node _name="Property Node" fields="write+Item Names,write+Number of Columns,write+Visible Items\\3AColumn Headers Visible,write+Visible Items\\3AHorizontal Scrollbar Visible" link="Menu" '
  'inputs="error in (no error):on.error out,Item Names:mi.value,Number of Columns:m1.value,Visible Items\\3AColumn Headers Visible:mf.value,Visible Items\\3AHorizontal Scrollbar Visible:mf.value" '
  'outputs="error out:mp.error out" type="{LV.MulticolumnListbox}" uid="mp" uid_parent="root"/>')
# the subpanel Screen, pasted in after the graft: found by its label among the panel's controls
w('  <Node _name="Property Node" fields="read+Front Panel" inputs="reference:,error in (no error):mp.error out" outputs="Front Panel:vp.fp,reference out:,error out:vp.error out" type="{LV.VI}" uid="vp" uid_parent="root"/>')
w('  <Node _name="Property Node" fields="read+Controls[]" inputs="reference:vp.fp,error in (no error):vp.error out" outputs="Controls[]:pc.c,reference out:,error out:pc.error out" type="{LV.Panel}" uid="pc" uid_parent="root"/>')
w('  <Structure _name="For Loop" count="" label="Which control is Screen" maxin="" maxout="" uid="fl" uid_parent="root">')
w('    <Tunnel _id="In1" inputs="value:pc.c" mode="index" outputs="value:fc.value" uid="fc" uid_parent="fl"/>')
w('    <Node _name="Property Node" fields="read+Label.Text" inputs="reference:fc.value" outputs="Label.Text:lt.text,reference out:,error out:" type="{LV.Control}" uid="lt" uid_parent="fl"/>')
const('sn', 'string', 'Screen', 'fl', ind=4)
node('Equal?', 'x:lt.text,y:sn.value', 'x = y?:eq.x = y?', 'eq', 'fl', ind=4)
w('    <Tunnel _id="Out1" inputs="value:eq.x = y?" mode="index" outputs="value:isS.value" uid="isS" uid_parent="fl"/>')
w('  </Structure>')
const('tr', 'bool', 'true', name='true')
node('Search 1D Array', '1D array:isS.value,element:tr.value', 'index of element:si.index of element', 'si')
node('Index Array', 'array:pc.c,index:si.index of element', 'element:sc.element', 'sc')
const('spc', 'ref{LV.SubPanel}', '', name='subpanel class')
node('To More Specific Class', 'target class:spc.value,reference:sc.element,error in:pc.error out', 'specific class reference:sp.ref,error out:sp.error out', 'sp')
# run every screen
node('Current VI\'s Path', '', 'path:cvp.path', 'cvp')
node('Strip Path', 'path:cvp.path', 'stripped path:dir.stripped path,name:', 'dir')
const('fold', 'string', 'Application Example', name='screens folder')
node('Build Path', 'base path:dir.stripped path,name or relative path:fold.value', 'appended path:sdir.appended path', 'sdir')
const('scr', 'array{string}', strs(SCREENS), name='screens')
const('nw', 'bool', 'false', name='no wait')
w('  <Structure _name="For Loop" count="" label="Open and run each screen" maxin="" maxout="" uid="rl" uid_parent="root">')
w('    <Tunnel _id="In1" inputs="value:scr.value" mode="index" outputs="value:rn.value" uid="rn" uid_parent="rl"/>')
w('    <Tunnel _id="In2" inputs="value:sdir.appended path" outputs="value:rd.value" uid="rd" uid_parent="rl"/>')
w('    <Tunnel _id="In3" inputs="value:nw.value" outputs="value:rw.value" uid="rw" uid_parent="rl"/>')
w('    <Tunnel _id="In4" inputs="value:sp.ref" outputs="value:rsp.value" uid="rsp" uid_parent="rl"/>')
w('    <ShiftReg uid="re_sr" uid_parent="rl">')
w('      <Left inputs="value:sp.error out" outputs="value:re.value" uid="re" uid_parent="re_sr"/>')
w('      <Right inputs="value:run.error out" outputs="value:" uid="re_r" uid_parent="re_sr"/>')
w('    </ShiftReg>')
node('Build Path', 'base path:rd.value,name or relative path:rn.value', 'appended path:rp.appended path', 'rp', 'rl', ind=4)
node('Open VI Reference', 'vi path:rp.appended path,error in (no error):re.value', 'vi reference:ov.vi reference,error out:ov.error out', 'ov', 'rl', ind=4)
# each screen starts inside the subpanel: a VI run with Run VI before it was ever inserted did not
# redraw its indicators the first time it was inserted later (measured; from the second insertion on it did)
w('    <Node _name="Invoke Node" target="Insert VI" type="{LV.SubPanel}" inputs="reference:rsp.value,error in (no error):ov.error out,VI Ref:ov.vi reference" outputs="reference out:,error out:rins.error out" uid="rins" uid_parent="rl"/>')
w('    <Node _name="Invoke Node" target="Run VI" type="{LV.VI}" inputs="reference:ov.vi reference,error in (no error):rins.error out,Wait until done:rw.value,Auto Dispose Ref:rw.value" outputs="reference out:,error out:run0.error out" uid="run0" uid_parent="rl"/>')
w('    <Node _name="Invoke Node" target="Remove VI" type="{LV.SubPanel}" inputs="reference:rsp.value,error in (no error):run0.error out" outputs="reference out:,error out:run.error out" uid="run" uid_parent="rl"/>')
w('    <Tunnel _id="Out1" inputs="value:ov.vi reference" mode="index" outputs="value:refs.value" uid="refs" uid_parent="rl"/>')
w('    <Tunnel _id="Out2" inputs="value:run.error out" outputs="value:rerr.value" uid="rerr" uid_parent="rl"/>')
w('  </Structure>')
const('z', 'int32', '0', name='first screen')
node('Index Array', 'array:refs.value,index:z.value', 'element:r0.element', 'r0')
w('  <Node _name="Invoke Node" target="Insert VI" type="{LV.SubPanel}" inputs="reference:sp.ref,error in (no error):rerr.value,VI Ref:r0.element" outputs="reference out:,error out:ins.error out" uid="ins" uid_parent="root"/>')
const('pg', 'array{string}', strs(PAGES), name='page names')
const('ms', 'int32', str(PERIOD_MS), name='loop period ms')
const('three', 'int32', '3', name='last page')
const('fo0', 'bool', 'false', name='panel not seen open yet')
w('  <Structure _name="While Loop" count="" label="Show the screen the menu selects" uid="sl" uid_parent="root">')
for k, (src, u) in enumerate([('sp.ref', 'l_sp'), ('refs.value', 'l_refs'), ('pg.value', 'l_pg'), ('ms.value', 'l_ms'), ('three.value', 'l_3')]):
    w('    <Tunnel _id="In%d" inputs="value:%s" outputs="value:%s.value" uid="%s" uid_parent="sl"/>' % (k + 1, src, u, u))
w('    <ShiftReg uid="cur_sr" uid_parent="sl">')
w('      <Left inputs="value:z.value" outputs="value:cur.value" uid="cur" uid_parent="cur_sr"/>')
w('      <Right inputs="value:want.min" outputs="value:" uid="cur_r" uid_parent="cur_sr"/>')
w('    </ShiftReg>')
w('    <ShiftReg uid="er_sr" uid_parent="sl">')
w('      <Left inputs="value:ins.error out" outputs="value:er.value" uid="er" uid_parent="er_sr"/>')
w('      <Right inputs="value:swc.err" outputs="value:" uid="er_r" uid_parent="er_sr"/>')
w('    </ShiftReg>')
w('    <ShiftReg uid="fo_sr" uid_parent="sl">')
w('      <Left inputs="value:fo0.value" outputs="value:fow.value" uid="fow" uid_parent="fo_sr"/>')
w('      <Right inputs="value:foo.x .or. y?" outputs="value:" uid="fo_r" uid_parent="fo_sr"/>')
w('    </ShiftReg>')
menu = ctl('Menu', 'int32', '0', 'menu', desc='The screens of the application. Select one to show it.', extra=' style="Listbox"')
quit_ = ctl('Quit', 'bool', 'false', 'quit', desc='Stops the application and the remote share.', extra=' style="latched"')
node('Greater Or Equal To 0?', 'x:menu.value', 'x &gt;= 0?:mv.x &gt;= 0?', 'mv', 'sl', ind=4)
node('Select', 't:menu.value,s:mv.x &gt;= 0?,f:cur.value', 's? t\\3Af:sel.s? t\\3Af', 'sel', 'sl', ind=4)
node('Max &amp; Min', 'x:sel.s? t\\3Af,y:l_3.value', 'max(x\\2Cy):,min(x\\2Cy):want.min', 'want', 'sl', ind=4)
node('Not Equal?', 'x:want.min,y:cur.value', 'x != y?:chg.x != y?', 'chg', 'sl', ind=4)
c = Case(o, 'swc', 'sl', 'chg.x != y?', ['l_sp.value', 'l_refs.value', 'want.min', 'er.value'], ['swc.err'], 4)
c.frame('Same screen', 'False', [3], None, lambda t: [t(3)])


def swap(L, t, f):
    L.append('<Node _name="Invoke Node" target="Remove VI" type="{LV.SubPanel}" inputs="reference:%s,error in (no error):%s" outputs="reference out:,error out:%srm.error out" uid="%srm" uid_parent="%s"/>' % (t(0), t(3), f, f, f))
    L_node(L, 'Index Array', 'array:%s,index:%s' % (t(1), t(2)), 'element:%sr.element' % f, f + 'r', f)
    # inserted twice: after the first Insert VI of a running VI its indicators did not redraw (measured on
    # LabVIEW 2026, also when the VI had been inserted once before it was run); after a second one they do
    L.append('<Node _name="Invoke Node" target="Insert VI" type="{LV.SubPanel}" inputs="reference:%s,error in (no error):%srm.error out,VI Ref:%sr.element" outputs="reference out:,error out:%si1.error out" uid="%si1" uid_parent="%s"/>' % (t(0), f, f, f, f, f))
    L.append('<Node _name="Invoke Node" target="Remove VI" type="{LV.SubPanel}" inputs="reference:%s,error in (no error):%si1.error out" outputs="reference out:,error out:%srm2.error out" uid="%srm2" uid_parent="%s"/>' % (t(0), f, f, f, f))
    L.append('<Node _name="Invoke Node" target="Insert VI" type="{LV.SubPanel}" inputs="reference:%s,error in (no error):%srm2.error out,VI Ref:%sr.element" outputs="reference out:,error out:%sin.error out" uid="%sin" uid_parent="%s"/>' % (t(0), f, f, f, f, f))


c.frame('Show the selected screen', 'True', [0, 1, 2, 3], swap, lambda t: ['swc_f1in.error out'])
c.emit()
node('Index Array', 'array:l_pg.value,index:want.min', 'element:pn.element', 'pn', 'sl', ind=4)
ind_('Page', 'string', 'pn.element', 'page', desc='The screen shown.')
w('    <Node _name="Wait (ms)" inputs="milliseconds to wait:l_ms.value" outputs="" uid="wt" uid_parent="sl"/>')
w('    <Tunnel _id="Out1" inputs="value:swc.err" outputs="value:lerr.value" uid="lerr" uid_parent="sl"/>')
# closing the panel quits like the Quit button: a VI started over VI Server keeps running without its panel
# (measured), with nothing left to stop it. Only once the panel has been seen open, so a VI that is run
# before its panel opens does not quit at once
w('    <Node _name="Property Node" fields="read+Front Panel Window\\3AOpen" inputs="reference:" outputs="Front Panel Window\\3AOpen:fpo.open,reference out:,error out:" type="{LV.VI}" uid="fpo" uid_parent="sl"/>')
node('Or', 'x:fow.value,y:fpo.open', 'x .or. y?:foo.x .or. y?', 'foo', 'sl', ind=4)
node('Not', 'x:fpo.open', '.not. x?:fnc..not. x?', 'fnc', 'sl', ind=4)
node('And', 'x:fow.value,y:fnc..not. x?', 'x .and. y?:fcl.x .and. y?', 'fcl', 'sl', ind=4)
node('Or', 'x:quit.value,y:fcl.x .and. y?', 'x .or. y?:stp.x .or. y?', 'stp', 'sl', ind=4)
w('    <Condition inputs="value:stp.x .or. y?" uid="slc" uid_parent="sl" value="stop"/>')
w('  </Structure>')
# stop: notify the screens, give them a moment, take the screen out, close the references
w('  <Node _name="Send Notification" inputs="notifier:on.notifier out,notification:tr.value,error in (no error):lerr.value" outputs="notifier out:,error out:sn2.error out" uid="sn2" uid_parent="root"/>')
const('gr', 'int32', '500', name='grace ms')
w('  <Node _name="Wait (ms)" inputs="milliseconds to wait:gr.value" outputs="" uid="wg" uid_parent="root"/>')
w('  <Node _name="Invoke Node" target="Remove VI" type="{LV.SubPanel}" inputs="reference:sp.ref,error in (no error):sn2.error out" outputs="reference out:,error out:rmv.error out" uid="rmv" uid_parent="root"/>')
w('  <Structure _name="For Loop" count="" label="Close each screen reference" maxin="" maxout="" uid="cl" uid_parent="root">')
w('    <Tunnel _id="In1" inputs="value:refs.value" mode="index" outputs="value:cr.value" uid="cr" uid_parent="cl"/>')
w('    <ShiftReg uid="ce_sr" uid_parent="cl">')
w('      <Left inputs="value:rmv.error out" outputs="value:ce.value" uid="ce" uid_parent="ce_sr"/>')
w('      <Right inputs="value:cref.error out" outputs="value:" uid="ce_r" uid_parent="ce_sr"/>')
w('    </ShiftReg>')
node('Close Reference', 'reference:cr.value,error in (no error):ce.value', 'error out:cref.error out', 'cref', 'cl', ind=4)
w('    <Tunnel _id="Out1" inputs="value:cref.error out" outputs="value:cerr.value" uid="cerr" uid_parent="cl"/>')
w('  </Structure>')
node('Release Notifier', 'notifier:on.notifier out,force destroy? (F):tr.value,error in (no error):cerr.value', 'notifier name:,last notification:,error out:rln.error out', 'rln')
w('  <Call inputs="port:port.value,error in:rln.error out" outputs="error out:spe.error out" target="RemoteVI Stop.vi" uid="spe" uid_parent="root"/>')
w('  <Indicator _name="error out" description="Errors of the share\\2C the screens and the subpanel." inputs="value:spe.error out" type="%s" uid="eo" uid_parent="root" value="[false,0,]"/>' % ERR)
w('</VI>')
save('app_main.xml')
