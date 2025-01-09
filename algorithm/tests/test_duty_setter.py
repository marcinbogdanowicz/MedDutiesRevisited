from unittest import TestCase

from algorithm.doctor import Doctor
from algorithm.duty_setter import DutySetter


class DutySetterTests(TestCase):
    def test_init(self):
        setter = DutySetter(2025, 1, 3)
        self.assertEqual(3, setter.duty_positions)
        self.assertIsNotNone(setter.schedule)

        schedule = setter.schedule
        self.assertEqual(31, len(schedule.day_numbers))
        self.assertEqual(3, len(schedule.position_numbers))

    def test_adding_doctors(self):
        doctor_1, doctor_2 = Doctor(1, 'John'), Doctor(2, 'Jane')
        setter = DutySetter(2025, 1, 3)

        setter.add_doctor(doctor_2, doctor_1)

        expected_doctors = [doctor_2, doctor_1]
        self.assertListEqual(setter.doctors, expected_doctors)

    def test_getting_doctors(self):
        doctor_1, doctor_2 = Doctor(1, 'John'), Doctor(2, 'Jane')
        setter = DutySetter(2025, 1, 3)

        setter.add_doctor(doctor_2, doctor_1)

        doctor = setter.get_doctor(2)
        self.assertEqual(doctor_2, doctor)

        doctor = setter.get_doctor(3)
        self.assertIsNone(doctor)
