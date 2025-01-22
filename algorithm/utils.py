from __future__ import annotations

import calendar
import math
from abc import ABC, abstractmethod
from collections import defaultdict
from contextlib import suppress
from datetime import date, timedelta
from functools import reduce
from itertools import product
from typing import TYPE_CHECKING, Any, Sequence

from algorithm.enums import StrainModifier, Weekday

if TYPE_CHECKING:
    from algorithm.doctor import Doctor
    from algorithm.schedule import Day, DoctorAvailabilitySchedule, DoctorAvailabilityScheduleRow, DutySchedule


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


def is_superset_included(subset: set, iterables: Sequence[Sequence]) -> bool:
    return any(set(iterable).issuperset(subset) for iterable in iterables)


def comma_join(objects: Sequence[Any]) -> str:
    return ", ".join(str(obj) for obj in objects)


def unique_product(*iterables: Sequence) -> list[tuple]:
    return [elem for elem in product(*iterables) if len(elem) == len(set(elem))]


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


class DoctorAvailabilityHelper:
    def __init__(self, doctors: list[Doctor], duty_schedule: DutySchedule) -> None:
        self.doctors = doctors
        self.duty_schedule = duty_schedule

    def get_availability_schedule(self) -> DoctorAvailabilitySchedule:
        from algorithm.schedule import DoctorAvailabilitySchedule

        availability_schedule = DoctorAvailabilitySchedule(
            self.duty_schedule.month, self.duty_schedule.year, self.duty_schedule.positions
        )

        for row in availability_schedule:
            day = row.day
            doctors = self.doctors.copy()
            free_positions = self.duty_schedule[day.number].free_positions()

            for duty in self.duty_schedule[day.number].set_duties():
                doctors.remove(duty.doctor)
                availability_schedule[day.number, duty.position].append(duty.doctor)
                availability_schedule[day.number, duty.position].is_set = True

            for doctor in doctors:
                if not self._has_doctor_received_duties_on_adjacent_days(
                    doctor, day.number
                ) and doctor.can_accept_duty_on_day(day):
                    available_free_positions = free_positions & set(doctor.preferences.preferred_positions)
                    for position in available_free_positions:
                        availability_schedule[day.number, position].append(doctor)

        return availability_schedule

    def _has_doctor_received_duties_on_adjacent_days(self, doctor: Doctor, day_number: int) -> bool:
        for day in [day_number - 1, day_number + 1]:
            with suppress(KeyError):
                if self.duty_schedule[day].has_duty(doctor):
                    return True

        return False


class BaseStrainModifier(ABC):
    modifier: StrainModifier

    def __init__(
        self,
        day: Day,
        doctor: Doctor,
        duty_schedule: DutySchedule,
    ) -> None:
        self.day = day
        self.doctor = doctor
        self.duty_schedule = duty_schedule

    def get(self) -> int:
        if self.should_apply():
            return self.get_modifier()

        return 0

    @abstractmethod
    def should_apply(self) -> bool:
        pass

    def get_modifier(self) -> int:
        return self.modifier


class JoinFridayWithSundayModifier(BaseStrainModifier):
    modifier = StrainModifier.JOIN_FRIDAY_WITH_SUNDAY

    def should_apply(self) -> bool:
        return (
            self.day.weekday == Weekday.SUNDAY
            and self.day.number > 2
            and self.duty_schedule[self.day.number - 2].has_duty(self.doctor)
        )


class DontStealSundaysModifier(BaseStrainModifier):
    modifier = StrainModifier.DONT_STEAL_SUNDAYS

    def should_apply(self) -> bool:
        return (
            self.day.weekday == Weekday.SUNDAY
            and self.day.number > 2
            and not self.duty_schedule[self.day.number - 2].has_duty(self.doctor)
        )


class AvoidSaturdayAfterThursdayModifier(BaseStrainModifier):
    modifier = StrainModifier.AVOID_SATURDAY_AFTER_THURSDAY

    def should_apply(self) -> bool:
        return (
            self.day.weekday == Weekday.SATURDAY
            and self.day.number > 2
            and self.duty_schedule[self.day.number - 2].has_duty(self.doctor)
        )


class IsThursdayOrdinaryModifier(BaseStrainModifier):
    modifier = StrainModifier.THURSDAY_IS_ORDINARY

    def should_apply(self) -> bool:
        # Day off after Thursday wouldn't make any difference.
        return self.day.weekday == Weekday.THURSDAY and self.doctor.preferences.no_duties_on_weekends


class NewWeekendModifier(BaseStrainModifier):
    modifier = StrainModifier.NEW_WEEKEND

    def should_apply(self) -> bool:
        return self.day.weekday in Weekday.weekend()

    def get_modifier(self) -> int:
        result = 0

        weeks_on_duty = self._get_week_numbers_on_duty(self.doctor)
        if self.day.week not in weeks_on_duty:
            result += self.modifier * (len(weeks_on_duty) + 1)

        return result

    def _get_week_numbers_on_duty(self, doctor: Doctor) -> set[int]:
        def is_weekend(row):
            return row.day.weekday in Weekday.weekend()

        return {row.day.week for row in self.duty_schedule if row.has_duty(doctor) and is_weekend(row)}


class AveragesDependentMixin:
    def __init__(
        self,
        average_duties_per_doctor: float,
        average_max_duties_preference: float,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.average_duties_per_doctor = average_duties_per_doctor
        self.average_max_duties_preference = average_max_duties_preference


class RemainingDutiesCountModifier(AveragesDependentMixin, BaseStrainModifier):
    modifier = StrainModifier.DUTY_LEFT

    def should_apply(self) -> bool:
        return True

    def get_modifier(self) -> int:
        max_duties_modifier = self._get_max_duties_modifier(self.doctor)
        duties_count = sum(1 for _ in self.duty_schedule.duties_for_doctor(self.doctor))
        if duties_count:
            remaining_duties_count = self.doctor.preferences.maximum_accepted_duties - duties_count
            return (remaining_duties_count - max_duties_modifier) * self.modifier

        # Encourage giving duties to doctors who haven't received any yet.
        return 20 * self.modifier

    def _get_max_duties_modifier(self, doctor: Doctor) -> int:
        maximum_accepted_duties = doctor.preferences.maximum_accepted_duties
        if maximum_accepted_duties < self.average_max_duties_preference:
            result = self.average_duties_per_doctor
        else:
            result = (
                self.average_duties_per_doctor
                * doctor.preferences.maximum_accepted_duties
                / self.average_max_duties_preference
            )

        return math.ceil(result)


class BaseDutyIntervalModifier(BaseStrainModifier, ABC):
    modifier = None

    @abstractmethod
    def get_modifier(self):
        pass

    def get_strain_for_duty_interval(self, days_interval: int) -> int:
        match days_interval:
            case 1:
                raise ValueError(
                    f'Unexpectedly evaluating a double duty with: {self.day}'
                )  # TODO Remove after testing; doctor should be excluded in availability schedule already
            case 2:
                return StrainModifier.TWO_DAYS_APART
            case 3:
                return StrainModifier.THREE_DAYS_APART
            case 4:
                return StrainModifier.FOUR_DAYS_APART
            case _:
                return 0


class AdjacentMonthStrainModifierMixin:
    def __init__(self, previous_month_length: int, current_month_length: int, **kwargs) -> None:
        super().__init__(**kwargs)

        self.previous_month_length = previous_month_length
        self.current_month_length = current_month_length


class PreviousMonthStrainModifier(AdjacentMonthStrainModifierMixin, BaseDutyIntervalModifier):
    def should_apply(self) -> bool:
        return self.day.number < 5

    def get_modifier(self) -> int:
        result = 0
        for i in range(5 - self.day.number):
            if self.previous_month_length - i in self.doctor.last_month_duties:
                result += self.get_strain_for_duty_interval(self.day.number + i)

        return result


class NextMonthStrainModifier(AdjacentMonthStrainModifierMixin, BaseDutyIntervalModifier):
    def should_apply(self):
        return self.day.number > self.current_month_length - 4

    def get_modifier(self):
        result = 0
        reversed_day_number = self.current_month_length - self.day.number
        for i in range(1, 5 - reversed_day_number):
            if i in self.doctor.next_month_duties:
                result += self.get_strain_for_duty_interval(reversed_day_number + i)

        return result


class CloseDutiesModifier(BaseDutyIntervalModifier):
    def should_apply(self):
        return True

    def get_modifier(self):
        result = 0
        for i in [*range(-4, -1), *range(2, 5)]:
            try:
                row = self.duty_schedule[self.day.number + i]
            except KeyError:
                continue

            if row.has_duty(self.doctor):
                result += self.get_strain_for_duty_interval(abs(i))

        return result


class DutyStrainEvaluator:
    strain_modifiers = [
        JoinFridayWithSundayModifier,
        DontStealSundaysModifier,
        AvoidSaturdayAfterThursdayModifier,
        IsThursdayOrdinaryModifier,
        NewWeekendModifier,
        RemainingDutiesCountModifier,
        PreviousMonthStrainModifier,
        NextMonthStrainModifier,
        CloseDutiesModifier,
    ]

    def __init__(self, year: int, month: int, positions: int, all_doctors: list[Doctor]) -> None:
        self.previous_month_length = self._get_previous_month_length(year, month)
        self.current_month_length = self._get_current_month_length(year, month)

        self.average_duties_per_doctor = self._get_average_duties_per_doctor(positions, all_doctors)
        self.average_max_duties_preference = self._get_average_max_duties_preference(all_doctors)

    def get_strain_table(
        self, day: Day, schedule: DutySchedule, availability_per_position: DoctorAvailabilityScheduleRow
    ) -> dict[int, dict[Doctor, int]]:
        strain_table = defaultdict(dict)

        doctors = availability_per_position.doctors_for_all_positions()
        for doctor in doctors:
            strain = self._get_strain(day, doctor, schedule)
            for position in availability_per_position.positions_for_doctor(doctor):
                strain_table[position][doctor] = strain

        return strain_table

    def _get_strain(self, day: Day, doctor: Doctor, schedule: DutySchedule) -> int:
        strain = day.strain_points

        for modifier_class in self.strain_modifiers:
            modifier = self._init_modifier(modifier_class, day, doctor, schedule)
            strain += modifier.get()

        return strain

    def _init_modifier(
        self, modifier: type[BaseStrainModifier], day: Day, doctor: Doctor, schedule: DutySchedule
    ) -> BaseStrainModifier:
        kwargs = {
            "day": day,
            "doctor": doctor,
            "duty_schedule": schedule,
        }

        if issubclass(modifier, AveragesDependentMixin):
            kwargs["average_duties_per_doctor"] = self.average_duties_per_doctor
            kwargs["average_max_duties_preference"] = self.average_max_duties_preference

        if issubclass(modifier, AdjacentMonthStrainModifierMixin):
            kwargs["previous_month_length"] = self.previous_month_length
            kwargs["current_month_length"] = self.current_month_length

        return modifier(**kwargs)

    def _get_previous_month_length(self, year: int, month: int) -> int:
        prev_month_last_day_dt = date(year, month, 1) - timedelta(days=1)
        return prev_month_last_day_dt.day

    def _get_current_month_length(self, year: int, month: int) -> int:
        return get_number_of_days_in_month(month, year)

    def _get_average_duties_per_doctor(self, positions_count: int, doctors: list[Doctor]) -> float:
        return self.current_month_length * positions_count / len(doctors)

    def _get_average_max_duties_preference(self, doctors: list[Doctor]) -> float:
        return sum(doctor.preferences.maximum_accepted_duties for doctor in doctors) / len(doctors)
