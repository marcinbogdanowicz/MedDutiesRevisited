from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from algorithm.schedule import Schedule

if TYPE_CHECKING:
    from algorithm.doctor import Doctor


@dataclass(frozen=True)
class Result:
    were_any_duties_set: bool
    were_all_duties_set: bool
    errors: list[str]
    duties: Schedule

    def to_dict(self) -> dict[str, Any]:
        return {}  # TODO implement


class DutySetter:
    def __init__(self, year: int, month: int, doctors_per_duty: int) -> None:
        self.duty_positions = doctors_per_duty
        self.schedule = Schedule(month, year, self.duty_positions)

        self.doctors = []

    def add_doctor(self, *doctors: Doctor) -> None:
        self.doctors.extend(doctors)

    def get_doctor(self, pk: int) -> Doctor | None:
        return next((doctor for doctor in self.doctors if doctor.pk == pk), None)

    def set_duties(self) -> None:
        pass  # TODO: Implement setting duties.

    def get_result(self) -> Result:
        pass  # TODO Implement
