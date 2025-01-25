from unittest import TestCase
from unittest.mock import Mock, call, patch

from algorithm.enums import StrainModifier
from algorithm.schedule import Day, DutySchedule
from algorithm.strain import (
    AvoidSaturdayAfterThursdayModifier,
    CloseDutiesModifier,
    DontStealSundaysModifier,
    DutyStrainEvaluator,
    IsThursdayOrdinaryModifier,
    JoinFridayWithSundayModifier,
    NewWeekendModifier,
    NextMonthStrainModifier,
    PreviousMonthStrainModifier,
    RemainingDutiesCountModifier,
)
from algorithm.tests.utils import InitDutySetterTestMixin, PreferencesKwargsTestMixin, doctor_factory


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

    @patch("algorithm.strain.issubclass", new=Mock(return_value=False))
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

    @patch("algorithm.strain.issubclass", new=Mock(return_value=False))
    def test_get_strains(self):
        evaluator = DutyStrainEvaluator(self.year, self.month, self.schedule.positions, self.doctors)
        day = Day(1, self.month, self.year)

        mock_strain_modifier = Mock()
        mock_strain_modifier.return_value = mock_strain_modifier
        mock_strain_modifier.get.return_value = 1
        evaluator.strain_modifiers = [mock_strain_modifier]

        strains = evaluator.get_strains(day, self.schedule, self.doctors)
        self.assertCountEqual(list(strains), self.doctors)
        for strain in strains.values():
            self.assertEqual(day.strain_points + 1, strain)

        self.assertEqual(14, len(mock_strain_modifier.mock_calls))


class ModifierTestMixin(PreferencesKwargsTestMixin):
    year = 2025
    month = 1
    duty_positions = 3

    def setUp(self):
        self.doctor = doctor_factory()
        self.doctor.init_preferences(**self.get_init_preferences_kwargs())

        self.schedule = DutySchedule(self.year, self.month, self.duty_positions)

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
