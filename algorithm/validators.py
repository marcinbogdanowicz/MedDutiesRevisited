from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from algorithm.exceptions import CantSetDutiesError

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


class DoctorsPreferredDaysValidator(BaseDutySettingValidator):
    def perform_validation(self) -> None:
        for doctor in self.doctors:
            self._validate_no_consecutive_dates(doctor)
            self._validate_no_coincidence_with_exceptions(doctor)
            self._validate_enough_duties_are_accepted(doctor)

    def _validate_no_consecutive_dates(self, doctor: Doctor) -> None:
        preferred_days = doctor.preferences.preferred_days

        requested_doubles = []
        for day in preferred_days:
            if day + 1 in preferred_days:
                requested_doubles.append(f'{day} and {day + 1}')

        if requested_doubles:
            doubles_str = ", ".join(requested_doubles)
            self.errors.append(f'{doctor} requested double duties on the following days: {doubles_str}')

    def _validate_no_coincidence_with_exceptions(self, doctor: Doctor) -> None:
        preferences = doctor.preferences

        conflicts = []
        for day in preferences.preferred_days:
            if day in preferences.exceptions:
                conflicts.append(day)

        if conflicts:
            conflicts_str = ', '.join(str(day) for day in conflicts)
            self.errors.append(f'{doctor} prefers and excludes the following dates: {conflicts_str}')

    def _validate_enough_duties_are_accepted(self, doctor: Doctor) -> None:
        preferences = doctor.preferences

        preferred_days_count = len(preferences.preferred_days)
        if preferred_days_count > preferences.maximum_accepted_duties:
            self.errors.append(
                f'{doctor} prefers duties on {preferred_days_count} days, but would accept only '
                f'{preferences.maximum_accepted_duties} duties.'
            )
