"""Add verified event information to TEST using a single normalized record.

This final, deterministic overlay consumes the exact live public catalogs, not a
second discovery scan. The independent baseline gate replays it from live input.
Source JSON, URLs, archives, images and artist verification remain untouched.
Curated additions have provenance and apply only to an exact ID/date. This module
and show_information_model are the promotion boundary for a future native build;
no test environment identity code belongs in a production promotion.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from live_mirror_v2 import TEST_BASE
from mobile_seo_preview import Document, replace_spans, test_source
from show_information_model import normalize

ROOT = Path(__file__).resolve().parents[1]
VERSION = '20261102-1'
FILES = frozenset({'assets/show-information.css'})
EVENT_TYPES = {'Event', 'MusicEvent'}


def norm(value):
    return str(value or '').strip().casefold()


def key(row):
    return norm(row.get('title')), str(row.get('startDate') or '')[:10], norm(row.get('city'))


def digest(value):
    hashed = 0x811C9DC5
    for byte in str(value).encode():
        hashed = ((hashed ^ byte) * 0x01000193) & 0xFFFFFFFF
    return f'{hashed:08x}'[:6]


def event_schemas(value):
    if isinstance(value, list):
        for item in value:
            yield from event_schemas(item)
    elif isinstance(value, dict):
        if value.get('@type') in EVENT_TYPES:
            yield value
        for child in value.values():
            if isinstance(child, (dict, list)):
                yield from event_schemas(child)


def schema_blocks(text):
    doc = Document(text)
    return [(n, json.loads(text[n.opening_end:n.closing_start])) for n in doc.nodes
            if n.tag == 'script' and n.attrs.get('type') == 'application/ld+json']


def schema_key(schema):
    address = (schema.get('location') or {}).get('address') or {}
    return norm(schema.get('name')), str(schema.get('startDate') or '')[:10], norm(address.get('addressLocality'))


def context(live):
    rows = {}
    # The primary public catalog wins. Supplemental records fill missing fields,
    # never replace a current cancellation, corrected date or billing decision.
    for filename in ('events.json', 'supplemental-events.json'):
        for row in json.loads((live / filename).read_text()):
            identity = row.get('id') or key(row)
            if identity not in rows:
                rows[identity] = deepcopy(row)
            else:
                for name, value in row.items():
                    if name not in rows[identity] or rows[identity][name] in ('', None, []):
                        rows[identity][name] = deepcopy(value)
    overrides = json.loads((ROOT / 'test-overrides/show-information-overrides.json').read_text())
    for identity, additions in overrides.items():
        if identity in rows and rows[identity].get('startDate') == additions['startDate']:
            rows[identity].update(additions)
    by_key, by_hash, by_path = {}, {}, {}
    for row in rows.values():
        record = normalize(row)
        by_key.setdefault(key(row), record)
        if str(row.get('canonicalPath') or '').startswith('/event/'):
            by_path[row['canonicalPath'].strip('/') + '/index.html'] = record
        if row.get('id'):
            by_hash[digest(row['id'])] = record
    pages = {}
    for path in sorted((live / 'event').glob('*/index.html')):
        rel = path.relative_to(live).as_posix()
        original = path.read_text()
        # Retained redirect/alias pages stay exactly as published.
        if 'class="event-detail-copy"' not in original:
            continue
        schemas = [s for _, value in schema_blocks(original) for s in event_schemas(value)]
        candidate = by_path.get(rel) or next((by_key[schema_key(s)] for s in schemas if schema_key(s) in by_key), None)
        if not candidate:
            match = re.search(r'-([0-9a-f]{6})/index.html$', rel)
            candidate = by_hash.get(match[1]) if match else None
        if candidate:
            # A stable ID may be retained by an old redirect with outdated content;
            # never rewrite a different dated occurrence merely because IDs match.
            if schemas and str(schemas[0].get('startDate') or '')[:10] != candidate.get('startDate'):
                continue
            candidate = deepcopy(candidate)
            current_status = re.search(r'<dt>\s*Status\s*</dt>\s*<dd>(.*?)</dd>', original, re.S)
            current_status = re.sub('<[^>]+>', '', current_status[1]).strip() if current_status else ''
            candidate['displayStatus'] = ('Private Event — not open to the public' if candidate.get('private') else
                                          'Sold out' if candidate.get('soldOut') and norm(candidate.get('status')) not in {'cancelled', 'canceled', 'postponed'} else current_status)
            pages[rel] = candidate
    return {'pages': pages, 'paths': {TEST_BASE + rel.removesuffix('index.html'): r for rel, r in pages.items()}}


def address_html(record):
    locality = ', '.join(str(record.get(k) or '').strip() for k in ('city', 'state') if record.get(k))
    if not record.get('private') and record.get('postalCode'):
        locality += ' ' + str(record['postalCode'])
    country = {'US': 'United States', 'CA': 'Canada', 'PR': 'Puerto Rico'}.get(record.get('country'), record.get('country', ''))
    lines = ([] if record.get('private') else [record.get('address'), record.get('address2') or record.get('suite')]) + [locality, country]
    return '<address class="kc-address">' + '<br>'.join(escape(str(x)) for x in lines if x) + '</address>'


def more_details(record):
    facts = []
    if record.get('priceLabel') and not record.get('private'):
        facts.append(('Price', escape(record['priceLabel'])))
    if record.get('organizerName'):
        organizer = escape(record['organizerName'])
        if record.get('organizerUrl'):
            organizer = f'<a href="{escape(record["organizerUrl"], quote=True)}" target="_blank" rel="noopener noreferrer">{organizer}</a>'
        facts.append(('Organizer / promoter', organizer))
    for source, label in (('doorsTimeLabel', 'Doors'), ('registrationTimeLabel', 'Concert registration'), ('endTimeLabel', 'Ends')):
        if record.get(source):
            value = record[source]
            if source == 'registrationTimeLabel' and record.get('registrationLocation'):
                value += ' · ' + record['registrationLocation']
            facts.append((label, escape(value)))
    # These are explicit billed roles, never inferred from artist array order.
    for source, label in (('headliner', 'Headliner'), ('supportActs', 'Support'), ('hosts', 'Hosts')):
        value = record.get(source)
        if value and (source != 'headliner' or record.get('supportActs')):
            facts.append((label, escape(' · '.join(value) if isinstance(value, list) else str(value))))
    for source, label in (('accessibility', 'Accessibility'), ('parking', 'Parking'), ('entryRequirements', 'Entry'), ('refundPolicy', 'Refund policy')):
        if isinstance(record.get(source), str) and record[source].strip():
            facts.append((label, escape(record[source])))
    # Preserve existing schedule/admission facts inside the one disclosure. In
    # particular, Winter Jam's early entry and Pre-Jam are not performer start
    # times. Structured fields above replace only exact same-label facts.
    labels = {label.casefold() for label, _ in facts}
    for item in record.get('scheduleDetails') or []:
        if not isinstance(item, dict):
            continue
        label, value = str(item.get('label') or '').strip(), str(item.get('text') or '').strip()
        if label and value and label.casefold() not in labels and label.casefold() != 'address':
            facts.append((escape(label), escape(value)))
            labels.add(label.casefold())
    description = record.get('description') or ''
    if not facts and not description:
        return ''
    content = f'<p>{escape(description)}</p>' if description else ''
    if facts:
        content += '<dl class="kc-extra-facts">' + ''.join(f'<div><dt>{label}</dt><dd>{value}</dd></div>' for label, value in facts) + '</dl>'
    if record.get('scheduleNote'):
        content += '<p>' + escape(record['scheduleNote']) + '</p>'
    return '<details class="kc-more-details"><summary>More show details</summary><div class="kc-more-body">' + content + '</div></details>'


def patched_schema(value, record):
    if isinstance(value, list):
        return [v for child in value if (v := patched_schema(child, record)) is not None]
    if not isinstance(value, dict):
        return value
    value = deepcopy(value)
    if value.get('@type') in EVENT_TYPES:
        if record.get('private'):
            return None
        for source, target in (('schemaStartDate', 'startDate'), ('schemaEndDate', 'endDate'), ('description', 'description')):
            if record.get(source):
                value[target] = record[source]
            elif target == 'endDate':
                value.pop(target, None)
        if record.get('organizerName'):
            value['organizer'] = {'@type': 'Organization', 'name': record['organizerName']}
            if record.get('organizerUrl'):
                value['organizer']['url'] = record['organizerUrl']
        address = value.setdefault('location', {'@type': 'Place'}).setdefault('address', {'@type': 'PostalAddress'})
        for source, target in (('address', 'streetAddress'), ('city', 'addressLocality'), ('state', 'addressRegion'), ('postalCode', 'postalCode'), ('country', 'addressCountry')):
            if record.get(source):
                address[target] = record[source]
        if record.get('address2') or record.get('suite'):
            address['streetAddress'] = ', '.join(x for x in [record.get('address'), record.get('address2') or record.get('suite')] if x)
        value.pop('offers', None)
        if record.get('offer'):
            value['offers'] = record['offer']
        return value
    for name, child in list(value.items()):
        if isinstance(child, (dict, list)):
            replacement = patched_schema(child, record)
            if replacement is None:
                value.pop(name)
            else:
                value[name] = replacement
    return value


def detail_transform(text, record):
    doc = Document(text)
    copy = doc.one(lambda n: n.has('event-detail-copy'))
    lists = [n for n in copy.children if n.has('detail-list')]
    if len(lists) != 1:
        raise ValueError('Expected one main Status/Date/Venue/Location list')
    details = lists[0]
    changes = []
    if record.get('scheduleDetails'):
        for n in copy.children:
            if 'data-kc-event-schedule' in n.attrs:
                changes.append((n.start, n.end, ''))
    for row in details.children:
        labels = [n for n in row.children if n.tag == 'dt']
        values = [n for n in row.children if n.tag == 'dd']
        if not labels or not values:
            continue
        label, value = doc.text(labels[0]), values[0]
        replacement = None
        if label == 'Location':
            replacement = address_html(record)
        elif label == 'Date' and record.get('dateLabel'):
            replacement = escape(record['dateLabel'])
        elif label == 'Status' and record.get('private'):
            replacement = escape(record.get('displayStatus') or 'Private Event — not open to the public')
        elif label == 'Status' and record.get('soldOut') and norm(record.get('status')) not in {'cancelled', 'canceled', 'postponed'}:
            replacement = 'Sold out'
        elif label == 'Age restriction':
            # One visible admission line by the main action avoids a duplicate row.
            changes.append((row.start, row.end, ''))
        if replacement is not None:
            changes.append((value.opening_end, value.closing_start, replacement))
    primary = [n for n in doc.nodes if n.tag == 'a' and n.has('primary-button') and copy.start < n.start < copy.end and doc.text(n) == 'Official details']
    if primary and record.get('officialDestination'):
        n = primary[0]
        raw = doc.raw(n)
        raw = re.sub(r'href="[^"]*"', f'href="{escape(record["officialDestination"]["url"], quote=True)}"', raw, count=1)
        changes.append((n.start, n.end, raw))
    insertion = primary[0].end if primary else details.end
    admission = record.get('admissionLabel') or ''
    if admission:
        position = primary[0].start if primary else details.end
        changes.append((position, position, f'<p class="kc-admission-restriction">{escape(admission)}</p>'))
    changes.append((insertion, insertion, more_details(record)))
    for node, value in schema_blocks(text):
        replacement = patched_schema(value, record)
        if replacement is None or replacement == []:
            changes.append((node.start, node.end, ''))
        elif replacement != value:
            changes.append((node.opening_end, node.closing_start, json.dumps(replacement, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')))
    return replace_spans(text, changes)


def listing_transform(text, ctx):
    doc = Document(text)
    changes = []
    for node in doc.nodes:
        if not (node.has('event-card') or node.has('kc-discovery-show') or node.has('kc-rd-show-row') or node.has('kc-rd-next-show')):
            continue
        raw = doc.raw(node)
        links = re.findall(r'href="([^"]+)"', raw)
        record = next((ctx['paths'][href] for href in links if href in ctx['paths']), None)
        if not record:
            continue
        destination = record.get('officialDestination')
        if destination:
            raw = re.sub(r'(<a\b[^>]*class="[^"]*official-button[^"]*"[^>]*href=")[^"]*', lambda m: m[1] + escape(destination['url'], quote=True), raw)
        if (node.has('kc-rd-show-row') or node.has('kc-rd-next-show')) and (record.get('private') or record.get('soldOut')):
            label = escape(record.get('displayStatus') or ('Private Event — not open to the public' if record.get('private') else 'Sold out'))
            status = '<span class="kc-rd-event-status">' + label + '</span>'
            if 'class="kc-rd-event-status"' in raw:
                raw = re.sub(r'<span class="kc-rd-event-status">.*?</span>', lambda m: status, raw, flags=re.S)
            else:
                raw = re.sub(r'(<span class="kc-rd-event-title">.*?</span>)', lambda m: m[1] + status, raw, flags=re.S)
        # Titles already contain cancellation/private warnings in the live mirror.
        # Surface a missing material restriction without expanding card addresses.
        admission = record.get('admissionLabel') or ''
        already_private = record.get('private') and re.search(r'private|invite[ -]only', doc.text(node), re.I)
        if admission and norm(admission) != 'all ages' and not already_private and norm(admission) not in norm(doc.text(node)):
            label = f'<span class="kc-listing-admission">{escape(admission)}</span>'
            if node.has('kc-rd-show-row') or node.has('kc-rd-next-show'):
                raw = raw.replace('<span class="kc-rd-chevron"', label + '<span class="kc-rd-chevron"', 1)
            elif 'class="event-footer"' in raw:
                raw = raw.replace('<div class="event-footer">', '<div class="event-footer">' + label, 1)
            else:
                raw = re.sub(r'(<p class="kc-teaser-venue"[^>]*>.*?</p>)', r'\1' + label, raw, count=1, flags=re.S)
        if raw != doc.raw(node):
            changes.append((node.start, node.end, raw))
    return replace_spans(text, changes)


def transform(relative, data, ctx):
    rel = str(relative)
    if not rel.endswith('.html'):
        return data
    text = data.decode()
    if rel in ctx['pages']:
        text = detail_transform(text, ctx['pages'][rel])
    else:
        text = listing_transform(text, ctx)
    if text == data.decode():
        return data
    stylesheet = f'<link rel="stylesheet" href="{TEST_BASE}assets/show-information.css?v={VERSION}">'
    return text.replace('</head>', stylesheet + '</head>', 1).encode()


def verify(live, site, ctx):
    assert (site / 'assets/show-information.css').read_bytes() == (ROOT / 'test-overrides/show-information.css').read_bytes()
    report = {'version': VERSION, 'eventPages': len(ctx['pages']), 'detailsPanels': 0, 'ticketOffers': 0, 'privatePages': 0, 'canadianPages': 0}
    for rel, record in ctx['pages'].items():
        before, after = Document(test_source(live, rel)), Document((site / rel).read_text())
        for tag in ('h1', 'img'):
            assert [before.raw(n) for n in before.nodes if n.tag == tag] == [after.raw(n) for n in after.nodes if n.tag == tag], f'{rel}: {tag} drift'
        for name in ('canonical',):
            assert [n.attrs for n in before.nodes if n.attrs.get('rel') == name] == [n.attrs for n in after.nodes if n.attrs.get('rel') == name], f'{rel}: URL drift'
        schemas = [s for _, v in schema_blocks(after.source) for s in event_schemas(v)]
        if record.get('private'):
            assert not schemas, f'{rel}: private event exposed in schema'
            report['privatePages'] += 1
        for schema in schemas:
            assert schema.get('offers') == record.get('offer'), f'{rel}: offer drift'
            if record.get('offer'):
                url = record['offer']['url']
                buttons = [n for n in after.nodes if n.tag == 'a' and n.has('primary-button') and n.attrs.get('href') == url and after.text(n) == 'Official details']
                assert len(buttons) == 1, f'{rel}: visible ticket/Offer mismatch'
                report['ticketOffers'] += 1
            if record.get('schemaStartDate'):
                assert schema.get('startDate') == record['schemaStartDate']
        panels = [n for n in after.nodes if n.tag == 'details' and n.has('kc-more-details')]
        assert len(panels) == int(bool(more_details(record))), f'{rel}: details missing or duplicated'
        report['detailsPanels'] += bool(panels)
        report['canadianPages'] += record.get('country') == 'CA'
        assert 'Final total confirmed at checkout' not in after.source
    return report


def build(site, live):
    ctx = context(live)
    for source in live.rglob('*.html'):
        rel = source.relative_to(live)
        target = site / rel
        if target.exists():
            target.write_bytes(transform(rel, target.read_bytes(), ctx))
    (site / 'assets/show-information.css').write_bytes((ROOT / 'test-overrides/show-information.css').read_bytes())
    report = verify(live, site, ctx)
    path = site / 'test-live-mirror-manifest.json'
    manifest = json.loads(path.read_text())
    manifest['showInformation'] = report
    manifest['testOnlyDifferences'].append('Verified show details and matched official ticket destinations; private events excluded from Event/Offer markup')
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('site', type=Path)
    parser.add_argument('live', type=Path)
    args = parser.parse_args()
    build(args.site, args.live)
