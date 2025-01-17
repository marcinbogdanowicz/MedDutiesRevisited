from contextlib import suppress
from unittest import TestCase
from unittest.mock import Mock, call, patch

from algorithm.duty_setter import DutySetter
from algorithm.schedule import DutySchedule
from algorithm.tests.utils import ExpectedError, InitDutySetterTestMixin, doctor_factory


class DutySetterTests(TestCase):
    def test_init(self):
        setter = DutySetter(2025, 1, 3)
        self.assertEqual(3, setter.duty_positions)
        self.assertIsNotNone(setter.schedule)

        schedule = setter.schedule
        self.assertEqual(31, schedule.days)
        self.assertEqual(3, schedule.positions)

    def test_adding_doctors(self):
        doctor_1, doctor_2 = doctor_factory(2)
        setter = DutySetter(2025, 1, 3)

        setter.add_doctor(doctor_2, doctor_1)

        expected_doctors = [doctor_2, doctor_1]
        self.assertListEqual(setter.doctors, expected_doctors)

    def test_getting_doctors(self):
        doctor_1, doctor_2 = doctor_factory(2)
        setter = DutySetter(2025, 1, 3)

        setter.add_doctor(doctor_2, doctor_1)

        doctor = setter.get_doctor(doctor_2.pk)
        self.assertEqual(doctor_2, doctor)

        doctor = setter.get_doctor(-1)
        self.assertIsNone(doctor)

    @patch('algorithm.duty_setter.DutySetter.check_if_duties_can_be_set', side_effect=ExpectedError)
    def test_validation_is_run_before_setting_duties(self, mock_check_if_duties_can_be_set):
        setter = DutySetter(2025, 1, 3)

        with suppress(ExpectedError):
            setter.set_duties()

        mock_check_if_duties_can_be_set.assert_called_once()

    def test_validation(self):
        setter = DutySetter(2025, 1, 3)

        mock_validator = Mock()
        with patch.object(setter, 'validator_classes', new=[mock_validator]):
            setter.check_if_duties_can_be_set()

        self.assertEqual(2, len(mock_validator.mock_calls))
        self.assertIn(call().run(), mock_validator.mock_calls)

    def test_get_result_without_running_checks(self):
        setter = DutySetter(2025, 1, 3)

        with self.assertRaises(AttributeError):
            setter.get_result()

    def test_get_results_errors_found(self):
        setter = DutySetter(2025, 1, 3)
        setter.set_duties()
        result = setter.get_result()

        self.assertFalse(result.were_all_duties_set)
        self.assertFalse(result.were_any_duties_set)
        self.assertListEqual(
            ['There are not enough doctors to fill all positions. Minimum required: 6, actual: 0.'],
            result.errors,
        )
        self.assertIsInstance(result.duties, DutySchedule)

    @patch('algorithm.duty_setter.RequestedDutiesSetter')
    def test_assign_requested_duties(self, mock_requested_duties_setter):
        setter = DutySetter(2025, 1, 3)
        setter.doctors = 'doctors'
        setter.schedule = 'schedule'

        setter._assign_requested_duties()

        self.assertListEqual(
            mock_requested_duties_setter.mock_calls,
            [call('doctors', 'schedule'), call().set_duties()],
        )


class RequestedDutiesSetterTests(InitDutySetterTestMixin, TestCase):
    year = 2025
    month = 1
    duty_positions = 3
    doctors_count = 4

    def test_duties_assigned_within_accepted_combinations(self):
        self.doctor_1.preferences.requested_days = [5]
        self.doctor_1.preferences.preferred_positions = [1, 2]
        self.doctor_2.preferences.requested_days = [5]
        self.doctor_2.preferences.preferred_positions = [2, 3]
        self.doctor_3.preferences.requested_days = [5]
        self.doctor_3.preferences.preferred_positions = [1]

        self.duty_setter._assign_requested_duties()

        for doctor in [self.doctor_1, self.doctor_2, self.doctor_3]:
            duties = list(self.schedule.duties_for_doctor(doctor))
            self.assertEqual(1, len(duties))
            self.assertEqual(5, duties[0].day.number)
            self.assertIn(duties[0].position, doctor.preferences.preferred_positions)

    def test_set_duties_are_respected(self):
        self.doctor_1.preferences.requested_days = [5]
        self.doctor_1.preferences.preferred_positions = [1, 2]
        self.doctor_2.preferences.requested_days = [5]
        self.doctor_2.preferences.preferred_positions = [2, 3]

        self.schedule[5, 2].update(self.doctor_3)

        self.duty_setter._assign_requested_duties()

        doctor_1_duties = list(self.schedule.duties_for_doctor(self.doctor_1))
        self.assertEqual(1, len(doctor_1_duties))
        self.assertEqual(5, doctor_1_duties[0].day.number)
        self.assertEqual(1, doctor_1_duties[0].position)

        doctor_2_duties = list(self.schedule.duties_for_doctor(self.doctor_2))
        self.assertEqual(1, len(doctor_2_duties))
        self.assertEqual(5, doctor_2_duties[0].day.number)
        self.assertEqual(3, doctor_2_duties[0].position)
