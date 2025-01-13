from unittest import TestCase

from algorithm.duty_setter import DutySetter
from algorithm.tests.utils import doctor_factory
from algorithm.validators import DoctorCountValidator, PreferencesCoherenceValidator, RequestedDaysConflictsValidator


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


class PreferencesCoherenceValidatorTests(TestCase):
    def setUp(self):
        self.doctor = doctor_factory()
        self.doctor.init_preferences(
            year=2025,
            month=1,
            exceptions=[],
            requested_days=[],
            preferred_weekdays=list(range(7)),
            preferred_positions=list(range(3)),
            maximum_accepted_duties=10,
        )

        self.duty_setter = DutySetter(2025, 1, 3)
        self.duty_setter.add_doctor(self.doctor)

    def test_consecutive_days_validation(self):
        preferences = self.doctor.preferences
        preferences.requested_days = [1, 3, 5, 7, 11]

        errors = self.duty_setter._run_validator(PreferencesCoherenceValidator)
        self.assertEqual(0, len(errors))

        preferences.requested_days.extend((2, 12))

        errors = self.duty_setter._run_validator(PreferencesCoherenceValidator)
        self.assertEqual(1, len(errors))

        for expected_msg in ['1 and 2', '2 and 3', '11 and 12']:
            self.assertIn(expected_msg, errors[0])

    def test_coincidence_with_exceptions_validation(self):
        preferences = self.doctor.preferences
        preferences.requested_days = [1, 3, 5]
        preferences.exceptions = [2, 4, 6]

        errors = self.duty_setter._run_validator(PreferencesCoherenceValidator)
        self.assertEqual(0, len(errors))

        preferences.exceptions.extend((3, 5))

        errors = self.duty_setter._run_validator(PreferencesCoherenceValidator)
        self.assertEqual(1, len(errors))
        self.assertIn('requests and excludes duties on the following dates: 3, 5', errors[0])

    def test_duties_count_validation(self):
        preferences = self.doctor.preferences
        preferences.requested_days = [1, 3, 5]
        preferences.maximum_accepted_duties = 3

        errors = self.duty_setter._run_validator(PreferencesCoherenceValidator)
        self.assertEqual(0, len(errors))

        preferences.maximum_accepted_duties = 2

        errors = self.duty_setter._run_validator(PreferencesCoherenceValidator)
        self.assertIn('requests duties on 3 days, but would accept only 2 duties.', errors[0])


class RequestedDaysConflictsValidatorTests(TestCase):
    def setUp(self):
        self.year = 2025
        self.month = 1
        self.duty_setter = DutySetter(self.year, self.month, 3)

        self.doctor_1, self.doctor_2, self.doctor_3, self.doctor_4 = doctor_factory(4)
        self.duty_setter.add_doctor(self.doctor_1, self.doctor_2, self.doctor_3, self.doctor_4)

    def get_kwargs(self):
        return {
            "year": self.year,
            "month": self.month,
            "exceptions": [],
            "preferred_weekdays": list(range(7)),
            "maximum_accepted_duties": 15,
        }

    def test_conflicts_same_position(self):
        self.doctor_1.init_preferences(requested_days=[5], preferred_positions=[1], **self.get_kwargs())
        self.doctor_2.init_preferences(requested_days=[5], preferred_positions=[1], **self.get_kwargs())
        self.doctor_3.init_preferences(requested_days=[], preferred_positions=[1, 2, 3], **self.get_kwargs())
        self.doctor_4.init_preferences(requested_days=[], preferred_positions=[1, 2, 3], **self.get_kwargs())

        errors = self.duty_setter._run_validator(RequestedDaysConflictsValidator)
        self.assertEqual(1, len(errors))
        self.assertIn('Duty on day 5', errors[0])
        self.assertIn('there are not enough positions available', errors[0])

    def test_no_conflicts_same_position(self):
        self.doctor_1.init_preferences(requested_days=[5], preferred_positions=[2], **self.get_kwargs())
        self.doctor_2.init_preferences(requested_days=[5], preferred_positions=[1], **self.get_kwargs())
        self.doctor_3.init_preferences(requested_days=[], preferred_positions=[1, 2, 3], **self.get_kwargs())
        self.doctor_4.init_preferences(requested_days=[], preferred_positions=[1, 2, 3], **self.get_kwargs())

        errors = self.duty_setter._run_validator(RequestedDaysConflictsValidator)
        self.assertEqual(0, len(errors))

    def test_conflicts_mixed_positions(self):
        self.doctor_1.init_preferences(requested_days=[5], preferred_positions=[1, 2, 3], **self.get_kwargs())
        self.doctor_2.init_preferences(requested_days=[5], preferred_positions=[1, 3], **self.get_kwargs())
        self.doctor_3.init_preferences(requested_days=[5], preferred_positions=[2, 3], **self.get_kwargs())
        self.doctor_4.init_preferences(requested_days=[5], preferred_positions=[1], **self.get_kwargs())

        errors = self.duty_setter._run_validator(RequestedDaysConflictsValidator)
        self.assertEqual(1, len(errors))
        self.assertIn('Duty on day 5', errors[0])
        self.assertIn('there are not enough positions available', errors[0])

    def test_conflicts_position_ordering(self):
        self.doctor_1.init_preferences(requested_days=[5], preferred_positions=[1], **self.get_kwargs())
        self.doctor_2.init_preferences(requested_days=[5], preferred_positions=[1, 2, 3], **self.get_kwargs())
        self.doctor_3.init_preferences(requested_days=[5], preferred_positions=[1], **self.get_kwargs())
        self.doctor_4.init_preferences(requested_days=[], preferred_positions=[1, 2, 3], **self.get_kwargs())

        errors = self.duty_setter._run_validator(RequestedDaysConflictsValidator)
        self.assertEqual(1, len(errors))
        self.assertIn('Duty on day 5', errors[0])
        self.assertIn('there are not enough positions available', errors[0])

    def test_conflicts_with_duties_set(self):
        self.doctor_1.init_preferences(requested_days=[5], preferred_positions=[1, 2, 3], **self.get_kwargs())
        self.doctor_2.init_preferences(requested_days=[5], preferred_positions=[1, 3], **self.get_kwargs())
        self.doctor_3.init_preferences(requested_days=[], preferred_positions=[2, 3], **self.get_kwargs())
        self.doctor_4.init_preferences(requested_days=[], preferred_positions=[1, 2, 3], **self.get_kwargs())

        self.duty_setter.schedule[5, 2].update(doctor=self.doctor_3, set_by_user=True)

        errors = self.duty_setter._run_validator(RequestedDaysConflictsValidator)
        self.assertEqual(0, len(errors))

        self.doctor_4.preferences.requested_days.append(5)

        errors = self.duty_setter._run_validator(RequestedDaysConflictsValidator)
        self.assertEqual(1, len(errors))
        self.assertIn('Duty on day 5', errors[0])
        self.assertIn('there are not enough positions available', errors[0])

    def test_no_conflicts(self):
        self.doctor_1.init_preferences(requested_days=[5], preferred_positions=[2, 3], **self.get_kwargs())
        self.doctor_2.init_preferences(requested_days=[5], preferred_positions=[1, 3], **self.get_kwargs())
        self.doctor_3.init_preferences(requested_days=[5], preferred_positions=[2], **self.get_kwargs())
        self.doctor_4.init_preferences(requested_days=[], preferred_positions=[1, 2, 3], **self.get_kwargs())

        errors = self.duty_setter._run_validator(RequestedDaysConflictsValidator)
        self.assertEqual(0, len(errors))
