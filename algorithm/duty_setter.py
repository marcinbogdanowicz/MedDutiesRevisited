from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from algorithm.exceptions import CantSetDutiesError
from algorithm.schedule import DutySchedule
from algorithm.utils import unique_product
from algorithm.validators import (
    BidailyDoctorAvailabilityValidator,
    DailyDoctorAvailabilityValidator,
    DoctorCountValidator,
    PreferencesCoherenceValidator,
    RequestedDaysConflictsValidator,
)

if TYPE_CHECKING:
    from algorithm.doctor import Doctor
    from algorithm.validators import BaseDutySettingValidator


@dataclass(frozen=True)
class Result:
    were_any_duties_set: bool
    were_all_duties_set: bool
    errors: list[str]
    duties: DutySchedule

    def to_dict(self) -> dict[str, Any]:
        return {}  # TODO implement


class DutySetter:
    validator_classes = [
        DoctorCountValidator,
        PreferencesCoherenceValidator,
        RequestedDaysConflictsValidator,
        DailyDoctorAvailabilityValidator,
        BidailyDoctorAvailabilityValidator,
    ]

    def __init__(self, year: int, month: int, doctors_per_duty: int) -> None:
        self.duty_positions = doctors_per_duty
        self.schedule = DutySchedule(month, year, self.duty_positions)

        self.doctors = []
        self.errors = None

    def add_doctor(self, *doctors: Doctor) -> None:
        self.doctors.extend(doctors)

    def get_doctor(self, pk: int) -> Doctor | None:
        return next((doctor for doctor in self.doctors if doctor.pk == pk), None)

    def set_duties(self) -> None:
        # In JS version we used to clear duties first. TODO: check if we need to.
        # We used to clear log here - TODO check if we need to.

        can_be_set = self.check_if_duties_can_be_set()
        if not can_be_set:
            return

        self._assign_requested_duties()

        # TODO: Finish

    def get_result(self) -> Result:
        if self.errors is None:
            raise AttributeError(
                f'{self.get_result.__name__} cannot be called if checks didn\'t run. '
                f'Run either {self.set_duties.__name__} or {self.check_if_duties_can_be_set.__name__} first.'
            )

        if self.errors:
            return Result(
                were_any_duties_set=False,
                were_all_duties_set=False,
                errors=self.errors,
                duties=self.schedule,
            )

    def check_if_duties_can_be_set(self) -> bool:
        self.errors = []
        for validator_class in self.validator_classes:
            self.errors += self._run_validator(validator_class)

        return bool(self.errors)

    def _run_validator(self, validator_class: type[BaseDutySettingValidator]) -> list[str]:
        try:
            validator_class(self.schedule, self.doctors).run()
            return []
        except CantSetDutiesError as exc:
            return exc.errors

    def _assign_requested_duties(self) -> None:
        setter = RequestedDutiesSetter(self.doctors, self.schedule)
        setter.set_duties()


class RequestedDutiesSetter:
    def __init__(self, doctors: list[Doctor], schedule: DutySchedule) -> None:
        self.doctors = doctors
        self.schedule = schedule

    def set_duties(self) -> None:
        daily_accepted_positions_per_doctor = self._get_daily_accepted_positions_per_doctor()

        for day_number, accepted_positions_per_doctor in daily_accepted_positions_per_doctor.items():
            # Combinations elements order will always follow the order of doctors.
            position_combinations = unique_product(*accepted_positions_per_doctor.values())

            positions = random.choice(position_combinations)
            doctors = accepted_positions_per_doctor.keys()

            for doctor, position in zip(doctors, positions):
                self.schedule[day_number, position].update(doctor)

    def _get_daily_accepted_positions_per_doctor(self) -> dict[int, dict[Doctor, list[int]]]:
        result = defaultdict(dict)

        for doctor in self.doctors:
            preferred_positions = set(doctor.preferences.preferred_positions)
            for requested_day in doctor.preferences.requested_days:
                possible_positions = preferred_positions & self.schedule[requested_day].free_positions()
                result[requested_day][doctor] = possible_positions

        return result
