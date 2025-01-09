from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

from algorithm.enums import DayCategory, StrainPoints, Weekday
from algorithm.utils import get_holidays, get_number_of_days_in_month, get_week_number_in_month

if TYPE_CHECKING:
    from algorithm.doctor import Doctor

HOLIDAYS = get_holidays()


class Day:
    def __init__(self, day: int, month: int, year: int) -> None:
        self.number = day
        self.month = month
        self.year = year

        dt = self._to_date()
        self.weekday = dt.weekday()
        self.week = get_week_number_in_month(dt)

        self.category = self._get_category()
        self.strain_points = self._get_strain_points()

    def _to_date(self) -> date:
        return date(self.year, self.month, self.number)

    def _get_category(self) -> str:
        if self.weekday == Weekday.THURSDAY:
            return DayCategory.THURSDAY

        if self.weekday in Weekday.weekend():
            return DayCategory.WEEKEND

        if self._is_holiday:
            return DayCategory.HOLIDAY

        return DayCategory.WEEKDAY

    def _get_strain_points(self) -> int:
        if self._is_holiday:
            return StrainPoints.HOLIDAY

        match self.weekday:
            case Weekday.THURSDAY:
                return StrainPoints.THURSDAY
            case Weekday.FRIDAY:
                return StrainPoints.FRIDAY
            case Weekday.SATURDAY:
                return StrainPoints.SATURDAY
            case Weekday.SUNDAY:
                return StrainPoints.SUNDAY
            case _:
                return StrainPoints.WEEKDAY

    @property
    def _is_holiday(self) -> bool:
        return self.number in HOLIDAYS[self.year][self.month]

    def __str__(self) -> str:
        return f'Day {self.number}/{self.month}/{self.year}'


class Duty:
    def __init__(self, day: Day, position: int, set_by_user: bool = False) -> None:
        self.day = day
        self.position = position
        self.strain_points = day.strain_points
        self.set_by_user = set_by_user

        self.pk = None
        self.doctor = None

    def update(
        self,
        doctor: Doctor,
        pk: int | None = None,
        strain_points: int | None = None,
        set_by_user: bool | None = None,
    ) -> None:
        self.doctor = doctor

        if set_by_user is not None:
            self.set_by_user = set_by_user

        if strain_points is not None:
            self.strain_points = strain_points

        if pk is not None:
            self.pk = pk


class Schedule:
    def __init__(self, month: int, year: int, positions: int) -> None:
        self.month = month
        self.year = year

        number_of_days = get_number_of_days_in_month(month, year)
        self.day_numbers = range(1, number_of_days + 1)
        self.position_numbers = range(1, positions + 1)
        self._cells = {
            day_number: {
                position_number: Duty(
                    day=Day(day_number, self.month, self.year),
                    position=position_number,
                )
                for position_number in self.position_numbers
            }
            for day_number in self.day_numbers
        }

    def __getitem__(self, key: int | tuple[int, int]) -> Any:
        day, position = key
        return self._cells[day][position]

    def __setitem__(self, key: Any, new_value: Any) -> None:
        raise AttributeError('Schedule items are immutable. Retrieve the desired duty and update it instead.')

    def __len__(self):
        return len(self._cells)

    def to_list(self) -> list[dict[str, Any]]:
        pass  # TODO
