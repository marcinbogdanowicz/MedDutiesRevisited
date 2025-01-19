from unittest import TestCase

from algorithm.duty_setter import DutySetter
from algorithm.enums import Weekday
from algorithm.tests.utils import doctor_factory
from algorithm.utils import DoctorAvailabilityHelper, get_max_number_of_duties_for_month


class UtilsTests(TestCase):
    def test_get_max_number_of_duties_per_month(self):
        months_with_expected_results = [
            ((1, 2025), 15),
            ((2, 2025), 14),
            ((3, 2025), 15),
            ((4, 2025), 15),
        ]

        for (month, year), expected_number in months_with_expected_results:
            result = get_max_number_of_duties_for_month(month, year)
            self.assertEqual(result, expected_number)


class DoctorAvailabilityHelperTests(TestCase):
    def setUp(self):
        self.year = 2025
        self.month = 1
        self.duty_setter = DutySetter(self.year, self.month, 2)
        self.schedule = self.duty_setter.schedule

        doctors = doctor_factory(4)
        self.duty_setter.add_doctor(*doctors)

        for doctor in doctors:
            doctor.init_preferences(**self.get_kwargs())

        self.doctor_1, self.doctor_2, self.doctor_3, self.doctor_4 = doctors

        self.helper = DoctorAvailabilityHelper(self.duty_setter.doctors, self.schedule)

    def get_kwargs(self):
        return {
            "year": self.year,
            "month": self.month,
            "exceptions": [],
            "requested_days": [],
            "preferred_weekdays": list(range(7)),
            "preferred_positions": [1, 2],
            "maximum_accepted_duties": 15,
        }

    def test_no_preferences_and_no_duties(self):
        availability_schedule = self.helper.get_availability_schedule()

        for row in availability_schedule:
            for cell in row:
                self.assertListEqual(cell, [self.doctor_1, self.doctor_2, self.doctor_3, self.doctor_4])

    def test_duties(self):
        self.schedule[1, 1].update(self.doctor_1)
        self.schedule[5, 1].update(self.doctor_2)
        self.schedule[5, 2].update(self.doctor_3)
        self.schedule[11, 1].update(self.doctor_4)  # Saturday
        self.doctor_4.preferences.preferred_weekdays.remove(Weekday.SATURDAY)

        availability_schedule = self.helper.get_availability_schedule()

        self.assertListEqual(availability_schedule[1, 1], [self.doctor_1])
        self.assertListEqual(availability_schedule[1, 2], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[2, 1], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[2, 2], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[4, 1], [self.doctor_1])
        self.assertListEqual(availability_schedule[4, 2], [self.doctor_1])
        self.assertListEqual(availability_schedule[5, 1], [self.doctor_2])
        self.assertListEqual(availability_schedule[5, 2], [self.doctor_3])
        self.assertListEqual(availability_schedule[6, 1], [self.doctor_1, self.doctor_4])
        self.assertListEqual(availability_schedule[6, 2], [self.doctor_1, self.doctor_4])
        self.assertListEqual(availability_schedule[10, 1], [self.doctor_1, self.doctor_2, self.doctor_3])
        self.assertListEqual(availability_schedule[10, 2], [self.doctor_1, self.doctor_2, self.doctor_3])
        self.assertListEqual(availability_schedule[11, 1], [self.doctor_4])
        self.assertListEqual(availability_schedule[11, 2], [self.doctor_1, self.doctor_2, self.doctor_3])
        self.assertListEqual(availability_schedule[12, 1], [self.doctor_1, self.doctor_2, self.doctor_3])
        self.assertListEqual(availability_schedule[12, 2], [self.doctor_1, self.doctor_2, self.doctor_3])

    def test_requested_days(self):
        self.doctor_1.preferences.requested_days = [5, 8]
        self.doctor_1.preferences.preferred_positions = [1]
        self.doctor_2.preferences.requested_days = [5]
        self.doctor_3.preferences.requested_days = [1]
        self.doctor_4.preferences.requested_days = [13]
        self.doctor_4.preferences.preferred_weekdays.remove(Weekday.MONDAY)

        availability_schedule = self.helper.get_availability_schedule()

        self.assertListEqual(availability_schedule[4, 1], [self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[4, 2], [self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[5, 1], [self.doctor_1, self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[5, 2], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[6, 1], [self.doctor_3])
        self.assertListEqual(availability_schedule[6, 1], [self.doctor_3])
        self.assertListEqual(availability_schedule[7, 1], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[7, 2], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[8, 1], [self.doctor_1, self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[8, 2], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[9, 1], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[9, 2], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[12, 1], [self.doctor_1, self.doctor_2, self.doctor_3])
        self.assertListEqual(availability_schedule[12, 2], [self.doctor_2, self.doctor_3])
        self.assertListEqual(availability_schedule[13, 1], [self.doctor_1, self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[13, 2], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[14, 1], [self.doctor_1, self.doctor_2, self.doctor_3])
        self.assertListEqual(availability_schedule[14, 2], [self.doctor_2, self.doctor_3])

    def test_preferred_weekdays(self):
        self.doctor_1.preferences.preferred_weekdays = [2]
        self.doctor_1.preferences.requested_days = [2]

        availability_schedule = self.helper.get_availability_schedule()

        self.assertNotIn(self.doctor_1, availability_schedule[1, 1])
        self.assertNotIn(self.doctor_1, availability_schedule[1, 2])
        self.assertIn(self.doctor_1, availability_schedule[2, 1])
        self.assertIn(self.doctor_1, availability_schedule[2, 2])
        self.assertNotIn(self.doctor_1, availability_schedule[3, 1])
        self.assertNotIn(self.doctor_1, availability_schedule[3, 2])

        expected_available_dates = range(8, 32, 7)
        for day in range(4, 32):
            assert_method = self.assertIn if day in expected_available_dates else self.assertNotIn
            assert_method(self.doctor_1, availability_schedule[day, 1])
            assert_method(self.doctor_1, availability_schedule[day, 2])

    def test_preferred_positions(self):
        self.doctor_1.preferences.preferred_positions = [1]
        self.doctor_2.preferences.preferred_positions = [2]
        self.schedule[5, 1].update(self.doctor_2)

        availability_schedule = self.helper.get_availability_schedule()

        for row in availability_schedule:
            if row.day.number != 5:
                self.assertIn(self.doctor_1, row[1])
                self.assertNotIn(self.doctor_1, row[2])

        self.assertNotIn(self.doctor_2, availability_schedule[4, 1])
        self.assertNotIn(self.doctor_2, availability_schedule[4, 2])
        self.assertIn(self.doctor_2, availability_schedule[5, 1])
        self.assertNotIn(self.doctor_2, availability_schedule[5, 2])
        self.assertNotIn(self.doctor_2, availability_schedule[6, 1])
        self.assertNotIn(self.doctor_2, availability_schedule[6, 2])

    def test_exceptions(self):
        self.doctor_1.preferences.exceptions = [1, 2, 3]

        availability_schedule = self.helper.get_availability_schedule()

        for day in range(1, 4):
            self.assertNotIn(self.doctor_1, availability_schedule[day, 1])
            self.assertNotIn(self.doctor_1, availability_schedule[day, 2])

        self.assertIn(self.doctor_1, availability_schedule[5, 1])
        self.assertIn(self.doctor_1, availability_schedule[5, 2])

    def test_previous_month_duties(self):
        self.doctor_1.last_month_duties = [11, 23]

        availability_schedule = self.helper.get_availability_schedule()

        self.assertIn(self.doctor_1, availability_schedule[1, 1])
        self.assertIn(self.doctor_1, availability_schedule[1, 2])

        self.doctor_1.last_month_duties.append(31)
        del self.doctor_1._can_take_duty_on_first_day_of_month

        availability_schedule = self.helper.get_availability_schedule()

        self.assertNotIn(self.doctor_1, availability_schedule[1, 1])
        self.assertNotIn(self.doctor_1, availability_schedule[1, 2])

    def test_next_month_duties(self):
        self.doctor_1.next_month_duties = [11, 23]

        availability_schedule = self.helper.get_availability_schedule()

        self.assertIn(self.doctor_1, availability_schedule[31, 1])
        self.assertIn(self.doctor_1, availability_schedule[31, 2])

        self.doctor_1.next_month_duties.append(1)
        del self.doctor_1._can_take_duty_on_last_day_of_month

        availability_schedule = self.helper.get_availability_schedule()

        self.assertNotIn(self.doctor_1, availability_schedule[31, 1])
        self.assertNotIn(self.doctor_1, availability_schedule[31, 2])

    def test_mix(self):
        self.doctor_1.preferences.preferred_positions = [1]
        self.doctor_1.preferences.preferred_weekdays = [2]
        self.doctor_1.preferences.exceptions = [8]
        self.doctor_1.preferences.requested_days = [9, 16]
        self.schedule[1, 2].update(self.doctor_1)

        availability_schedule = self.helper.get_availability_schedule()

        self.assertNotIn(self.doctor_1, availability_schedule[1, 1])
        self.assertIn(self.doctor_1, availability_schedule[1, 2])
        self.assertNotIn(self.doctor_1, availability_schedule[8, 1])
        self.assertNotIn(self.doctor_1, availability_schedule[8, 2])
        self.assertIn(self.doctor_1, availability_schedule[9, 1])
        self.assertNotIn(self.doctor_1, availability_schedule[9, 2])
        self.assertNotIn(self.doctor_1, availability_schedule[15, 1])
        self.assertNotIn(self.doctor_1, availability_schedule[15, 2])
        self.assertIn(self.doctor_1, availability_schedule[16, 1])
        self.assertNotIn(self.doctor_1, availability_schedule[16, 2])

        for day in [22, 29]:
            self.assertIn(self.doctor_1, availability_schedule[day, 1])
            self.assertNotIn(self.doctor_1, availability_schedule[day, 2])

        for day in {*range(1, 32)} - {1, 8, 9, 15, 16, 22, 29}:
            self.assertNotIn(self.doctor_1, availability_schedule[day, 1])
            self.assertNotIn(self.doctor_1, availability_schedule[day, 2])
