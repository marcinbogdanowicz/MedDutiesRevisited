import random
from contextlib import suppress
from unittest import TestCase
from unittest.mock import Mock, call, patch

from algorithm.duty_setter import Algorithm, DutySetter, Node
from algorithm.schedule import DutySchedule
from algorithm.tests.utils import ExpectedError, InitDutySetterTestMixin, ScheduleValidator, doctor_factory
from algorithm.utils import DoctorAvailabilityHelper


class DutySetterTests(TestCase):
    def test_init(self):
        setter = DutySetter(2025, 1, 3)
        self.assertEqual(3, setter.duty_positions)
        self.assertIsNotNone(setter.schedule)

        schedule = setter.schedule
        self.assertEqual(31, schedule.days)
        self.assertEqual(3, schedule.positions)

    def test_adding_doctors(self):
        doctor_1, doctor_2 = doctor_factory(2)
        setter = DutySetter(2025, 1, 3)

        setter.add_doctor(doctor_2, doctor_1)

        expected_doctors = [doctor_2, doctor_1]
        self.assertListEqual(setter.doctors, expected_doctors)

    def test_getting_doctors(self):
        doctor_1, doctor_2 = doctor_factory(2)
        setter = DutySetter(2025, 1, 3)

        setter.add_doctor(doctor_2, doctor_1)

        doctor = setter.get_doctor(doctor_2.pk)
        self.assertEqual(doctor_2, doctor)

        doctor = setter.get_doctor(-1)
        self.assertIsNone(doctor)

    @patch('algorithm.duty_setter.DutySetter.check_if_duties_can_be_set', side_effect=ExpectedError)
    def test_validation_is_run_before_setting_duties(self, mock_check_if_duties_can_be_set):
        setter = DutySetter(2025, 1, 3)

        with suppress(ExpectedError):
            setter.set_duties()

        mock_check_if_duties_can_be_set.assert_called_once()

    def test_validation(self):
        setter = DutySetter(2025, 1, 3)

        mock_validator = Mock()
        with patch.object(setter, 'validator_classes', new=[mock_validator]):
            setter.check_if_duties_can_be_set()

        self.assertEqual(2, len(mock_validator.mock_calls))
        self.assertIn(call().run(), mock_validator.mock_calls)

    def test_get_result_without_running_checks(self):
        setter = DutySetter(2025, 1, 3)

        with self.assertRaises(AttributeError):
            setter.get_result()

    def test_get_results_errors_found(self):
        setter = DutySetter(2025, 1, 3)
        setter.set_duties()
        result = setter.get_result()

        self.assertFalse(result.were_all_duties_set)
        self.assertFalse(result.were_any_duties_set)
        self.assertListEqual(
            ['There are not enough doctors to fill all positions. Minimum required: 6, actual: 0.'],
            result.errors,
        )
        self.assertIsInstance(result.duties, DutySchedule)

    @patch('algorithm.duty_setter.RequestedDutiesSetter')
    def test_assign_requested_duties(self, mock_requested_duties_setter):
        setter = DutySetter(2025, 1, 3)
        setter.doctors = 'doctors'
        setter.schedule = 'schedule'

        setter._assign_requested_duties()

        self.assertListEqual(
            mock_requested_duties_setter.mock_calls,
            [call('doctors', 'schedule'), call().set_duties()],
        )


class RequestedDutiesSetterTests(InitDutySetterTestMixin, TestCase):
    year = 2025
    month = 1
    duty_positions = 3
    doctors_count = 4

    def test_duties_assigned_within_accepted_combinations(self):
        self.doctor_1.preferences.requested_days = [5]
        self.doctor_1.preferences.preferred_positions = [1, 2]
        self.doctor_2.preferences.requested_days = [5]
        self.doctor_2.preferences.preferred_positions = [2, 3]
        self.doctor_3.preferences.requested_days = [5]
        self.doctor_3.preferences.preferred_positions = [1]

        self.duty_setter._assign_requested_duties()

        for doctor in [self.doctor_1, self.doctor_2, self.doctor_3]:
            duties = list(self.schedule.duties_for_doctor(doctor))
            self.assertEqual(1, len(duties))
            self.assertEqual(5, duties[0].day.number)
            self.assertIn(duties[0].position, doctor.preferences.preferred_positions)

    def test_set_duties_are_respected(self):
        self.doctor_1.preferences.requested_days = [5]
        self.doctor_1.preferences.preferred_positions = [1, 2]
        self.doctor_2.preferences.requested_days = [5]
        self.doctor_2.preferences.preferred_positions = [2, 3]

        self.schedule[5, 2].update(self.doctor_3)

        self.duty_setter._assign_requested_duties()

        doctor_1_duties = list(self.schedule.duties_for_doctor(self.doctor_1))
        self.assertEqual(1, len(doctor_1_duties))
        self.assertEqual(5, doctor_1_duties[0].day.number)
        self.assertEqual(1, doctor_1_duties[0].position)

        doctor_2_duties = list(self.schedule.duties_for_doctor(self.doctor_2))
        self.assertEqual(1, len(doctor_2_duties))
        self.assertEqual(5, doctor_2_duties[0].day.number)
        self.assertEqual(3, doctor_2_duties[0].position)


class NodeTests(InitDutySetterTestMixin, TestCase):
    year = 2025
    month = 1
    duty_positions = 2
    doctors_count = 5

    def get_random_doctors(self):
        return random.choices(self.doctors, k=self.duty_positions)

    def test_empty(self):
        node = Node.get_empty()
        self.assertIsNone(node.day_number)
        self.assertIsNone(node.parent)
        self.assertIsNone(node.doctors)
        self.assertEqual(0, node.strain)

        self.assertTrue(node.is_empty)

    def test_doctors_with_positions(self):
        node = Node(1, [self.doctor_1, self.doctor_3, self.doctor_2], 100, Node.get_empty())

        expected_values = [(self.doctor_1, 1), (self.doctor_3, 2), (self.doctor_2, 3)]
        self.assertListEqual(expected_values, list(node.get_doctors_with_positions()))

    def test_total_strain(self):
        node_1 = Node.get_empty()
        node_2 = Node(1, self.get_random_doctors(), 100, node_1)
        node_3 = Node(2, self.get_random_doctors(), 200, node_2)

        self.assertEqual(0, node_1.total_strain)
        self.assertEqual(100, node_2.total_strain)
        self.assertEqual(300, node_3.total_strain)

    def test_days_set(self):
        node_1 = Node.get_empty()
        node_2 = Node(1, self.get_random_doctors(), 100, node_1)
        node_3 = Node(2, self.get_random_doctors(), 200, node_2)

        self.assertEqual(0, node_1.days_set)
        self.assertEqual(1, node_2.days_set)
        self.assertEqual(2, node_3.days_set)


class AlgorithmTests(InitDutySetterTestMixin, TestCase):
    year = 2025
    month = 1
    duty_positions = 3
    doctors_count = 7

    def setUp(self):
        super().setUp()

        self.algorithm = Algorithm(self.doctors, self.schedule)

    def get_random_doctors(self):
        return random.choices(self.doctors, k=self.duty_positions)

    def test_initialize_frontier(self):
        self.assertEqual(0, len(self.algorithm.frontier))

        self.algorithm._initialize_frontier()

        self.assertEqual(1, len(self.algorithm.frontier))
        self.assertTrue(self.algorithm.frontier[0].is_empty)

    def test_is_best_node(self):
        empty_node = Node.get_empty()
        node_1 = Node(1, self.get_random_doctors(), 180, empty_node)

        node_2 = Node(1, self.get_random_doctors(), 120, empty_node)
        node_3 = Node(3, self.get_random_doctors(), 100, node_2)

        node_4 = Node(1, self.get_random_doctors(), 80, empty_node)
        node_5 = Node(3, self.get_random_doctors(), 60, node_4)

        self.assertIsNone(self.algorithm.best_node)
        self.assertFalse(self.algorithm._is_best_node(empty_node))

        self.algorithm.best_node = empty_node
        self.assertTrue(self.algorithm._is_best_node(node_1))

        self.algorithm.best_node = node_1
        self.assertTrue(self.algorithm._is_best_node(node_3))

        self.algorithm.best_node = node_3
        self.assertFalse(self.algorithm._is_best_node(node_1))
        self.assertTrue(self.algorithm._is_best_node(node_5))

    def test_are_all_duties_set(self):
        node = Node(1, self.get_random_doctors(), 100, Node.get_empty())

        with patch('algorithm.duty_setter.Node.days_set', new=30):
            self.assertFalse(self.algorithm._are_all_duties_set(node))

        with patch('algorithm.duty_setter.Node.days_set', new=31):
            self.assertTrue(self.algorithm._are_all_duties_set(node))

    def test_node_expansion(self):
        empty_node = Node.get_empty()

        node_1 = Node(1, self.get_random_doctors(), 100, empty_node)
        node_2 = Node(1, self.get_random_doctors(), 100, empty_node)
        node_3 = Node(1, self.get_random_doctors(), 100, empty_node)
        node_4 = Node(1, self.get_random_doctors(), 100, empty_node)
        round_1 = [node_1, node_2, node_3, node_4]

        with patch('algorithm.duty_setter.Algorithm._get_nodes', return_value=round_1):
            self.algorithm._expand(empty_node)

        self.assertListEqual([node_4, node_3, node_2, node_1], list(self.algorithm.frontier))
        self.assertEqual(node_1, self.algorithm._remove_node_from_frontier())

        node_5 = Node(3, self.get_random_doctors(), 100, node_1)
        node_6 = Node(3, self.get_random_doctors(), 100, node_1)
        node_7 = Node(3, self.get_random_doctors(), 100, node_1)
        round_2 = [node_5, node_6, node_7]

        with patch('algorithm.duty_setter.Algorithm._get_nodes', return_value=round_2):
            self.algorithm._expand(empty_node)

        # First one is added to the front, others to the back
        self.assertListEqual([node_7, node_6, node_4, node_3, node_2, node_5], list(self.algorithm.frontier))
        self.assertEqual(node_5, self.algorithm._remove_node_from_frontier())

    def test_construct_schedule(self):
        node_0 = Node.get_empty()
        node_1 = Node(1, [self.doctor_3, self.doctor_1, self.doctor_2], 100, node_0)
        node_2 = Node(2, [self.doctor_7, self.doctor_4, self.doctor_5], 200, node_1)
        node_3 = Node(3, [self.doctor_6, self.doctor_2, self.doctor_1], 150, node_2)

        schedule = self.algorithm._construct_schedule(node_3)

        self.assertEqual(self.doctor_3, schedule[1, 1].doctor)
        self.assertEqual(self.doctor_1, schedule[1, 2].doctor)
        self.assertEqual(self.doctor_2, schedule[1, 3].doctor)
        self.assertEqual(self.doctor_7, schedule[2, 1].doctor)
        self.assertEqual(self.doctor_4, schedule[2, 2].doctor)
        self.assertEqual(self.doctor_5, schedule[2, 3].doctor)
        self.assertEqual(self.doctor_6, schedule[3, 1].doctor)
        self.assertEqual(self.doctor_2, schedule[3, 2].doctor)
        self.assertEqual(self.doctor_1, schedule[3, 3].doctor)

        for day in range(4, 32):
            for position in range(1, 4):
                self.assertFalse(schedule[day, position].is_set)

    def test_day_with_least_available_doctors(self):
        availability_schedule = DoctorAvailabilityHelper(self.doctors, self.schedule).get_availability_schedule()

        day = self.algorithm._get_day_with_least_available_doctors_per_free_position(availability_schedule)
        self.assertEqual(1, day.number)

        availability_schedule[11, 2].pop()

        day = self.algorithm._get_day_with_least_available_doctors_per_free_position(availability_schedule)
        self.assertEqual(11, day.number)

        self.schedule[11, 2].update(self.doctor_1)
        availability_schedule = DoctorAvailabilityHelper(self.doctors, self.schedule).get_availability_schedule()

        day = self.algorithm._get_day_with_least_available_doctors_per_free_position(availability_schedule)
        self.assertEqual(10, day.number)  # Doctor_1 not available on 10 and 12

    def test_dropping_doctor_combinations_conflicting_with_other_day_availability(self):
        combinations = [(self.doctor_1, self.doctor_2, self.doctor_3), (self.doctor_4, self.doctor_5, self.doctor_6)]
        other_day_doctors = {self.doctor_2, self.doctor_5, self.doctor_6, self.doctor_7}

        result = self.algorithm._drop_conflicting_combinations(combinations, other_day_doctors)

        self.assertListEqual(combinations[:1], list(result))

        other_day_doctors.add(self.doctor_1)

        result = self.algorithm._drop_conflicting_combinations(combinations, other_day_doctors)

        self.assertListEqual(combinations, list(result))

    def test_get_nodes(self):
        self.schedule[10, 1].update(self.doctor_1)
        self.schedule[10, 2].update(self.doctor_2)
        self.schedule[10, 3].update(self.doctor_3)
        self.doctor_4.preferences.exceptions = [9]

        node_0 = Node.get_empty()

        nodes = self.algorithm._get_nodes(node_0)

        self.assertSetEqual({9}, {node.day_number for node in nodes})
        for node in nodes:
            self.assertSetEqual({self.doctor_5, self.doctor_6, self.doctor_7}, set(node.doctors))

    def test_get_nodes_dropping_conflicts(self):
        self.schedule[1, 1].update(self.doctor_1)
        self.schedule[1, 2].update(self.doctor_2)
        self.schedule[1, 3].update(self.doctor_3)

        self.doctor_1.preferences.exceptions = [3]
        self.doctor_7.preferences.exceptions = [3]

        node_0 = Node.get_empty()

        nodes = self.algorithm._get_nodes(node_0)

        self.assertGreater(len(nodes), 0)
        for node in nodes:
            self.assertFalse({self.doctor_4, self.doctor_5, self.doctor_6} == set(node.doctors))

    def test_get_nodes_respect_set_duties(self):
        self.schedule[4, 1].update(self.doctor_1)
        self.doctor_2.preferences.exceptions = [4]
        self.doctor_3.preferences.exceptions = [4]

        node_0 = Node.get_empty()

        nodes = self.algorithm._get_nodes(node_0)
        self.assertGreater(len(nodes), 0)
        self.assertEqual(4, nodes[0].day_number)

        for node in nodes:
            self.assertEqual(self.doctor_1, node.doctors[0])

    def test_get_nodes_respect_preferred_positions(self):
        self.doctor_1.preferences.preferred_positions = [1]
        self.doctor_2.preferences.preferred_positions = [2]
        self.doctor_3.preferences.preferred_positions = [3]

        self.doctor_4.preferences.exceptions = [19]
        self.doctor_5.preferences.exceptions = [19]
        self.doctor_6.preferences.exceptions = [19]
        self.doctor_7.preferences.exceptions = [19]

        node_0 = Node.get_empty()

        nodes = self.algorithm._get_nodes(node_0)

        self.assertEqual(1, len(nodes))
        self.assertEqual(self.doctor_1, nodes[0].doctors[0])
        self.assertEqual(self.doctor_2, nodes[0].doctors[1])
        self.assertEqual(self.doctor_3, nodes[0].doctors[2])

    def test_get_nodes_result_ordering(self):
        self.doctor_1.preferences.exceptions = [11]  # Saturday
        self.doctor_2.preferences.exceptions = [11]
        self.doctor_3.preferences.exceptions = [11]

        self.schedule[13, 1].update(self.doctor_4)
        self.schedule[15, 1].update(self.doctor_4)

        self.schedule[13, 2].update(self.doctor_5)

        self.schedule[9, 1].update(self.doctor_6)  # Thursday

        node_0 = Node.get_empty()

        nodes = self.algorithm._get_nodes(node_0)

        strains = sorted({node.strain for node in nodes})
        self.assertGreater(len(strains), 1)
        self.assertEqual(nodes[0].strain, strains[0])
        self.assertEqual(nodes[-1].strain, strains[-1])

        # Check if the order is not the same every time, but ordering by strains is kept
        nodes_other_run = self.algorithm._get_nodes(node_0)
        self.assertNotEqual(nodes, nodes_other_run)
        self.assertSetEqual(set(nodes), set(nodes_other_run))
        self.assertEqual(nodes[0].strain, strains[0])
        self.assertEqual(nodes[-1].strain, strains[-1])

    def test_get_nodes_doctor_count_is_limited_by_depth(self):
        new_doctors = doctor_factory(5)
        for doctor in new_doctors:
            doctor.init_preferences(**self.get_init_preferences_kwargs())

        self.doctors.extend(new_doctors)

        node_0 = Node.get_empty()

        nodes = self.algorithm._get_nodes(node_0)
        self.assertEqual(120, len(nodes))  # With 6 doctors per position, unique combinations count equals 6 * 5 * 4

        self.algorithm.depth = 3
        nodes = self.algorithm._get_nodes(node_0)
        self.assertEqual(504, len(nodes))  # 9 * 8 * 7

        self.algorithm.depth = 4
        nodes = self.algorithm._get_nodes(node_0)
        self.assertEqual(1320, len(nodes))  # 12 * 11 * 10

    def test_setting_duties(self):
        new_doctors = doctor_factory(7)
        for doctor in new_doctors:
            doctor.init_preferences(**self.get_init_preferences_kwargs())

        self.doctors.extend(new_doctors)

        self.schedule[10, 1].update(self.doctor_1, set_by_user=True)  # Friday
        self.schedule[23, 2].update(self.doctor_1, set_by_user=False)  # Thursday, simulate requested day already set

        self.doctor_1.preferences.exceptions = list(range(13, 20))  # Monday - Sunday
        self.doctor_1.preferences.preferred_weekdays.remove(0)
        self.doctor_1.preferences.preferred_positions = [1, 2]
        self.doctor_1.preferences.maximum_accepted_duties = 5

        self.algorithm.set_duties()

        self.assertEqual(self.schedule[10, 1].doctor, self.doctor_1)
        self.assertIn(self.doctor_1, self.schedule[12].doctors)
        self.assertEqual(self.schedule[23, 2].doctor, self.doctor_1)
        self.assertNotEqual(self.schedule[25, 2].doctor, self.doctor_1)

        for day in range(13, 20):
            self.assertNotIn(self.doctor_1, self.schedule[day].doctors)

        doctor_1_duties = list(self.schedule.duties_for_doctor(self.doctor_1))
        self.assertIn(len(doctor_1_duties), range(3, 6))

        ScheduleValidator(self.doctors, self.schedule).assert_no_invalid_duties(
            check_requested_duties=False
        )  # Requested duties are not set by the algorithm

        empty_duties = [duty for duty in self.schedule.cells() if not duty.is_set]
        self.assertEqual(0, len(empty_duties))
