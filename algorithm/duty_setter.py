from __future__ import annotations

import random
from collections import defaultdict, deque
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Any, Iterator

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
        self._assign_duties()

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

        return not self.errors

    def _run_validator(self, validator_class: type[BaseDutySettingValidator]) -> list[str]:
        try:
            validator_class(self.schedule, self.doctors).run()
            return []
        except CantSetDutiesError as exc:
            return exc.errors

    def _assign_requested_duties(self) -> None:
        setter = RequestedDutiesSetter(self.doctors, self.schedule)
        setter.set_duties()

    def _assign_duties(self) -> None:
        algorithm = Algorithm(self.doctors, self.schedule)
        algorithm.set_duties()


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


@dataclass(slots=True)
class Node:
    day_number: int | None
    doctors: tuple[Doctor, ...] | None
    strain: int
    parent: Node | None

    @classmethod
    def get_empty(cls) -> Node:
        return cls(day_number=None, doctors=None, strain=0, parent=None)

    def get_doctors_with_positions(self) -> Iterator[int, int]:
        return ((doctor, position) for doctor, position in enumerate(self.doctors, start=1))

    @cached_property
    def total_strain(self) -> int:
        if self.parent is None:
            return self.strain

        return self.strain + self.parent.total_strain

    @cached_property
    def days_set(self) -> int:
        if self.parent is None:
            return 0

        return 1 + self.parent.days_set


class Algorithm:
    def __init__(self, doctors: list[Doctor], schedule: DutySchedule) -> None:
        self.doctors = doctors
        self.schedule = schedule

        self.frontier = deque()

        self.best_node = None
        self.steps = 0

    def set_duties(self) -> None:
        self._initialize_frontier()

        while True:
            self.steps += 1
            if not self.frontier:
                raise CantSetDutiesError('Could not set duties.')

            node = self.frontier.pop()

            if self._is_best_node(self, node):
                self.best_node = node

            if self._are_all_duties_set(node):
                self.best_node = node
                break

            self._expand(node)

        # TODO: Finish - set duties, control max steps etc.

    def _initialize_frontier(self) -> None:
        initial_node = Node.get_empty()
        self.frontier.append(initial_node)

    def _is_best_node(self, node: Node) -> bool:
        if self.best_node is None:
            return True

        if node.days_set > self.best_node.days_set:
            return True

        if node.days_set == self.best_node.days_set and node.total_strain < self.best_node.total_strain:
            return True

        return False

    def _are_all_duties_set(self, node: Node) -> bool:
        return node.days_set == len(self.schedule)

    def _expand(self, node: Node) -> None:
        nodes = self._get_nodes(node)

        # TODO Add new nodes to the frontier

    def _get_nodes(self, node: Node) -> list[Node]:
        schedule = self._construct_schedule(node)
        # TODO: Finish

    def _construct_schedule(self, node: Node) -> DutySchedule:
        schedule = self.schedule.copy_empty()

        while node.parent:
            for doctor, position in node.get_doctors_with_positions():
                schedule[node.day_number, position].update(doctor)

            node = node.parent

        return schedule
