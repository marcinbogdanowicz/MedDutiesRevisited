from unittest import TestCase

from algorithm.duty_setter import DutySetter
from algorithm.tests.utils import doctor_factory
from algorithm.validators import (
    BidailyDoctorAvailabilityValidator,
    DailyDoctorAvailabilityValidator,
    DoctorCountValidator,
    PreferencesCoherenceValidator,
    RequestedDaysConflictsValidator,
)


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


class DailyDoctorAvailabilityValidatorTests(TestCase):
    def setUp(self):
        self.year = 2025
        self.month = 1
        self.duty_setter = DutySetter(self.year, self.month, 3)
        self.schedule = self.duty_setter.schedule

        doctors = doctor_factory(4)
        self.duty_setter.add_doctor(*doctors)

        for doctor in doctors:
            doctor.init_preferences(**self.get_kwargs())

        self.doctor_1, self.doctor_2, self.doctor_3, self.doctor_4 = doctors

    def get_kwargs(self):
        return {
            "year": self.year,
            "month": self.month,
            "exceptions": [],
            "requested_days": [],
            "preferred_weekdays": list(range(7)),
            "preferred_positions": [1, 2, 3],
            "maximum_accepted_duties": 15,
        }

    def test_no_errors(self):
        self.doctor_1.preferences.exceptions = [5, 6, 7]

        errors = self.duty_setter._run_validator(DailyDoctorAvailabilityValidator)
        self.assertEqual(0, len(errors))

    def test_position_errors(self):
        doctor_5 = doctor_factory()
        self.duty_setter.add_doctor(doctor_5)
        doctor_5.init_preferences(**self.get_kwargs())
        self.doctor_1.preferences.preferred_positions = [2, 3]
        self.doctor_2.preferences.preferred_positions = [1]
        self.doctor_2.preferences.exceptions = [8]
        self.doctor_3.preferences.preferred_positions = [2, 3]
        self.doctor_4.preferences.preferred_positions = [2, 3]
        doctor_5.preferences.preferred_positions = [2, 3]

        errors = self.duty_setter._run_validator(DailyDoctorAvailabilityValidator)
        self.assertEqual(1, len(errors))
        self.assertIn('there are no doctors available for duty', errors[0])
        self.assertIn('8/1/2025: [1]', errors[0])

    def test_day_errors(self):
        self.doctor_1.preferences.preferred_weekdays = [3]
        self.doctor_2.preferences.exceptions = [8]

        errors = self.duty_setter._run_validator(DailyDoctorAvailabilityValidator)
        self.assertEqual(1, len(errors))
        self.assertIn('not enough doctors are available for duty', errors[0])
        self.assertIn(str(self.doctor_3), errors[0])
        self.assertIn(str(self.doctor_4), errors[0])


class BidailyDoctorAvailabilityValidatorTests(TestCase):
    def setUp(self):
        self.year = 2025
        self.month = 1
        self.duty_setter = DutySetter(self.year, self.month, 3)
        self.schedule = self.duty_setter.schedule

        doctors = doctor_factory(7)
        self.duty_setter.add_doctor(*doctors)

        for doctor in doctors:
            doctor.init_preferences(**self.get_kwargs())

        self.doctor_1, self.doctor_2, self.doctor_3, self.doctor_4, self.doctor_5, self.doctor_6, self.doctor_7 = (
            doctors
        )

    def get_kwargs(self):
        return {
            "year": self.year,
            "month": self.month,
            "exceptions": [],
            "requested_days": [],
            "preferred_weekdays": list(range(7)),
            "preferred_positions": [1, 2, 3],
            "maximum_accepted_duties": 15,
        }

    def test_no_errors(self):
        self.doctor_1.preferences.preferred_positions = [1]
        self.doctor_2.preferences.preferred_positions = [1]
        self.doctor_2.preferences.exceptions = [11]

        for doctor in [self.doctor_3, self.doctor_4, self.doctor_5, self.doctor_6, self.doctor_7]:
            doctor.preferences.preferred_positions = [2, 3]

        errors = self.duty_setter._run_validator(BidailyDoctorAvailabilityValidator)
        self.assertEqual(0, len(errors))

    def test_all_day_pairs_are_checked(self):
        for doctor in [
            self.doctor_1,
            self.doctor_2,
            self.doctor_3,
            self.doctor_4,
            self.doctor_5,
            self.doctor_6,
            self.doctor_7,
        ]:
            doctor.preferences.preferred_positions = [1, 2]

        errors = self.duty_setter._run_validator(BidailyDoctorAvailabilityValidator)
        self.assertEqual(30, len(errors))

        for day_1, day_2, error in zip(range(1, 31), range(2, 32), errors):
            self.assertIn(f'days {day_1} and {day_2}', error)

    def test_missing_doctors_one_position(self):
        self.doctor_1.preferences.preferred_positions = [1]
        self.doctor_2.preferences.preferred_positions = [1]
        self.doctor_2.preferences.exceptions = [11, 12]

        for doctor in [self.doctor_3, self.doctor_4, self.doctor_5, self.doctor_6, self.doctor_7]:
            doctor.preferences.preferred_positions = [2, 3]

        errors = self.duty_setter._run_validator(BidailyDoctorAvailabilityValidator)
        self.assertEqual(1, len(errors))
        self.assertIn('days 11 and 12, position 1', errors[0])
        self.assertIn('1 doctor less', errors[0])
        self.assertIn(f'Available: {self.doctor_1} (pos. 1)', errors[0])

    def test_missing_doctors_two_positions(self):
        for doctor in [self.doctor_1, self.doctor_2, self.doctor_3, self.doctor_4]:
            doctor.preferences.preferred_positions = [1, 3]

        for doctor in [self.doctor_5, self.doctor_6, self.doctor_7]:
            doctor.preferences.preferred_positions = [2]

        self.doctor_2.preferences.exceptions = [11, 12]

        errors = self.duty_setter._run_validator(BidailyDoctorAvailabilityValidator)
        self.assertEqual(1, len(errors))
        self.assertIn('days 11 and 12, position 1, 3', errors[0])
        self.assertIn('1 doctor less', errors[0])

    def test_missing_doctors_overlapping_combinations(self):
        for doctor in [self.doctor_1, self.doctor_2]:
            doctor.preferences.preferred_positions = [1]

        for doctor in [self.doctor_3, self.doctor_4]:
            doctor.preferences.preferred_positions = [2]

        for doctor in [self.doctor_5, self.doctor_6, self.doctor_7]:
            doctor.preferences.preferred_positions = [3]

        self.doctor_2.preferences.exceptions = [11, 12]
        self.doctor_6.preferences.exceptions = [11, 12]
        self.doctor_7.preferences.exceptions = [11]

        errors = self.duty_setter._run_validator(BidailyDoctorAvailabilityValidator)
        self.assertEqual(1, len(errors))
        self.assertIn('days 11 and 12, position 1, 2', errors[0])
        self.assertIn('1 doctor less', errors[0])
