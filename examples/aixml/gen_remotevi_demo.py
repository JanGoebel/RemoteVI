"""Generates examples/aixml/remotevi_demo.xml, the source of examples/RemoteVI Demo.vi.

The demo is a data logger: its configuration (acquisition, channels, trigger, logging) on the
pages of a tab control, a live graph of four simulated channels, status indicators, and buttons
that open a LabVIEW dialog (Apply) and the native file dialog (Load Configuration). It shares its
own panel with RemoteVI Start.vi on port 8088. Nothing is written to disk: the data are simulated.

The panel is laid out afterwards by tools/dev/Style Panel.vi with build_demo.py's rows.

usage: python examples/aixml/gen_remotevi_demo.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools', 'aixml'))
from aixml_case import Case  # noqa: E402

ERR = 'cluster{bool.status,int32.code,string.source}'
o = []
w = o.append


def ctl(name, typ, value, uid, parent='sl', desc='', extra=''):
    w('    <Control _name="%s" description="%s" outputs="value:%s.value" type="%s" uid="%s" uid_parent="%s" value="%s"%s/>'
      % (name, desc, uid, typ, uid, parent, value, extra))


def ind(name, typ, net, uid, parent='sl', desc='', extra='', value=''):
    w('    <Indicator _name="%s" description="%s" inputs="value:%s" type="%s" uid="%s" uid_parent="%s" value="%s"%s/>'
      % (name, desc, net, typ, uid, parent, value, extra))


w('<VI _name="RemoteVI Demo.vi" description="RemoteVI example\\3A a data logger operated from a web browser. RemoteVI Start.vi shares this panel on port 8088 (this computer only)\\3B Remote Link shows the link with its access token - open it in a browser. The tabs hold the logger\\27s configuration (acquisition\\2C channels\\2C trigger\\2C logging - one control of every common kind)\\2C Acquire starts and stops four simulated channels on the Live Data graph\\2C Apply asks for confirmation in a LabVIEW dialog and Load Configuration opens the native file dialog - both are answered in the browser like the panel is operated. Quit stops the logger and RemoteVI Stop.vi ends the share. The data are simulated\\3B nothing is written to disk.">')
w('  <FreeLabel comment="Share the panel\\2C run the logger until Quit\\2C stop sharing" uid="lbl" uid_parent="root"/>')
w('  <Constant _name="port" outputs="value:port.value" type="uint16" uid="port" uid_parent="root" value="8088"/>')
w('  <Call inputs="port:port.value" outputs="URL:st.URL,error out:st.error out" target="RemoteVI Start.vi" uid="st" uid_parent="root"/>')
w('  <Indicator _name="Remote Link" description="Open this link in a browser to operate the panel remotely (RemoteVI)." inputs="value:st.URL" type="string" uid="url" uid_parent="root" value=""/>')
w('  <Constant _name="history length" outputs="value:hl.value" type="int32" uid="hl" uid_parent="root" value="1000"/>')
w('  <Constant _name="loop period ms" outputs="value:ms.value" type="int32" uid="ms" uid_parent="root" value="50"/>')
w('  <Constant _name="no data yet (one row per channel)" outputs="value:h0.value" type="array.2{double}" uid="h0" uid_parent="root" value="[[NaN],[NaN],[NaN],[NaN]]"/>')
w('  <Constant _name="no samples" outputs="value:k0.value" type="double" uid="k0" uid_parent="root" value="0"/>')
w('  <Constant _name="first status" outputs="value:s0.value" type="string" uid="s0" uid_parent="root" value="Ready. Press Acquire to start the simulated channels."/>')
w('  <Structure _name="While Loop" count="" label="Logger loop\\2C every 50 ms" uid="sl" uid_parent="root">')
w('    <Tunnel _id="In1" inputs="value:hl.value" outputs="value:l_hl.value" uid="l_hl" uid_parent="sl"/>')
w('    <Tunnel _id="In2" inputs="value:ms.value" outputs="value:l_ms.value" uid="l_ms" uid_parent="sl"/>')
w('    <Tunnel _id="In3" inputs="value:st.error out" outputs="value:l_err.value" uid="l_err" uid_parent="sl"/>')
w('    <ShiftReg uid="sr_h" uid_parent="sl">')
w('      <Left inputs="value:h0.value" outputs="value:hist.value" uid="sr_hl" uid_parent="sr_h"/>')
w('      <Right inputs="value:acq.hist" outputs="value:" uid="sr_hr" uid_parent="sr_h"/>')
w('    </ShiftReg>')
w('    <ShiftReg uid="sr_k" uid_parent="sl">')
w('      <Left inputs="value:k0.value" outputs="value:kk.value" uid="sr_kl" uid_parent="sr_k"/>')
w('      <Right inputs="value:acq.k" outputs="value:" uid="sr_kr" uid_parent="sr_k"/>')
w('    </ShiftReg>')
w('    <ShiftReg uid="sr_s" uid_parent="sl">')
w('      <Left inputs="value:s0.value" outputs="value:stat.value" uid="sr_sl" uid_parent="sr_s"/>')
w('      <Right inputs="value:ld.status" outputs="value:" uid="sr_sr" uid_parent="sr_s"/>')
w('    </ShiftReg>')

# --- configuration controls (read every iteration) ---
ctl('Device', 'string', 'Dev1 (simulated)', 'dev', desc='The acquisition device. Simulated in this example.')
ctl('Sample Rate (Hz)', 'double', '1000', 'rate', desc='Samples per second and channel.')
ctl('Samples per Read', 'double', '50', 'spr', desc='Samples read per channel in each 50 ms loop (10 to 500).')
ctl('Acquisition Mode', 'uint16{Continuous,Finite,Triggered}', '0', 'mode', desc='Continuous, a finite number of samples, or started by the trigger.')
ctl('Duration (s)', 'double', '60', 'dur', desc='Length of a finite acquisition.')
ctl('Add Noise', 'bool', 'true', 'noise', desc='Adds random noise to the simulated signals.')
ctl('Channels', 'array.2{string}', '[[Channel,Name,Unit,Scale],[AI0,Supply pressure,bar,0.25 bar/V],[AI1,Return pressure,bar,0.25 bar/V],[AI2,Coolant temperature,degC,10 degC/V],[AI3,Flow,l/min,2 l/min/V]]', 'chn', desc='Name\\2C unit and scale of each channel - click a cell to edit it.')
for c in range(4):
    ctl('CH%d' % c, 'bool', 'true' if c < 2 else 'false', 'en%d' % c, desc='Acquire and show channel AI%d.' % c)
ctl('Input Range', 'uint16{+-1 V,+-5 V,+-10 V}', '2', 'rng', desc='Input range of all channels.')
ctl('Trigger Source', 'int32', '0', 'tsrc', desc='What starts a triggered acquisition.', extra=' items="Immediate,Software,Analog edge" style="Ring" values="[0,1,2]"')
ctl('Trigger Level (V)', 'double', '2.5', 'tlev', desc='Level of the analog edge trigger.')
ctl('Trigger Slope', 'uint16{Rising,Falling}', '0', 'tslp', desc='Edge of the analog trigger.')
ctl('Filter Cutoff (Hz)', 'double', '250', 'fcut', desc='Cutoff frequency of the anti-aliasing filter.')
ctl('Log Folder', 'path', 'C\\3A\\5CData\\5CDatalogger', 'lf', desc='Where log files would be written (browse with the folder button).')
ctl('File Prefix', 'string', 'cooling-loop', 'fpx', desc='Start of each log file name.')
ctl('File Format', 'uint16{CSV,TDMS,Binary}', '1', 'ffmt', desc='Format of the log files.')
ctl('Split Every (min)', 'double', '15', 'split', desc='Starts a new log file after this many minutes.')
ctl('Scheduled Start', 'timestamp', '', 'tst', desc='When a scheduled acquisition starts.')
ctl('Comment', 'string', 'Bench test of the cooling loop', 'cmt', desc='Stored in the header of every log file.')
ctl('Acquire', 'bool', 'false', 'acqb', desc='Starts and stops the acquisition.')
ctl('Apply', 'bool', 'false', 'apb', desc='Applies the configuration (asks first in a dialog).', extra=' style="latched"')
ctl('Load Configuration', 'bool', 'false', 'ldb', desc='Opens a configuration file (native file dialog).', extra=' style="latched"')
ctl('Quit', 'bool', 'false', 'quit', desc='Stops the logger and the remote share.', extra=' style="latched"')

w('    <Node _name="Build Array" inputs="element:en0.value,element:en1.value,element:en2.value,element:en3.value" outputs="appended array:ens.appended array" uid="ens" uid_parent="sl"/>')
w('    <Constant outputs="value:c10.value" type="double" uid="c10" uid_parent="sl" value="10"/>')
w('    <Constant outputs="value:c500.value" type="double" uid="c500" uid_parent="sl" value="500"/>')
w('    <Node _name="Max &amp; Min" inputs="x:spr.value,y:c10.value" outputs="max(x\\2Cy):mx1.max,min(x\\2Cy):" uid="mx1" uid_parent="sl"/>')
w('    <Node _name="Max &amp; Min" inputs="x:mx1.max,y:c500.value" outputs="max(x\\2Cy):,min(x\\2Cy):mx2.min" uid="mx2" uid_parent="sl"/>')
w('    <Constant outputs="value:c1.value" type="double" uid="c1" uid_parent="sl" value="1"/>')
w('    <Node _name="Max &amp; Min" inputs="x:rate.value,y:c1.value" outputs="max(x\\2Cy):mx3.max,min(x\\2Cy):" uid="mx3" uid_parent="sl"/>')

# --- acquisition: inputs 0 hist, 1 k, 2 enables, 3 n, 4 rate, 5 noise, 6 history length
acq = Case(o, 'acq', 'sl', 'acqb.value', ['hist.value', 'kk.value', 'ens.appended array', 'mx2.min', 'mx3.max', 'noise.value', 'l_hl.value'], ['acq.hist', 'acq.k'], 4)
acq.frame('Stopped\\3A keep the data', 'False', [0, 1], None, lambda t: [t(0), t(1)])


def acquire(L, t, f):
    L.append('<Structure _name="For Loop" count="%sch.value" label="Each channel" maxin="" maxout="" uid="%sch" uid_parent="%s">' % (f, f, f))
    L.append('  <Tunnel _id="In1" inputs="value:%s" mode="index" outputs="value:%sen.value" uid="%sen" uid_parent="%sch"/>' % (t(2), f, f, f))
    L.append('  <Tunnel _id="In2" inputs="value:%s" mode="index" outputs="value:%srow.subarray" uid="%srow" uid_parent="%sch"/>' % (t(0), f, f, f))
    for k, (src, nm) in enumerate([(t(1), 'k'), (t(3), 'n'), (t(4), 'r'), (t(5), 'z'), (t(6), 'L')]):
        L.append('  <Tunnel _id="In%d" inputs="value:%s" outputs="value:%s%s.value" uid="%s%s" uid_parent="%sch"/>' % (k + 3, src, f, nm, f, nm, f))
    c = f + 'ch'
    L.append('  <Node _name="To Double Precision Float" inputs="number:%sch.value" outputs="double precision float:%scd.double precision float" uid="%scd" uid_parent="%s"/>' % (f, f, f, c))
    L.append('  <Constant outputs="value:%sa0.value" type="double" uid="%sa0" uid_parent="%s" value="0.5"/>' % (f, f, c))
    L.append('  <Node _name="Multiply" inputs="x:%scd.double precision float,y:%sa0.value" outputs="x*y:%sa1.x*y" uid="%sa1" uid_parent="%s"/>' % (f, f, f, f, c))
    L.append('  <Constant outputs="value:%sa2.value" type="double" uid="%sa2" uid_parent="%s" value="1"/>' % (f, f, c))
    L.append('  <Node _name="Add" inputs="x:%sa1.x*y,y:%sa2.value" outputs="x+y:%samp.x+y" uid="%samp" uid_parent="%s"/>' % (f, f, f, f, c))
    L.append('  <Constant outputs="value:%sf0.value" type="double" uid="%sf0" uid_parent="%s" value="12.566370614359172"/>' % (f, f, c))
    L.append('  <Node _name="Add" inputs="x:%scd.double precision float,y:%sa2.value" outputs="x+y:%sf1.x+y" uid="%sf1" uid_parent="%s"/>' % (f, f, f, f, c))
    L.append('  <Node _name="Multiply" inputs="x:%sf1.x+y,y:%sf0.value" outputs="x*y:%sw.x*y" uid="%sw" uid_parent="%s"/>' % (f, f, f, f, c))
    L.append('  <Constant outputs="value:%snan.value" type="double" uid="%snan" uid_parent="%s" value="NaN"/>' % (f, f, c))
    L.append('  <Constant outputs="value:%snz.value" type="double" uid="%snz" uid_parent="%s" value="0.3"/>' % (f, f, c))
    # samples of this channel
    s = f + 'sm'
    L.append('  <Structure _name="For Loop" count="%s.value" label="Each sample" maxin="%sn.value" maxout="" uid="%s" uid_parent="%s">' % (s, f, s, c))
    for k, (src, nm) in enumerate([(f + 'k.value', 'k'), (f + 'r.value', 'r'), (f + 'w.x*y', 'w'), (f + 'amp.x+y', 'a'), (f + 'z.value', 'z'),
                                   (f + 'en.value', 'e'), (f + 'nan.value', 'q'), (f + 'nz.value', 'm')]):
        L.append('    <Tunnel _id="In%d" inputs="value:%s" outputs="value:%s%s.value" uid="%s%s" uid_parent="%s"/>' % (k + 1, src, s, nm, s, nm, s))
    L.append('    <Node _name="To Double Precision Float" inputs="number:%s.value" outputs="double precision float:%sjd.double precision float" uid="%sjd" uid_parent="%s"/>' % (s, s, s, s))
    L.append('    <Node _name="Add" inputs="x:%sk.value,y:%sjd.double precision float" outputs="x+y:%skj.x+y" uid="%skj" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('    <Node _name="Divide" inputs="x:%skj.x+y,y:%sr.value" outputs="x/y:%st.x/y" uid="%st" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('    <Node _name="Multiply" inputs="x:%st.x/y,y:%sw.value" outputs="x*y:%sph.x*y" uid="%sph" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('    <Node _name="Sine" inputs="x:%sph.x*y" outputs="sin(x):%ssn.sin(x)" uid="%ssn" uid_parent="%s"/>' % (s, s, s, s))
    L.append('    <Node _name="Multiply" inputs="x:%ssn.sin(x),y:%sa.value" outputs="x*y:%sy.x*y" uid="%sy" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('    <Node _name="Random Number (0-1)" inputs="" outputs="number\\3A 0 to 1:%srn.number\\3A 0 to 1" uid="%srn" uid_parent="%s"/>' % (s, s, s))
    L.append('    <Constant outputs="value:%sh5.value" type="double" uid="%sh5" uid_parent="%s" value="0.5"/>' % (s, s, s))
    L.append('    <Node _name="Subtract" inputs="x:%srn.number\\3A 0 to 1,y:%sh5.value" outputs="x-y:%sr0.x-y" uid="%sr0" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('    <Node _name="Multiply" inputs="x:%sr0.x-y,y:%sm.value" outputs="x*y:%sr1.x*y" uid="%sr1" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('    <Constant outputs="value:%szero.value" type="double" uid="%szero" uid_parent="%s" value="0"/>' % (s, s, s))
    L.append('    <Node _name="Select" inputs="t:%sr1.x*y,s:%sz.value,f:%szero.value" outputs="s? t\\3Af:%snoi.s? t\\3Af" uid="%snoi" uid_parent="%s"/>' % (s, s, s, s, s, s))
    L.append('    <Node _name="Add" inputs="x:%sy.x*y,y:%snoi.s? t\\3Af" outputs="x+y:%sv.x+y" uid="%sv" uid_parent="%s"/>' % (s, s, s, s, s))
    L.append('    <Node _name="Select" inputs="t:%sv.x+y,s:%se.value,f:%sq.value" outputs="s? t\\3Af:%sout.s? t\\3Af" uid="%sout" uid_parent="%s"/>' % (s, s, s, s, s, s))
    L.append('    <Tunnel _id="Out1" inputs="value:%sout.s? t\\3Af" mode="index" outputs="value:%sblk.value" uid="%sblk" uid_parent="%s"/>' % (s, s, s, s))
    L.append('  </Structure>')
    # append, keep the last L samples
    L.append('  <Node _name="Build Array" concat="true" inputs="array:%srow.subarray,array:%sblk.value" outputs="appended array:%scat.appended array" uid="%scat" uid_parent="%s"/>' % (f, s, f, f, c))
    L.append('  <Node _name="Array Size" inputs="array:%scat.appended array" outputs="size(s):%ssz.size(s)" uid="%ssz" uid_parent="%s"/>' % (f, f, f, c))
    L.append('  <Node _name="Subtract" inputs="x:%ssz.size(s),y:%sL.value" outputs="x-y:%sst.x-y" uid="%sst" uid_parent="%s"/>' % (f, f, f, f, c))
    L.append('  <Constant outputs="value:%si0.value" type="int32" uid="%si0" uid_parent="%s" value="0"/>' % (f, f, c))
    L.append('  <Node _name="Max &amp; Min" inputs="x:%sst.x-y,y:%si0.value" outputs="max(x\\2Cy):%sst0.max,min(x\\2Cy):" uid="%sst0" uid_parent="%s"/>' % (f, f, f, f, c))
    L.append('  <Node _name="Array Subset" inputs="array:%scat.appended array,index:%sst0.max,length:%sL.value" outputs="subarray:%skeep.subarray" uid="%skeep" uid_parent="%s"/>' % (f, f, f, f, f, c))
    L.append('  <Tunnel _id="Out1" inputs="value:%skeep.subarray" mode="index" outputs="value:%snh.value" uid="%snh" uid_parent="%s"/>' % (f, f, f, c))
    L.append('</Structure>')
    L.append('<Node _name="To Double Precision Float" inputs="number:%s" outputs="double precision float:%snd.double precision float" uid="%snd" uid_parent="%s"/>' % (t(3), f, f, f))
    L.append('<Node _name="Add" inputs="x:%s,y:%snd.double precision float" outputs="x+y:%sk1.x+y" uid="%sk1" uid_parent="%s"/>' % (t(1), f, f, f, f))


acq.frame('Acquiring\\3A four simulated channels', 'True', [0, 1, 2, 3, 4, 5, 6], acquire, lambda t: ['acq_f1nh.value', 'acq_f1k1.x+y'])
acq.emit()

w('    <Indicator _name="Live Data" description="The last 1000 samples of every enabled channel." inputs="value:acq.hist" style="graph21703" type="array.2{double}" uid="graph" uid_parent="sl" value="[]"/>')
ind('Acquiring', 'bool', 'acqb.value', 'led', desc='Lit while the channels are acquired.', value='false')
ind('Samples Acquired', 'double', 'acq.k', 'cnt', desc='Samples per channel since the start.', value='0')
w('    <Node _name="Array Size" inputs="array:acq.hist" outputs="size(s):hsz.size(s)" uid="hsz" uid_parent="sl"/>')
w('    <Node _name="Array Max &amp; Min" inputs="array:hsz.size(s)" outputs="max value:hcols.max value,max index (indices):,min value:,min index (indices):" uid="hcols" uid_parent="sl"/>')
w('    <Node _name="To Double Precision Float" inputs="number:hcols.max value" outputs="double precision float:hcd.double precision float" uid="hcd" uid_parent="sl"/>')
w('    <Constant outputs="value:pct.value" type="double" uid="pct" uid_parent="sl" value="0.1"/>')
w('    <Node _name="Multiply" inputs="x:hcd.double precision float,y:pct.value" outputs="x*y:buf.x*y" uid="buf" uid_parent="sl"/>')
ind('Buffer Usage (%)', 'double', 'buf.x*y', 'bufi', desc='How full the 1000-sample display buffer is.', value='0')
w('    <Constant outputs="value:tsc.value" type="double" uid="tsc" uid_parent="sl" value="0.0002"/>')
w('    <Node _name="Multiply" inputs="x:acq.k,y:tsc.value" outputs="x*y:tph.x*y" uid="tph" uid_parent="sl"/>')
w('    <Node _name="Sine" inputs="x:tph.x*y" outputs="sin(x):tsn.sin(x)" uid="tsn" uid_parent="sl"/>')
w('    <Constant outputs="value:t3.value" type="double" uid="t3" uid_parent="sl" value="4"/>')
w('    <Node _name="Multiply" inputs="x:tsn.sin(x),y:t3.value" outputs="x*y:tdv.x*y" uid="tdv" uid_parent="sl"/>')
w('    <Constant outputs="value:t35.value" type="double" uid="t35" uid_parent="sl" value="38"/>')
w('    <Node _name="Add" inputs="x:tdv.x*y,y:t35.value" outputs="x+y:temp.x+y" uid="temp" uid_parent="sl"/>')
ind('Board (degC)', 'double', 'temp.x+y', 'tmpi', desc='Temperature of the acquisition board (simulated).', value='0')
w('    <Node _name="And" inputs="x:acqb.value,y:en0.value" outputs="x .and. y?:on0.x .and. y?" uid="on0" uid_parent="sl"/>')
w('    <Node _name="Random Number (0-1)" inputs="" outputs="number\\3A 0 to 1:rr.number\\3A 0 to 1" uid="rr" uid_parent="sl"/>')
w('    <Constant outputs="value:r02.value" type="double" uid="r02" uid_parent="sl" value="0.02"/>')
w('    <Node _name="Multiply" inputs="x:rr.number\\3A 0 to 1,y:r02.value" outputs="x*y:rj.x*y" uid="rj" uid_parent="sl"/>')
w('    <Constant outputs="value:rms0.value" type="double" uid="rms0" uid_parent="sl" value="0.7071"/>')
w('    <Node _name="Add" inputs="x:rms0.value,y:rj.x*y" outputs="x+y:rmsv.x+y" uid="rmsv" uid_parent="sl"/>')
w('    <Constant outputs="value:zr.value" type="double" uid="zr" uid_parent="sl" value="0"/>')
w('    <Node _name="Select" inputs="t:rmsv.x+y,s:on0.x .and. y?,f:zr.value" outputs="s? t\\3Af:rms.s? t\\3Af" uid="rms" uid_parent="sl"/>')
ind('AI0 RMS (V)', 'double', 'rms.s? t\\3Af', 'rmsi', desc='RMS value of channel AI0.', value='0')

# --- Apply: Two Button Dialog
ap = Case(o, 'ap', 'sl', 'apb.value', ['stat.value'], ['ap.status'], 4)
ap.frame('Nothing to apply', 'False', [0], None, lambda t: [t(0)])


def apply_body(L, t, f):
    L.append('<Constant _name="message" outputs="value:%sm.value" type="string" uid="%sm" uid_parent="%s" value="Apply this configuration to the data logger?"/>' % (f, f, f))
    L.append('<Constant _name="yes" outputs="value:%sy.value" type="string" uid="%sy" uid_parent="%s" value="Apply"/>' % (f, f, f))
    L.append('<Constant _name="no" outputs="value:%sn.value" type="string" uid="%sn" uid_parent="%s" value="Cancel"/>' % (f, f, f))
    L.append('<Node _name="Two Button Dialog" inputs="message:%sm.value,T button name (&quot;OK&quot;):%sy.value,F button name (&quot;Cancel&quot;):%sn.value" outputs="T button?:%sd.T button?" uid="%sd" uid_parent="%s"/>' % (f, f, f, f, f, f))
    L.append('<Constant outputs="value:%sok.value" type="string" uid="%sok" uid_parent="%s" value="Configuration applied."/>' % (f, f, f))
    L.append('<Constant outputs="value:%sno.value" type="string" uid="%sno" uid_parent="%s" value="Apply cancelled - the configuration was not changed."/>' % (f, f, f))
    L.append('<Node _name="Select" inputs="t:%sok.value,s:%sd.T button?,f:%sno.value" outputs="s? t\\3Af:%ss.s? t\\3Af" uid="%ss" uid_parent="%s"/>' % (f, f, f, f, f, f))


ap.frame('Ask the remote user', 'True', [0], apply_body, lambda t: ['ap_f1s.s? t\\3Af'])
ap.emit()

# --- Load Configuration: native file dialog
ld = Case(o, 'ld', 'sl', 'ldb.value', ['ap.status'], ['ld.status'], 4)
ld.frame('Nothing to load', 'False', [0], None, lambda t: [t(0)])


def load_body(L, t, f):
    L.append('<Node _name="File Dialog" inputs="" outputs="selected path:%sd.selected path,error out:" uid="%sd" uid_parent="%s"/>' % (f, f, f))
    L.append('<Node _name="Not A Number/Path/Refnum?" inputs="number/path/refnum:%sd.selected path" outputs="NaN/Path/Refnum?:%sc.NaN/Path/Refnum?" uid="%sc" uid_parent="%s"/>' % (f, f, f, f))
    L.append('<Node _name="Strip Path" inputs="path:%sd.selected path" outputs="stripped path:,name:%sp.string" uid="%sp" uid_parent="%s"/>' % (f, f, f, f))
    L.append('<Constant outputs="value:%sfm.value" type="string" uid="%sfm" uid_parent="%s" value="Loaded configuration %%s (simulated)."/>' % (f, f, f))
    L.append('<Node _name="Format Into String" inputs="format string:%sfm.value,input 1:%sp.string" outputs="resulting string:%sm.resulting string" uid="%sm" uid_parent="%s"/>' % (f, f, f, f, f))
    L.append('<Constant outputs="value:%sx.value" type="string" uid="%sx" uid_parent="%s" value="Load cancelled."/>' % (f, f, f))
    L.append('<Node _name="Select" inputs="t:%sx.value,s:%sc.NaN/Path/Refnum?,f:%sm.resulting string" outputs="s? t\\3Af:%ss.s? t\\3Af" uid="%ss" uid_parent="%s"/>' % (f, f, f, f, f, f))


ld.frame('Let the remote user choose a file', 'True', [0], load_body, lambda t: ['ld_f1s.s? t\\3Af'])
ld.emit()
ind('Status', 'string', 'ld.status', 'stati', desc='What the logger did last.')

w('    <Node _name="Wait (ms)" inputs="milliseconds to wait:l_ms.value" outputs="" uid="wt" uid_parent="sl"/>')
w('    <Tunnel _id="Out1" inputs="value:l_err.value" outputs="value:err_end.value" uid="err_end" uid_parent="sl"/>')
w('    <Condition inputs="value:quit.value" uid="slc" uid_parent="sl" value="stop"/>')
w('  </Structure>')
w('  <Call inputs="port:port.value,error in:err_end.value" outputs="error out:sp.error out" target="RemoteVI Stop.vi" uid="sp" uid_parent="root"/>')
w('  <Indicator _name="error out" description="Errors of RemoteVI Start.vi and RemoteVI Stop.vi." inputs="value:sp.error out" type="%s" uid="eo" uid_parent="root" value="[false,0,]"/>' % ERR)
w('</VI>')

open(os.path.join(HERE, 'remotevi_demo.xml'), 'w', encoding='utf-8', newline='\n').write('\n'.join(o) + '\n')
print('wrote remotevi_demo.xml,', len(o), 'lines')
