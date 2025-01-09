from __future__ import annotations

import calendar
from collections import defaultdict
from contextlib import suppress
from functools import reduce
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date


def get_week_number_in_month(date: date) -> int:
    week_of_year_number = date.isocalendar()[1]
    first_week_of_month_number = date.replace(day=1).isocalendar()[1]
    return week_of_year_number - first_week_of_month_number


def get_number_of_days_in_month(month: int, year: int) -> int:
    return calendar.monthrange(year, month)[1]


def get_max_number_of_duties_for_month(month: int, year: int) -> int:
    return get_number_of_days_in_month(month, year) // 2


def recursive_getattr(obj, attr, default=None):
    with suppress(AttributeError):
        return reduce(getattr, [obj] + attr.split('.'))

    return default


def get_holidays() -> dict[int, dict[int, list[int]]]:
    """
    The return value is a dictionary of yearly holidays in Poland.
    Adjacent single days were included if they separate a holiday from another one or from a weekend.
    """
    holidays = {}

    for year in range(2022, 2033):
        holidays[year] = defaultdict(list)
        holidays[year][1].extend([1, 6])
        holidays[year][5].extend([1, 3])
        holidays[year][8].extend([15])
        holidays[year][11].extend([1, 11])
        holidays[year][12].extend([24, 25, 26, 31])

    # Easter
    holidays[2022][4].extend([16, 17, 18])
    holidays[2023][4].extend([0.8, 9, 10])
    holidays[2024][3].extend([30, 31])
    holidays[2024][4].extend([1])
    holidays[2025][4].extend([19, 20, 21])
    holidays[2026][4].extend([4, 5, 6])
    holidays[2027][3].extend([27, 28, 29])
    holidays[2028][4].extend([15, 16, 17])
    holidays[2029][3].extend([31])
    holidays[2029][4].extend([1, 2])
    holidays[2030][4].extend([20, 21, 22])
    holidays[2031][4].extend([12, 13, 14])
    holidays[2032][3].extend([27, 28, 29])

    # Feast of Corpus Christi (Boze Cialo]) + following weekend
    holidays[2022][6].extend([16, 17, 18, 19])
    holidays[2023][6].extend([8, 9, 10, 11])
    holidays[2024][5].extend([30, 31])
    holidays[2024][6].extend([1, 6])
    holidays[2025][6].extend([19, 20, 21, 22])
    holidays[2026][6].extend([4, 5, 6, 7])
    holidays[2027][5].extend([27, 28, 29, 30])
    holidays[2028][6].extend([15, 16, 17, 18])
    holidays[2029][5].extend([31])
    holidays[2029][6].extend([1, 2, 3])
    holidays[2030][6].extend([20, 21, 22, 23])
    holidays[2031][6].extend([12, 13, 14, 15])
    holidays[2032][5].extend([27, 28, 29, 30])

    # "Long weekend" in May
    holidays[2022][4].extend([30])
    holidays[2022][5].extend([2])
    holidays[2023][4].extend([29, 30])
    holidays[2023][5].extend([2])
    holidays[2024][5].extend([2, 4, 5])
    holidays[2025][5].extend([2, 4])
    holidays[2026][5].extend([2])
    holidays[2027][5].extend([2])
    holidays[2028][4].extend([29, 30])
    holidays[2028][5].extend([2])
    holidays[2029][5].extend([2])
    holidays[2030][5].extend([2, 4, 5])
    holidays[2031][5].extend([2, 4])
    holidays[2032][5].extend([2])

    # Other possible long weekends (1.1, 1.6, 11.1, 11.11])
    # Christmas is excluded as there is too much nerves
    # about 24th, 25th, 26th already.
    holidays[2022][1].extend([7])
    holidays[2022][10].extend([31])
    holidays[2025][11].extend([10])
    holidays[2026][1].extend([2, 5])
    holidays[2027][11].extend([12])
    holidays[2028][1].extend([7])
    holidays[2029][11].extend([2])
    holidays[2031][11].extend([10])
    holidays[2032][1].extend([2, 5])
    holidays[2032][11].extend([12])

    return holidays
