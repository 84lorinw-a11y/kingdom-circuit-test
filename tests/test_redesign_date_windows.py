from __future__ import annotations

import datetime as dt
import importlib.util
import json
import pathlib
import sys
import tempfile
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
    def test_cutoff_archives_yesterday_and_uses_multiday_end_date(self) -> None:
        today = dt.date(2026, 9, 21)
        cutoff = redesign.visibility_cutoff(today)
        self.assertEqual(cutoff, dt.date(2026, 9, 21))

        yesterday = {
            "startDate": "2026-09-18",
            "endDate": "2026-09-20",
        }
        two_days_old = {
            "startDate": "2026-09-18",
            "endDate": "2026-09-19",
        }
        today_show = {
            "startDate": "2026-09-21",
            "endDate": "2026-09-21",
        }
        self.assertFalse(redesign.is_active_event(yesterday, cutoff))
        self.assertFalse(redesign.is_active_event(two_days_old, cutoff))
        self.assertTrue(redesign.is_active_event(today_show, cutoff))

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
        self.assertNotIn("Yesterday Festival", pruned)
        self.assertNotIn("Two Days Old", pruned)
        self.assertEqual(pruned.count("data-event-card"), 0)

    def test_runtime_uses_the_same_zero_day_cutoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            app = root / "app.js"
            app.write_text(
                'async function boot() {\n  const staticCards = [...document.querySelectorAll("[data-event-card]")];',
                encoding="utf-8",
            )
            redesign.patch_runtime(root)
            runtime = app.read_text(encoding="utf-8")

        self.assertIn("cutoff.getUTCDate() - 0", runtime)
        self.assertNotIn("__KC_PAST_GRACE_DAYS__", runtime)


class TestPastShowsMigration(unittest.TestCase):
    def test_expired_hulvey_show_moves_into_past_shows_once(self) -> None:
        cutoff = dt.date(2026, 9, 20)
        archived_rows = "".join(
            f'''<article class="past-show-row"><div class="past-show-date">Sep {15 - index}, 2026</div>
<div class="past-show-copy"><h3><a href="/kingdom-circuit-test/event/old-{index}/">Old {index}</a></h3><p>Old Venue · Old City</p></div></article>'''
            for index in range(12)
        )
        archive = f'''<section class="past-shows-archive" data-past-shows-archive><details>
<summary><span>Past shows</span><span class="past-count">12 archived shows</span></summary>
<div class="past-show-list">{archived_rows}</div>
<p class="past-archive-note">Past listings are preserved for concert history.</p>
</details></section>'''
        chicago = event_card(
            title="Hulvey - Could Be Tonight Tour",
            slug="hulvey-could-be-tonight-tour-2026-09-19-chicago-96a450",
            start="2026-09-19",
            end="2026-09-19",
            city="Chicago",
            state="IL",
            artists="Hulvey|indie tribe.|Kijan Boone",
        )
        detroit = event_card(
            title="Hulvey - Could Be Tonight Tour",
            slug="hulvey-could-be-tonight-tour-2026-09-18-detroit-0bd71c",
            start="2026-09-18",
            end="2026-09-18",
            city="Detroit",
            state="MI",
            artists="Hulvey|indie tribe.|Kijan Boone",
        )
        minneapolis = event_card(
            title="Hulvey Live at First Ave",
            slug="hulvey-live-at-first-ave-2026-09-20-minneapolis-31908f",
            start="2026-09-20",
            end="2026-09-20",
            city="Minneapolis",
            state="MN",
            artists="Hulvey|indie tribe.|Kijan Boone",
        )
        document = f"<main>{chicago}{detroit}{minneapolis}{archive}</main>"

        migrated, added = redesign.archive_expired_profile_cards(document, cutoff)
        self.assertEqual(added, 2)
        self.assertEqual(migrated.count('class="past-show-row"'), 14)
        self.assertIn("14 archived shows", migrated)
        self.assertIn("/kingdom-circuit-test/event/old-11/", migrated)
        chicago_href = "/kingdom-circuit-test/event/hulvey-could-be-tonight-tour-2026-09-19-chicago-96a450/"
        detroit_href = "/kingdom-circuit-test/event/hulvey-could-be-tonight-tour-2026-09-18-detroit-0bd71c/"
        self.assertEqual(migrated.count(chicago_href), 2)
        self.assertEqual(migrated.count(detroit_href), 2)
        archive_start = migrated.index("past-show-list")
        self.assertLess(
            migrated.index(chicago_href, archive_start),
            migrated.index(detroit_href, archive_start),
        )

        pruned = redesign.prune_expired_event_cards(migrated, cutoff)
        self.assertEqual(pruned.count(chicago_href), 1)
        self.assertEqual(pruned.count(detroit_href), 1)
        self.assertEqual(pruned.count("data-event-card"), 1)
        self.assertIn("Minneapolis", pruned)

        migrated_again, added_again = redesign.archive_expired_profile_cards(migrated, cutoff)
        self.assertEqual(added_again, 0)
        self.assertEqual(migrated_again, migrated)

    def test_expired_card_creates_archive_when_profile_has_none(self) -> None:
        cutoff = dt.date(2026, 9, 20)
        chicago = event_card(
            title="Hulvey - Could Be Tonight Tour",
            slug="hulvey-could-be-tonight-tour-2026-09-19-chicago-96a450",
            start="2026-09-19",
            end="2026-09-19",
            city="Chicago",
            state="IL",
            artists="Hulvey",
        )
        migrated, added = redesign.archive_expired_profile_cards(f"<main>{chicago}</main>", cutoff)
        self.assertEqual(added, 1)
        self.assertIn('class="past-shows-archive"', migrated)
        self.assertIn("1 archived show", migrated)
        self.assertIn("Chicago, IL", migrated)
        self.assertIn("Test Venue", migrated)


class TestFullPastHistory(unittest.TestCase):
    def test_distinct_same_day_performance_times_are_not_deduplicated(self) -> None:
        morning = {
            "title": "808 BEEZY — Live at RWG TOUR 2026",
            "startDate": "2026-09-18",
            "startTime": "08:45",
            "venue": "RWG TOUR 2026",
            "city": "Dola",
            "state": "OH",
        }
        later = {**morning, "startTime": "09:45"}
        self.assertFalse(redesign.history_event_duplicate(morning, later))

    def test_history_has_no_display_cap_and_deduplicates_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            site = pathlib.Path(temp)
            (site / "config").mkdir()
            (site / "config" / "artists.json").write_text(
                json.dumps(
                    [
                        {
                            "name": "Hulvey",
                            "aliases": ["Hulvey Music"],
                            "enabled": True,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            records = []
            for day in range(1, 15):
                records.append(
                    {
                        "observedOnOrAfterEventDate": True,
                        "event": {
                            "id": f"official:{day}",
                            "title": f"Past Show {day}",
                            "startDate": f"2026-08-{day:02d}",
                            "venue": f"Venue {day}",
                            "city": "Atlanta",
                            "state": "GA",
                            "country": "US",
                            "artists": ["Hulvey Music"],
                            "confidence": "high",
                            "officialUrl": f"https://tickets.example.test/{day}",
                        },
                    }
                )
            records.append(
                {
                    "observedOnOrAfterEventDate": True,
                    "event": {
                        **records[0]["event"],
                        "id": "ticketmaster:duplicate",
                    },
                }
            )
            records.append(
                {
                    "observedOnOrAfterEventDate": True,
                    "event": {
                        **records[0]["event"],
                        "id": "official:second-venue",
                        "venue": "A Different Venue",
                        "officialUrl": "https://tickets.example.test/second-venue",
                    },
                }
            )
            history = site / "history.json"
            history.write_text(json.dumps({"events": records}), encoding="utf-8")

            events, profiles, aliases = redesign.load_source_history(
                [history],
                site,
                dt.date(2026, 9, 20),
            )

            self.assertEqual(len(events), 15)
            self.assertEqual(len(profiles["hulvey"]), 15)
            self.assertEqual(aliases["hulvey music"], "hulvey")
            rows = [redesign.history_archive_row(event, aliases) for event in profiles["hulvey"]]
            archive = redesign.replace_profile_archive("<main></main>", rows)
            self.assertEqual(archive.count('class="past-show-row"'), 15)
            self.assertIn("15 archived shows", archive)


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
