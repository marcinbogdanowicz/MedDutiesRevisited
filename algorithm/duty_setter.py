from __future__ import annotations

import random
from collections import defaultdict, deque
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Any, Iterator

from algorithm.exceptions import CantSetDutiesError
from algorithm.schedule import DutySchedule
from algorithm.strain import DutyStrainEvaluator
from algorithm.utils import DoctorAvailabilityHelper, unique_product
from algorithm.validators import (
    BidailyDoctorAvailabilityValidator,
    DailyDoctorAvailabilityValidator,
    DoctorCountValidator,
    PreferencesCoherenceValidator,
    RequestedDaysConflictsValidator,
)

if TYPE_CHECKING:
    from algorithm.doctor import Doctor
    from algorithm.schedule import Day, DoctorAvailabilitySchedule
    from algorithm.validators import BaseDutySettingValidator


@dataclass(frozen=True)
class Result:
    were_any_duties_set: bool
    were_all_duties_set: bool
    errors: list[str]
    duties: DutySchedule

    def to_dict(self) -> dict[str, Any]:
        result = vars(self).copy()
        result["duties"] = self.duties.to_dict()

        return result


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
        self.schedule = DutySchedule(year, month, self.duty_positions)

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

        return Result(
            were_any_duties_set=True,
            were_all_duties_set=self.schedule.is_filled,
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
            position_combinations = list(unique_product(*accepted_positions_per_doctor.values()))

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


@dataclass(frozen=True)
class Node:
    day_number: int | None
    doctors: tuple[Doctor, ...] | None
    strain: int
    parent: Node | None

    @classmethod
    def get_empty(cls) -> Node:
        return cls(day_number=None, doctors=None, strain=0, parent=None)

    def is_empty(self) -> bool:
        return self.day_number is None and self.doctors is None

    def get_doctors_with_positions(self) -> Iterator[Doctor, int]:
        return ((doctor, position) for position, doctor in enumerate(self.doctors, start=1))

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
    max_steps = 1_000

    def __init__(self, doctors: list[Doctor], schedule: DutySchedule, depth: int = 2) -> None:
        self.doctors = doctors
        self.schedule = schedule

        self.frontier = deque()

        self.best_node = None
        self.steps = 0
        self.depth = depth

        self.strain_evaluator = None

    @property
    def combined_doctors_per_position(self) -> int:
        return self.depth * self.schedule.positions

    def set_duties(self) -> None:
        self._initialize_frontier()

        while True:
            self.steps += 1
            if not self.frontier:
                break

            node = self._remove_node_from_frontier()

            if self._is_best_node(node):
                self.best_node = node

            if self._are_all_duties_set(node):
                self.best_node = node
                break

            self._expand(node)

            if self.steps > 2 * len(self.schedule) and self.combined_doctors_per_position < len(self.doctors):
                return Algorithm(self.doctors, self.schedule, self.depth + 1).set_duties()
            elif self.steps > self.max_steps:
                break

        if self.best_node:
            final_schedule = self._construct_schedule(self.best_node)
            self.schedule.merge(final_schedule)

    def _initialize_frontier(self) -> None:
        initial_node = Node.get_empty()
        self.frontier.append(initial_node)

    def _remove_node_from_frontier(self) -> Node:
        return self.frontier.pop()

    def _is_best_node(self, node: Node) -> bool:
        if node.is_empty():
            return False

        if self.best_node is None:
            return True

        if node.days_set > self.best_node.days_set:
            return True

        if node.days_set == self.best_node.days_set and node.total_strain < self.best_node.total_strain:
            return True

        return False

    def _are_all_duties_set(self, node: Node) -> bool:
        return node.days_set == self.schedule.not_filled_rows_count()

    def _expand(self, node: Node) -> None:
        if nodes := self._get_nodes(node):
            first_node = nodes.pop(0)
            self.frontier.append(first_node)
            self.frontier.extendleft(nodes)

    def _get_nodes(self, node: Node) -> list[Node]:
        schedule = self._construct_schedule(node)
        doctor_availability_schedule = DoctorAvailabilityHelper(self.doctors, schedule).get_availability_schedule()

        day = self._get_day_with_least_available_doctors_per_free_position(doctor_availability_schedule)
        available_doctors_per_position = doctor_availability_schedule[day.number]

        available_doctors = available_doctors_per_position.doctors_for_all_positions()
        strain_per_doctor = self._get_strain_per_doctor(day, schedule, available_doctors)

        for available_doctors_list in available_doctors_per_position:
            available_doctors_list.sort(key=lambda doctor: strain_per_doctor[doctor])

        doctors_combinations = unique_product(
            *(
                available_doctors[: self.combined_doctors_per_position]
                for available_doctors in available_doctors_per_position
            )
        )

        if day.number > 1:
            previous_day_doctors = doctor_availability_schedule[day.number - 1].doctors_for_all_positions()
            doctors_combinations = self._drop_conflicting_combinations(doctors_combinations, previous_day_doctors)

        if day.number < len(self.schedule):
            next_day_doctors = doctor_availability_schedule[day.number + 1].doctors_for_all_positions()
            doctors_combinations = self._drop_conflicting_combinations(doctors_combinations, next_day_doctors)

        nodes = [
            Node(
                day_number=day.number,
                doctors=doctors_combination,
                strain=sum(strain_per_doctor[doctor] for doctor in doctors_combination),
                parent=node,
            )
            for doctors_combination in doctors_combinations
        ]
        random.shuffle(nodes)  # Prevent patterns
        nodes.sort(key=lambda node: node.strain)

        return nodes

    def _construct_schedule(self, node: Node) -> DutySchedule:
        schedule = self.schedule.copy()

        while node.parent:
            for doctor, position in node.get_doctors_with_positions():
                schedule[node.day_number, position].update(doctor)

            node = node.parent

        return schedule

    def _get_day_with_least_available_doctors_per_free_position(
        self, availability_schedule: DoctorAvailabilitySchedule
    ) -> Day:
        unset_rows = (row for row in availability_schedule if not row.is_set)
        row_with_least_doctors_per_free_position = min(
            unset_rows,
            key=lambda row: row.average_doctors_per_free_position,
        )
        return row_with_least_doctors_per_free_position.day

    def _get_strain_per_doctor(
        self, day: Day, current_schedule: DutySchedule, available_doctors: list[Doctor]
    ) -> dict[Doctor, int]:
        evaluator = self._get_strain_evaluator()
        return evaluator.get_strains(day, current_schedule, available_doctors)

    def _get_strain_evaluator(self) -> DutyStrainEvaluator:
        if self.strain_evaluator is None:
            self.strain_evaluator = DutyStrainEvaluator(
                self.schedule.year, self.schedule.month, self.schedule.positions, self.doctors
            )

        return self.strain_evaluator

    def _drop_conflicting_combinations(
        self,
        doctors_combinations: list[tuple[Doctor, ...]],
        other_day_doctors: set[Doctor],
    ) -> Iterator[tuple[Doctor, ...]]:
        def is_conflicting_with_other_day_availability(combination: tuple[Doctor, ...]) -> bool:
            return len(other_day_doctors - set(combination)) < self.schedule.positions

        return (
            combination
            for combination in doctors_combinations
            if not is_conflicting_with_other_day_availability(combination)
        )
