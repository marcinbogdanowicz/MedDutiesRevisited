from __future__ import annotations

from abc import ABC
from datetime import date
from itertools import chain
from typing import TYPE_CHECKING, Any, Iterator

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


class Cell(ABC):
    def __init__(self, day: Day, position: int) -> None:
        self.day = day
        self.position = position


class Schedule(ABC):
    cell_class: Cell

    def __init__(self, month: int, year: int, positions: int) -> None:
        self.month = month
        self.year = year

        self.days = get_number_of_days_in_month(month, year)
        self.positions = positions

        self._schedule = [
            [
                self.cell_class(day=Day(row + 1, self.month, self.year), position=col + 1)
                for col in range(self.positions)
            ]
            for row in range(self.days)
        ]

    def __getitem__(self, key: int) -> Cell:
        if isinstance(key, int):
            return self._schedule[key]

        raise KeyError(f'Unsupported {self.__class__.__name__} row key: {key}.')

    def __setitem__(self, key: Any, new_value: Any) -> None:
        raise AttributeError(
            f'{self.__class__.__name__} cells are immutable. Retrieve the desired cell and update it instead.'
        )

    def __len__(self) -> int:
        return len(self._schedule)

    def get(self, day: int, position: int) -> Cell:
        if 0 < day <= self.days and 0 < position <= self.positions:
            return self._schedule[day - 1][position - 1]

        raise KeyError(f'{self.__class__.__name__} doesn\'t include day {day}, position {position}.')


class Duty(Cell):
    def __init__(self, day: Day, position: int, set_by_user: bool = False) -> None:
        super().__init__(day, position)

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


class DutySchedule(Schedule):
    cell_class = Duty

    def cells(self) -> Iterator[Duty]:
        return chain(*self._schedule)


class PreferencesList(Cell, list):
    pass


class PreferencesSchedule(Schedule):
    cell_class = PreferencesList
