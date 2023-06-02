import datetime

from dateutil.tz import tzlocal

from ..plugin import BaseFunction


class Function(BaseFunction):
    """Return 'now' as a timezone-aware datetime object."""

    def __call__(self, **replacements) -> datetime.datetime:  # type: ignore[override]
        localized = (
            datetime.datetime.now().replace(tzinfo=tzlocal()).replace(**replacements)
        )

        return localized
