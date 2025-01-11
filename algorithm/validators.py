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
