import random

from faker import Faker

from algorithm.doctor import Doctor
from algorithm.schedule import Day
from algorithm.utils import get_max_number_of_duties_for_month

faker = Faker()


def input_factory(
    year: int = 2025,
    month: int = 1,
    doctors_per_duty: int = 1,
    doctors_count: int = 10,
    duties_count: int = 0,
):
    positions = range(1, doctors_per_duty + 1)
    accepted_duties = get_max_number_of_duties_for_month(month, year)

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

    duty_days = [Day(i, month, year) for i in range(1, min(duties_count, accepted_duties) * 2, 2)]
    duties = [
        {
            "pk": random.choice((i + 1, None)),
            "doctor_pk": random.choice(doctor_pks),
            "day": day.number,
            "position": random.choice(positions),
            "strain_points": day.strain_points,
            "set_by_user": True,
        }
        for i, day in enumerate(duty_days)
    ]

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
            "pk": kwargs.get('pk', faker.unique.random_int(min=1, max=99)),
            "last_month_duties": kwargs.get('last_month_duties', []),
            "next_month_duties": kwargs.get('next_month_duties', []),
        }

    if count == 1:
        return Doctor(**get_init_data())

    return [Doctor(**get_init_data()) for _ in range(count)]


class ExpectedError(Exception):
    pass
