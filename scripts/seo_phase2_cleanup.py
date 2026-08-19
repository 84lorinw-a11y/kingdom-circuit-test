from __future__ import annotations

import pathlib
import shutil
import urllib.parse
import xml.etree.ElementTree as ET

ROOT = pathlib.Path('_site')
SITEMAP = ROOT / 'sitemap.xml'
BASE = '/kingdom-circuit-test/'


def main() -> None:
    tree = ET.fromstring(SITEMAP.read_text(encoding='utf-8'))
    ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls = [el.text.strip() for el in tree.findall('sm:url/sm:loc', ns) if el.text]

    desired_event_dirs = set()
    for url in urls:
        path = urllib.parse.urlsplit(url).path
        if path.startswith(BASE + 'event/'):
            parts = path.strip('/').split('/')
            if len(parts) >= 3:
                desired_event_dirs.add(parts[-1])

    event_root = ROOT / 'event'
    removed = []
    if event_root.exists():
        for child in event_root.iterdir():
            if child.is_dir() and child.name not in desired_event_dirs:
                removed.append(str(child.relative_to(ROOT)))
                shutil.rmtree(child)

    # Legacy state pages are superseded by /shows/<state>/ and should not be deployed.
    legacy_states = ROOT / 'states'
    if legacy_states.exists():
        removed.append('states/')
        shutil.rmtree(legacy_states)

    leftovers = []
    if event_root.exists():
        for child in event_root.iterdir():
            if not child.is_dir():
                continue
            name = child.name.lower()
            if 'sponsor-' in name or '-leander-austin-' in name or '-richmond-houston-' in name or '-southlake-dallas-' in name or '-fair-oaks-sacramento-' in name:
                leftovers.append(child.name)

    if leftovers:
        raise SystemExit('Stale/dirty event paths remain: ' + ', '.join(leftovers))
    if legacy_states.exists():
        raise SystemExit('Legacy states directory still exists')

    print(f'Removed {len(removed)} stale generated path(s).')
    for item in removed[:20]:
        print(' -', item)


if __name__ == '__main__':
    main()
