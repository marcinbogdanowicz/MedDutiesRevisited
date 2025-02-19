from collections import defaultdict
from copy import deepcopy
from datetime import date
from statistics import mean
from typing import Any
from unittest import TestCase

from algorithm.main import set_duties
from algorithm.tests.utils import input_factory


class E2ETests(TestCase):
    def get_base_input_data(self, doctors_per_duty: int) -> dict[str, Any]:
        input_data = deepcopy(self._base_input_data)
        input_data["unit"]["doctors_per_duty"] = doctors_per_duty
        for doctor_data in input_data["unit"]["doctors"]:
            doctor_data["preferred_positions"] = list(range(doctors_per_duty))

        return input_data

    def get_doctors_on_duty(self, day_number, duties_list) -> list[int]:
        return [
            duty["doctor_pk"] for duty in duties_list if duty["doctor_pk"] is not None and duty["day"] == day_number
        ]

    def get_duties_for_doctor(self, doctor_pk, duties_list) -> list[dict[str, Any]]:
        return [duty for duty in duties_list if duty["doctor_pk"] == doctor_pk]

    def test_success(self):
        input_data = input_factory(doctors_per_duty=3)

        result = set_duties(input_data)

        self.assertTrue(result.get("were_any_duties_set"))
        self.assertTrue(result.get("were_all_duties_set"))
        self.assertListEqual([], result["errors"])

        duties = result["duties"]

        day_numbers_in_1_2025 = set(range(1, 32))
        day_numbers_of_duties = {duty["day"] for duty in duties}
        self.assertSetEqual(day_numbers_in_1_2025, day_numbers_of_duties)

        doctor_pks = [doctor["pk"] for doctor in input_data["doctors"]]

        for duty in duties:
            self.assertIsInstance(duty["day"], int)
            self.assertIn(duty["position"], range(1, input_data["doctors_per_duty"] + 1))
            self.assertIsNone(duty["pk"])
            self.assertIn(duty["doctor_pk"], doctor_pks)
            self.assertFalse(duty["set_by_user"])
            self.assertGreater(duty["strain_points"], 0)

        # Strain and number of duties are +/- even among doctors
        strain_per_doctor = defaultdict(int)
        number_of_duties_per_doctor = defaultdict(int)
        for duty in duties:
            strain_per_doctor[duty["doctor_pk"]] += duty["strain_points"]
            number_of_duties_per_doctor[duty["doctor_pk"]] += 1

        def assert_difference_from_mean_less_equal(accepted_difference_ratio: float, values: list[int]):
            mean_strain = mean(values)
            for strain in values:
                strain_to_mean_difference_ratio = abs(mean_strain - strain) / mean_strain
                self.assertLessEqual(strain_to_mean_difference_ratio, accepted_difference_ratio)

        assert_difference_from_mean_less_equal(0.2, strain_per_doctor.values())
        assert_difference_from_mean_less_equal(0.1, number_of_duties_per_doctor.values())

    def test_preferences_are_respected(self):
        input_data = input_factory(doctors_per_duty=3)

        doctors = input_data["doctors"]

        doctors[0]["preferences"]["requested_days"] = [1, 6, 19]
        doctors[0]["preferences"]["exceptions"] = [2, 3, 4, 5]
        doctors[0]["preferences"]["maximum_accepted_duties"] = 5

        doctors[1]["preferences"]["preferred_positions"] = [3]

        doctors[2]["preferences"]["preferred_weekdays"] = [5, 6]

        doctors[3]["preferences"]["requested_days"] = [20]
        doctors[4]["preferences"]["requested_days"] = [20]
        doctors[5]["preferences"]["requested_days"] = [20]

        result = set_duties(input_data)

        self.assertTrue(result.get("were_any_duties_set"))
        self.assertTrue(result.get("were_all_duties_set"))
        self.assertListEqual([], result["errors"])

        duties = result["duties"]

        for day in doctors[0]["preferences"]["requested_days"]:
            doctors_on_duty = self.get_doctors_on_duty(day, duties)
            self.assertIn(doctors[0]["pk"], doctors_on_duty)

        for day in doctors[0]["preferences"]["exceptions"]:
            doctors_on_duty = self.get_doctors_on_duty(day, duties)
            self.assertNotIn(doctors[0]["pk"], doctors_on_duty)

        doctor_0_duties = self.get_duties_for_doctor(doctors[0]["pk"], duties)
        self.assertLessEqual(len(doctor_0_duties), doctors[0]["preferences"]["maximum_accepted_duties"])

        doctor_0_duty_days = {duty["day"] for duty in doctor_0_duties}
        for day in doctors[0]["preferences"]["requested_days"]:
            self.assertIn(day, doctor_0_duty_days)

        for day in doctors[0]["preferences"]["exceptions"]:
            self.assertNotIn(day, doctor_0_duty_days)

        doctor_1_duties = self.get_duties_for_doctor(doctors[1]["pk"], duties)
        self.assertSetEqual({3}, {duty["position"] for duty in doctor_1_duties})

        doctor_2_duties = self.get_duties_for_doctor(doctors[2]["pk"], duties)
        for duty in doctor_2_duties:
            duty_weekday = date(input_data["year"], input_data["month"], duty["day"]).weekday()
            self.assertIn(duty_weekday, input_data["doctors"][2]["preferences"]["preferred_weekdays"])

        doctors_on_duty_on_20 = [duty["doctor_pk"] for duty in duties if duty["day"] == 20]
        self.assertCountEqual([doctors[3]["pk"], doctors[4]["pk"], doctors[5]["pk"]], doctors_on_duty_on_20)

    def test_not_enough_doctors_error(self):
        input_data = input_factory(doctors_per_duty=3, doctors_count=5)

        result = set_duties(input_data)

        self.assertFalse(result.get("were_any_duties_set"))
        self.assertFalse(result.get("were_all_duties_set"))
        self.assertEqual(1, len(result["errors"]))
        self.assertIn('not enough doctors to fill all positions', result["errors"][0])

    def test_incoherent_preferences_errors(self):
        input_data = input_factory()

        doctors = input_data["doctors"]

        doctors[0]["preferences"]["requested_days"] = [1, 2]

        doctors[1]["preferences"]["requested_days"] = [5]
        doctors[1]["preferences"]["exceptions"] = [5]

        doctors[2]["preferences"]["requested_days"] = [10, 12, 14, 16, 18]
        doctors[2]["preferences"]["maximum_accepted_duties"] = 4

        result = set_duties(input_data)

        self.assertFalse(result.get("were_any_duties_set"))
        self.assertFalse(result.get("were_all_duties_set"))
        self.assertEqual(3, len(result["errors"]))

        self.assertTrue(any('requested double duties on the following days' in error for error in result["errors"]))
        self.assertTrue(
            any('requests and excludes duties on the following dates' in error for error in result["errors"])
        )
        self.assertTrue(
            any('requests duties on 5 days, but would accept only 4' in error for error in result["errors"])
        )

    def test_requested_days_errors(self):
        input_data = input_factory(doctors_per_duty=3, duties_count=3)

        doctors = input_data["doctors"]

        doctors[0]["preferences"]["requested_days"] = [19]
        doctors[1]["preferences"]["requested_days"] = [19]
        doctors[2]["preferences"]["requested_days"] = [19]
        doctors[3]["preferences"]["requested_days"] = [19]

        doctors[4]["preferences"]["requested_days"] = [4]
        duties = input_data["duties"]
        for i, (doctor, duty) in enumerate(zip(doctors[5:], duties), start=1):
            duty["day"] = 4
            duty["doctor_pk"] = doctor["pk"]
            duty["position"] = i

        result = set_duties(input_data)

        self.assertFalse(result.get("were_any_duties_set"))
        self.assertFalse(result.get("were_all_duties_set"))
        self.assertEqual(2, len(result["errors"]))

        self.assertIn('requested duties on day 4, but it was already filled by user', result["errors"][0])
        self.assertIn('Duty on day 19 was requested', result["errors"][1])
        self.assertIn('not enough positions available', result["errors"][1])

    def test_no_available_doctors_error(self):
        input_data = input_factory(doctors_per_duty=2, doctors_count=5)

        doctors = input_data["doctors"]
        doctors[0]["preferences"]["exceptions"] = [11]
        doctors[1]["preferences"]["exceptions"] = [11]
        doctors[2]["preferences"]["exceptions"] = [11]

        doctors[0]["preferences"]["preferred_positions"] = [1]
        doctors[1]["preferences"]["preferred_positions"] = [1]
        doctors[2]["preferences"]["preferred_positions"] = [1]
        doctors[3]["preferences"]["preferred_positions"] = [2]
        doctors[4]["preferences"]["preferred_positions"] = [2]

        result = set_duties(input_data)

        self.assertFalse(result.get("were_any_duties_set"))
        self.assertFalse(result.get("were_all_duties_set"))
        self.assertEqual(1, len(result["errors"]))
        self.assertIn(
            'On the following positions on the following days, there are no doctors available for duty',
            result["errors"][0],
        )

    def test_not_enough_doctors_shared_between_days(self):
        input_data = input_factory(doctors_per_duty=2, doctors_count=5)

        doctors = input_data["doctors"]
        doctors[0]["preferences"]["exceptions"] = [16, 17]
        doctors[1]["preferences"]["exceptions"] = [16, 17]
        doctors[2]["preferences"]["exceptions"] = [16]

        result = set_duties(input_data)

        self.assertEqual(1, len(result["errors"]))
        self.assertIn('On days 16 and 17, position 1, 2, there is 1 doctor less than required.', result["errors"][0])
