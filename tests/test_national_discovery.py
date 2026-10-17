from datetime import date
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import national_discovery_preview as discovery


class NationalDiscoveryTests(unittest.TestCase):
    def test_every_artwork_shape_uses_brenno_standard_frame(self):
        for width, height, shape, ratio in [
            (1092,1440,'portrait','1092 / 1440'),
            (1080,1350,'portrait','1092 / 1440'),
            (1000,1500,'portrait','1092 / 1440'),
            (1080,1920,'tall','1092 / 1440'),
            (1080,1080,'square','1092 / 1440'),
            (1280,692,'landscape','1092 / 1440'),
        ]:
            with self.subTest(shape=shape, width=width, height=height):
                self.assertEqual(discovery.artwork_layout(f'<img width="{width}" height="{height}">'), (shape,ratio))

    def test_unknown_dimensions_use_safe_uncropped_portrait_frame(self):
        for attributes in ['', 'width="0" height="100"', 'width="-30" height="20"', 'width="bad" height="100"']:
            self.assertEqual(discovery.artwork_layout(f'<img {attributes}>'), ('unknown','1092 / 1440'))

    def test_adaptive_teaser_preserves_original_image_and_all_event_facts(self):
        image = '<img src="real.webp" srcset="small.webp 320w, real.webp 1080w" width="1080" height="1920" sizes="100vw" alt="Full flyer" loading="lazy" style="object-position:center">'
        record = {'attrs':{'data-date':'2026-10-17'}, 'href':'/event/a/', 'image':image,
                  'name':'Show name', 'artists':'<p class="artist-line">Brenno</p>',
                  'badges':'<div class="event-badges">Concert</div>',
                  'meta':{'Date':'Saturday, 3:30 PM','Venue':'Music Hall','Location':'Buffalo, NY'}}
        output = discovery.teaser(record, eager=True)
        self.assertIn('data-artwork-shape="tall"',output)
        self.assertIn('style="--kc-artwork-ratio:1092 / 1440"',output)
        self.assertIn('sizes="178px"',output)
        self.assertIn('loading="eager" fetchpriority="high"',output)
        old = discovery.Document(image).one(lambda n:n.tag=='img')
        shown = discovery.Document(output).one(lambda n:n.tag=='img')
        for attr in ['src','srcset','width','height','alt','style']:
            self.assertEqual(old.attrs[attr],shown.attrs[attr])
        for value in ['Show name','Brenno','Saturday, 3:30 PM','Music Hall','Buffalo, NY','Concert']:
            self.assertIn(value,output)
        self.assertEqual(output.count('href="/event/a/"'),2)

    def test_uniform_card_styles_bound_title_and_text_without_cropping_images(self):
        css = (Path(__file__).resolve().parents[1] / 'test-overrides/fan-discovery.css').read_text()
        self.assertIn('width: 180px; height: 350px;',css)
        self.assertIn('grid-template-rows: 14px 34px 14px 14px 14px;',css)
        self.assertIn('-webkit-line-clamp: 2;',css)
        self.assertIn('text-overflow: ellipsis;',css)
        self.assertIn('object-fit: contain;',css)

    def test_unknown_flyers_and_replacement_dimensions_never_get_a_crop(self):
        for image in ['<img src="new-flyer.webp" width="800" height="800">',
                      '<img src="/assets/9aaded4384127f8719630099-w1280.webp" width="640" height="640">',
                      '<img width="0" height="800">', '<img>']:
            self.assertEqual(discovery.artwork_presentation(image), ('contain', '', 178))

    def test_only_plain_artist_photos_get_automatic_fill(self):
        self.assertEqual(discovery.artwork_presentation('<img class="artist-photo" width="1000" height="1000">'),
                         ('photo-fill', '', 235))
        self.assertEqual(discovery.artwork_presentation('<img class="event-artwork" data-artist-key="mission" width="1000" height="1000">'),
                         ('contain', '', 178))

    def test_reviewed_crop_geometry_preserves_ratio_and_entire_safe_rectangle(self):
        frame_height = 1440 / 1092
        for filename, (width, height, bounds) in discovery.ARTWORK_SAFE_BOUNDS.items():
            with self.subTest(image=filename):
                treatment, style, sizes = discovery.artwork_presentation(f'<img src="/assets/{filename}" width="{width}" height="{height}">')
                self.assertEqual(treatment, 'border-trim')
                values = {key: float(value.rstrip('%')) / 100 for key, value in (v.split(':') for v in style.split(';'))}
                w, h, x, y = (values['--kc-art-' + key] for key in ('w','h','x','y'))
                self.assertAlmostEqual(w / (h * frame_height), width / height, places=5)
                left, top, right, bottom = bounds
                self.assertGreaterEqual(x + w * left, -.00001)
                self.assertGreaterEqual(y + h * top, -.00001)
                self.assertLessEqual(x + w * right, 1.00001)
                self.assertLessEqual(y + h * bottom, 1.00001)
                self.assertGreaterEqual(sizes, w * 178 - .001)
                self.assertGreaterEqual(w, min(1, frame_height * width / height))

    def test_artwork_crop_is_preview_only_and_fallback_is_not_cropped(self):
        image = '<img src="/assets/9aaded4384127f8719630099-w1280.webp" width="1280" height="1280" style="object-position:center" sizes="100vw">'
        record = {'attrs':{'data-date':'2026-10-17'}, 'href':'/event/a/', 'image':image,
                  'name':'The Sazon Experience', 'artists':'<p class="artist-line">Giovani</p>', 'badges':'', 'meta':{}}
        output = discovery.teaser(record)
        self.assertEqual(record['image'], image)
        self.assertIn('data-artwork-treatment="border-trim"', output)
        self.assertIn('sizes="235px"', output)
        shown = discovery.Document(output).one(lambda n:n.tag == 'img')
        original = discovery.Document(image).one(lambda n:n.tag == 'img')
        for attr in ('src','width','height','style'):
            self.assertEqual(shown.attrs[attr], original.attrs[attr])
        css = (Path(__file__).resolve().parents[1] / 'test-overrides/fan-discovery.css').read_text()
        self.assertIn('[data-artwork-treatment="border-trim"] img:not([data-kc-fallback-used])',css)

    def test_card_formats_gallery_uses_same_teasers_as_home(self):
        records = [{'attrs':{'data-date':'2026-10-17'},'href':f'/event/{shape}/','name':shape,
                    'image':f'<img src="{shape}.webp" width="{w}" height="{h}">',
                    'artists':'<p class="artist-line">Artist</p>','badges':'Concert','meta':{'Venue':'Music Hall'}}
                   for shape,w,h in [('portrait',800,1000),('tall',600,1100),('square',1000,1000),('landscape',1600,900)]]
        page = discovery.card_sample_page(Path('/no-live-files'), {'records':records,'active':records}).decode()
        for record in records:
            self.assertIn(discovery.teaser(record),page)
        self.assertIn('noindex,nofollow',page)
        self.assertNotIn('Other homepage show cards have not been resized',page)

    def test_week_shelf_is_not_capped_at_six_and_next_remains_limited(self):
        def record(i, day):
            return {'name':f'Show {i}', 'href':str(i), 'attrs':{'data-date':day}, 'meta':{'Venue':'Hall'}, 'badges':'Concert'}
        records = [record(i, '2026-10-17') for i in range(15)] + [record(i+15, '2026-10-23') for i in range(10)]
        week, following = discovery.home_selection({'as_of':date(2026,10,17), 'active':records})
        self.assertEqual(len(week), 15)
        self.assertEqual(len(following), 6)

    def test_neighbors_are_actual_border_states_with_inventory(self):
        states = [{'name':name, 'count':count} for name,count in [('Kansas',0),('Colorado',2),('Missouri',4),('Oklahoma',0),('Florida',15)]]
        self.assertEqual([s['name'] for s in discovery.neighbor_states(states[0],states)], ['Missouri','Colorado'])
        self.assertEqual(discovery.neighbor_states({'name':'Puerto Rico'}, states), [])
        for state, neighbors in discovery.STATE_NEIGHBORS.items():
            for neighbor in filter(None,neighbors.split('|')):
                self.assertIn(state, discovery.STATE_NEIGHBORS[neighbor].split('|'))

    def test_artist_details_add_exact_full_cards_below_untouched_summary(self):
        card = '<article data-event-card>Full flyer, date, location and official link</article>'
        schedule = '<section class="kc-rd-profile-shows"><a class="kc-rd-show-row" href="/event/a/">Compact summary</a></section>'
        source = '<article data-kc-rd-artist-profile>' + schedule + '<section class="past-shows-archive">Past history</section></article>'
        output = discovery.artist_details(source, {'records':[{'href':'/event/a/','html':card}]})
        self.assertIn(schedule, output)
        self.assertLess(output.index(schedule),output.index(card))
        self.assertLess(output.index(card),output.index('Past history'))
        self.assertEqual(output.count('data-artist-show-details'),1)
        with self.assertRaises(AssertionError):
            discovery.artist_details(source, {'records':[]})

    def test_no_empty_artist_detail_filler(self):
        source = '<article data-kc-rd-artist-profile><section class="kc-rd-profile-shows">No shows yet</section></article>'
        self.assertEqual(discovery.artist_details(source,{'records':[]}), source)

    def test_normal_listing_has_no_retired_view_toggle(self):
        text = discovery.mobile.add_calendar_tools('<div class="event-grid"></div>',[])
        self.assertNotIn('Quick list',text)
        self.assertNotIn('data-show-view',text)
        self.assertIn('data-selected-state',text)

    def test_published_minified_card_metadata_keeps_adjacent_dd(self):
        html = ('<article data-event-card data-date="2026-10-16"><img src="photo.webp">'
                '<h3><a href="/event/test/">Test &amp; Show</a></h3><p class="artist-line">Artist</p>'
                '<div class="event-badges">Sold out</div><dl><dt>Date</dt><dd>Friday</dd>'
                '<dt>Venue</dt><dd>Hall</dd><dt>Location</dt><dd>Dallas, TX</dd></dl></article>')
        record = discovery.card_records(html)[0]
        self.assertEqual(record['meta'], {'Date':'Friday', 'Venue':'Hall', 'Location':'Dallas, TX'})
        self.assertEqual(record['name'], 'Test & Show')

    def test_weekend_includes_friday_through_sunday(self):
        expected = (date(2026, 10, 16), date(2026, 10, 18))
        for day in range(12, 19):
            self.assertEqual(discovery.weekend_window(date(2026, 10, day)), expected)
        self.assertEqual(discovery.weekend_window(date(2026, 10, 19)), (date(2026, 10, 23), date(2026, 10, 25)))

    def test_year_boundary_and_explicit_labels(self):
        self.assertEqual(discovery.weekend_window(date(2027, 1, 1)), (date(2027, 1, 1), date(2027, 1, 3)))
        self.assertEqual(discovery.date_label(date(2027, 12, 31), date(2028, 1, 2)), 'Dec 31, 2027 – Jan 2, 2028')
        self.assertEqual(discovery.date_label(date(2026, 10, 30), date(2026, 11, 1)), 'Oct 30 – Nov 1, 2026')

    def test_weekend_overlap_not_start_date_only(self):
        saturday = date(2026, 10, 17)
        self.assertTrue(discovery.weekend_matches('2026-10-15', '2026-10-18', saturday))
        self.assertFalse(discovery.weekend_matches('2026-10-16', '2026-10-16', saturday))
        self.assertFalse(discovery.weekend_matches('2026-10-19', None, saturday))
        self.assertTrue(discovery.weekend_matches('2026-10-18', None, saturday))

    def test_invalid_dates_fail_build_instead_of_inventing_a_date(self):
        with self.assertRaises(ValueError):
            discovery.weekend_matches('not-a-date', '', date(2026, 10, 13))

    def test_private_school_and_cancelled_shows_are_not_home_features(self):
        record = {'name':'Concert', 'meta':{'Venue':'Music Hall'}, 'badges':'Concert'}
        self.assertTrue(discovery.feature_eligible(record))
        for label in ['Invite Only', 'School', 'Cancelled', 'Sold out', 'Details pending', 'Venue to be announced']:
            self.assertFalse(discovery.feature_eligible({**record, 'name':label}))

    def test_new_sitemap_entry_keeps_all_existing_urls_and_has_no_fake_lastmod(self):
        old = b'<urlset><url><loc>original</loc></url></urlset>'
        new = discovery.transform(Path('sitemap.xml'), old, {})
        self.assertIn(b'<loc>original</loc>', new)
        self.assertIn(b'/shows/this-weekend/', new)
        self.assertIn(b'/about-us/', new)
        self.assertNotIn(b'lastmod', new)
        with self.assertRaises(AssertionError):
            discovery.transform(Path('sitemap.xml'), new, {})

    def test_data_images_and_isolated_experiments_are_not_changed(self):
        for path in ['events.json','config/artists.json','assets/image.webp','test-all-shows/index.html']:
            self.assertEqual(discovery.transform(Path(path), b'unchanged', {}), b'unchanged')

    def test_home_uses_requested_single_heading_and_moves_mission_to_about(self):
        source = ('<main><h1>Find shows</h1><p class="mission-statement">Our existing mission.</p></main>'
                  '<script src="/kingdom-circuit-test/app.js?v=old" defer></script>')
        context = {'states': [], 'as_of': date(2026, 10, 13), 'weekend': [], 'active': [],
                   'recent': [], 'artists': [], 'artist_total': 361}
        home = discovery.home_content(source, context)
        self.assertIn('<h1 class="kc-rd-home-title">Find CHH Shows Near You!</h1>', home)
        self.assertNotIn('CHH Live and Connected', home)
        self.assertIn('<div class="kc-discovery-intro"><h1', home)
        self.assertIn('<p class="kc-discovery-deck">CHH concerts, christian rap shows and festivals!</p>', home)
        self.assertNotIn('across the U.S.', home)
        self.assertNotIn('mission-statement', home)
        self.assertNotIn('Why we exist', home)
        self.assertIn('361</strong> artists', home)
        self.assertIn('Browse all 0 shows', home)
        self.assertIn('data-discovery-empty>', home)
        self.assertNotIn('Artists with upcoming shows', home)
        self.assertNotIn('/app.js', home)
        self.assertIn('/seo-static.js', home)
        self.assertIn('name="q"', home)
        self.assertIn('Search shows by artist, city, venue or show name</label>', home)
        self.assertNotIn('kc-discovery-when', home)
        self.assertNotIn('kc-find-artist', home)
        self.assertIn('aria-label="Browse shows by state"', home)

    def test_compact_home_keeps_finder_before_shows_and_state_directory_after_shelves(self):
        source = '<main><h1>Old home</h1></main>'
        context = {'states': [], 'as_of': date(2026, 10, 13), 'weekend': [], 'active': [],
                   'recent': [], 'artists': [], 'artist_total': 361}
        doc = discovery.Document(discovery.home_content(source, context))
        calendar = doc.one(lambda n: n.attrs.get('id') == 'calendar')
        self.assertLess(doc.one(lambda n: n.has('kc-discovery-search')).end, calendar.start)
        self.assertGreater(doc.one(lambda n: n.attrs.get('id') == 'browse-states').start, calendar.end)
        counts = doc.one(lambda n: n.has('kc-discovery-counts'))
        self.assertEqual([n.attrs['href'] for n in counts.children if n.tag == 'a'],
                         [discovery.TEST_BASE + 'shows/', discovery.TEST_BASE + 'artists/'])
        search = doc.one(lambda n: n.has('kc-discovery-search'))
        self.assertEqual(search.attrs['action'], discovery.TEST_BASE + 'shows/')
        self.assertEqual(search.attrs['method'], 'get')

    def test_week_shelves_are_date_driven_nonoverlapping_and_skip_postponed(self):
        def card(day, title='Show'):
            return {'name':title, 'href':day, 'attrs':{'data-date':day}, 'meta':{'Venue':'Hall'}, 'badges':'Concert'}
        items = [card('2026-10-19'), card('2026-10-18'), card('2026-10-16','Postponed show'), card('2026-10-15')]
        week, upcoming = discovery.home_selection({'as_of':date(2026,10,15),'active':items})
        self.assertEqual([r['href'] for r in week], ['2026-10-15','2026-10-18'])
        self.assertEqual([r['href'] for r in upcoming], ['2026-10-19'])
        self.assertEqual(discovery.week_end(date(2026,12,31)), date(2027,1,3))

    def test_about_transfers_exact_mission_and_has_its_own_identity(self):
        source = ('<head><title>Original home</title><meta name="robots" content="noindex,nofollow">'
                  '<meta name="description" content="Old"><meta property="og:url" content="old">'
                  '<link rel="canonical" href="old"><script type="application/ld+json">{}</script></head>'
                  '<main id="kc-main-content"><h1>Old home</h1>'
                  '<p class="mission-statement">Connect music &amp; community.</p></main>'
                  '<script src="/kingdom-circuit-test/app.js?v=old" defer></script>')
        about = discovery.about_content(source)
        self.assertIn('<p class="mission-statement">Connect music &amp; community.</p>', about)
        self.assertIn('<h1 id="kc-about-title">About Us</h1>', about)
        self.assertIn('<h2>Why we exist</h2>', about)
        self.assertIn('<title>About Us | Kingdom Circuit</title>', about)
        self.assertIn('"@type": "AboutPage"', about)
        self.assertIn(f'<link rel="canonical" href="{discovery.TEST_SITE}/about-us/">', about)
        self.assertIn('content="noindex,nofollow"', about)
        self.assertNotIn('/app.js', about)
        self.assertIn('/seo-static.js', about)

    def test_eight_navigation_links_and_correct_active_new_pages(self):
        labels = [('Home',''), ('All Shows','shows/'), ('This Month','shows/this-month/'),
                  ('Festivals','festivals/'), ('New Shows','new-shows/'), ('Artists','artists/')]
        links = ''.join(f'<a href="{discovery.TEST_BASE}{path}"' + (' aria-current="page"' if not path else '') + f'>{label}</a>' for label, path in labels)
        source = f'<nav class="kc-rd-nav">{links}</nav><div class="footer-links"></div>'
        for relative, expected in [('index.html', discovery.TEST_BASE),
                                   (discovery.ABOUT_PATH, discovery.ABOUT_HREF),
                                   (discovery.WEEKEND_PATH, discovery.WEEKEND_HREF)]:
            doc = discovery.Document(discovery.add_shared_navigation(source, relative))
            nav = doc.one(lambda n: n.has('kc-rd-nav'))
            self.assertEqual([doc.text(n) for n in nav.children],
                             ['Home','All Shows','This Weekend','This Month','Festivals','New Shows','Artists','About Us'])
            self.assertEqual([n.attrs['href'] for n in nav.children if n.attrs.get('aria-current') == 'page'], [expected])
            for label, path in labels:
                self.assertIn(discovery.TEST_BASE + path, [n.attrs['href'] for n in nav.children])

    def test_changed_upstream_navigation_fails_closed(self):
        with self.assertRaises(AssertionError):
            discovery.add_shared_navigation('<nav class="kc-rd-nav"><a href="/">Home</a></nav>', 'index.html')

    def test_artist_tile_preserves_real_image_and_focal_point_without_duplicate_name(self):
        tile = discovery.artist_tile({'name':'Artist & Co', 'href':'/artists/a/', 'count':2,
            'image':'<img src="real.webp" srcset="real-320.webp 320w" alt="Artist &amp; Co" sizes="100vw" style="object-position:50% 25%">'})
        self.assertIn('src="real.webp"', tile)
        self.assertIn('srcset="real-320.webp 320w"', tile)
        self.assertIn('object-position:50% 25%', tile)
        self.assertIn('alt=""', tile)
        self.assertIn('<strong>Artist &amp; Co</strong>', tile)
        self.assertIn('2 upcoming shows', tile)

    def test_pipeline_runs_national_before_final_artifact_verification(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / '.github/workflows/mirror-live.yml').read_text()
        self.assertLess(workflow.index('python scripts/mobile_seo_preview.py _site'), workflow.index('python scripts/national_discovery_preview.py _site'))
        self.assertLess(workflow.index('python scripts/national_discovery_preview.py _site'), workflow.index('python scripts/verify_live_baseline.py _live_site'))


if __name__ == '__main__':
    unittest.main()
