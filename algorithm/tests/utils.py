from __future__ import annotations

import random
from typing import TYPE_CHECKING

from faker import Faker

from algorithm.doctor import Doctor
from algorithm.duty_setter import DutySetter
from algorithm.schedule import Day
from algorithm.utils import comma_join, get_max_number_of_duties_for_month, get_number_of_days_in_month

if TYPE_CHECKING:
    from algorithm.schedule import Duty, DutySchedule

faker = Faker()


def input_factory(
    year: int = 2025,
    month: int = 1,
    doctors_per_duty: int = 1,
    doctors_count: int = 10,
    duties_count: int = 0,
):
    positions = range(1, doctors_per_duty + 1)
    accepted_duties = get_max_number_of_duties_for_month(year, month)

    doctor_pks = list(range(1, doctors_count + 1))
    doctors = [
        {
            "pk": pk,
            "name": faker.name(),
            "preferences": {
                "exceptions": [],
                "requested_days": [],
                "preferred_weekdays": [0, 1, 2, 3, 4, 5, 6],
                "preferred_positions": list(positions),
                "maximum_accepted_duties": accepted_duties,
            },
            "last_month_duties": [],
            "next_month_duties": [],
        }
        for pk in doctor_pks
    ]

    days_count = get_number_of_days_in_month(year, month)

    duties = []
    duty_pk = 1
    for day_number in range(1, days_count + 1):
        day = Day(day_number, month, year)
        for position in positions:
            duties.append(
                {
                    "pk": duty_pk,
                    "doctor": None,
                    "day": day.number,
                    "position": position,
                    "strain_points": day.strain_points,
                    "set_by_user": False,
                }
            )
            duty_pk += 1

    set_duties_count = min(duties_count, accepted_duties)
    for i in range(0, set_duties_count * len(positions) * 2, len(positions) * 2):
        duties[i]["doctor"] = random.choice(doctor_pks)
        duties[i]["set_by_user"] = True

    return {
        "year": year,
        "month": month,
        "doctors_per_duty": doctors_per_duty,
        "doctors": doctors,
        "duties": duties,
    }


def doctor_factory(count=1, /, **kwargs):
    def get_init_data():
        return {
            "name": kwargs.get('name', faker.first_name()),
            "pk": kwargs.get('pk', faker.unique.random_int(min=1, max=9999)),
            "last_month_duties": kwargs.get('last_month_duties', []),
            "next_month_duties": kwargs.get('next_month_duties', []),
        }

    if count == 1:
        return Doctor(**get_init_data())

    return [Doctor(**get_init_data()) for _ in range(count)]


class ExpectedError(Exception):
    pass


class PreferencesKwargsTestMixin:
    year: int
    month: int
    duty_positions: int

    def get_init_preferences_kwargs(self):
        return {
            "year": self.year,
            "month": self.month,
            "exceptions": [],
            "requested_days": [],
            "preferred_weekdays": list(range(7)),
            "preferred_positions": list(range(1, self.duty_positions + 1)),
            "maximum_accepted_duties": get_max_number_of_duties_for_month(self.year, self.month),
        }


class InitDutySetterTestMixin(PreferencesKwargsTestMixin):
    year: int
    month: int
    duty_positions: int
    doctors_count: int

    def setUp(self):
        self.duty_setter = DutySetter(self.year, self.month, self.duty_positions)
        self.schedule = self.duty_setter.schedule

        doctors = doctor_factory(self.doctors_count) if self.doctors_count > 1 else [doctor_factory(self.doctors_count)]
        self.duty_setter.add_doctor(*doctors)

        for doctor in doctors:
            doctor.init_preferences(**self.get_init_preferences_kwargs())

        # Unpack doctors to self.doctor_{i} properties
        exec('\n'.join(f'self.doctor_{i} = doctors[{i} - 1]' for i in range(1, self.doctors_count + 1)))

        self.doctors = doctors


class ScheduleValidator:
    def __init__(self, doctors: list[Doctor], schedule: DutySchedule):
        self.doctors = doctors
        self.schedule = schedule

        self.errors = []

    def assert_no_invalid_duties(self, check_requested_duties: bool = True) -> None:
        for doctor in self.doctors:
            duties = list(self.schedule.duties_for_doctor(doctor))
            self._validate_duties(doctor, duties, check_requested_duties)

        if self.errors:
            raise AssertionError(f'Invalid duties were found:\n{"\n".join(self.errors)}')

    def _validate_duties(self, doctor: Doctor, duties: list[Duty], check_requested_duties: bool) -> None:
        if not duties:
            self.errors.append(f'{doctor} has no duties.')

        if len(duties) > doctor.preferences.maximum_accepted_duties:
            self.errors.append(f'{doctor} has more duties than they can accept.')

        duty_days = sorted(duty.day.number for duty in duties)
        for day in duty_days:
            if day + 1 in duty_days:
                self.errors.append(f'{doctor} has consecutive duties on days {day}, {day + 1}.')

        if 1 in duty_days and not doctor.can_take_duty_on_first_day_of_month:
            self.errors.append(f'{doctor} has consecutive duties on first day of month and last day of previous month.')

        last_day_of_month = len(self.schedule)
        if last_day_of_month in duty_days and not doctor.can_take_duty_on_last_day_of_month:
            self.errors.append(f'{doctor} has consecutive duties on last day of month and first day of next month.')

        if check_requested_duties and (
            missing_duties := [day for day in doctor.preferences.requested_days if day not in duty_days]
        ):
            self.errors.append(f'{doctor} has missing requested duties on days: {comma_join(missing_duties)}.')

        for duty in duties:
            self._validate_duty(duty)

    def _validate_duty(self, duty: Duty) -> None:
        doctor = duty.doctor
        day = duty.day

        if day.number in doctor.preferences.exceptions:
            self.errors.append(f'{doctor} got duty on {day}, which they put on exceptions list.')

        if not duty.set_by_user:
            if day.weekday not in doctor.preferences.preferred_weekdays:
                self.errors.append(f'{doctor} got duty on {day}, which is not their preferred weekday.')

            if duty.position not in doctor.preferences.preferred_positions:
                self.errors.append(f'{doctor} got duty on {day}, which is not their preferred position.')
