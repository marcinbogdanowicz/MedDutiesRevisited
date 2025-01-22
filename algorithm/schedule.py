from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from functools import cached_property
from itertools import chain
from typing import Any, Iterator, Self

from algorithm.doctor import Doctor
from algorithm.enums import DayCategory, StrainPoints, Weekday
from algorithm.utils import get_holidays, get_number_of_days_in_month, get_week_number_in_month

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

    @cached_property
    def is_last_day_of_month(self) -> bool:
        return self.number == get_number_of_days_in_month(self.month, self.year)

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

    def __repr__(self) -> str:
        return f'{self.number}/{self.month}/{self.year}'


class ContainerSequence(ABC):
    _members: dict[int, Any]

    @abstractmethod
    def __init__(self):
        pass

    @property
    @abstractmethod
    def member_class(self) -> type:
        pass

    def __getitem__(self, key: int) -> Any:
        if isinstance(key, int):
            return self._members[key]

        raise KeyError(f'Unsupported key: {key}')

    def __setitem__(self, key: Any, new_value: Any) -> None:
        raise AttributeError(
            f'{self.__class__.__name__} is immutable. Retrieve the desired element and update it instead.'
        )

    def __iter__(self) -> Iterator[Any]:
        return (elem for elem in self._members.values())

    def __len__(self) -> int:
        return len(self._members)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}: {list(self)}'


class ScheduleRow(ContainerSequence, ABC):
    def __init__(self, day: Day, positions: int) -> None:
        self.day = day
        self._members = {
            position: self.member_class(day=day, position=position) for position in range(1, positions + 1)
        }


class Schedule(ContainerSequence, ABC):
    def __init__(self, month: int, year: int, positions: int) -> None:
        self.month = month
        self.year = year

        self.days = get_number_of_days_in_month(month, year)
        self.positions = positions

        self._members = {
            day_number: self.member_class(
                day=Day(day_number, self.month, self.year),
                positions=self.positions,
            )
            for day_number in range(1, self.days + 1)
        }

    def __getitem__(self, key: int | tuple[int, int]) -> Any:
        if isinstance(key, tuple) and len(key) == 2:
            day, position = key
            return self._members[day][position]

        return super().__getitem__(key)


class Cell:
    def __init__(self, day: Day, position: int) -> None:
        self.day = day
        self.position = position

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} ({self.day}, {self.position})'


class Duty(Cell):
    def __init__(self, day: Day, position: int, set_by_user: bool = False) -> None:
        super().__init__(day, position)

        self.strain_points = day.strain_points
        self.set_by_user = set_by_user

        self.doctor = None
        self.pk = None

    def __contains__(self, item: Any) -> bool:
        if isinstance(item, Doctor):
            return item == self.doctor

        raise KeyError(f'{item} is not a {Doctor.__name__} instance')

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

    @property
    def is_set(self) -> bool:
        return self.doctor is not None

    def __repr__(self) -> str:
        return f'{super().__repr__()}: {self.doctor}'


class DutyRow(ScheduleRow):
    member_class = Duty

    def has_duty(self, doctor: Doctor) -> bool:
        return any(doctor in duty for duty in self)

    def free_positions(self) -> set[int]:
        return {duty.position for duty in self if not duty.is_set}

    def set_duties(self) -> Iterator[Duty]:
        return (duty for duty in self if duty.is_set)


class DutySchedule(Schedule):
    member_class = DutyRow

    def cells(self) -> Iterator[Duty]:
        return chain(*self)

    def duties_for_doctor(self, doctor: Doctor) -> Iterator[Duty]:
        return (duty for duty in self.cells() if doctor in duty)

    def copy_empty(self) -> Self:
        return self.__class__(self.month, self.year, self.positions)


class AvailableDoctorList(Cell, list):
    def __init__(self, day: Day, position: int) -> None:
        super().__init__(day, position)
        self.is_set = False

    def __repr__(self) -> str:
        return f'{super().__repr__()}: {list.__repr__(self)}'


class DoctorAvailabilityScheduleRow(ScheduleRow):
    member_class = AvailableDoctorList

    def doctors_for_positions(self, *positions: int) -> set[Doctor]:
        return set(sum((self[position] for position in positions), []))

    def doctors_for_all_positions(self) -> set[Doctor]:
        return self.doctors_for_positions(*range(1, len(self) + 1))

    def positions_for_doctor(self, doctor: Doctor) -> Iterator[int]:
        return (position.position for position in self if doctor in position)

    @property
    def is_set(self) -> bool:
        return all(position.is_set for position in self)

    @property
    def average_doctors_per_free_position(self) -> float:
        doctors_counts = [len(position) for position in self if not position.is_set]
        return sum(doctors_counts) / len(doctors_counts) if doctors_counts else 0


class DoctorAvailabilitySchedule(Schedule):
    member_class = DoctorAvailabilityScheduleRow
