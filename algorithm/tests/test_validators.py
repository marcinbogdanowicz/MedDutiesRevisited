from unittest import TestCase

from algorithm.duty_setter import DutySetter
from algorithm.tests.utils import doctor_factory
from algorithm.validators import DoctorCountValidator


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
