"""Freeze date-sensitive production builders when recreating a deployed release.

Python imports ``sitecustomize`` automatically when this directory is placed on
``PYTHONPATH``. Normal local commands are unchanged; the clock is frozen only
when ``KC_MIRROR_DATE`` contains an ISO date.
"""

from __future__ import annotations

import datetime as _datetime
import os as _os


_value = _os.environ.get("KC_MIRROR_DATE", "").strip()
if _value:
    _frozen = _datetime.date.fromisoformat(_value)
    _real_date = _datetime.date
    _real_datetime = _datetime.datetime

    class _FrozenDate(_real_date):
        @classmethod
        def today(cls) -> "_FrozenDate":
            return cls(_frozen.year, _frozen.month, _frozen.day)

    class _FrozenDateTime(_real_datetime):
        @classmethod
        def now(cls, tz: _datetime.tzinfo | None = None) -> "_FrozenDateTime":
            instant = _real_datetime(
                _frozen.year,
                _frozen.month,
                _frozen.day,
                12,
                tzinfo=_datetime.timezone.utc,
            )
            if tz is None:
                return cls(
                    instant.year,
                    instant.month,
                    instant.day,
                    instant.hour,
                    instant.minute,
                    instant.second,
                    instant.microsecond,
                )
            converted = instant.astimezone(tz)
            return cls(
                converted.year,
                converted.month,
                converted.day,
                converted.hour,
                converted.minute,
                converted.second,
                converted.microsecond,
                tzinfo=converted.tzinfo,
                fold=converted.fold,
            )

        @classmethod
        def utcnow(cls) -> "_FrozenDateTime":
            return cls(_frozen.year, _frozen.month, _frozen.day, 12)

    _datetime.date = _FrozenDate
    _datetime.datetime = _FrozenDateTime
