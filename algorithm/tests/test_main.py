from contextlib import suppress
from unittest import TestCase
from unittest.mock import Mock, patch

from algorithm.duty_setter import Result
from algorithm.main import create_duty_setter, set_duties, validate_data, validate_duties_can_be_set
from algorithm.tests.utils import ExpectedError, input_factory
from algorithm.utils import get_number_of_days_in_month


class SetDutiesFunctionTests(TestCase):
    @patch('algorithm.main.InputSerializer.model_validate', side_effect=ExpectedError)
    def test_data_is_validated(self, mock_model_validate):
        with suppress(ExpectedError):
            set_duties({'test': 'data'})

        mock_model_validate.assert_called_once()

    def test_classes_initialization(self):
        input_data = input_factory(doctors_per_duty=2, duties_count=2)

        validated_data = validate_data(input_data)
        duty_setter = create_duty_setter(validated_data)

        self.assertEqual(input_data["doctors_per_duty"], duty_setter.duty_positions)

        self.assertIsNotNone(duty_setter.schedule)
        schedule = duty_setter.schedule
        self.assertEqual(schedule.year, input_data["year"])
        self.assertEqual(schedule.month, input_data["month"])
        expected_days_count = get_number_of_days_in_month(input_data["year"], input_data["month"])
        self.assertEqual(expected_days_count, schedule.days)
        self.assertEqual(input_data["doctors_per_duty"], schedule.positions)

        for duty_data in input_data["duties"]:
            day = duty_data["day"]
            position = duty_data["position"]

            duty = schedule[day, position]
            self.assertEqual(duty.day.number, day)
            self.assertEqual(duty.position, position)
            self.assertEqual(duty.doctor.pk, duty_data["doctor_pk"])
            self.assertEqual(duty.strain_points, duty_data["strain_points"])
            self.assertEqual(duty.set_by_user, duty_data["set_by_user"])

        self.assertEqual(10, len(duty_setter.doctors))
        for doctor_data in input_data["doctors"]:
            doctor = duty_setter.get_doctor(doctor_data["pk"])
            self.assertEqual(doctor.name, doctor_data["name"])
            self.assertListEqual(doctor.last_month_duties, doctor_data["last_month_duties"])
            self.assertListEqual(doctor.next_month_duties, doctor_data["next_month_duties"])

            preferences_data = doctor_data["preferences"]
            preferences = doctor.preferences
            for name, value in preferences_data.items():
                self.assertEqual(getattr(preferences, name), value)


class ValidateDutiesCanBeSetFunctionTests(TestCase):
    @patch('algorithm.main.InputSerializer.model_validate', side_effect=ExpectedError)
    def test_data_is_validated(self, mock_model_validate):
        with suppress(ExpectedError):
            validate_duties_can_be_set({'test': 'data'})

        mock_model_validate.assert_called_once()

    @patch('algorithm.main.DutySetter._assign_requested_duties')
    @patch('algorithm.main.DutySetter._assign_duties')
    @patch('algorithm.main.DutySetter.get_result', new=Mock(return_value=Result(False, False, [], None)))
    def test_duty_setting_is_not_ran(self, mock_assign_duties, mock_assign_requested_duties):
        input_data = input_factory()

        validate_duties_can_be_set(input_data)

        mock_assign_requested_duties.assert_not_called()
        mock_assign_duties.assert_not_called()

    @patch('algorithm.main.DutySetter.get_result', new=Mock(return_value=Result(False, False, ['Error #1'], None)))
    def test_validation_result(self):
        input_data = input_factory()

        result = validate_duties_can_be_set(input_data)

        self.assertIsInstance(result, dict)
        self.assertListEqual(['Error #1'], result['errors'])
