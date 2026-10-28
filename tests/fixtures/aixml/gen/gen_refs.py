import os
AX = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def gen(vi, names, caller_list_note):
    lst = '\\2C '.join(names)
    L = ['<VI _name="%s.vi" description="Helper of RemoteVI Complex Fixture Events.vi. Splits the array of control references RemoteVI Complex Fixture Find Controls.vi returns for %s into one named reference each\\2C so Register For Events names each event source after its control (&lt;%s Ref&gt;).">' % (vi, lst, names[0]),
         '  <FreeLabel comment="One named reference per control" uid="lbl" uid_parent="root"/>',
         '  <Control _name="Controls" conIdx="0" connection="required" description="References in the order %s." outputs="value:c.value" type="array{ref{LV.Control}}" uid="c" uid_parent="root" value="[]"/>' % lst]
    for i, n in enumerate(names):
        L.append('  <Constant _name="%d" outputs="value:k%d.value" type="int32" uid="k%d" uid_parent="root" value="%d"/>' % (i, i, i, i))
        L.append('  <Node _name="Index Array" inputs="array:c.value,index:k%d.value" outputs="element:x%d.element" uid="x%d" uid_parent="root"/>' % (i, i, i))
        L.append('  <Indicator _name="%s Ref" conIdx="%d" connection="recommended" description="The control %s." inputs="value:x%d.element" type="ref{LV.Control}" uid="o%d" uid_parent="root" value=""/>' % (n, 4 + i, n, i, i))
    L.append('</VI>')
    open(os.path.join(AX, vi + '.xml'), 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')


gen('RemoteVI Complex Fixture Refs', ['Settings', 'Rate', 'Level', 'Nav', 'Scope', 'Channel', 'Results', 'Steps'], '')
gen('RemoteVI Complex Fixture Button Refs', ['Stop', 'Inspector', 'View', 'Data File'], '')
