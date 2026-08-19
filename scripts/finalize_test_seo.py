from __future__ import annotations
import pathlib, re, sys

BAD='https://84lorinw-a11y.github.io/kingdom-circuit-test/kingdom-circuit-test/'
GOOD='https://84lorinw-a11y.github.io/kingdom-circuit-test/'
MARKER='<!-- KC SEO TEST SCHEMA -->'

def first(pattern,text):
    m=re.search(pattern,text,re.S|re.I)
    return m.group(1).strip() if m else ''

def set_meta(text, prop, value):
    if not value: return text
    pattern=rf'<meta property="{re.escape(prop)}" content="[^"]*">'
    tag=f'<meta property="{prop}" content="{value}">'
    if re.search(pattern,text,re.I):
        return re.sub(pattern,tag,text,count=1,flags=re.I)
    return text.replace('</head>',tag+'\n</head>',1)

def drop_inherited_breadcrumb(text):
    if MARKER not in text: return text
    before, after=text.split(MARKER,1)
    pattern=r'<script type="application/ld\+json">.*?</script>'
    def repl(match):
        block=match.group(0)
        return '' if 'BreadcrumbList' in block else block
    before=re.sub(pattern,repl,before,flags=re.S)
    return before+MARKER+after

def main(root):
    root=pathlib.Path(root)
    failures=[]; changed=0
    for p in root.rglob('*.html'):
        text=p.read_text(encoding='utf-8',errors='ignore')
        original=text
        text=text.replace(BAD,GOOD)
        text=drop_inherited_breadcrumb(text)
        text=text.replace('>1 shows<','>1 show<')
        title=first(r'<title>(.*?)</title>',text)
        desc=first(r'<meta name="description" content="([^"]*)">',text)
        canon=first(r'<link rel="canonical" href="([^"]+)">',text)
        text=set_meta(text,'og:title',title)
        text=set_meta(text,'og:description',desc)
        text=set_meta(text,'og:url',canon)
        if BAD in text: failures.append(f'duplicate-canonical:{p}')
        if 'name="robots" content="noindex,nofollow"' not in text: failures.append(f'noindex:{p}')
        if MARKER in text:
            marker_at=text.index(MARKER)
            if 'BreadcrumbList' in text[:marker_at]: failures.append(f'inherited-breadcrumb:{p}')
        if text!=original:
            p.write_text(text,encoding='utf-8'); changed+=1
    sitemap=root/'sitemap.xml'
    if sitemap.exists():
        text=sitemap.read_text(encoding='utf-8').replace(BAD,GOOD)
        sitemap.write_text(text,encoding='utf-8')
    for rel in ['artists/index.html','artists/kb/index.html']:
        p=root/rel
        if not p.exists(): failures.append(f'missing:{rel}'); continue
        t=p.read_text(encoding='utf-8')
        if BAD in t: failures.append(f'bad-prefix:{rel}')
        if GOOD not in t: failures.append(f'missing-test-origin:{rel}')
    if failures: raise SystemExit('\n'.join(failures[:80]))
    print(f'Finalized SEO test output: {changed} HTML files normalized')

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('Usage: finalize_test_seo.py SITE_ROOT')
    main(sys.argv[1])
