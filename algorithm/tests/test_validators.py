from unittest import TestCase

from algorithm.duty_setter import DutySetter
from algorithm.tests.utils import doctor_factory
from algorithm.validators import DoctorCountValidator, DoctorsPreferredDaysValidator


class DoctorCountValidatorTests(TestCase):
    def test_doctor_count_validation(self):
        test_data = (
            (1, [doctor_factory()]),
            (3, doctor_factory(5)),
        )
        for duty_positions, initial_doctors in test_data:
            with self.subTest(duty_positions=duty_positions, initial_doctors_count=len(initial_doctors)):
                setter = DutySetter(2025, 1, duty_positions)

                doctor = doctor_factory()
                setter.add_doctor(*initial_doctors)

                errors = setter._run_validator(DoctorCountValidator)
                self.assertEqual(1, len(errors))
                self.assertIn('not enough doctors', errors[0])

                doctor = doctor_factory()
                setter.add_doctor(doctor)

                errors = setter._run_validator(DoctorCountValidator)
                self.assertEqual(0, len(errors))


class PreferredDaysValidatorTests(TestCase):
    def setUp(self):
        self.doctor = doctor_factory()
        self.doctor.init_preferences(
            year=2025,
            month=1,
            exceptions=[],
            preferred_days=[],
            preferred_weekdays=list(range(7)),
            preferred_positions=list(range(3)),
            maximum_accepted_duties=10,
        )

        self.duty_setter = DutySetter(2025, 1, 3)
        self.duty_setter.add_doctor(self.doctor)

    def test_consecutive_days_validation(self):
        preferences = self.doctor.preferences
        preferences.preferred_days = [1, 3, 5, 7, 11]

        errors = self.duty_setter._run_validator(DoctorsPreferredDaysValidator)
        self.assertEqual(0, len(errors))

        preferences.preferred_days.extend((2, 12))

        errors = self.duty_setter._run_validator(DoctorsPreferredDaysValidator)
        self.assertEqual(1, len(errors))

        for expected_msg in ['1 and 2', '2 and 3', '11 and 12']:
            self.assertIn(expected_msg, errors[0])

    def test_coincidence_with_exceptions_validation(self):
        preferences = self.doctor.preferences
        preferences.preferred_days = [1, 3, 5]
        preferences.exceptions = [2, 4, 6]

        errors = self.duty_setter._run_validator(DoctorsPreferredDaysValidator)
        self.assertEqual(0, len(errors))

        preferences.exceptions.extend((3, 5))

        errors = self.duty_setter._run_validator(DoctorsPreferredDaysValidator)
        self.assertEqual(1, len(errors))
        self.assertIn('prefers and excludes the following dates: 3, 5', errors[0])

    def test_duties_count_validation(self):
        preferences = self.doctor.preferences
        preferences.preferred_days = [1, 3, 5]
        preferences.maximum_accepted_duties = 3

        errors = self.duty_setter._run_validator(DoctorsPreferredDaysValidator)
        self.assertEqual(0, len(errors))

        preferences.maximum_accepted_duties = 2

        errors = self.duty_setter._run_validator(DoctorsPreferredDaysValidator)
        self.assertIn('prefers duties on 3 days, but would accept only 2 duties.', errors[0])
