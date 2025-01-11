from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from algorithm.exceptions import CantSetDutiesError
from algorithm.schedule import Schedule
from algorithm.validators import DoctorCountValidator, DoctorsRequestedDaysValidator

if TYPE_CHECKING:
    from algorithm.doctor import Doctor
    from algorithm.validators import BaseDutySettingValidator


@dataclass(frozen=True)
class Result:
    were_any_duties_set: bool
    were_all_duties_set: bool
    errors: list[str]
    duties: Schedule

    def to_dict(self) -> dict[str, Any]:
        return {}  # TODO implement


class DutySetter:
    validator_classes = [DoctorCountValidator, DoctorsRequestedDaysValidator]

    def __init__(self, year: int, month: int, doctors_per_duty: int) -> None:
        self.duty_positions = doctors_per_duty
        self.schedule = Schedule(month, year, self.duty_positions)

        self.doctors = []

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
        pass  # TODO Implement

    def check_if_duties_can_be_set(self) -> None:
        errors = []
        for validator_class in self.validator_classes:
            errors += self._run_validator(validator_class)

    def _run_validator(self, validator_class: type[BaseDutySettingValidator]) -> list[str]:
        try:
            validator_class(self.schedule, self.doctors).run()
            return []
        except CantSetDutiesError as exc:
            return exc.errors
