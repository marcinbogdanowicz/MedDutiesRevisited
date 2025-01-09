from unittest import TestCase

from algorithm.doctor import Doctor, DoctorsDutyPreferences


class DoctorTests(TestCase):
    def test_init_params(self):
        doctor = Doctor(1, 'John', [1], [31])

        self.assertEqual(1, doctor.pk)
        self.assertEqual('John', doctor.name)
        self.assertIsNone(doctor.preferences)
        self.assertListEqual([1], doctor.last_month_duties)
        self.assertListEqual([31], doctor.next_month_duties)

    def test_init_preferences(self):
        doctor = Doctor(1, 'John')

        month = 1
        year = 2025
        kwargs = {
            'exceptions': [1],
            'preferred_days': [2],
            'preferred_weekdays': [0, 1, 2, 3, 4, 5, 6],
            'preferred_positions': [1],
            'maximum_accepted_duties': 15,
        }
        doctor.init_preferences(
            month=month,
            year=year,
            **kwargs,
        )

        preferences = doctor.preferences

        self.assertIsInstance(preferences, DoctorsDutyPreferences)
        self.assertEqual(month, preferences.month)
        self.assertEqual(year, preferences.year)

        for key, value in kwargs.items():
            if isinstance(value, list):
                self.assertListEqual(value, getattr(preferences, key))

            self.assertEqual(value, getattr(preferences, key))
