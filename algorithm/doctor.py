from __future__ import annotations

from datetime import date, timedelta
from functools import cached_property
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from algorithm.schedule import Day


class Doctor:
    def __init__(
        self,
        pk: int,
        name: str,
        last_month_duties: list[int] | None = None,
        next_month_duties: list[int] | None = None,
    ) -> None:
        self.pk = pk
        self.name = name

        self.preferences = None

        self.last_month_duties = last_month_duties or []
        self.next_month_duties = next_month_duties or []

    def init_preferences(self, **kwargs) -> None:
        self.preferences = DoctorsDutyPreferences(**kwargs)

    def can_accept_duty_on_day(self, day: Day) -> bool:
        if day.number + 1 in self.preferences.requested_days or day.number - 1 in self.preferences.requested_days:
            return False

        if day.weekday not in self.preferences.preferred_weekdays and day.number not in self.preferences.requested_days:
            return False

        if day.number in self.preferences.exceptions:
            return False

        if day.number == 1 and not self._can_take_duty_on_first_day_of_month:
            return False

        if day.is_last_day_of_month and not self._can_take_duty_on_last_day_of_month:
            return False

        return True

    @cached_property
    def _can_take_duty_on_first_day_of_month(self) -> bool:
        last_month_last_day = (date(self.preferences.year, self.preferences.month, 1) - timedelta(days=1)).day
        return last_month_last_day not in self.last_month_duties

    @cached_property
    def _can_take_duty_on_last_day_of_month(self) -> bool:
        return 1 not in self.next_month_duties

    def __str__(self) -> str:
        return f'Doctor {self.name}'

    def __repr__(self) -> str:
        return f'{self} (pk={self.pk})'


class DoctorsDutyPreferences:
    def __init__(
        self,
        month: int,
        year: int,
        exceptions: Sequence[int],
        requested_days: Sequence[int],
        preferred_weekdays: Sequence[int],
        preferred_positions: Sequence[int],
        maximum_accepted_duties: int,
    ) -> None:
        self.month = month
        self.year = year

        self.exceptions = exceptions
        self.requested_days = requested_days
        self.preferred_weekdays = preferred_weekdays
        self.preferred_positions = preferred_positions
        self.maximum_accepted_duties = maximum_accepted_duties
