from collections import defaultdict
from copy import deepcopy
from statistics import mean
from typing import Any
from unittest import TestCase

from algorithm.main import main


class E2ETests(TestCase):
    _base_input_data = {
        "year": 2025,
        "month": 1,
        "unit": {
            "pk": 1,
            "name": "Surgery",
            "doctors_per_duty": 1,
            "doctors": [
                {
                    "pk": 1,
                    "name": "John",
                    "preferences": {
                        "exceptions": [],
                        "preferred_days": [],
                        "preferred_weekdays": [0, 1, 2, 3, 4, 5, 6],
                        "preferred_positions": [0],
                        "maximum_accepted_duties": 15,
                    },
                    "duties": [],
                    "last_month_duties": [],
                    "next_month_duties": [],
                },
                {
                    "pk": 2,
                    "name": "Ben",
                    "preferences": {
                        "exceptions": [],
                        "preferred_days": [],
                        "preferred_weekdays": [0, 1, 2, 3, 4, 5, 6],
                        "preferred_positions": [0],
                        "maximum_accepted_duties": 15,
                    },
                    "duties": [],
                    "last_month_duties": [],
                    "next_month_duties": [],
                },
                {
                    "pk": 3,
                    "name": "George",
                    "preferences": {
                        "exceptions": [],
                        "preferred_days": [],
                        "preferred_weekdays": [0, 1, 2, 3, 4, 5, 6],
                        "preferred_positions": [0],
                        "maximum_accepted_duties": 15,
                    },
                    "duties": [],
                    "last_month_duties": [],
                    "next_month_duties": [],
                },
                {
                    "pk": 4,
                    "name": "Anne",
                    "preferences": {
                        "exceptions": [],
                        "preferred_days": [],
                        "preferred_weekdays": [0, 1, 2, 3, 4, 5, 6],
                        "preferred_positions": [0],
                        "maximum_accepted_duties": 15,
                    },
                    "duties": [],
                    "last_month_duties": [],
                    "next_month_duties": [],
                },
                {
                    "pk": 5,
                    "name": "Hans",
                    "preferences": {
                        "exceptions": [],
                        "preferred_days": [],
                        "preferred_weekdays": [0, 1, 2, 3, 4, 5, 6],
                        "preferred_positions": [0],
                        "maximum_accepted_duties": 15,
                    },
                    "duties": [],
                    "last_month_duties": [],
                    "next_month_duties": [],
                },
                {
                    "pk": 6,
                    "name": "Paul",
                    "preferences": {
                        "exceptions": [],
                        "preferred_days": [],
                        "preferred_weekdays": [0, 1, 2, 3, 4, 5, 6],
                        "preferred_positions": [0],
                        "maximum_accepted_duties": 15,
                    },
                    "duties": [],
                    "last_month_duties": [],
                    "next_month_duties": [],
                },
                {
                    "pk": 7,
                    "name": "Simone",
                    "preferences": {
                        "exceptions": [],
                        "preferred_days": [],
                        "preferred_weekdays": [0, 1, 2, 3, 4, 5, 6],
                        "preferred_positions": [0],
                        "maximum_accepted_duties": 15,
                    },
                    "duties": [],
                    "last_month_duties": [],
                    "next_month_duties": [],
                },
                {
                    "pk": 8,
                    "name": "Mark",
                    "preferences": {
                        "exceptions": [],
                        "preferred_days": [],
                        "preferred_weekdays": [0, 1, 2, 3, 4, 5, 6],
                        "preferred_positions": [0],
                        "maximum_accepted_duties": 15,
                    },
                    "duties": [],
                    "last_month_duties": [],
                    "next_month_duties": [],
                },
                {
                    "pk": 9,
                    "name": "James",
                    "preferences": {
                        "exceptions": [],
                        "preferred_days": [],
                        "preferred_weekdays": [0, 1, 2, 3, 4, 5, 6],
                        "preferred_positions": [0],
                        "maximum_accepted_duties": 15,
                    },
                    "duties": [],
                    "last_month_duties": [],
                    "next_month_duties": [],
                },
            ],
        },
    }

    def get_base_input_data(self, doctors_per_duty: int) -> dict[str, Any]:
        input_data = deepcopy(self._base_input_data)
        input_data["unit"]["doctors_per_duty"] = doctors_per_duty
        for doctor_data in input_data["unit"]["doctors"]:
            doctor_data["preferred_positions"] = list(range(doctors_per_duty))

        return input_data

    def test_success(self):
        input_data = self.get_base_input_data(doctors_per_duty=1)

        first_result = main(input_data)
        second_result = main(input_data)

        for result in (first_result, second_result):
            self.assertIsInstance(result, dict)

            """
            Expected output format:

            {
                "were_any_duties_set": True,
                "were_all_duties_set": True,
                "errors": [],
                "duties": [
                    {
                        "day": 1,
                        "position": 0,
                        "doctor_pk": 2,
                        "strain": 60,
                        "set_manually": False
                    },
                    ...
                ]
            }
            """

            self.assertTrue(result.get("were_any_duties_set"))
            self.assertTrue(result.get("were_all_duties_set"))
            self.assertListEqual([], result.get("errors"))

            duties = result.get("duties")

            day_numbers_in_1_2025 = set(range(1, 32))
            day_numbers_of_duties = {duty.get("day") for duty in duties}
            self.assertSetEqual(day_numbers_in_1_2025, day_numbers_of_duties)

            each_duty_contains_info_about_position = all(isinstance(duty.get("position"), bool) for duty in duties)
            self.assertTrue(each_duty_contains_info_about_position)

            each_duty_contains_info_about_strain = all(duty.get("strain", -1) > 0 for duty in duties)
            self.assertTrue(each_duty_contains_info_about_strain)

            each_duty_contains_info_on_if_it_was_set_manually = all(
                isinstance(duty.get("set_manually"), bool) for duty in duties
            )
            self.assertTrue(each_duty_contains_info_on_if_it_was_set_manually)

            doctors_pks = [doctor["pk"] for doctor in input_data["doctors"]]
            each_duty_contains_a_valid_doctor_pk = all(duty.get("doctor_pk") in doctors_pks for duty in duties)
            self.assertTrue(each_duty_contains_a_valid_doctor_pk)

            # Strain and number of duties are +/- even among doctors
            strain_per_doctor = defaultdict(int)
            number_of_duties_per_doctor = defaultdict(int)
            for duty in duties:
                strain_per_doctor[duty["doctor_pk"]] += duty["strain"]
                number_of_duties_per_doctor[duty["doctor_pk"]] += 1

            def assert_difference_from_mean_less_equal(accepted_difference_ratio: float, values: list[int]):
                mean_strain = mean(values)
                for strain in values:
                    strain_to_mean_difference_ratio = abs(mean_strain - strain) / mean
                    self.assertLessEqual(strain_to_mean_difference_ratio, accepted_difference_ratio)

            assert_difference_from_mean_less_equal(0.5, strain_per_doctor.values())
            assert_difference_from_mean_less_equal(0.5, number_of_duties_per_doctor.values())

        self.assertFalse(first_result == second_result)
