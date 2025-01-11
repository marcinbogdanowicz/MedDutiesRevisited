from unittest import TestCase

from algorithm.serializers import InputSerializer
from algorithm.tests.utils import input_factory
from algorithm.utils import get_max_number_of_duties_for_month


class SerializersTests(TestCase):
    def setUp(self):
        self.data = input_factory(doctors_count=1, duties_count=2)

    def test_correct_data_validation(self):
        serializer = InputSerializer.model_validate(self.data)
        validated_data = serializer.model_dump()

        self.assertDictEqual(self.data, validated_data)

    def test_type_conversions(self):
        def convert_values_to_string(obj):
            if isinstance(obj, dict):
                return {k: convert_values_to_string(v) for k, v in obj.items()}

            if isinstance(obj, list):
                return [convert_values_to_string(elem) for elem in obj]

            return str(obj) if obj is not None else None

        data_with_string_values = convert_values_to_string(self.data)

        serializer = InputSerializer.model_validate(data_with_string_values)
        validated_data = serializer.model_dump()

        self.assertDictEqual(validated_data, self.data)

    def test_maximum_accepted_duties_adjusted_when_too_high(self):
        self.data["doctors"][0]["preferences"]["maximum_accepted_duties"] = 99

        serializer = InputSerializer.model_validate(self.data)
        validated_data = serializer.model_dump()

        maximum_accepted_duties = validated_data["doctors"][0]["preferences"]["maximum_accepted_duties"]
        expected_maximum_accepted_duties = get_max_number_of_duties_for_month(self.data["month"], self.data["year"])
        self.assertEqual(maximum_accepted_duties, expected_maximum_accepted_duties)

    def test_manually_set_duties_validation(self):
        self.data["duties"][0]["day"] = 32

        with self.assertRaises(ValueError):
            InputSerializer.model_validate(self.data)

        self.data["duties"][0]["day"] = 0

        with self.assertRaises(ValueError):
            InputSerializer.model_validate(self.data)

    def test_preferred_days_validation(self):
        self.data["doctors"][0]["preferences"]["preferred_days"] = [32]

        with self.assertRaises(ValueError):
            InputSerializer.model_validate(self.data)

        self.data["doctors"][0]["preferences"]["preferred_days"] = [0]

        with self.assertRaises(ValueError):
            InputSerializer.model_validate(self.data)

    def test_exceptions_validation(self):
        self.data["doctors"][0]["preferences"]["exceptions"] = [32]

        with self.assertRaises(ValueError):
            InputSerializer.model_validate(self.data)

        self.data["doctors"][0]["preferences"]["exceptions"] = [0]

        with self.assertRaises(ValueError):
            InputSerializer.model_validate(self.data)

    def test_next_month_duties_validation(self):
        self.data["doctors"][0]["next_month_duties"] = [29]

        with self.assertRaises(ValueError):
            InputSerializer.model_validate(self.data)

        self.data["month"] = 12
        self.data["doctors"][0]["next_month_duties"] = [31]

        InputSerializer.model_validate(self.data)

    def test_last_month_duties_validation(self):
        self.data["doctors"][0]["last_month_duties"] = [31]

        InputSerializer.model_validate(self.data)

        self.data["month"] = 3
        self.data["doctors"][0]["last_month_duties"] = [29]

        with self.assertRaises(ValueError):
            InputSerializer.model_validate(self.data)

    def test_month_validation(self):
        self.data["month"] = 0

        with self.assertRaises(ValueError):
            InputSerializer.model_validate(self.data)

        self.data["month"] = 13

        with self.assertRaises(ValueError):
            InputSerializer.model_validate(self.data)

    def test_preferred_positions_validation(self):
        self.data["doctors"][0]["preferences"]["preferred_positions"].append(2)

        with self.assertRaises(ValueError):
            InputSerializer.model_validate(self.data)

    def test_preferred_weekdays_validation(self):
        self.data["doctors"][0]["preferences"]["preferred_weekdays"].append(7)

        with self.assertRaises(ValueError):
            InputSerializer.model_validate(self.data)
