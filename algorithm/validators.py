from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from functools import cached_property
from typing import TYPE_CHECKING

from algorithm.exceptions import CantSetDutiesError
from algorithm.utils import comma_join

if TYPE_CHECKING:
    from algorithm.doctor import Doctor
    from algorithm.schedule import Schedule


class BaseDutySettingValidator(ABC):
    def __init__(self, schedule: Schedule, doctors: list[Doctor]) -> None:
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
        positions_count = len(self.schedule.position_numbers)
        doctors_count = len(self.doctors)

        minimum_doctors_count = positions_count * 2
        if doctors_count < minimum_doctors_count:
            self.errors.append(
                f'There are not enough doctors to fill all positions. Minimum required: {minimum_doctors_count}, '
                f'actual: {doctors_count}.'
            )


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
        for duty in self.schedule.duties():
            if duty.doctor and duty.set_by_user:
                filled_positions[duty.day.number].add(duty.position)

        return filled_positions

    @cached_property
    def _filled_days(self) -> list[int]:
        def all_positions_filled(position_list):
            return len(position_list) == len(self.schedule.position_numbers)

        return [
            day_number
            for day_number, filled_positions in self._filled_positions_daily.items()
            if all_positions_filled(filled_positions)
        ]
