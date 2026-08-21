import re, sys, markdown

md_path, out_path, title, eyebrow, subtitle = sys.argv[1:6]
md = open(md_path).read()
lines = md.split('\n')
md_body = '\n'.join(l for l in lines if not l.startswith('# '))
html = markdown.markdown(md_body, extensions=['tables', 'attr_list'])

toc = []
def slug(t):
    s = re.sub(r'<[^>]+>', '', t)
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

def mk(level):
    def sub(m):
        inner = m.group(1)
        sid = slug(inner)
        txt = re.sub(r'<[^>]+>', '', inner)
        num, label = '', txt
        nm = re.match(r'^(\d+)\.\s*(.+)$', txt)
        if nm: num, label = nm.group(1), nm.group(2)
        toc.append((sid, num, label, level))
        n = f'<span class="s-num">{num}</span>' if num else '<span class="s-num s-num--none">·</span>'
        return f'<h{level} id="{sid}">{n}<span class="s-label">{label}</span></h{level}>'
    return sub

def both(m):
    lvl = int(m.group(1))
    return mk(lvl)(re.match(r'<h\d>(.*?)</h\d>', m.group(0), re.S))
html = re.sub(r'<h([23])>(.*?)</h\1>', lambda m: mk(int(m.group(1)))(re.match(r'<h\d>(.*?)</h\d>', m.group(0), re.S)), html, flags=re.S)

html = html.replace('<table>', '<div class="tw"><table>').replace('</table>', '</table></div>')

toc_html = '\n'.join(
    f'<li class="lvl{lvl}"><a href="#{sid}"><span class="t-num">{num or "·"}</span><span>{label}</span></a></li>'
    for sid, num, label, lvl in toc)

shell = open('shell_template.html').read()
out = (shell.replace('__TITLE__', title).replace('__EYEBROW__', eyebrow)
            .replace('__SUBTITLE__', subtitle).replace('__TOC__', toc_html)
            .replace('__BODY__', html))
open(out_path, 'w').write(out)
print('sections:', len(toc), 'bytes:', len(out))
