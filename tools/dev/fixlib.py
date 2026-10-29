import subprocess, re, os
repo = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
head = subprocess.run(['git', '-C', repo, 'show', 'HEAD:source/RemoteVI.lvlib'], capture_output=True).stdout.decode('utf-8')
src = os.path.join(repo, 'source')
lines = head.split('\n')
out = []
folder = None
items = {}
order = []
pre = []
post = []
state = 'pre'
i = 0
# parse folders
cur = None
for ln in lines:
    m = re.match(r'\t<Item Name="([^"]+)" Type="Folder">', ln)
    if m:
        cur = m.group(1); items[cur] = []; order.append(cur); state = 'in'; continue
    if state == 'in' and ln.startswith('\t</Item>'):
        cur = None; state = 'between'; continue
    if cur:
        items[cur].append(ln); continue
    if state == 'pre':
        pre.append(ln)
    else:
        post.append(ln)
# rebuild from the files on disk: every .vi in each folder
for extra in ('App',):
    if extra not in order and os.path.isdir(os.path.join(src, extra)):
        items[extra] = []
        order.insert(order.index('API') + 1, extra)
for f in order:
    d = os.path.join(src, f)
    vis = sorted([n for n in os.listdir(d) if n.endswith('.vi')], key=str.lower)
    eol = '\r' if lines[0].endswith('\r') else ''
    items[f] = ['\t\t<Item Name="%s" Type="VI" URL="../%s/%s"/>%s' % (n, f, n, eol) for n in vis]
eol = '\r' if lines[0].endswith('\r') else ''
res = list(pre)
for f in order:
    res.append('\t<Item Name="%s" Type="Folder">%s' % (f, eol))
    res += items[f]
    res.append('\t</Item>%s' % eol)
res += post
open(os.path.join(src, 'RemoteVI.lvlib'), 'w', encoding='utf-8', newline='').write('\n'.join(res))
print(order, sum(len(v) for v in items.values()))
