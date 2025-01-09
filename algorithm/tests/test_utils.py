from unittest import TestCase

from algorithm.utils import get_max_number_of_duties_for_month


class UtilsTests(TestCase):
    def test_get_max_number_of_duties_per_month(self):
        months_with_expected_results = [
            ((1, 2025), 15),
            ((2, 2025), 14),
            ((3, 2025), 15),
            ((4, 2025), 15),
        ]

        for (month, year), expected_number in months_with_expected_results:
            result = get_max_number_of_duties_for_month(month, year)
            self.assertEqual(result, expected_number)
