from typing import Sequence


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


class DoctorsDutyPreferences:
    def __init__(
        self,
        month: int,
        year: int,
        exceptions: Sequence[int],
        preferred_days: Sequence[int],
        preferred_weekdays: Sequence[int],
        preferred_positions: Sequence[int],
        maximum_accepted_duties: int,
    ) -> None:
        self.month = month
        self.year = year

        self.exceptions = exceptions
        self.preferred_days = preferred_days
        self.preferred_weekdays = preferred_weekdays
        self.preferred_positions = preferred_positions
        self.maximum_accepted_duties = maximum_accepted_duties
