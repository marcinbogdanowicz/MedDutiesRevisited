from __future__ import annotations

import calendar
from collections import defaultdict
from contextlib import suppress
from datetime import date
from functools import reduce
from itertools import product
from typing import TYPE_CHECKING, Any, Iterator, Sequence

if TYPE_CHECKING:
    from algorithm.doctor import Doctor
    from algorithm.schedule import DoctorAvailabilitySchedule, DutySchedule


def get_week_number_in_month(date: date) -> int:
    week_of_year_number = date.isocalendar()[1]
    first_week_of_month_number = date.replace(day=1).isocalendar()[1]
    return week_of_year_number - first_week_of_month_number


def get_number_of_days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def get_max_number_of_duties_for_month(year: int, month: int) -> int:
    return get_number_of_days_in_month(year, month) // 2


def recursive_getattr(obj, attr, default=None):
    with suppress(AttributeError):
        return reduce(getattr, [obj] + attr.split('.'))

    return default


def is_superset_included(subset: set, iterables: Sequence[Sequence]) -> bool:
    return any(set(iterable).issuperset(subset) for iterable in iterables)


def comma_join(objects: Sequence[Any]) -> str:
    return ", ".join(str(obj) for obj in objects)


def unique_product(*iterables: Sequence) -> Iterator[tuple]:
    return (elem for elem in product(*iterables) if len(elem) == len(set(elem)))


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
        self.duty_schedule = duty_schedule
        self.doctors = [doctor for doctor in doctors if self._doctor_has_less_duties_than_maximum(doctor)]

    def get_availability_schedule(self) -> DoctorAvailabilitySchedule:
        from algorithm.schedule import DoctorAvailabilitySchedule

        availability_schedule = DoctorAvailabilitySchedule(
            self.duty_schedule.year, self.duty_schedule.month, self.duty_schedule.positions
        )

        for row in availability_schedule:
            day = row.day
            doctors = self.doctors.copy()
            free_positions = self.duty_schedule[day.number].free_positions()

            for duty in self.duty_schedule[day.number].set_duties():
                availability_schedule[day.number, duty.position].append(duty.doctor)
                availability_schedule[day.number, duty.position].is_set = True
                with suppress(ValueError):
                    doctors.remove(duty.doctor)

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

    def _doctor_has_less_duties_than_maximum(self, doctor: Doctor) -> bool:
        doctor_duties_count = len(list(self.duty_schedule.duties_for_doctor(doctor)))
        return doctor_duties_count < doctor.preferences.maximum_accepted_duties
