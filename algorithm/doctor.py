from __future__ import annotations

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

    def can_accept_duty_on_day(self, day: Day) -> bool:
        if day.number + 1 in self.requested_days or day.number - 1 in self.requested_days:
            return False

        if day.weekday not in self.preferred_weekdays and day.number not in self.requested_days:
            return False

        if day.number in self.exceptions:
            return False

        return True
