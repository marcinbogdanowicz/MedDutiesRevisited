from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from functools import cached_property
from itertools import combinations
from typing import TYPE_CHECKING

from algorithm.exceptions import CantSetDutiesError
from algorithm.utils import DoctorAvailabilityHelper, comma_join, is_superset_included

if TYPE_CHECKING:
    from algorithm.doctor import Doctor
    from algorithm.schedule import DoctorAvailabilitySchedule, DutySchedule


class BaseDutySettingValidator(ABC):
    def __init__(self, schedule: DutySchedule, doctors: list[Doctor]) -> None:
        self.schedule = schedule
        self.doctors = doctors

        self.errors = []

    def run(self) -> None:
        self.perform_validation()

        if self.errors:
            raise CantSetDutiesError(*self.errors)

    @abstractmethod
    def perform_validation(self) -> None:
        raise NotImplementedError


class DoctorCountValidator(BaseDutySettingValidator):
    def perform_validation(self) -> None:
        doctors_count = len(self.doctors)
        minimum_doctors_count = self.schedule.positions * 2

        if doctors_count < minimum_doctors_count:
            self.errors.append(
                f'There are not enough doctors to fill all positions. Minimum required: {minimum_doctors_count}, '
                f'actual: {doctors_count}.'
            )


class DoctorCountDependentMixin:
    def run(self) -> None:
        try:
            DoctorCountValidator(self.schedule, self.doctors).run()
        except CantSetDutiesError:
            return

        super().run()


class PreferencesCoherenceValidator(BaseDutySettingValidator):
    def perform_validation(self) -> None:
        for doctor in self.doctors:
            self._validate_no_consecutive_dates(doctor)
            self._validate_no_coincidence_with_exceptions(doctor)
            self._validate_enough_duties_are_accepted(doctor)

    def _validate_no_consecutive_dates(self, doctor: Doctor) -> None:
        requested_days = doctor.preferences.requested_days

        requested_doubles = []
        for day in requested_days:
            if day + 1 in requested_days:
                requested_doubles.append(f'{day} and {day + 1}')

        if requested_doubles:
            self.errors.append(
                f'{doctor} requested double duties on the following days: {comma_join(requested_doubles)}'
            )

    def _validate_no_coincidence_with_exceptions(self, doctor: Doctor) -> None:
        preferences = doctor.preferences

        conflicts = []
        for day in preferences.requested_days:
            if day in preferences.exceptions:
                conflicts.append(day)

        if conflicts:
            self.errors.append(f'{doctor} requests and excludes duties on the following dates: {comma_join(conflicts)}')

    def _validate_enough_duties_are_accepted(self, doctor: Doctor) -> None:
        preferences = doctor.preferences

        requested_days_count = len(preferences.requested_days)
        if requested_days_count > preferences.maximum_accepted_duties:
            self.errors.append(
                f'{doctor} requests duties on {requested_days_count} days, but would accept only '
                f'{preferences.maximum_accepted_duties} duties.'
            )


class RequestedDaysConflictsValidator(BaseDutySettingValidator):
    def __init__(self, schedule, doctors) -> None:
        super().__init__(schedule, doctors)
        self._doctors_who_requested_each_day = self._get_doctors_who_requested_each_day()

    def perform_validation(self) -> None:
        self._validate_already_filled_days()
        self._validate_requested_days_can_be_granted()

    def _get_doctors_who_requested_each_day(self) -> dict[int, list[Doctor]]:
        result = defaultdict(list)
        for doctor in self.doctors:
            for day_number in doctor.preferences.requested_days:
                result[day_number].append(doctor)

        return result

    def _validate_already_filled_days(self) -> None:
        requested_days_which_were_already_filled_by_user = set(self._doctors_who_requested_each_day.keys()) & set(
            self._filled_days
        )
        for day_number in requested_days_which_were_already_filled_by_user:
            doctors_who_requested_this_day = self._doctors_who_requested_each_day[day_number]
            self.errors.append(
                f'{comma_join(doctors_who_requested_this_day)} requested duties on day {day_number}, '
                'but it was already filled by user.'
            )

    def _validate_requested_days_can_be_granted(self) -> None:
        requested_days_not_filled_by_user = set(self._doctors_who_requested_each_day.keys()) - set(self._filled_days)

        for day_number in requested_days_not_filled_by_user:
            if not self._can_duties_on_requested_day_be_granted(day_number):
                doctors_who_requested_duties = self._doctors_who_requested_each_day[day_number]
                self.errors.append(
                    f'Duty on day {day_number} was requested by {comma_join(doctors_who_requested_duties)}, '
                    'but there are not enough positions available (due to requesting doctors count, positions conflicts '
                    'or already set duties).'
                )

    def _can_duties_on_requested_day_be_granted(self, day_number: int) -> bool:
        doctors_who_requested_duties = self._doctors_who_requested_each_day[day_number].copy()
        doctors_who_requested_duties.sort(key=lambda doctor: len(doctor.preferences.preferred_positions))

        filled_or_requested_positions = self._filled_positions_daily[day_number].copy()

        for doctors_count, doctor in enumerate(
            doctors_who_requested_duties,
            start=len(filled_or_requested_positions) + 1,  # One for the current doctor
        ):
            filled_or_requested_positions |= set(doctor.preferences.preferred_positions)
            if doctors_count > len(filled_or_requested_positions):
                return False

        return True

    @cached_property
    def _filled_positions_daily(self) -> dict[int, set[int]]:
        filled_positions = defaultdict(set)
        for duty in self.schedule.cells():
            if duty.doctor and duty.set_by_user:
                filled_positions[duty.day.number].add(duty.position)

        return filled_positions

    @cached_property
    def _filled_days(self) -> list[int]:
        def all_positions_filled(position_list):
            return len(position_list) == self.schedule.positions

        return [
            day_number
            for day_number, filled_positions in self._filled_positions_daily.items()
            if all_positions_filled(filled_positions)
        ]


class BaseDoctorAvailabilityValidator(DoctorCountDependentMixin, BaseDutySettingValidator):
    def __init__(self, schedule, doctors):
        super().__init__(schedule, doctors)
        self.availability_schedule = self._get_availability_schedule()

    def _get_availability_schedule(self) -> DoctorAvailabilitySchedule:
        helper = DoctorAvailabilityHelper(self.doctors, self.schedule)
        return helper.get_availability_schedule()


class DailyDoctorAvailabilityValidator(BaseDoctorAvailabilityValidator):
    def perform_validation(self) -> None:
        self._validate_each_position()
        self._validate_each_day()

    def _validate_each_position(self) -> None:
        days_with_missing_doctors = []

        for row in self.availability_schedule:
            day = row.day
            if positions_with_missing_doctors := [
                available_doctors.position for available_doctors in row if not available_doctors
            ]:
                days_with_missing_doctors.append(f'{day}: {positions_with_missing_doctors}')

        if days_with_missing_doctors:
            days_with_positions_str = '; '.join(days_with_missing_doctors)
            self.errors.append(
                'On the following positions on the following days, there are no doctors available for duty: '
                f'{days_with_positions_str}.'
            )

    def _validate_each_day(self) -> None:
        for row in self.availability_schedule:
            available_doctors = row.doctors_for_all_positions()
            if len(available_doctors) < self.availability_schedule.positions:
                available_doctors_str = f' - only: {comma_join(available_doctors)}' if available_doctors else ''
                self.errors.append(f'On {row.day} not enough doctors are available for duty{available_doctors_str}.')


class BidailyDoctorAvailabilityValidator(BaseDoctorAvailabilityValidator):
    def __init__(self, schedule, doctors):
        super().__init__(schedule, doctors)
        self.position_combinations = self._get_position_combinations()

    def perform_validation(self) -> None:
        for day_number in range(1, self.availability_schedule.days):
            self._validate_day(day_number)

    def _validate_day(self, day_number: int) -> None:
        errors: dict[tuple, str] = {}

        for positions_combination in self.position_combinations:
            available_doctors = self._get_available_doctors(day_number, positions_combination)
            missing_doctors = len(positions_combination) * 2 - len(available_doctors)

            if missing_doctors > 0 and not is_superset_included(set(positions_combination), errors.keys()):
                errors[positions_combination] = self._get_error_str(
                    day_number, positions_combination, missing_doctors, available_doctors
                )

        if errors:
            self.errors.extend(errors.values())

    def _get_available_doctors(self, day_number: int, positions: tuple[int]) -> set[Doctor]:
        today = self.availability_schedule[day_number]
        tommorrow = self.availability_schedule[day_number + 1]
        return today.doctors_for_positions(*positions) | tommorrow.doctors_for_positions(*positions)

    def _get_error_str(
        self,
        day_number: int,
        positions_combination: tuple[int, ...],
        missing_count: int,
        available_doctors: set[Doctor],
    ) -> str:
        missing_doctors_pluralized = (
            f'are {missing_count} doctors' if missing_count > 1 else f'is {missing_count} doctor'
        )
        available_doctors_str = (
            comma_join(
                f'{doctor} (pos. {comma_join(doctor.preferences.preferred_positions)})' for doctor in available_doctors
            )
            if available_doctors
            else '-'
        )
        return (
            f'On days {day_number} and {day_number + 1}, position {comma_join(positions_combination)}, '
            f'there {missing_doctors_pluralized} less than required. '
            f'(Available: {available_doctors_str}).'
        )

    def _get_position_combinations(self) -> list[tuple[int, ...]]:
        combs = []
        positions = range(1, self.schedule.positions + 1)
        for i in reversed(positions):
            combs.extend(combinations(positions, i))

        return combs
