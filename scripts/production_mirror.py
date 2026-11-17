"""Detect a complete native location release before skipping retired previews."""
import argparse
import json
import os
from pathlib import Path

REQUIRED = ('shows/states/index.html', 'shows/cities/index.html',
            'assets/location-navigation.css', 'assets/location-navigation.js',
            'assets/location-navigation-data.json')

def promoted(live):
    present = [(live / p).is_file() for p in REQUIRED]
    if not any(present):return False
    if not all(present):raise ValueError('Incomplete production location release')
    for path in ('index.html','shows/index.html','shows/states/index.html','shows/cities/index.html'):
        text=(live/path).read_text()
        if 'data-location-navigation-version=' not in text or 'kc-location-nav' not in text:
            raise ValueError('Incomplete native navigation on '+path)
    data=json.loads((live/'assets/location-navigation-data.json').read_text())
    if not data.get('locations'):raise ValueError('Production location mappings are empty')
    for path in data['locations'].values():
        if not path.startswith('/shows/') or not path.endswith('/') or '..' in path or not (live/path.lstrip('/')/'index.html').is_file():
            raise ValueError('Invalid published location target '+path)
    return True

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('live',type=Path);p.add_argument('--github-output',action='store_true');args=p.parse_args()
    value=promoted(args.live)
    if args.github_output:
        with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('promoted='+str(value).lower()+'\n')
    print(json.dumps({'nativeProductionStructure':value}))
