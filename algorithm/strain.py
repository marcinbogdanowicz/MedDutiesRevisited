from __future__ import annotations

import math
from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import TYPE_CHECKING

from algorithm.enums import StrainModifier, Weekday
from algorithm.utils import get_number_of_days_in_month

if TYPE_CHECKING:
    from algorithm.doctor import Doctor
    from algorithm.schedule import Day, DutySchedule


class BaseStrainModifier(ABC):
    modifier: StrainModifier

    def __init__(
        self,
        day: Day,
        doctor: Doctor,
        duty_schedule: DutySchedule,
    ) -> None:
        self.day = day
        self.doctor = doctor
        self.duty_schedule = duty_schedule

    def get(self) -> int:
        if self.should_apply():
            return self.get_modifier()

        return 0

    @abstractmethod
    def should_apply(self) -> bool:
        pass

    def get_modifier(self) -> int:
        return self.modifier


class JoinFridayWithSundayModifier(BaseStrainModifier):
    modifier = StrainModifier.JOIN_FRIDAY_WITH_SUNDAY

    def should_apply(self) -> bool:
        return (
            self.day.weekday == Weekday.SUNDAY
            and self.day.number > 2
            and self.duty_schedule[self.day.number - 2].has_duty(self.doctor)
        )


class DontStealSundaysModifier(BaseStrainModifier):
    modifier = StrainModifier.DONT_STEAL_SUNDAYS

    def should_apply(self) -> bool:
        return (
            self.day.weekday == Weekday.SUNDAY
            and self.day.number > 2
            and not self.duty_schedule[self.day.number - 2].has_duty(self.doctor)
        )


class AvoidSaturdayAfterThursdayModifier(BaseStrainModifier):
    modifier = StrainModifier.AVOID_SATURDAY_AFTER_THURSDAY

    def should_apply(self) -> bool:
        return (
            self.day.weekday == Weekday.SATURDAY
            and self.day.number > 2
            and self.duty_schedule[self.day.number - 2].has_duty(self.doctor)
        )


class IsThursdayOrdinaryModifier(BaseStrainModifier):
    modifier = StrainModifier.THURSDAY_IS_ORDINARY

    def should_apply(self) -> bool:
        # Day off after Thursday wouldn't make any difference.
        return self.day.weekday == Weekday.THURSDAY and self.doctor.preferences.no_duties_on_weekends


class NewWeekendModifier(BaseStrainModifier):
    modifier = StrainModifier.NEW_WEEKEND

    def should_apply(self) -> bool:
        return self.day.weekday in Weekday.weekend()

    def get_modifier(self) -> int:
        result = 0

        weeks_on_duty = self._get_week_numbers_on_duty(self.doctor)
        if self.day.week not in weeks_on_duty:
            result += self.modifier * (len(weeks_on_duty) + 1)

        return result

    def _get_week_numbers_on_duty(self, doctor: Doctor) -> set[int]:
        def is_weekend(row):
            return row.day.weekday in Weekday.weekend()

        return {row.day.week for row in self.duty_schedule if row.has_duty(doctor) and is_weekend(row)}


class AveragesDependentMixin:
    def __init__(
        self,
        average_duties_per_doctor: float,
        average_max_duties_preference: float,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.average_duties_per_doctor = average_duties_per_doctor
        self.average_max_duties_preference = average_max_duties_preference


class RemainingDutiesCountModifier(AveragesDependentMixin, BaseStrainModifier):
    modifier = StrainModifier.DUTY_LEFT

    def should_apply(self) -> bool:
        return True

    def get_modifier(self) -> int:
        max_duties_modifier = self._get_max_duties_modifier(self.doctor)
        duties_count = sum(1 for _ in self.duty_schedule.duties_for_doctor(self.doctor))
        if duties_count:
            remaining_duties_count = self.doctor.preferences.maximum_accepted_duties - duties_count
            return (remaining_duties_count - max_duties_modifier) * self.modifier

        # Encourage giving duties to doctors who haven't received any yet.
        return 20 * self.modifier

    def _get_max_duties_modifier(self, doctor: Doctor) -> int:
        maximum_accepted_duties = doctor.preferences.maximum_accepted_duties
        if maximum_accepted_duties < self.average_max_duties_preference:
            result = self.average_duties_per_doctor
        else:
            result = (
                self.average_duties_per_doctor
                * doctor.preferences.maximum_accepted_duties
                / self.average_max_duties_preference
            )

        return math.ceil(result)


class BaseDutyIntervalModifier(BaseStrainModifier, ABC):
    modifier = None

    @abstractmethod
    def get_modifier(self):
        pass

    def get_strain_for_duty_interval(self, days_interval: int) -> int:
        match days_interval:
            case 1:
                raise ValueError(
                    f'Unexpectedly evaluating a double duty with: {self.day}'
                )  # TODO Remove after testing; doctor should be excluded in availability schedule already
            case 2:
                return StrainModifier.TWO_DAYS_APART
            case 3:
                return StrainModifier.THREE_DAYS_APART
            case 4:
                return StrainModifier.FOUR_DAYS_APART
            case _:
                return 0


class AdjacentMonthStrainModifierMixin:
    def __init__(self, previous_month_length: int, current_month_length: int, **kwargs) -> None:
        super().__init__(**kwargs)

        self.previous_month_length = previous_month_length
        self.current_month_length = current_month_length


class PreviousMonthStrainModifier(AdjacentMonthStrainModifierMixin, BaseDutyIntervalModifier):
    def should_apply(self) -> bool:
        return self.day.number < 5

    def get_modifier(self) -> int:
        result = 0
        for i in range(5 - self.day.number):
            if self.previous_month_length - i in self.doctor.last_month_duties:
                result += self.get_strain_for_duty_interval(self.day.number + i)

        return result


class NextMonthStrainModifier(AdjacentMonthStrainModifierMixin, BaseDutyIntervalModifier):
    def should_apply(self):
        return self.day.number > self.current_month_length - 4

    def get_modifier(self):
        result = 0
        reversed_day_number = self.current_month_length - self.day.number
        for i in range(1, 5 - reversed_day_number):
            if i in self.doctor.next_month_duties:
                result += self.get_strain_for_duty_interval(reversed_day_number + i)

        return result


class CloseDutiesModifier(BaseDutyIntervalModifier):
    def should_apply(self):
        return True

    def get_modifier(self):
        result = 0
        for i in [*range(-4, -1), *range(2, 5)]:
            try:
                row = self.duty_schedule[self.day.number + i]
            except KeyError:
                continue

            if row.has_duty(self.doctor):
                result += self.get_strain_for_duty_interval(abs(i))

        return result


class DutyStrainEvaluator:
    strain_modifiers = [
        JoinFridayWithSundayModifier,
        DontStealSundaysModifier,
        AvoidSaturdayAfterThursdayModifier,
        IsThursdayOrdinaryModifier,
        NewWeekendModifier,
        RemainingDutiesCountModifier,
        PreviousMonthStrainModifier,
        NextMonthStrainModifier,
        CloseDutiesModifier,
    ]

    def __init__(self, year: int, month: int, positions: int, all_doctors: list[Doctor]) -> None:
        self.previous_month_length = self._get_previous_month_length(year, month)
        self.current_month_length = self._get_current_month_length(year, month)

        self.average_duties_per_doctor = self._get_average_duties_per_doctor(positions, all_doctors)
        self.average_max_duties_preference = self._get_average_max_duties_preference(all_doctors)

    def get_strains(self, day: Day, schedule: DutySchedule, available_doctors: list[Doctor]) -> dict[Doctor, int]:
        return {doctor: self._get_strain(day, doctor, schedule) for doctor in available_doctors}

    def _get_strain(self, day: Day, doctor: Doctor, schedule: DutySchedule) -> int:
        strain = day.strain_points

        for modifier_class in self.strain_modifiers:
            modifier = self._init_modifier(modifier_class, day, doctor, schedule)
            strain += modifier.get()

        return strain

    def _init_modifier(
        self, modifier: type[BaseStrainModifier], day: Day, doctor: Doctor, schedule: DutySchedule
    ) -> BaseStrainModifier:
        kwargs = {
            "day": day,
            "doctor": doctor,
            "duty_schedule": schedule,
        }

        if issubclass(modifier, AveragesDependentMixin):
            kwargs["average_duties_per_doctor"] = self.average_duties_per_doctor
            kwargs["average_max_duties_preference"] = self.average_max_duties_preference

        if issubclass(modifier, AdjacentMonthStrainModifierMixin):
            kwargs["previous_month_length"] = self.previous_month_length
            kwargs["current_month_length"] = self.current_month_length

        return modifier(**kwargs)

    def _get_previous_month_length(self, year: int, month: int) -> int:
        prev_month_last_day_dt = date(year, month, 1) - timedelta(days=1)
        return prev_month_last_day_dt.day

    def _get_current_month_length(self, year: int, month: int) -> int:
        return get_number_of_days_in_month(year, month)

    def _get_average_duties_per_doctor(self, positions_count: int, doctors: list[Doctor]) -> float:
        return self.current_month_length * positions_count / len(doctors)

    def _get_average_max_duties_preference(self, doctors: list[Doctor]) -> float:
        return sum(doctor.preferences.maximum_accepted_duties for doctor in doctors) / len(doctors)
