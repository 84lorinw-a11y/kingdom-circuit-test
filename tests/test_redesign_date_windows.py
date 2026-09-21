from __future__ import annotations

import datetime as dt
import importlib.util
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "apply_test_redesign.py"
SPEC = importlib.util.spec_from_file_location("apply_test_redesign", MODULE_PATH)
assert SPEC and SPEC.loader
redesign = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = redesign
SPEC.loader.exec_module(redesign)


def event_card(
    *,
    title: str,
    slug: str,
    start: str,
    end: str,
    city: str,
    state: str,
    artists: str,
) -> str:
    return f'''<article class="event-card" data-event-card data-artists="{artists}" data-state="{state}" data-date="{start}" data-end-date="{end}">
  <h3><a href="/kingdom-circuit-test/event/{slug}/">{title}</a></h3>
  <dl class="event-meta">
    <div><dt>Date</dt><dd>{start}</dd></div>
    <div><dt>Venue</dt><dd>Test Venue</dd></div>
    <div><dt>Location</dt><dd>{city}, {state}</dd></div>
  </dl>
</article>'''


class TestActiveEventWindow(unittest.TestCase):
    def test_cutoff_keeps_yesterday_and_uses_multiday_end_date(self) -> None:
        today = dt.date(2026, 9, 21)
        cutoff = redesign.visibility_cutoff(today)
        self.assertEqual(cutoff, dt.date(2026, 9, 20))

        yesterday = {
            "startDate": "2026-09-18",
            "endDate": "2026-09-20",
        }
        two_days_old = {
            "startDate": "2026-09-18",
            "endDate": "2026-09-19",
        }
        self.assertTrue(redesign.is_active_event(yesterday, cutoff))
        self.assertFalse(redesign.is_active_event(two_days_old, cutoff))

        document = "<main>" + event_card(
            title="Yesterday Festival",
            slug="yesterday-festival",
            start="2026-09-18",
            end="2026-09-20",
            city="Detroit",
            state="MI",
            artists="Hulvey",
        ) + event_card(
            title="Two Days Old",
            slug="two-days-old",
            start="2026-09-18",
            end="2026-09-19",
            city="Chicago",
            state="IL",
            artists="indie tribe.",
        ) + "</main>"

        pruned = redesign.prune_expired_event_cards(document, cutoff)
        self.assertIn("Yesterday Festival", pruned)
        self.assertNotIn("Two Days Old", pruned)
        self.assertEqual(pruned.count("data-event-card"), 1)


class TestNewShowsWindow(unittest.TestCase):
    def test_recent_window_includes_ages_zero_through_six_only(self) -> None:
        today = dt.date(2026, 9, 21)

        def source_event(event_id: str, first_seen: str | None) -> dict[str, object]:
            event: dict[str, object] = {
                "id": event_id,
                "title": event_id.replace("-", " ").title(),
                "startDate": "2026-10-02",
                "city": "Detroit",
            }
            if first_seen is not None:
                event["firstSeen"] = first_seen
            return event

        included = [
            source_event("age-zero", "2026-09-21T05:00:00Z"),
            source_event("age-six", "2026-09-15T23:59:59Z"),
        ]
        excluded = [
            source_event("age-seven", "2026-09-14T00:00:00Z"),
            # Noon UTC is unambiguously the next calendar day in the site's
            # America/Los_Angeles timezone as well as in UTC.
            source_event("future-seen", "2026-09-22T12:00:00Z"),
            source_event("missing-seen", None),
        ]

        recent = redesign.recent_event_keys(included + excluded, today, days=7)
        self.assertEqual(len(recent), 2)
        for event in included:
            self.assertEqual(len(redesign.recent_event_keys([event], today, days=7)), 1)
        for event in excluded:
            self.assertEqual(len(redesign.recent_event_keys([event], today, days=7)), 0)

    def test_new_shows_transform_filters_cards_using_recent_keys(self) -> None:
        today = dt.date(2026, 9, 21)
        source_events = [
            {
                "id": "fresh-show",
                "title": "Fresh Show",
                "startDate": "2026-10-02",
                "city": "Detroit",
                "firstSeen": "2026-09-20T12:00:00Z",
            },
            {
                "id": "stale-show",
                "title": "Stale Show",
                "startDate": "2026-10-03",
                "city": "Chicago",
                "firstSeen": "2026-09-01T12:00:00Z",
            },
        ]
        recent = redesign.recent_event_keys(source_events, today, days=7)
        document = '''<html><head>
<meta name="description" content="Shows added in the last 14 days.">
</head><body><main>
<p class="hero-text">See Christian hip-hop shows added in the past 14 days.</p>
<p class="results-count" data-results-count>2 shows</p>
<div class="event-grid" data-event-grid>''' + event_card(
            title="Fresh Show",
            slug="fresh-show",
            start="2026-10-02",
            end="2026-10-02",
            city="Detroit",
            state="MI",
            artists="Hulvey",
        ) + event_card(
            title="Stale Show",
            slug="stale-show",
            start="2026-10-03",
            end="2026-10-03",
            city="Chicago",
            state="IL",
            artists="Kijan Boone",
        ) + "</div></main></body></html>"

        transformed = redesign.transform_new_shows(document, recent)
        self.assertIn("Fresh Show", transformed)
        self.assertNotIn("Stale Show", transformed)
        self.assertEqual(transformed.count("data-event-card"), 1)
        self.assertIn("7 days", transformed)
        self.assertIn(">1 show<", transformed)


class TestThisMonthSummary(unittest.TestCase):
    def test_summary_counts_shows_states_and_unique_artists(self) -> None:
        document = '''<main>
<section class="page-hero hero-compact">
  <div class="stat-row">
    <div><strong data-month-show-count>—</strong><span>Shows</span></div>
    <div><strong data-month-state-count>—</strong><span>States</span></div>
    <div><strong data-month-festival-count>—</strong><span>Festivals</span></div>
  </div>
</section>
<div class="calendar-heading"><p class="section-intro">Browse the month chronologically, or filter by artist, state, or event type.</p></div>
<div class="event-grid" data-event-grid>''' + event_card(
            title="Detroit Night",
            slug="detroit-night",
            start="2026-09-22",
            end="2026-09-22",
            city="Detroit",
            state="MI",
            artists="Hulvey|indie tribe.",
        ) + event_card(
            title="Chicago Night",
            slug="chicago-night",
            start="2026-09-23",
            end="2026-09-23",
            city="Chicago",
            state="IL",
            artists="Hulvey|Kijan Boone",
        ) + event_card(
            title="Grand Rapids Night",
            slug="grand-rapids-night",
            start="2026-09-24",
            end="2026-09-24",
            city="Grand Rapids",
            state="MI",
            artists="indie tribe.",
        ) + "</div></main>"

        transformed = redesign.transform_this_month(document)
        self.assertIn("data-month-show-count>3</strong><span>Shows</span>", transformed)
        self.assertIn("data-month-state-count>2</strong><span>States</span>", transformed)
        self.assertIn("data-month-artist-count>3</strong><span>Artists</span>", transformed)
        self.assertNotIn("data-month-festival-count", transformed)
        self.assertNotIn(
            "Browse the month chronologically, or filter by artist, state, or event type.",
            transformed,
        )


if __name__ == "__main__":
    unittest.main()
