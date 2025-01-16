from contextlib import suppress
from unittest import TestCase
from unittest.mock import Mock, call, patch

from algorithm.duty_setter import DutySetter
from algorithm.schedule import DutySchedule
from algorithm.tests.utils import ExpectedError, doctor_factory


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
