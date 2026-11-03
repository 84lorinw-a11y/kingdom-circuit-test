"""Add verified event information to TEST using a single normalized record.

This final, deterministic overlay consumes the exact live public catalogs, not a
second discovery scan. The independent baseline gate replays it from live input.
Source JSON, URLs, archives, original media and artist verification remain intact.
Reviewed artwork adds local files and replaces only the matched event's rendered
image, social metadata and schema references.
Curated additions have provenance and apply only to an exact ID/date. This module
and show_information_model are the promotion boundary for a future native build;
no test environment identity code belongs in a production promotion.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
from html import escape
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import urlsplit

from live_mirror_v2 import TEST_BASE, TEST_ORIGIN
from mobile_seo_preview import Document, replace_spans, test_source
from show_information_model import normalize

ROOT = Path(__file__).resolve().parents[1]
VERSION = '20261103-2'
EVENT_TYPES = {'Event', 'MusicEvent'}
ARTWORK_PREFIX = 'assets/ignite-tour/'
PENDING_STATUS = re.compile(r'\b(?:details pending|to be announced|not confirmed)\b', re.I)
MATERIAL_STATUS = re.compile(r'\b(?:private|invite[ -]?only|sold[ _-]?out|cancelled|canceled|postponed)\b', re.I)


def artwork_path(value):
    """Only explicitly named, local TEST WebPs can be artwork additions."""
    if not isinstance(value, str) or not re.fullmatch(r'assets/ignite-tour/[A-Za-z0-9][A-Za-z0-9._-]*\.webp', value):
        raise ValueError('Artwork must use a local assets/ignite-tour/*.webp path')
    if str(PurePosixPath(value)) != value or '..' in PurePosixPath(value).parts:
        raise ValueError('Unsafe artwork path')
    return value


def artwork_definition(record):
    """Validate {src,width,height,alt,srcset?}; srcset uses local paths and Nw."""
    value = record.get('artwork')
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError('Artwork must be an object')
    src = artwork_path(value.get('src'))
    for field in ('width', 'height'):
        if type(value.get(field)) is not int or value[field] <= 0:
            raise ValueError('Artwork dimensions must be positive integers')
    if not isinstance(value.get('alt'), str) or not value['alt'].strip():
        raise ValueError('Artwork needs factual alt text')
    variants = []
    if value.get('srcset'):
        if not isinstance(value['srcset'], str):
            raise ValueError('Artwork srcset must be a string')
        for item in value['srcset'].split(','):
            match = re.fullmatch(r'\s*(\S+)\s+([1-9]\d*)w\s*', item)
            if not match:
                raise ValueError('Invalid artwork srcset candidate')
            variants.append((artwork_path(match[1]), int(match[2])))
        if len({width for _, width in variants}) != len(variants):
            raise ValueError('Duplicate artwork srcset width')
    return {'src': src, 'width': value['width'], 'height': value['height'],
            'alt': value['alt'].strip(), 'variants': variants}


def artwork_files():
    overrides = json.loads((ROOT / 'test-overrides/show-information-overrides.json').read_text())
    files = set()
    for record in overrides.values():
        artwork = artwork_definition(record)
        if artwork:
            files.add(artwork['src'])
            files.update(path for path, _ in artwork['variants'])
    return frozenset(files)


# The exact baseline gate enumerates these additions and independently replays
# transform(). New artwork never replaces a captured production asset.
FILES = frozenset({'assets/show-information.css'}) | artwork_files()


def artwork_source(relative):
    relative = artwork_path(relative)
    anchor = (ROOT / 'test-overrides').resolve()
    directory = ROOT / 'test-overrides' / ARTWORK_PREFIX
    source = ROOT / 'test-overrides' / relative
    if (directory.is_symlink() or not directory.resolve().is_relative_to(anchor) or source.is_symlink()
            or not source.resolve().is_relative_to(directory.resolve()) or not source.is_file()):
        raise ValueError(f'Missing or unsafe artwork source: {relative}')
    return source


def copy_artwork(site, live):
    for relative in artwork_files():
        if (live / relative).exists():
            raise ValueError(f'Artwork addition collides with captured production: {relative}')
        source = artwork_source(relative)
        target = site / relative
        if target.is_symlink() or not target.resolve().is_relative_to(site.resolve()):
            raise ValueError(f'Unsafe artwork output: {relative}')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def verify_artwork_files(site, live):
    files = artwork_files()
    for relative in files:
        assert not (live / relative).exists(), f'Artwork replaces production asset: {relative}'
        target = site / relative
        assert not target.is_symlink() and target.resolve().is_relative_to(site.resolve()), f'Unsafe artwork output: {relative}'
        expected = hashlib.sha256(artwork_source(relative).read_bytes()).hexdigest()
        assert target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == expected, f'Artwork bytes differ: {relative}'
    return len(files)


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
    reviewed_artwork = {}
    reviewed_bills, reviewed_notices, reviewed_descriptions = set(), set(), set()
    for identity, additions in overrides.items():
        if identity in rows and rows[identity].get('startDate') == additions['startDate']:
            rows[identity].update(additions)
            if additions.get('artwork') is not None:
                artwork_definition(additions)
                reviewed_artwork[identity] = additions['artwork']
            if additions.get('detailsPending') is False:
                rows[identity]['_refreshPendingStatus'] = True
            if 'officialBill' in additions:
                reviewed_bills.add(identity)
            if 'publicNotice' in additions:
                reviewed_notices.add(identity)
            if isinstance(additions.get('publicDescription'), str) and additions['publicDescription'].strip():
                reviewed_descriptions.add(identity)
    by_key, by_hash, by_path = {}, {}, {}
    for identity, row in rows.items():
        record = normalize(row)
        # The TEST-only artwork contract is activated by an exact reviewed
        # override, never by an unrelated source field with the same name.
        record.pop('artwork', None)
        if identity in reviewed_artwork:
            record['artwork'] = deepcopy(reviewed_artwork[identity])
        # Source catalogs already contain these public fields. Only an explicit
        # reviewed key for this occurrence authorizes changing the rendered copy.
        record.pop('_refreshOfficialBill', None)
        record.pop('_refreshPublicNotice', None)
        record.pop('_refreshPublicDescription', None)
        if identity in reviewed_bills:
            record['_refreshOfficialBill'] = True
            official_bill(record)
        if identity in reviewed_notices:
            record['_refreshPublicNotice'] = True
            public_notice(record)
        if identity in reviewed_descriptions:
            record['_refreshPublicDescription'] = True
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
            candidate['displayStatus'] = display_status(candidate, current_status)
            pages[rel] = candidate
    return {'pages': pages, 'paths': {TEST_BASE + rel.removesuffix('index.html'): r for rel, r in pages.items()}}


def display_status(record, existing):
    if record.get('private'):
        return 'Private Event — not open to the public'
    closed = {'cancelled': 'Cancelled', 'canceled': 'Cancelled', 'postponed': 'Postponed'}
    if norm(record.get('status')) in closed:
        expected = closed[norm(record['status'])]
        matching = r'\b(?:cancelled|canceled)\b' if expected == 'Cancelled' else r'\bpostponed\b'
        return existing if re.search(matching, existing, re.I) else expected
    if record.get('soldOut'):
        return 'Sold out'
    if MATERIAL_STATUS.search(existing):
        return existing
    if record.get('_refreshPendingStatus') and PENDING_STATUS.search(existing):
        return 'Scheduled'
    return existing


def billing_key(value):
    """Match complete decoded names without group/member or substring aliases."""
    return ' '.join(norm(value).translate(str.maketrans({'’': "'", '‘': "'", 'ʼ': "'"})).split())


def official_bill(record):
    """The reviewed ordered bill is independent of artist membership/indexing."""
    if not record.get('_refreshOfficialBill'):
        return None
    bill = record.get('officialBill')
    if not isinstance(bill, list) or any(not isinstance(name, str) or not name.strip() for name in bill):
        raise ValueError('Official bill must be an ordered array of nonempty names')
    if len({billing_key(name) for name in bill}) != len(bill):
        raise ValueError('Official bill contains duplicate names')
    return [name.strip() for name in bill]


def public_notice(record):
    """An explicit empty notice removes obsolete public copy."""
    if not record.get('_refreshPublicNotice'):
        return None
    notice = record.get('publicNotice')
    if not isinstance(notice, str):
        raise ValueError('Public notice must be a plain string; use an empty string to remove it')
    return notice.strip()


def billing_notice_transform(text, record, *, detail=False):
    bill, notice = official_bill(record), public_notice(record)
    if bill is None and notice is None:
        return text
    doc = Document(text)
    scope = doc.one(lambda n: n.has('event-detail-copy')) if detail else None
    nodes = [n for n in doc.nodes if not scope or scope.start < n.start < scope.end]
    changes = []
    if bill is not None:
        for line in (n for n in nodes if n.has('artist-line')):
            links = {billing_key(doc.text(n)): n for n in nodes
                     if n.tag == 'a' and line.start < n.start < line.end and n.attrs.get('href')}
            rendered = []
            for name in bill:
                link = links.get(billing_key(name))
                rendered.append(text[link.start:link.opening_end] + escape(name) + text[link.closing_start:link.end]
                                if link else '<span>' + escape(name) + '</span>')
            if rendered:
                changes.append((line.opening_end, line.closing_start, ' - '.join(rendered)))
            else:
                changes.append((line.start, line.end, ''))
    if notice is not None:
        notices = [n for n in nodes if 'data-kc-event-notice' in n.attrs]
        for index, node in enumerate(notices):
            if notice and index == 0:
                changes.append((node.opening_end, node.closing_start, escape(notice)))
            else:
                changes.append((node.start, node.end, ''))
        if notice and not notices and detail:
            # Keep compact cards compact; their existing notice slots are still
            # refreshed when present. A new notice belongs beside detail facts.
            position = next(n.start for n in scope.children if n.has('detail-list'))
            changes.append((position, position, '<p data-kc-event-notice>' + escape(notice) + '</p>'))
    return replace_spans(text, changes)


def address_html(record):
    locality = ', '.join(str(record.get(k) or '').strip() for k in ('city', 'state') if record.get(k))
    if not record.get('private') and record.get('postalCode'):
        locality += ' ' + str(record['postalCode'])
    country = {'US': 'United States', 'CA': 'Canada', 'PR': 'Puerto Rico'}.get(record.get('country'), record.get('country', ''))
    lines = ([] if record.get('private') else [record.get('address'), record.get('address2') or record.get('suite')]) + [locality, country]
    if not record.get('private') and not record.get('address'):
        lines.insert(0, 'Address not confirmed')
    return '<address class="kc-address">' + '<br> '.join(escape(str(x)) for x in lines if x) + '</address>'


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
        if source == 'doorsTimeLabel' and record.get('primaryTimeKind') == 'doors' and not record.get('startTimeLabel'):
            continue
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
        bill = official_bill(record)
        if bill is not None:
            existing = value.get('performer') or []
            if isinstance(existing, dict):
                existing = [existing]
            performers = {billing_key(p.get('name')): p for p in existing if isinstance(p, dict) and p.get('name')}
            if bill:
                value['performer'] = [dict(deepcopy(performers.get(billing_key(name), {'@type': 'Person'})), name=name)
                                      for name in bill]
            else:
                value.pop('performer', None)
        artwork = artwork_definition(record)
        if artwork:
            value['image'] = [TEST_ORIGIN + TEST_BASE + artwork['src']]
        location = value.setdefault('location', {'@type': 'Place'})
        if record.get('venue'):
            location['name'] = record['venue']
        else:
            location.pop('name', None)
        address = location.setdefault('address', {'@type': 'PostalAddress'})
        for source, target in (('address', 'streetAddress'), ('city', 'addressLocality'), ('state', 'addressRegion'), ('postalCode', 'postalCode'), ('country', 'addressCountry')):
            if record.get(source):
                address[target] = record[source]
            elif source in {'address', 'postalCode'}:
                address.pop(target, None)
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
    text = artwork_transform(text, record, detail=True)
    text = billing_notice_transform(text, record, detail=True)
    doc = Document(text)
    copy = doc.one(lambda n: n.has('event-detail-copy'))
    lists = [n for n in copy.children if n.has('detail-list')]
    if len(lists) != 1:
        raise ValueError('Expected one main Status/Date/Venue/Location list')
    details = lists[0]
    changes = []
    original_date = ''
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
            original_date = doc.text(value)
            replacement = escape(record['dateLabel'])
            if not record.get('startTimeLabel'):
                replacement += '<br> <span class="kc-unconfirmed">Start time not confirmed</span>'
        elif (label == 'Time' and record.get('_refreshPendingStatus') and record.get('startTimeLabel')
              and norm(doc.text(value)) in {'pending', 'tbd', 'tba', 'not confirmed', 'to be announced', 'time not confirmed'}):
            # The confirmed Date row now carries the clock time. Remove only a
            # stale unknown-time row from this exact reviewed occurrence.
            changes.append((row.start, row.end, ''))
        elif label == 'Venue':
            replacement = escape(record['venueLabel'])
        elif label == 'Status' and record.get('private'):
            replacement = escape(record.get('displayStatus') or 'Private Event — not open to the public')
        elif label == 'Status' and record.get('soldOut') and norm(record.get('status')) not in {'cancelled', 'canceled', 'postponed'}:
            replacement = 'Sold out'
        elif label == 'Status' and record.get('_refreshPendingStatus'):
            replacement = escape(display_status(record, doc.text(value)))
        elif label == 'Age restriction':
            # One visible admission line by the main action avoids a duplicate row.
            changes.append((row.start, row.end, ''))
        if replacement is not None:
            changes.append((value.opening_end, value.closing_start, replacement))
    # An exact reviewed public description also replaces stale search/sharing
    # claims. Other records retain source copy with generated date updates only.
    date_changed = original_date and original_date != record.get('dateLabel')
    if date_changed or record.get('_refreshPublicDescription'):
        for n in doc.nodes:
            meta = n.attrs.get('name') or n.attrs.get('property')
            is_title = n.tag == 'title' or (n.tag == 'meta' and meta in {'og:title', 'twitter:title'})
            is_description = n.tag == 'meta' and meta in {'description', 'og:description', 'twitter:description'}
            if not (is_title or is_description):
                continue
            old = doc.text(n) if n.tag == 'title' else n.attrs.get('content', '')
            if is_description and record.get('_refreshPublicDescription'):
                new = record['description']
            elif date_changed:
                pattern = (r'( — )' + re.escape(original_date) + r'(?= \|)' if is_title else
                           r'(\bon )' + re.escape(original_date) + r'(?=[.!]|$)')
                new = re.sub(pattern, lambda m: m[1] + record['dateLabel'], old)
            else:
                continue
            if new != old:
                if n.tag == 'title':
                    changes.append((n.opening_end, n.closing_start, escape(new)))
                else:
                    changes.append((n.start, n.opening_end, attributes(doc.raw(n), {'content': new})))
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


def attributes(opening, values):
    """Replace selected attributes without reserializing unrelated markup."""
    for name, value in values.items():
        pattern = r'(?<![\w:-])' + re.escape(name) + r'\s*=\s*(?:"[^"]*"|\'[^\']*\')'
        if value is None:
            opening = re.sub(r'\s+' + pattern, '', opening)
            continue
        attribute = name + '="' + escape(str(value), quote=True) + '"'
        if re.search(pattern, opening):
            opening = re.sub(pattern, lambda m: attribute, opening, count=1)
        else:
            opening = re.sub(r'\s*/?>$', lambda m: ' ' + attribute + m[0], opening, count=1)
    return opening


def artwork_transform(text, record, *, detail=False):
    """Replace one matched event's artwork; never substitute by shared filename."""
    artwork = artwork_definition(record)
    if not artwork:
        return text
    doc = Document(text)
    media = [n for n in doc.nodes if n.has('event-detail-media')] if detail else []
    changes = []
    src = TEST_BASE + artwork['src']
    srcset = ', '.join(f'{TEST_BASE}{path} {width}w' for path, width in artwork['variants']) or None
    for n in doc.nodes:
        if n.tag == 'img' and ((detail and any(m.start < n.start < m.end for m in media)) or
                               (not detail and (n.has('event-artwork') or n.has('artist-photo')))):
            classes = [name for name in n.attrs.get('class', '').split() if name != 'artist-photo']
            if 'event-artwork' not in classes:
                classes.append('event-artwork')
            style = re.sub(r'(?:^|;)\s*object-(?:position|fit)\s*:[^;]*', '', n.attrs.get('style', '')).strip('; ')
            style = (style + ';' if style else '') + 'object-fit:contain;object-position:center'
            opening = attributes(text[n.start:n.opening_end], {
                'src': src, 'srcset': srcset, 'width': artwork['width'], 'height': artwork['height'],
                'alt': artwork['alt'], 'class': ' '.join(classes), 'style': style,
            })
            changes.append((n.start, n.opening_end, opening))
        elif n.tag == 'a' and n.has('event-image-enlarge') and detail:
            changes.append((n.start, n.opening_end, attributes(text[n.start:n.opening_end], {'href': src})))
        elif n.has('kc-teaser-image'):
            # A previous poster may have a reviewed crop. New showcards always
            # use their complete frame and never inherit that crop geometry.
            changes.append((n.start, n.opening_end, attributes(text[n.start:n.opening_end], {
                'data-artwork-treatment': 'contain', 'style': '',
            })))
        elif n.has('kc-discovery-show'):
            ratio = artwork['width'] / artwork['height']
            shape = 'tall' if ratio < .65 else 'portrait' if ratio < .9 else 'square' if ratio <= 1.1 else 'landscape'
            changes.append((n.start, n.opening_end, attributes(text[n.start:n.opening_end], {'data-artwork-shape': shape})))
        elif detail and n.tag == 'meta':
            identity = n.attrs.get('property') or n.attrs.get('name')
            values = {'og:image': TEST_ORIGIN + src, 'og:image:secure_url': TEST_ORIGIN + src,
                      'twitter:image': TEST_ORIGIN + src, 'og:image:alt': artwork['alt'],
                      'twitter:image:alt': artwork['alt'], 'og:image:width': str(artwork['width']),
                      'og:image:height': str(artwork['height']), 'og:image:type': 'image/webp'}
            if identity in values:
                changes.append((n.start, n.opening_end, attributes(text[n.start:n.opening_end], {'content': values[identity]})))
    return replace_spans(text, changes)


def listing_facts(raw, record):
    """Refresh the existing compact fact slots and their accessible labels."""
    doc = Document(raw)
    root = doc.nodes[0]
    changes = []
    for n in doc.nodes:
        replacement = None
        if n.tag == 'dd':
            # Calendar facts are explicit dt/dd siblings, not title text.
            row = next((row for row in doc.nodes if n in row.children), None)
            labels = [child for child in row.children if child.tag == 'dt'] if row else []
            label = doc.text(labels[0]) if labels else ''
            replacement = record.get({'Date': 'dateLabel', 'Venue': 'venueLabel'}.get(label, ''))
        elif n.has('kc-teaser-date'):
            replacement = record.get('dateLabel')
        elif n.has('kc-teaser-venue'):
            replacement = record.get('venueLabel')
        elif n.has('kc-rd-show-venue') or n.has('kc-rd-next-venue'):
            venue = record.get('venueLabel')
            if venue:
                time_label = record.get('startTimeLabel')
                if not time_label and record.get('primaryTimeKind') == 'doors' and record.get('doorsTimeLabel'):
                    time_label = 'Doors ' + record['doorsTimeLabel']
                replacement = ' · '.join(x for x in (venue, time_label) if x)
        elif (record.get('_refreshPendingStatus') and (n.has('kc-rd-event-status') or n.has('badge'))
              and (PENDING_STATUS.search(doc.text(n)) or (n.has('kc-rd-event-status') and norm(doc.text(n)) == 'scheduled'))):
            replacement = display_status(record, doc.text(n))
            if n.has('kc-rd-event-status') and norm(replacement) == 'scheduled':
                # Compact artist rows carry exceptional statuses only, matching
                # finalize_artist_details.event_details on the final detail page.
                changes.append((n.start, n.end, ''))
                continue
        if replacement:
            changes.append((n.opening_end, n.closing_start, escape(replacement)))
            if 'title' in n.attrs:
                changes.append((n.start, n.opening_end, attributes(raw[n.start:n.opening_end], {'title': replacement})))
    root_attributes = {}
    if record.get('startTimeLabel') and record.get('startTime'):
        root_attributes['data-start-time'] = record['startTime']
    if root.has('kc-rd-show-row') or root.has('kc-rd-next-show'):
        title_node = next((n for n in doc.nodes if n.has('kc-rd-event-title')), None)
        title = doc.text(title_node) if title_node else record.get('title', '')
        place = ', '.join(record.get(k, '') for k in ('city', 'state') if record.get(k))
        status_node = next((n for n in doc.nodes if n.has('kc-rd-event-status')), None)
        status = doc.text(status_node) if status_node else ''
        status_label = record.get('displayStatus') or record.get('status') or ''
        if record.get('private') or record.get('soldOut'):
            status = record.get('displayStatus') or ('Private Event — not open to the public' if record.get('private') else 'Sold out')
        elif MATERIAL_STATUS.search(status_label):
            status = status_label
        elif record.get('_refreshPendingStatus') and PENDING_STATUS.search(status):
            status = display_status(record, status)
        if record.get('_refreshPendingStatus') and norm(status) == 'scheduled':
            status = ''
        # An explicit aria-label replaces all descendant text in the accessible
        # name, including the visible material status badge.
        identity = ' · '.join(x for x in (title, status) if x)
        root_attributes['aria-label'] = ', '.join(x for x in (record.get('dateLabel'), place, record.get('venueLabel')) if x) + (' | ' + identity if identity else '')
    if root_attributes:
        changes.append((root.start, root.opening_end, attributes(raw[root.start:root.opening_end], root_attributes)))
    result = replace_spans(raw, changes)
    if 'data-search' in root.attrs:
        # Search follows the corrected rendered facts. Keep billing, location
        # and title text as rendered instead of substituting inside event names.
        updated = Document(result)
        search_nodes = [n for n in updated.nodes if n.tag in {'h3', 'dd'} or n.has('artist-line')]
        search = ' '.join(updated.text(n) for n in search_nodes).casefold()
        result = attributes(result[:updated.nodes[0].opening_end], {'data-search': search}) + result[updated.nodes[0].opening_end:]
    return result


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
        raw = billing_notice_transform(artwork_transform(raw, record), record)
        raw = listing_facts(raw, record)
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
    report = {'version': VERSION, 'eventPages': len(ctx['pages']), 'detailsPanels': 0, 'ticketOffers': 0, 'privatePages': 0, 'canadianPages': 0,
              'artworkAssets': verify_artwork_files(site, live), 'artworkPages': 0}
    for rel, record in ctx['pages'].items():
        before, after = Document(test_source(live, rel)), Document((site / rel).read_text())
        expected_images = Document(artwork_transform(before.source, record, detail=True))
        for tag, expected in (('h1', before), ('img', expected_images)):
            assert [expected.raw(n) for n in expected.nodes if n.tag == tag] == [after.raw(n) for n in after.nodes if n.tag == tag], f'{rel}: {tag} drift'
        artwork = artwork_definition(record)
        if artwork:
            report['artworkPages'] += 1
            for n in after.nodes:
                if n.tag == 'a' and n.has('event-image-enlarge'):
                    assert n.attrs.get('href') == TEST_BASE + artwork['src'], f'{rel}: artwork enlarge drift'
                if n.tag == 'meta' and (n.attrs.get('property') or n.attrs.get('name')) in {'og:image', 'twitter:image'}:
                    assert n.attrs.get('content') == TEST_ORIGIN + TEST_BASE + artwork['src'], f'{rel}: artwork social drift'
        for name in ('canonical',):
            assert [n.attrs for n in before.nodes if n.attrs.get('rel') == name] == [n.attrs for n in after.nodes if n.attrs.get('rel') == name], f'{rel}: URL drift'
        if record.get('_refreshPublicDescription'):
            for n in after.nodes:
                if n.tag == 'meta' and (n.attrs.get('name') or n.attrs.get('property')) in {'description', 'og:description', 'twitter:description'}:
                    assert n.attrs.get('content') == record['description'], f'{rel}: reviewed description metadata drift'
        main = after.one(lambda n: n.has('event-detail-copy'))
        bill = official_bill(record)
        if bill is not None:
            lines = [n for n in after.nodes if n.has('artist-line') and main.start < n.start < main.end]
            assert [after.text(n) for n in lines] == ([' - '.join(bill)] if bill else []), f'{rel}: reviewed billing drift'
        notice = public_notice(record)
        if notice is not None:
            notices = [n for n in after.nodes if 'data-kc-event-notice' in n.attrs and main.start < n.start < main.end]
            assert [after.text(n) for n in notices] == ([notice] if notice else []), f'{rel}: public notice drift'
        facts = next(n for n in main.children if n.has('detail-list'))
        for row in facts.children:
            labels = [n for n in row.children if n.tag == 'dt']
            values = [n for n in row.children if n.tag == 'dd']
            field = {'Date': 'dateLabel', 'Venue': 'venueLabel'}.get(after.text(labels[0])) if labels else None
            if field and record.get(field):
                expected = record[field]
                if field == 'dateLabel' and not record.get('startTimeLabel'):
                    expected += ' Start time not confirmed'
                assert len(values) == 1 and after.text(values[0]) == expected, f'{rel}: visible {field} drift'
        schemas = [s for _, v in schema_blocks(after.source) for s in event_schemas(v)]
        if record.get('private'):
            assert not schemas, f'{rel}: private event exposed in schema'
            report['privatePages'] += 1
        for schema in schemas:
            if bill is not None:
                assert [p.get('name') for p in schema.get('performer', [])] == bill, f'{rel}: performer billing drift'
            if artwork:
                assert schema.get('image') == [TEST_ORIGIN + TEST_BASE + artwork['src']], f'{rel}: artwork schema drift'
            if record.get('venue'):
                assert schema.get('location', {}).get('name') == record['venue'], f'{rel}: schema venue drift'
            else:
                assert 'name' not in schema.get('location', {}), f'{rel}: unconfirmed venue in schema'
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
    copy_artwork(site, live)
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
    manifest['testOnlyDifferences'].append('Verified show details, reviewed event artwork and matched official destinations; private events excluded from Event/Offer markup')
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('site', type=Path)
    parser.add_argument('live', type=Path)
    args = parser.parse_args()
    build(args.site, args.live)
