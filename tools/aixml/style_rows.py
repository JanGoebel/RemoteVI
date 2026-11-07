"""Inputs of tools/dev/Style Panel.vi (a tab: (Tab, Pages, Tab Width, Width, Height), Width 0 keeps its size) as LabVIEW XML (for lvai_run_vi_and_read_values).

A row: (Label, Ctl, Tab, Page, Pane, Left, Top, Width, Height, Text, Tip, Show Label, Visible).
Ctl is relative to vi.lib\\silver_ctls ('' keeps the control); Tab '' with Pane -1 places the
control on the panel; Width/Height 0 keep the size.
"""
import json
from xml.sax.saxutils import escape


def _s(name, v):
    return '<String><Name>%s</Name><Val>%s</Val></String>' % (name, escape(v))


def _i(name, v):
    return '<I32><Name>%s</Name><Val>%d</Val></I32>' % (name, v)


def _b(name, v):
    return '<Boolean><Name>%s</Name><Val>%d</Val></Boolean>' % (name, 1 if v else 0)


def row(label, ctl='', tab='', page=0, pane=-1, left=0, top=0, width=0, height=0, text='', tip='',
        show_label=True, visible=True):
    return (label, ctl, tab, page, pane, left, top, width, height, text, tip, show_label, visible)


def rows_xml(rows):
    els = []
    for (label, ctl, tab, page, pane, left, top, width, height, text, tip, show, vis) in rows:
        els.append('<Cluster><Name></Name><NumElts>13</NumElts>%s%s%s%s%s%s%s%s%s%s%s%s%s</Cluster>' % (
            _s('Label', label), _s('Ctl', ctl), _s('Tab', tab), _i('Page', page), _i('Pane', pane),
            _i('Left', left), _i('Top', top), _i('Width', width), _i('Height', height), _s('Text', text),
            _s('Tip', tip), _b('Show Label', show), _b('Visible', vis)))
    return '<Array><Name>Rows</Name><Dimsize>%d</Dimsize>%s</Array>' % (len(rows), ''.join(els))


def tabs_xml(tabs):
    els = []
    for (tab, pages, width, w, h) in tabs:
        pg = '<Array><Name>Pages</Name><Dimsize>%d</Dimsize>%s</Array>' % (len(pages), ''.join(_s('', p) for p in pages))
        els.append('<Cluster><Name></Name><NumElts>5</NumElts>%s%s%s%s%s</Cluster>' % (_s('Tab', tab), pg, _i('Tab Width', width), _i('Width', w), _i('Height', h)))
    return '<Array><Name>Tabs</Name><Dimsize>%d</Dimsize>%s</Array>' % (len(tabs), ''.join(els))


def window_xml(l, t, r, b):
    return '<Cluster><Name>Window</Name><NumElts>4</NumElts>%s%s%s%s</Cluster>' % (_i('Left', l), _i('Top', t), _i('Right', r), _i('Bottom', b))


def spec_xml(rows, tabs, window):
    """The Spec file of Style Panel.vi: a cluster of Rows, Tabs and Window as LabVIEW XML."""
    return '<Cluster><Name>spec</Name><NumElts>3</NumElts>%s%s%s</Cluster>' % (rows_xml(rows), tabs_xml(tabs), window_xml(*window))


def write_spec(path, rows, tabs, window):
    open(path, 'w', encoding='utf-8', newline='\n').write(spec_xml(rows, tabs, window))


def inputs_json(vi, silver, spec_path):
    """inputsJson for lvai_run_vi_and_read_values on tools/dev/Style Panel.vi."""
    return json.dumps({'VI': vi, 'Silver': silver, 'Spec': spec_path})
