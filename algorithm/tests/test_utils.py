from unittest import TestCase
from unittest.mock import Mock, call, patch

from algorithm.duty_setter import DutySetter
from algorithm.enums import StrainModifier, Weekday
from algorithm.schedule import Day, DoctorAvailabilityScheduleRow, DutySchedule
from algorithm.tests.utils import InitDutySetterTestMixin, PreferencesKwargsTestMixin, doctor_factory
from algorithm.utils import (
    AvoidSaturdayAfterThursdayModifier,
    CloseDutiesModifier,
    DoctorAvailabilityHelper,
    DontStealSundaysModifier,
    DutyStrainEvaluator,
    IsThursdayOrdinaryModifier,
    JoinFridayWithSundayModifier,
    NewWeekendModifier,
    NextMonthStrainModifier,
    PreviousMonthStrainModifier,
    RemainingDutiesCountModifier,
    get_max_number_of_duties_for_month,
)


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


class DoctorAvailabilityHelperTests(TestCase):
    def setUp(self):
        self.year = 2025
        self.month = 1
        self.duty_setter = DutySetter(self.year, self.month, 2)
        self.schedule = self.duty_setter.schedule

        doctors = doctor_factory(4)
        self.duty_setter.add_doctor(*doctors)

        for doctor in doctors:
            doctor.init_preferences(**self.get_kwargs())

        self.doctor_1, self.doctor_2, self.doctor_3, self.doctor_4 = doctors

        self.helper = DoctorAvailabilityHelper(self.duty_setter.doctors, self.schedule)

    def get_kwargs(self):
        return {
            "year": self.year,
            "month": self.month,
            "exceptions": [],
            "requested_days": [],
            "preferred_weekdays": list(range(7)),
            "preferred_positions": [1, 2],
            "maximum_accepted_duties": 15,
        }

    def test_no_preferences_and_no_duties(self):
        availability_schedule = self.helper.get_availability_schedule()

        for row in availability_schedule:
            for cell in row:
                self.assertListEqual(cell, [self.doctor_1, self.doctor_2, self.doctor_3, self.doctor_4])

    def test_duties(self):
        self.schedule[1, 1].update(self.doctor_1)
        self.schedule[5, 1].update(self.doctor_2)
        self.schedule[5, 2].update(self.doctor_3)
        self.schedule[11, 1].update(self.doctor_4)  # Saturday
        self.doctor_4.preferences.preferred_weekdays.remove(Weekday.SATURDAY)

        availability_schedule = self.helper.get_availability_schedule()

        self.assertListEqual(availability_schedule[1, 1], [self.doctor_1])
        self.assertListEqual(availability_schedule[1, 2], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[2, 1], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[2, 2], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[4, 1], [self.doctor_1])
        self.assertListEqual(availability_schedule[4, 2], [self.doctor_1])
        self.assertListEqual(availability_schedule[5, 1], [self.doctor_2])
        self.assertListEqual(availability_schedule[5, 2], [self.doctor_3])
        self.assertListEqual(availability_schedule[6, 1], [self.doctor_1, self.doctor_4])
        self.assertListEqual(availability_schedule[6, 2], [self.doctor_1, self.doctor_4])
        self.assertListEqual(availability_schedule[10, 1], [self.doctor_1, self.doctor_2, self.doctor_3])
        self.assertListEqual(availability_schedule[10, 2], [self.doctor_1, self.doctor_2, self.doctor_3])
        self.assertListEqual(availability_schedule[11, 1], [self.doctor_4])
        self.assertListEqual(availability_schedule[11, 2], [self.doctor_1, self.doctor_2, self.doctor_3])
        self.assertListEqual(availability_schedule[12, 1], [self.doctor_1, self.doctor_2, self.doctor_3])
        self.assertListEqual(availability_schedule[12, 2], [self.doctor_1, self.doctor_2, self.doctor_3])

    def test_requested_days(self):
        self.doctor_1.preferences.requested_days = [5, 8]
        self.doctor_1.preferences.preferred_positions = [1]
        self.doctor_2.preferences.requested_days = [5]
        self.doctor_3.preferences.requested_days = [1]
        self.doctor_4.preferences.requested_days = [13]
        self.doctor_4.preferences.preferred_weekdays.remove(Weekday.MONDAY)

        availability_schedule = self.helper.get_availability_schedule()

        self.assertListEqual(availability_schedule[4, 1], [self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[4, 2], [self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[5, 1], [self.doctor_1, self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[5, 2], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[6, 1], [self.doctor_3])
        self.assertListEqual(availability_schedule[6, 1], [self.doctor_3])
        self.assertListEqual(availability_schedule[7, 1], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[7, 2], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[8, 1], [self.doctor_1, self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[8, 2], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[9, 1], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[9, 2], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[12, 1], [self.doctor_1, self.doctor_2, self.doctor_3])
        self.assertListEqual(availability_schedule[12, 2], [self.doctor_2, self.doctor_3])
        self.assertListEqual(availability_schedule[13, 1], [self.doctor_1, self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[13, 2], [self.doctor_2, self.doctor_3, self.doctor_4])
        self.assertListEqual(availability_schedule[14, 1], [self.doctor_1, self.doctor_2, self.doctor_3])
        self.assertListEqual(availability_schedule[14, 2], [self.doctor_2, self.doctor_3])

    def test_preferred_weekdays(self):
        self.doctor_1.preferences.preferred_weekdays = [2]
        self.doctor_1.preferences.requested_days = [2]

        availability_schedule = self.helper.get_availability_schedule()

        self.assertNotIn(self.doctor_1, availability_schedule[1, 1])
        self.assertNotIn(self.doctor_1, availability_schedule[1, 2])
        self.assertIn(self.doctor_1, availability_schedule[2, 1])
        self.assertIn(self.doctor_1, availability_schedule[2, 2])
        self.assertNotIn(self.doctor_1, availability_schedule[3, 1])
        self.assertNotIn(self.doctor_1, availability_schedule[3, 2])

        expected_available_dates = range(8, 32, 7)
        for day in range(4, 32):
            assert_method = self.assertIn if day in expected_available_dates else self.assertNotIn
            assert_method(self.doctor_1, availability_schedule[day, 1])
            assert_method(self.doctor_1, availability_schedule[day, 2])

    def test_preferred_positions(self):
        self.doctor_1.preferences.preferred_positions = [1]
        self.doctor_2.preferences.preferred_positions = [2]
        self.schedule[5, 1].update(self.doctor_2)

        availability_schedule = self.helper.get_availability_schedule()

        for row in availability_schedule:
            if row.day.number != 5:
                self.assertIn(self.doctor_1, row[1])
                self.assertNotIn(self.doctor_1, row[2])

        self.assertNotIn(self.doctor_2, availability_schedule[4, 1])
        self.assertNotIn(self.doctor_2, availability_schedule[4, 2])
        self.assertIn(self.doctor_2, availability_schedule[5, 1])
        self.assertNotIn(self.doctor_2, availability_schedule[5, 2])
        self.assertNotIn(self.doctor_2, availability_schedule[6, 1])
        self.assertNotIn(self.doctor_2, availability_schedule[6, 2])

    def test_exceptions(self):
        self.doctor_1.preferences.exceptions = [1, 2, 3]

        availability_schedule = self.helper.get_availability_schedule()

        for day in range(1, 4):
            self.assertNotIn(self.doctor_1, availability_schedule[day, 1])
            self.assertNotIn(self.doctor_1, availability_schedule[day, 2])

        self.assertIn(self.doctor_1, availability_schedule[5, 1])
        self.assertIn(self.doctor_1, availability_schedule[5, 2])

    def test_previous_month_duties(self):
        self.doctor_1.last_month_duties = [11, 23]

        availability_schedule = self.helper.get_availability_schedule()

        self.assertIn(self.doctor_1, availability_schedule[1, 1])
        self.assertIn(self.doctor_1, availability_schedule[1, 2])

        self.doctor_1.last_month_duties.append(31)
        del self.doctor_1._can_take_duty_on_first_day_of_month

        availability_schedule = self.helper.get_availability_schedule()

        self.assertNotIn(self.doctor_1, availability_schedule[1, 1])
        self.assertNotIn(self.doctor_1, availability_schedule[1, 2])

    def test_next_month_duties(self):
        self.doctor_1.next_month_duties = [11, 23]

        availability_schedule = self.helper.get_availability_schedule()

        self.assertIn(self.doctor_1, availability_schedule[31, 1])
        self.assertIn(self.doctor_1, availability_schedule[31, 2])

        self.doctor_1.next_month_duties.append(1)
        del self.doctor_1._can_take_duty_on_last_day_of_month

        availability_schedule = self.helper.get_availability_schedule()

        self.assertNotIn(self.doctor_1, availability_schedule[31, 1])
        self.assertNotIn(self.doctor_1, availability_schedule[31, 2])

    def test_mix(self):
        self.doctor_1.preferences.preferred_positions = [1]
        self.doctor_1.preferences.preferred_weekdays = [2]
        self.doctor_1.preferences.exceptions = [8]
        self.doctor_1.preferences.requested_days = [9, 16]
        self.schedule[1, 2].update(self.doctor_1)

        availability_schedule = self.helper.get_availability_schedule()

        self.assertNotIn(self.doctor_1, availability_schedule[1, 1])
        self.assertIn(self.doctor_1, availability_schedule[1, 2])
        self.assertNotIn(self.doctor_1, availability_schedule[8, 1])
        self.assertNotIn(self.doctor_1, availability_schedule[8, 2])
        self.assertIn(self.doctor_1, availability_schedule[9, 1])
        self.assertNotIn(self.doctor_1, availability_schedule[9, 2])
        self.assertNotIn(self.doctor_1, availability_schedule[15, 1])
        self.assertNotIn(self.doctor_1, availability_schedule[15, 2])
        self.assertIn(self.doctor_1, availability_schedule[16, 1])
        self.assertNotIn(self.doctor_1, availability_schedule[16, 2])

        for day in [22, 29]:
            self.assertIn(self.doctor_1, availability_schedule[day, 1])
            self.assertNotIn(self.doctor_1, availability_schedule[day, 2])

        for day in {*range(1, 32)} - {1, 8, 9, 15, 16, 22, 29}:
            self.assertNotIn(self.doctor_1, availability_schedule[day, 1])
            self.assertNotIn(self.doctor_1, availability_schedule[day, 2])


class DutyStrainEvaluatorTests(InitDutySetterTestMixin, TestCase):
    year = 2025
    month = 1
    duty_positions = 3
    doctors_count = 7

    def test_previous_month_length(self):
        year_month_expected_result = [(2025, 1, 31), (2025, 3, 28), (2024, 3, 29)]
        for year, month, expected_result in year_month_expected_result:
            evaluator = DutyStrainEvaluator(year, month, self.schedule.positions, self.doctors)
            self.assertEqual(evaluator.previous_month_length, expected_result)

    def test_current_month_length(self):
        year_month_expected_result = [(2025, 1, 31), (2025, 2, 28), (2024, 2, 29), (2025, 12, 31)]
        for year, month, expected_result in year_month_expected_result:
            evaluator = DutyStrainEvaluator(year, month, self.schedule.positions, self.doctors)
            self.assertEqual(evaluator.current_month_length, expected_result)

    def test_average_duties_per_doctor(self):
        evaluator = DutyStrainEvaluator(self.year, self.month, self.schedule.positions, self.doctors)
        self.assertAlmostEqual(13.28, evaluator.average_duties_per_doctor, delta=0.01)

        evaluator = DutyStrainEvaluator(self.year, self.month, self.schedule.positions, self.doctors[:-1])
        self.assertEqual(15.5, evaluator.average_duties_per_doctor)

        evaluator = DutyStrainEvaluator(self.year, 2, 2, self.doctors)
        self.assertEqual(8, evaluator.average_duties_per_doctor)

    def test_average_max_duties_preference(self):
        evaluator = DutyStrainEvaluator(self.year, self.month, self.schedule.positions, self.doctors)
        self.assertEqual(15, evaluator.average_max_duties_preference)

        maximum_accepted_duties_values = list(range(5, 12))
        for doctor, maximum_accepted_duties in zip(self.doctors, maximum_accepted_duties_values):
            doctor.preferences.maximum_accepted_duties = maximum_accepted_duties

        evaluator = DutyStrainEvaluator(self.year, self.month, self.schedule.positions, self.doctors)
        self.assertEqual(8, evaluator.average_max_duties_preference)

        evaluator = DutyStrainEvaluator(self.year, self.month, self.schedule.positions, self.doctors[:-2])
        self.assertEqual(7, evaluator.average_max_duties_preference)

    @patch("algorithm.utils.issubclass", new=Mock(return_value=False))
    def test_get_strain(self):
        evaluator = DutyStrainEvaluator(self.year, self.month, self.schedule.positions, self.doctors)
        day = Day(1, self.month, self.year)

        mock_strain_modifier = Mock()
        mock_strain_modifier.return_value = mock_strain_modifier
        mock_strain_modifier.get.return_value = 1
        evaluator.strain_modifiers = [mock_strain_modifier]

        evaluator._get_strain(day, None, None)
        self.assertEqual(2, len(mock_strain_modifier.mock_calls))
        self.assertEqual(call.get(), mock_strain_modifier.mock_calls[-1])

    @patch("algorithm.utils.issubclass", new=Mock(return_value=False))
    def test_get_strain_table(self):
        evaluator = DutyStrainEvaluator(self.year, self.month, self.schedule.positions, self.doctors)
        day = Day(1, self.month, self.year)

        mock_strain_modifier = Mock()
        mock_strain_modifier.return_value = mock_strain_modifier
        mock_strain_modifier.get.return_value = 1
        evaluator.strain_modifiers = [mock_strain_modifier]

        availability_per_position = DoctorAvailabilityScheduleRow(day, self.duty_positions)
        availability_per_position[1].extend(self.doctors[:3])
        availability_per_position[2].extend(self.doctors[3:5])
        availability_per_position[3].extend(self.doctors)

        strain_table = evaluator.get_strain_table(day, self.schedule, availability_per_position)
        for strain_per_doctor in strain_table.values():
            for strain in strain_per_doctor.values():
                self.assertEqual(day.strain_points + 1, strain)

        self.assertCountEqual(list(strain_table[1].keys()), self.doctors[:3])
        self.assertCountEqual(list(strain_table[2].keys()), self.doctors[3:5])
        self.assertCountEqual(list(strain_table[3].keys()), self.doctors)

        self.assertEqual(14, len(mock_strain_modifier.mock_calls))


class ModifierTestMixin(PreferencesKwargsTestMixin):
    year = 2025
    month = 1
    duty_positions = 3

    def setUp(self):
        self.doctor = doctor_factory()
        self.doctor.init_preferences(**self.get_init_preferences_kwargs())

        self.schedule = DutySchedule(self.month, self.year, self.duty_positions)

    def get_day(self, number: int) -> Day:
        return Day(number, self.month, self.year)


class JoinFridayWithSundayModifierTests(ModifierTestMixin, TestCase):
    def test_applicable(self):
        day = self.get_day(12)
        self.schedule[10, 1].update(self.doctor)

        modifier = JoinFridayWithSundayModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(modifier.modifier, result)

    def test_weekday_factor(self):
        day = self.get_day(11)
        self.schedule[9, 1].update(self.doctor)

        modifier = JoinFridayWithSundayModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(0, result)

    def test_duty_factor(self):
        day = self.get_day(12)

        modifier = JoinFridayWithSundayModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(0, result)

    def test_day_number_no_error(self):
        day = self.get_day(1)

        modifier = JoinFridayWithSundayModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(0, result)


class DontStealSundaysModifierTests(ModifierTestMixin, TestCase):
    def test_applicable(self):
        day = self.get_day(12)

        modifier = DontStealSundaysModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(modifier.modifier, result)

    def test_weekday_factor(self):
        day = self.get_day(11)

        modifier = DontStealSundaysModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(0, result)

    def test_duty_factor(self):
        day = self.get_day(12)
        self.schedule[10, 1].update(self.doctor)

        modifier = DontStealSundaysModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(0, result)

    def test_day_no_error(self):
        day = self.get_day(1)

        modifier = DontStealSundaysModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(0, result)


class AvoidSaturdayAfterThursdayModifierTests(ModifierTestMixin, TestCase):
    def test_applicable(self):
        day = self.get_day(25)
        self.schedule[23, 1].update(self.doctor)

        modifier = AvoidSaturdayAfterThursdayModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(modifier.modifier, result)

    def test_weekday_condition(self):
        day = self.get_day(24)
        self.schedule[22, 1].update(self.doctor)

        modifier = AvoidSaturdayAfterThursdayModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(0, result)

    def test_duty_condition(self):
        day = self.get_day(25)

        modifier = AvoidSaturdayAfterThursdayModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(0, result)

    def test_day_no_error(self):
        day = self.get_day(1)

        modifier = AvoidSaturdayAfterThursdayModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(0, result)


class IsThursdayOrdinaryModifierTests(ModifierTestMixin, TestCase):
    def test_applicable(self):
        day = self.get_day(23)
        self.doctor.preferences.preferred_weekdays = list(range(4))

        modifier = IsThursdayOrdinaryModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(modifier.modifier, result)

    def test_weekday_condition(self):
        day = self.get_day(24)
        self.doctor.preferences.preferred_weekdays = list(range(4))

        modifier = IsThursdayOrdinaryModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(0, result)

    def test_preferred_weekdays_condition(self):
        day = self.get_day(23)
        self.assertFalse(self.doctor.preferences.no_duties_on_weekends)

        modifier = IsThursdayOrdinaryModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(0, result)


class NewWeekendModifierTests(ModifierTestMixin, TestCase):
    def test_not_a_weekend(self):
        day = self.get_day(16)

        modifier = NewWeekendModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(0, result)

    def test_applicable(self):
        for day_number in (17, 18, 19):
            day = self.get_day(day_number)

            modifier = NewWeekendModifier(day, self.doctor, self.schedule)
            result = modifier.get()

            self.assertGreater(result, 0)

    def test_strain_amount(self):
        day = self.get_day(25)

        modifier = NewWeekendModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(modifier.modifier, result)

        self.schedule[17, 1].update(self.doctor)

        result = modifier.get()

        self.assertEqual(2 * modifier.modifier, result)

        self.schedule[12, 2].update(self.doctor)

        result = modifier.get()

        self.assertEqual(3 * modifier.modifier, result)


class RemainingDutiesCountModifierTests(ModifierTestMixin, TestCase):
    def get_modifier(self, duties_count, maximum_accepted_duties, average_duties, average_max_duties):
        day = self.get_day(1)

        self.doctor.preferences.maximum_accepted_duties = maximum_accepted_duties
        for i in range(1, duties_count + 1):
            self.schedule[i, 1].update(self.doctor)

        modifier = RemainingDutiesCountModifier(
            day=day,
            doctor=self.doctor,
            duty_schedule=self.schedule,
            average_duties_per_doctor=average_duties,
            average_max_duties_preference=average_max_duties,
        )
        return modifier.get()

    def test_modifier_no_duties(self):
        day = self.get_day(1)

        modifier = RemainingDutiesCountModifier(
            day=day,
            doctor=self.doctor,
            duty_schedule=self.schedule,
            average_duties_per_doctor=10,
            average_max_duties_preference=10,
        )
        result = modifier.get()

        self.assertEqual(20 * RemainingDutiesCountModifier.modifier, result)

    def test_maximum_accepted_duties_below_average_few_duties(self):
        duties_count = 1
        maximum_accepted_duties = 4
        average_duties = 10
        average_max_duties = average_duties
        result = self.get_modifier(duties_count, maximum_accepted_duties, average_duties, average_max_duties)

        self.assertEqual(-7 * RemainingDutiesCountModifier.modifier, result)  # 4 - 1 - 10 * modifier, positive result

    def test_maximum_accepted_duties_below_average_many_duties(self):
        duties_count = 3
        maximum_accepted_duties = 4
        average_duties = 10
        average_max_duties = average_duties
        result = self.get_modifier(duties_count, maximum_accepted_duties, average_duties, average_max_duties)

        self.assertEqual(-9 * RemainingDutiesCountModifier.modifier, result)  # 4 - 3 - 10 * modifier, positive result

    def test_maximum_accepted_duties_above_average_few_duties(self):
        duties_count = 1
        maximum_accepted_duties = 8
        average_duties = 5
        average_max_duties = average_duties
        result = self.get_modifier(duties_count, maximum_accepted_duties, average_duties, average_max_duties)

        self.assertEqual(-1 * RemainingDutiesCountModifier.modifier, result)  # 8 - 1 - 8 * modifier, positive result

    def test_maximum_accepted_duties_above_average_many_duties(self):
        duties_count = 7
        maximum_accepted_duties = 8
        average_duties = 5
        average_max_duties = average_duties
        result = self.get_modifier(duties_count, maximum_accepted_duties, average_duties, average_max_duties)

        self.assertEqual(-7 * RemainingDutiesCountModifier.modifier, result)  # 8 - 7 - 8 * modifier, positive result

    def test_default_maximum_few_duties(self):
        duties_count = 2
        maximum_accepted_duties = 15
        average_duties = 5
        average_max_duties = 11
        result = self.get_modifier(duties_count, maximum_accepted_duties, average_duties, average_max_duties)

        self.assertEqual(6 * RemainingDutiesCountModifier.modifier, result)  # 15 - 2 - 7 * modifier, negative result

    def test_default_maximum_medium_duties(self):
        duties_count = 7
        maximum_accepted_duties = 15
        average_duties = 5
        average_max_duties = 11
        result = self.get_modifier(duties_count, maximum_accepted_duties, average_duties, average_max_duties)

        self.assertEqual(1 * RemainingDutiesCountModifier.modifier, result)  # 15 - 7 - 7 * modifier, negative result

    def test_default_maximum_many_duties(self):
        duties_count = 12
        maximum_accepted_duties = 15
        average_duties = 5
        average_max_duties = 11
        result = self.get_modifier(duties_count, maximum_accepted_duties, average_duties, average_max_duties)

        self.assertEqual(-4 * RemainingDutiesCountModifier.modifier, result)  # 15 - 12 - 7 * modifier, positive result


class CloseDutiesModifierTests(ModifierTestMixin, TestCase):
    def test_result(self):
        test_data = [
            (3, 5, 7, StrainModifier.TWO_DAYS_APART),
            (2, 5, 8, StrainModifier.THREE_DAYS_APART),
            (1, 5, 9, StrainModifier.FOUR_DAYS_APART),
            (1, 6, 11, 0),
        ]
        for duty_day_1, evaluated_day, duty_day_2, expected_strain_modifier in test_data:
            day = self.get_day(evaluated_day)
            self.schedule[duty_day_1, 1].update(self.doctor)

            modifier = CloseDutiesModifier(day, self.doctor, self.schedule)
            result = modifier.get()

            self.assertEqual(expected_strain_modifier, result)

            self.schedule[duty_day_2, 1].update(self.doctor)

            modifier = CloseDutiesModifier(day, self.doctor, self.schedule)
            result = modifier.get()

            self.assertEqual(2 * expected_strain_modifier, result)

            self.schedule[duty_day_1, 1].update(None)
            self.schedule[duty_day_2, 1].update(None)

    def test_duties_stack_up(self):
        day = self.get_day(17)
        self.schedule[13, 1].update(self.doctor)
        self.schedule[15, 1].update(self.doctor)

        modifier = CloseDutiesModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(StrainModifier.FOUR_DAYS_APART + StrainModifier.TWO_DAYS_APART, result)

    def test_day_after_duty(self):
        day = self.get_day(2)
        self.schedule[1, 1].update(self.doctor)

        modifier = CloseDutiesModifier(day, self.doctor, self.schedule)
        result = modifier.get()

        self.assertEqual(0, result)


class PreviousMonthStrainModifierTests(ModifierTestMixin, TestCase):
    def test_result(self):
        test_data = [
            (1, 30, StrainModifier.TWO_DAYS_APART),
            (1, 29, StrainModifier.THREE_DAYS_APART),
            (1, 28, StrainModifier.FOUR_DAYS_APART),
            (3, 31, StrainModifier.THREE_DAYS_APART),
        ]
        for evaluated_day, last_month_duty, expected_modifier in test_data:
            day = self.get_day(evaluated_day)
            self.doctor.last_month_duties = [last_month_duty]
            modifier = PreviousMonthStrainModifier(
                day=day,
                doctor=self.doctor,
                duty_schedule=self.schedule,
                previous_month_length=31,
                current_month_length=31,
            )
            result = modifier.get()

            self.assertEqual(result, expected_modifier)

    def test_modifiers_stack_up(self):
        day = self.get_day(1)
        self.doctor.last_month_duties = [28, 30]

        modifier = PreviousMonthStrainModifier(
            day=day,
            doctor=self.doctor,
            duty_schedule=self.schedule,
            previous_month_length=31,
            current_month_length=31,
        )
        result = modifier.get()

        self.assertEqual(StrainModifier.TWO_DAYS_APART + StrainModifier.FOUR_DAYS_APART, result)


class NextMonthStrainModifierTests(ModifierTestMixin, TestCase):
    def test_result(self):
        test_data = [
            (31, 2, StrainModifier.TWO_DAYS_APART),
            (31, 3, StrainModifier.THREE_DAYS_APART),
            (31, 4, StrainModifier.FOUR_DAYS_APART),
            (29, 2, StrainModifier.FOUR_DAYS_APART),
        ]

        for evaluated_day, duty_day, expected_modifier in test_data:
            day = self.get_day(evaluated_day)
            self.doctor.next_month_duties = [duty_day]

            modifier = NextMonthStrainModifier(
                day=day,
                doctor=self.doctor,
                duty_schedule=self.schedule,
                previous_month_length=31,
                current_month_length=31,
            )
            result = modifier.get()

            self.assertEqual(expected_modifier, result)

    def test_modifiers_stack_up(self):
        day = self.get_day(31)
        self.doctor.next_month_duties = [2, 4]

        modifier = NextMonthStrainModifier(
            day=day,
            doctor=self.doctor,
            duty_schedule=self.schedule,
            previous_month_length=31,
            current_month_length=31,
        )
        result = modifier.get()

        self.assertEqual(StrainModifier.TWO_DAYS_APART + StrainModifier.FOUR_DAYS_APART, result)
