from unittest import TestCase

from algorithm.enums import DayCategory, StrainPoints
from algorithm.schedule import Day, Duty, DutySchedule
from algorithm.tests.utils import doctor_factory


class DutyScheduleTests(TestCase):
    def test_schedule_init(self):
        schedule = DutySchedule(1, 2025, 3)

        self.assertEqual(31, schedule.days)
        self.assertEqual(3, schedule.positions)

        self.assertEqual(31, len(schedule))
        self.assertTrue(all(len(row) == 3 for row in schedule))

    def test_accessing_cells(self):
        schedule = DutySchedule(1, 2025, 3)

        duty = schedule.get(1, 3)
        self.assertEqual(1, duty.day.number)
        self.assertEqual(3, duty.position)

        self.assertEqual(duty, schedule[0][2])

    def test_accessing_cells_errors(self):
        schedule = DutySchedule(1, 2025, 3)

        with self.assertRaises(KeyError):
            schedule.get(0, 2)

        with self.assertRaises(KeyError):
            schedule.get(32, 2)

        with self.assertRaises(KeyError):
            schedule.get(3, 0)

        with self.assertRaises(KeyError):
            schedule.get(3, 4)

    def test_immutability(self):
        schedule = DutySchedule(1, 2025, 3)

        with self.assertRaises(AttributeError):
            schedule[0] = ['duty', 'duty', 'duty']

    def test_cells_iterator(self):
        schedule = DutySchedule(1, 2025, 3)

        cells = list(schedule.cells())
        self.assertEqual(93, len(cells))

        unique_days_and_positions = {(cell.day.number, cell.position) for cell in cells}
        self.assertEqual(len(unique_days_and_positions), len(cells))


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
        doctor = doctor_factory()

        duty.update(doctor, 2, 20, True)

        self.assertEqual(2, duty.pk)
        self.assertEqual(doctor, duty.doctor)
        self.assertEqual(20, duty.strain_points)
        self.assertTrue(duty.set_by_user)
