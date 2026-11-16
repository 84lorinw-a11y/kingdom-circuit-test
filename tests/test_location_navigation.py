"""Guard public counts and factual preservation at the location preview boundary."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import location_navigation_preview as location
from mobile_seo_preview import Document

class LocationNavigationTests(unittest.TestCase):
    def card(self, path, title='Concert', badge='Concert'):
        return f'<article data-event-card data-state="FL"><h3><a href="{path}">{title}</a></h3><div class="event-badges">{badge}</div><dl><div><dt>Location</dt><dd>Orlando, FL</dd></div></dl></article>'
    def test_counts_distinct_public_shows_and_preserves_sold_out(self):
        one=self.card('/event/one/')
        html=one+one+self.card('/event/private/',badge='Private Event')+self.card('/event/cancelled/',badge='Cancelled')+self.card('/event/postponed/',badge='Postponed')+self.card('/event/sold/',badge='Sold Out')
        result=location.public_cards(html)
        self.assertEqual(set(result),{'/event/one/','/event/sold/'})
        self.assertEqual(result['/event/one/']['location'],'Orlando, FL')
    def test_test_host_and_production_paths_resolve_same_identity(self):
        self.assertEqual(location.path_of('https://84lorinw-a11y.github.io/kingdom-circuit-test/shows/orlando-florida/'),'/shows/orlando-florida/')
        self.assertEqual(location.href('/shows/orlando-florida/'),'/kingdom-circuit-test/shows/orlando-florida/')
    def test_sitemap_adds_only_directory_routes_and_keeps_existing_dates(self):
        source=b'<urlset><url><loc>https://example.com/old/</loc><lastmod>2026-09-21</lastmod></url></urlset>'
        result=location.transform('sitemap.xml',source,{})
        self.assertIn(b'<lastmod>2026-09-21</lastmod>',result)
        self.assertEqual(result.count(b'<lastmod>'),1)
        self.assertEqual(result.count(b'<url>'),3)
        self.assertEqual(location.transform('sitemap.xml',result,{}),result)

    def test_directory_metadata_and_sitemap_use_the_correct_test_root(self):
        template='<html><head><title>About Us</title><meta name="robots" content="noindex,nofollow"><meta name="twitter:title" content="About Us"><link rel="canonical" href="https://example.com/about/"></head><body><header class="kc-rd-header"><div class="kc-rd-primary"></div></header><main>About content</main><footer><div class="footer-links"></div></footer></body></html>'
        ctx={'template':template,'regions':{},'cities':{},'locations':{}}
        for kind in ['states','cities']:
            page=location.directory(ctx,kind).decode();doc=Document(page)
            canonical=doc.one(lambda n:n.attrs.get('rel')=='canonical').attrs['href']
            self.assertEqual(canonical,'https://84lorinw-a11y.github.io/kingdom-circuit-test/shows/'+kind+'/')
            self.assertNotIn('content="About Us"',page)
            self.assertIn('content="noindex,nofollow"',page)

    def test_zero_count_does_not_claim_future_event(self):
        self.assertIn('No upcoming shows listed',location.location_link({'path':'/shows/florida/','name':'Florida','count':0}))
    def test_new_navigation_contains_five_links_and_current_state(self):
        doc=Document(location.nav('/shows/states/'))
        links=[n for n in doc.nodes if n.tag=='a']
        self.assertEqual([doc.text(n) for n in links],['Shows','States','Cities','Artists','Festivals'])
        self.assertEqual([doc.text(n) for n in links if n.attrs.get('aria-current')],['States'])
    def test_about_and_date_shortcuts_remain_crawlable(self):
        doc=Document(location.menu())
        names={doc.text(n) for n in doc.nodes if n.tag=='a'}
        self.assertTrue({'About Us','This Weekend','This Month','New Shows','Submit a Show'} <= names)
    def test_transform_preserves_canonical_and_original_artwork_and_archive(self):
        image='<img src="/kingdom-circuit-test/assets/original.webp" width="500" height="700">'
        archive='<section data-past-shows-archive><dd>Orlando, FL</dd></section>'
        text='<html><head><link rel="canonical" href="https://84lorinw-a11y.github.io/kingdom-circuit-test/artists/kb/"></head><body><header class="kc-rd-header"><div class="kc-rd-primary"></div></header><main>'+image+'<dd>Orlando, FL</dd>'+archive+'</main><footer><div class="footer-links"></div></footer></body></html>'
        ctx={'cities':{},'regions':{},'locations':{'Orlando, FL':'/shows/orlando-florida/'}}
        result=location.transform('artists/kb/index.html',text.encode(),ctx).decode()
        self.assertIn(image,result);self.assertIn(archive,result)
        self.assertIn('class="kc-location-inline"',result)
        self.assertIn('<link rel="canonical" href="https://84lorinw-a11y.github.io/kingdom-circuit-test/artists/kb/">',result)
        self.assertEqual(location.transform('artists/kb/index.html',result.encode(),ctx),result.encode())
if __name__=='__main__':unittest.main()
