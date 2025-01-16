from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from algorithm.exceptions import CantSetDutiesError
from algorithm.schedule import DutySchedule
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

    def check_if_duties_can_be_set(self) -> None:
        self.errors = []
        for validator_class in self.validator_classes:
            self.errors += self._run_validator(validator_class)

    def _run_validator(self, validator_class: type[BaseDutySettingValidator]) -> list[str]:
        try:
            validator_class(self.schedule, self.doctors).run()
            return []
        except CantSetDutiesError as exc:
            return exc.errors
