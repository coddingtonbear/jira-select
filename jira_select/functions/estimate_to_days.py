import re
from typing import Optional

from ..plugin import BaseFunction


class Function(BaseFunction):
    """Converts a string estimate to days."""

    def __call__(self, value_str: str, day_hour_count=8) -> Optional[float]:  # type: ignore[override]
        unit_mapping = {
            "w": 5,
            "d": 1,
            "h": 1 / day_hour_count,
            "m": 1 / day_hour_count / 60,
        }
        unit_matcher = re.compile(r"(?P<value>[\d.]+)(?P<unit>[^\d]+)")
        total_value: float = 0

        for value_str_unit in value_str.split(" "):
            match = unit_matcher.match(value_str_unit)
            if not match:
                raise ValueError(value_str)

            unit = match.groupdict()["unit"]
            value = float(match.groupdict()["value"])

            try:
                total_value += unit_mapping[unit] * value
            except KeyError:
                pass

        return total_value
