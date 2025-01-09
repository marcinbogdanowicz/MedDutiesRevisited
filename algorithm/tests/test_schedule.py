from unittest import TestCase

from algorithm.doctor import Doctor
from algorithm.enums import DayCategory, StrainPoints
from algorithm.schedule import Day, Duty, Schedule


class ScheduleTests(TestCase):
    def test_schedule_init(self):
        schedule = Schedule(1, 2025, 3)

        day_rows = schedule._cells
        self.assertEqual(31, len(day_rows))
        self.assertTrue(all(len(position_cols) == 3 for position_cols in day_rows.values()))

    def test_accessing_cells(self):
        schedule = Schedule(1, 2025, 3)

        duty = schedule[1, 3]
        self.assertEqual(1, duty.day.number)
        self.assertEqual(3, duty.position)

    def test_immutability(self):
        schedule = Schedule(1, 2025, 3)

        with self.assertRaises(AttributeError):
            schedule[31, 1] = 'tomato'

    def test_acessing_errors(self):
        schedule = Schedule(1, 2025, 3)

        with self.assertRaises(TypeError):
            schedule[0]

        with self.assertRaises(ValueError):
            schedule[1, 2, 3]

        with self.assertRaises(TypeError):
            schedule[1:8]

        with self.assertRaises(KeyError):
            schedule[0, 2]

        with self.assertRaises(KeyError):
            schedule[32, 1]

        with self.assertRaises(KeyError):
            schedule[2, 4]


class DayTests(TestCase):
    def test_category(self):
        day = Day(1, 1, 2025)
        self.assertEqual(DayCategory.HOLIDAY, day.category)

        day = Day(2, 1, 2025)
        self.assertEqual(DayCategory.THURSDAY, day.category)

        for i in range(3, 6):
            day = Day(i, 1, 2025)
            self.assertEqual(DayCategory.WEEKEND, day.category)

        for i in range(13, 16):
            day = Day(i, 1, 2025)
            self.assertEqual(DayCategory.WEEKDAY, day.category)

    def test_strain_points(self):
        expected_results = {
            1: StrainPoints.HOLIDAY,
            2: StrainPoints.THURSDAY,
            3: StrainPoints.FRIDAY,
            4: StrainPoints.SATURDAY,
            5: StrainPoints.SUNDAY,
            6: StrainPoints.HOLIDAY,
            7: StrainPoints.WEEKDAY,
            8: StrainPoints.WEEKDAY,
            13: StrainPoints.WEEKDAY,
        }

        for day_number, expected_strain_points in expected_results.items():
            day = Day(day_number, 1, 2025)
            self.assertEqual(expected_strain_points, day.strain_points)

    def test_week_number(self):
        expected_results = {
            range(1, 6): 0,
            range(6, 13): 1,
            range(13, 20): 2,
            range(20, 27): 3,
            range(27, 32): 4,
        }

        for day_range, expected_week_number in expected_results.items():
            for day_number in day_range:
                day = Day(day_number, 1, 2025)
                self.assertEqual(
                    expected_week_number,
                    day.week,
                    f'{day} is expected to be in week {expected_week_number}.',
                )


class DutyTests(TestCase):
    def test_duty_update(self):
        day = Day(1, 1, 2025)
        duty = Duty(day, 1)
        doctor = Doctor(1, 'John', [], [])

        duty.update(doctor, 2, 20, True)

        self.assertEqual(2, duty.pk)
        self.assertEqual(doctor, duty.doctor)
        self.assertEqual(20, duty.strain_points)
        self.assertTrue(duty.set_by_user)
