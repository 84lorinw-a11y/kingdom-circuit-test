"""Deterministic location navigation preview over the exact published catalog.

No event, artist, historical URL, image, date or source record is rewritten.
Test identity remains noindex. This module is separate from production pins.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from html import escape, unescape
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from mobile_seo_preview import Document, replace_spans, test_source
from live_mirror_v2 import TEST_BASE, TEST_SITE

ROOT = Path(__file__).resolve().parents[1]
VERSION = '20261115-1'
FILES = frozenset({'shows/states/index.html', 'shows/cities/index.html',
                   'assets/location-navigation.css', 'assets/location-navigation.js',
                   'assets/location-navigation-data.json'})
ARROW = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M5 12h14m-6-6 6 6-6 6" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>'
SEARCH = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="m16 16 5 5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>'
NEARBY = [('orlando-florida','kissimmee-florida'), ('dallas-texas','arlington-texas'),
          ('dallas-texas','fort-worth-texas'), ('phoenix-arizona','mesa-arizona'),
          ('detroit-michigan','belleville-michigan'), ('fort-lauderdale-florida','north-lauderdale-florida')]

def path_of(href):
    path = urlsplit(href).path
    return '/' + path.removeprefix(TEST_BASE).lstrip('/') if path.startswith(TEST_BASE) else path

def href(path):
    return TEST_BASE + path.lstrip('/')

def public_cards(text):
    doc = Document(text)
    records = {}
    for n in doc.nodes:
        if 'data-event-card' not in n.attrs: continue
        part = Document(doc.raw(n))
        heading = next((x for x in part.nodes if x.tag == 'h3'), None)
        if heading is None: continue
        anchor = next((x for x in part.nodes if x.tag == 'a' and heading.start < x.start < heading.end), None)
        if anchor is None: continue
        material = ' '.join(part.text(x) for x in part.nodes if x.has('event-badges')) + ' ' + part.text(heading)
        if re.search(r'private|invite[\s-]?only|cancelled|canceled|postponed', material, re.I): continue
        meta = {}
        for row in (x for x in part.nodes if x.tag == 'div'):
            dt = next((x for x in row.children if x.tag == 'dt'), None)
            dd = next((x for x in row.children if x.tag == 'dd'), None)
            if dt and dd: meta[part.text(dt)] = part.text(dd)
        records[path_of(anchor.attrs['href'])] = {'location':meta.get('Location',''), 'state':n.attrs.get('data-state','')}
    return records

def breadcrumbs(text):
    for value in re.findall(r'<script\b[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', text, re.S):
        obj=json.loads(value)
        if isinstance(obj,dict) and obj.get('@type')=='BreadcrumbList': return obj.get('itemListElement',[])
    return []

def context(live):
    # The final published All Shows calendar already owns expiry and deduplication.
    public = public_cards((live/'shows/index.html').read_text())
    doc=Document((live/'shows/index.html').read_text())
    permanent=doc.one(lambda n:'data-permanent-state-navigation' in n.attrs or (n.tag=='nav' and n.has('kc-state-links') and 'state' in n.attrs.get('aria-label','')))
    regions={}
    for n in doc.nodes:
        if n.tag=='a' and permanent.start<n.start<permanent.end:
            path=path_of(n.attrs['href'])
            label=next((doc.text(child) for child in n.children if child.tag=='span'),doc.text(n))
            regions[path]={'path':path,'name':label,'cities':[]}
    cities={}; locations={}
    for file in sorted((live/'shows').glob('*/index.html')):
        path='/'+file.parent.relative_to(live).as_posix()+'/'
        text=file.read_text();crumb=breadcrumbs(text)
        if path not in regions and not (len(crumb)==3 and path_of(crumb[-1].get('item',''))==path and path_of(crumb[-2].get('item','')) in regions):continue
        members=set(public_cards(text))&set(public)
        if path in regions:
            regions[path].update(count=len(members),events=sorted(members))
        else:
            parent=path_of(crumb[-2]['item'])
            city={'path':path,'name':crumb[-1]['name'],'region':parent,'count':len(members),'events':sorted(members)}
            cities[path]=city
            if members:
                regions[parent]['cities'].append(path)
                for event in members:
                    label=public[event]['location']
                    if label in locations and locations[label]!=path:raise ValueError('Ambiguous city label: '+label)
                    locations[label]=path
    for region in regions.values():
        assert 'count' in region,region
        region['cities'].sort(key=lambda p:(-cities[p]['count'],cities[p]['name']))
    assert regions and cities and public
    template=test_source(live,'about-us/index.html')
    ctx={'regions':regions,'cities':cities,'locations':locations,'publicCount':len(public),'template':template}
    ctx['generated']=generate(ctx)
    return ctx

def count_label(n):return f'{n} show'+('' if n==1 else 's')

def location_link(row, cls='kc-location-row', secondary=None):
    sub = secondary if secondary is not None else (count_label(row['count'])+' upcoming' if row['count'] else 'No upcoming shows listed')
    return (f'<a class="{cls}" href="{href(row["path"])}" data-location-entry data-search="{escape(row["name"].casefold(),quote=True)}">'
            f'<span><strong>{escape(row["name"])}</strong><small>{escape(sub)}</small></span>{ARROW}</a>')

def quick_links(ctx):
    top=sorted((c for c in ctx['cities'].values() if c['count']),key=lambda c:(-c['count'],c['name']))[:4]
    links=''.join(f'<a href="{href(c["path"])}">{escape(c["name"])}</a>' for c in top)
    return (f'<section class="kc-location-start" aria-label="Browse shows by location">'
            f'<div class="kc-location-start-actions"><a href="{href("/shows/states/")}"><span>Browse states</span>{ARROW}</a>'
            f'<a href="{href("/shows/cities/")}"><span>Browse cities</span>{ARROW}</a></div>'
            f'<nav class="kc-location-shortcuts" aria-label="Cities with the most upcoming shows">{links}</nav></section>')

def nav(active):
    items=[('Shows','/shows/'),('States','/shows/states/'),('Cities','/shows/cities/'),('Artists','/artists/'),('Festivals','/festivals/')]
    return '<nav class="kc-location-nav" aria-label="Primary navigation">'+''.join(
        f'<a href="{href(path)}"'+(' aria-current="page"' if path==active else '')+f'>{label}</a>' for label,path in items)+'</nav>'

def menu():
    return (f'<details class="kc-location-menu"><summary aria-label="More navigation"><span>Menu</span>'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 7h14M5 12h14M5 17h14" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg></summary>'
            f'<nav aria-label="More navigation"><a href="{TEST_BASE}">Home</a><a href="{href("/about-us/")}">About Us</a>'
            f'<a href="{href("/submit/")}">Submit a Show</a><a href="{href("/shows/this-weekend/")}">This Weekend</a>'
            f'<a href="{href("/shows/this-month/")}">This Month</a><a href="{href("/new-shows/")}">New Shows</a></nav></details>')

def transform(relative,data,ctx):
    rel=str(relative)
    if rel=='sitemap.xml':
        text=data.decode()
        for route in ['shows/states/','shows/cities/']:
            url=TEST_SITE+'/'+route
            if '<loc>'+url+'</loc>' not in text:text=text.replace('</urlset>','<url><loc>'+url+'</loc></url></urlset>')
        return text.encode()
    if not rel.endswith('.html'):return data
    text=data.decode()
    if 'class="kc-rd-header' not in text:return data
    if 'data-location-navigation-version=' in text:return data
    doc=Document(text);changes=[]
    path='/' if rel=='index.html' else '/'+rel.removesuffix('index.html')
    active='/shows/cities/' if path in ctx['cities'] or path=='/shows/cities/' else '/shows/states/' if path in ctx['regions'] or path=='/shows/states/' else '/artists/' if path.startswith('/artists/') else '/festivals/' if path.startswith('/festivals/') else '/shows/' if path.startswith(('/shows/','/new-shows/','/event/')) or path=='/' else ''
    header=doc.one(lambda n:n.tag=='header' and n.has('kc-rd-header'))
    hdoc=Document(doc.raw(header));hc=[]
    oldnav=[n for n in hdoc.nodes if n.tag=='nav' and n.has('kc-rd-nav')]
    for n in oldnav:hc.append((n.start,n.end,nav(active)))
    if not oldnav:
        root=hdoc.one(lambda n:n.tag=='header' and n.has('kc-rd-header'));hc.append((root.closing_start,root.closing_start,nav(active)))
    primary=hdoc.one(lambda n:n.has('kc-rd-primary'))
    hc.append((primary.closing_start,primary.closing_start,menu()))
    head=replace_spans(hdoc.source,hc).replace('class="kc-rd-header','data-location-navigation-version="'+VERSION+'" class="kc-rd-header',1)
    changes.append((header.start,header.end,head))
    for n in doc.nodes:
        if n.has('footer-links'):
            links=''.join(f'<a href="{href(p)}">{label}</a>' for label,p in [('All Shows','/shows/'),('States','/shows/states/'),('Cities','/shows/cities/'),('Artists','/artists/'),('Festivals','/festivals/'),('About Us','/about-us/'),('Submit a Show','/submit/')])
            changes.append((n.opening_end,n.closing_start,links))
    if rel=='index.html':
        hero=doc.one(lambda n:n.tag=='section' and n.has('kc-discovery-hero'))
        changes.append((hero.end,hero.end,quick_links(ctx)))
    if path in ctx['regions']:
        region=ctx['regions'][path];old=[n for n in doc.nodes if n.tag=='section' and (n.has('kc-city-links') or (n.has('seo-location-strip') and 'Browse cities' in doc.raw(n)))]
        children=[ctx['cities'][c] for c in region['cities']]
        block=(f'<section class="kc-location-related" aria-label="Cities in {escape(region["name"])}"><div class="kc-location-section-heading"><h2>Cities in {escape(region["name"])}</h2><a href="{href("/shows/cities/")}">All cities</a></div><div class="kc-location-related-links">'+''.join(location_link(c,secondary=count_label(c['count'])) for c in children)+'</div></section>') if children else ''
        if old:changes.append((old[0].start,old[0].end,block))
        elif block:
            calendar=doc.one(lambda n:n.tag=='section' and n.has('calendar'));changes.append((calendar.end,calendar.end,block))
    if path in ctx['cities']:
        city=ctx['cities'][path];region=ctx['regions'][city['region']]
        near={('/shows/'+b+'/') for a,b in NEARBY if path=='/shows/'+a+'/'}|{('/shows/'+a+'/') for a,b in NEARBY if path=='/shows/'+b+'/'}
        nearby=[ctx['cities'][p] for p in near if p in ctx['cities'] and ctx['cities'][p]['count']]
        choices=nearby or [ctx['cities'][p] for p in region['cities'] if p!=path][:3]
        title='Nearby cities' if nearby else 'More cities in '+region['name']
        if choices:
            block=f'<section class="kc-location-related" aria-label="{escape(title)}"><div class="kc-location-section-heading"><h2>{escape(title)}</h2><a href="{href(city["region"])}">All {escape(region["name"])} shows</a></div><div class="kc-location-related-links">'+''.join(location_link(c,secondary=count_label(c['count'])) for c in choices)+'</div></section>'
            calendar=doc.one(lambda n:n.tag=='section' and n.has('calendar'));changes.append((calendar.end,calendar.end,block))
    if path in ['/shows/','/shows/this-weekend/','/shows/this-month/','/new-shows/']:
        hero=next((n for n in doc.nodes if n.tag=='section' and n.has('page-hero')),None)
        if hero:
            shortcuts=[('All dates','/shows/'),('This Weekend','/shows/this-weekend/'),('This Month','/shows/this-month/'),('New Shows','/new-shows/')]
            block='<nav class="kc-location-dates" aria-label="Show calendars">'+''.join(f'<a href="{href(p)}"'+(' aria-current="page"' if p==path else '')+f'>{label}</a>' for label,p in shortcuts)+'</nav>'
            changes.append((hero.end,hero.end,block))
    # Add links only around existing visible location labels. Text and facts stay exact.
    for n in doc.nodes:
        if n.tag=='dd' or n.has('kc-teaser-location'):
            value=doc.text(n)
            if value in ctx['locations'] and not n.children:
                if not any(start<=n.start<end for start,end,_ in changes) and not any(a.start<n.start<a.end for a in doc.nodes if 'data-past-shows-archive' in a.attrs):
                    changes.append((n.opening_end,n.closing_start,f'<a class="kc-location-inline" href="{href(ctx["locations"][value])}">{text[n.opening_end:n.closing_start]}</a>'))
    text=replace_spans(text,changes)
    assets=f'<link rel="stylesheet" href="{TEST_BASE}assets/location-navigation.css?v={VERSION}"><script src="{TEST_BASE}assets/location-navigation.js?v={VERSION}" defer></script>'
    return text.replace('</head>',assets+'</head>',1).encode()

def directory(ctx,kind):
    is_city=kind=='cities';regions=sorted(ctx['regions'].values(),key=lambda r:r['name'])
    cities=[c for c in ctx['cities'].values() if c['count']]
    title='Find CHH shows by '+('city' if is_city else 'state')
    desc='Browse Christian hip hop concerts by city, grouped by state and province.' if is_city else 'Explore Christian hip hop concerts across the United States and Canada.'
    options='<option value="">All states and provinces</option>'+''.join(f'<option value="{escape(href(r["path"]))}">{escape(r["name"])}</option>' for r in regions if r['cities'])
    search=f'<div class="kc-location-filters" data-location-filters hidden><label class="kc-location-search"><span>Search {kind}</span><div>{SEARCH}<input type="search" placeholder="'+('City or state' if is_city else 'State or province')+'" data-location-search autocomplete="off"></div></label>'
    if is_city:search+=f'<label class="kc-location-region"><span>State or province</span><select data-location-region>{options}</select></label>'
    search+='<button type="button" class="kc-location-clear" data-location-clear hidden>Clear</button></div>'
    groups=''
    if is_city:
        for r in regions:
            if not r['cities']:continue
            entries=''.join(location_link(ctx['cities'][p],secondary=count_label(ctx['cities'][p]['count'])+' upcoming') for p in sorted(r['cities'],key=lambda p:ctx['cities'][p]['name']))
            groups+=f'<section class="kc-location-group" data-location-group data-region="{escape(href(r["path"]))}" data-region-name="{escape(r["name"].casefold())}"><div class="kc-location-section-heading"><h2>{escape(r["name"])}</h2><a href="{href(r["path"])}">All shows {ARROW}</a></div><div class="kc-location-city-grid">{entries}</div></section>'
    else:
        groups='<div class="kc-location-state-grid" data-location-group>'+''.join(location_link(r) for r in regions)+'</div>'
    total=len(cities) if is_city else len(regions)
    label='cities with upcoming public shows' if is_city else 'states and provinces'
    body=f'<main id="kc-main-content" class="kc-location-directory" data-location-directory data-location-kind="{kind}"><div class="kc-location-breadcrumb"><a href="{TEST_BASE}">Home</a><span aria-hidden="true">/</span><span>{kind.title()}</span></div><header class="kc-location-hero"><h1>{title}</h1><p>{desc}</p></header><nav class="kc-location-switch" aria-label="Location directories"><a href="{href("/shows/states/")}"'+(' aria-current="page"' if not is_city else '')+'>States</a><a href="'+href('/shows/cities/')+'"'+(' aria-current="page"' if is_city else '')+f'>Cities</a></nav>{search}<p class="kc-location-result-count" role="status" aria-live="polite" data-location-count>{total} {label}</p><div class="kc-location-groups">{groups}</div><div class="kc-location-empty" data-location-empty hidden><h2>No matching locations</h2><p>Try another name or clear your filters.</p></div><p class="kc-location-note">Counts include public upcoming shows. Confirm final details with the organizer before traveling.</p></main>'
    template=ctx['template'];doc=Document(template);main=doc.one(lambda n:n.tag=='main')
    changes=[(main.start,main.end,body)]
    url=TEST_SITE+'/shows/'+kind+'/'
    for n in doc.nodes:
        if n.tag=='title':changes.append((n.opening_end,n.closing_start,escape(title+' | Kingdom Circuit')))
        if n.tag=='link' and n.attrs.get('rel')=='canonical':changes.append((n.start,n.end,f'<link rel="canonical" href="{url}">'))
        if n.tag=='meta' and n.attrs.get('name')=='description':changes.append((n.start,n.end,f'<meta name="description" content="{desc}">'))
        if n.tag=='meta' and n.attrs.get('name') in ['twitter:title','twitter:description']:
            val=title+' | Kingdom Circuit' if n.attrs['name']=='twitter:title' else desc
            changes.append((n.start,n.end,f'<meta name="{n.attrs["name"]}" content="{escape(val,quote=True)}">'))
        if n.tag=='meta' and n.attrs.get('property') in ['og:title','og:description','og:url']:
            val={'og:title':title+' | Kingdom Circuit','og:description':desc,'og:url':url}[n.attrs['property']]
            changes.append((n.start,n.end,f'<meta property="{n.attrs["property"]}" content="{escape(val,quote=True)}">'))
        if n.tag=='script' and n.attrs.get('type')=='application/ld+json':changes.append((n.start,n.end,''))
    page=replace_spans(template,changes)
    page=re.sub(r'<body\b[^>]*>','<body class="kc-location-directory-body">',page,count=1)
    items=cities if is_city else regions
    schema={'@context':'https://schema.org','@graph':[{'@type':'CollectionPage','name':title,'url':url,'description':desc},{'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Home','item':TEST_SITE+'/'},{'@type':'ListItem','position':2,'name':kind.title(),'item':url}]},{'@type':'ItemList','itemListElement':[{'@type':'ListItem','position':i+1,'name':r['name'],'url':TEST_SITE+r['path']} for i,r in enumerate(sorted(items,key=lambda r:r['name']))]}]}
    page=page.replace('</head>','<script type="application/ld+json">'+json.dumps(schema).replace('<','\\u003c')+'</script></head>',1)
    return transform('shows/'+kind+'/index.html',page.encode(),ctx)

def generate(ctx):
    return {**{f'assets/location-navigation.{ext}':(ROOT/f'test-overrides/location-navigation.{ext}').read_bytes() for ext in ['css','js']},
            'assets/location-navigation-data.json':json.dumps({'locations':{k:href(v) for k,v in ctx['locations'].items()}},ensure_ascii=False).encode(),
            'shows/states/index.html':directory(ctx,'states'),'shows/cities/index.html':directory(ctx,'cities')}

def verify(live,site,ctx):
    for rel,data in ctx['generated'].items():assert (site/rel).read_bytes()==data, f'Location directory/asset drift: {rel}'
    for rel in ['index.html','shows/index.html','artists/index.html','artists/kb/index.html','about-us/index.html']:
        text=(site/rel).read_text();doc=Document(text)
        assert len([n for n in doc.nodes if n.has('kc-location-nav')])==1,rel
        assert '<meta name="robots" content="noindex,nofollow">' in text,rel
        assert 'G-N2KK9XF4TJ' not in text,rel
        assert any(n.tag=='a' and n.attrs.get('href')==href('/about-us/') for n in doc.nodes),rel
    for region in ctx['regions'].values():
        doc=Document((site/(region['path'].lstrip('/')+'index.html')).read_text())
        links={n.attrs.get('href') for n in doc.nodes if n.tag=='a'}
        assert all(href(c) in links for c in region['cities']),region['name']
    for kind in ['states','cities']:
        assert TEST_SITE+'/shows/'+kind+'/' in (site/'sitemap.xml').read_text()
        doc=Document((site/f'shows/{kind}/index.html').read_text())
        assert len([n for n in doc.nodes if n.tag=='h1'])==1
        assert not any(n.attrs.get('type')=='application/ld+json' and re.search(r'"@type":\s*"(?:MusicEvent|Event|Offer)"',doc.raw(n)) for n in doc.nodes)
    about_before=Document(test_source(live,'about-us/index.html'));about_after=Document((site/'about-us/index.html').read_text())
    assert about_before.raw(about_before.one(lambda n:n.tag=='main'))==about_after.raw(about_after.one(lambda n:n.tag=='main')),'About Us content changed'
    return {'version':VERSION,'publicShows':ctx['publicCount'],'statesAndProvinces':len(ctx['regions']),'publicCities':sum(bool(c['count']) for c in ctx['cities'].values()),'allCityCalendars':len(ctx['cities']),'aboutContentPreserved':True}

def build(site,live):
    ctx=context(live)
    for rel in FILES:assert not (live/rel).exists(),f'New preview route replaces production file: {rel}'
    sitemap=site/'sitemap.xml';sitemap.write_bytes(transform('sitemap.xml',sitemap.read_bytes(),ctx))
    for source in sorted(live.rglob('*.html')):
        rel=source.relative_to(live);target=site/rel
        if target.exists():target.write_bytes(transform(rel,target.read_bytes(),ctx))
    for rel,data in ctx['generated'].items():
        target=site/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    report=verify(live,site,ctx)
    path=site/'test-live-mirror-manifest.json';manifest=json.loads(path.read_text());manifest['locationNavigation']=report
    manifest['testOnlyDifferences'].append('States and Cities directories, compact navigation, contextual location links and nearby city browsing')
    path.write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('site',type=Path);parser.add_argument('live',type=Path);args=parser.parse_args();build(args.site,args.live)
