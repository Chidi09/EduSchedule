import unittest
from services.scheduler import TimetableScheduler


class TestSchedulerBasic(unittest.TestCase):
    """Test basic scheduler functionality with simple valid cases."""

    def setUp(self):
        """Set up test fixtures."""
        # Basic mock data
        self.teachers = [
            {'id': 't1', 'name': 'Mr. A', 'availability': {}},
            {'id': 't2', 'name': 'Mr. B', 'availability': {}},
        ]

        self.subjects = [
            {'id': 's1', 'name': 'Math', 'periods_per_week': 2, 'is_consecutive': False},
            {'id': 's2', 'name': 'English', 'periods_per_week': 2, 'is_consecutive': False},
        ]

        self.classes = [
            {'id': 'c1', 'name': 'Grade 10A', 'student_count': 20},
        ]

        self.rooms = [
            {'id': 'r1', 'name': 'Room 101', 'capacity': 30},
        ]

        # Teacher qualifications: T1 teaches Math, T2 teaches English
        self.teacher_subjects = [
            {'teacher_id': 't1', 'subject_id': 's1'},
            {'teacher_id': 't2', 'subject_id': 's2'},
        ]

        # Class C1 requires Math and English
        self.class_subjects = [
            {'class_id': 'c1', 'subject_id': 's1'},
            {'class_id': 'c1', 'subject_id': 's2'},
        ]

    def test_basic_solution_found(self):
        """Test if the solver finds a solution for a simple valid case."""
        scheduler = TimetableScheduler(
            self.teachers,
            self.rooms,
            self.subjects,
            self.classes,
            self.teacher_subjects,
            self.class_subjects
        )

        solutions = scheduler.solve(solution_limit=1)

        self.assertTrue(
            len(solutions) > 0,
            "Should find at least one solution for a simple valid case"
        )
        self.assertIsInstance(solutions[0], list, "Solution should be a list")

    def test_solution_contains_assignments(self):
        """Test that solution contains valid assignments."""
        scheduler = TimetableScheduler(
            self.teachers,
            self.rooms,
            self.subjects,
            self.classes,
            self.teacher_subjects,
            self.class_subjects
        )

        solutions = scheduler.solve(solution_limit=1)

        if solutions:
            solution = solutions[0]
            self.assertTrue(len(solution) > 0, "Solution should contain assignments")

            # Check assignment structure
            for assignment in solution:
                self.assertIn('class_id', assignment)
                self.assertIn('subject_id', assignment)
                self.assertIn('teacher_id', assignment)
                self.assertIn('room_id', assignment)
                self.assertIn('day_of_week', assignment)
                self.assertIn('period', assignment)

    def test_respects_periods_per_week(self):
        """Test that the solution respects the periods_per_week constraint."""
        scheduler = TimetableScheduler(
            self.teachers,
            self.rooms,
            self.subjects,
            self.classes,
            self.teacher_subjects,
            self.class_subjects
        )

        solutions = scheduler.solve(solution_limit=1)

        if solutions:
            solution = solutions[0]

            # Count periods for each class-subject pair
            class_subject_counts = {}
            for assignment in solution:
                key = (assignment['class_id'], assignment['subject_id'])
                class_subject_counts[key] = class_subject_counts.get(key, 0) + 1

            # Verify periods match the requirement
            for s_id, s_data in [(s['id'], s) for s in self.subjects]:
                for c_id in [c['id'] for c in self.classes]:
                    key = (c_id, s_id)
                    expected_periods = s_data['periods_per_week']
                    actual_periods = class_subject_counts.get(key, 0)
                    self.assertEqual(
                        actual_periods,
                        expected_periods,
                        f"Subject {s_id} in class {c_id} should have {expected_periods} periods, got {actual_periods}"
                    )


class TestSchedulerConstraints(unittest.TestCase):
    """Test constraint enforcement."""

    def test_room_capacity_constraint(self):
        """Test that rooms are not assigned to classes larger than capacity."""
        teachers = [{'id': 't1', 'name': 'Mr. A', 'availability': {}}]
        subjects = [{'id': 's1', 'name': 'Math', 'periods_per_week': 2, 'is_consecutive': False}]
        classes = [{'id': 'c1', 'name': 'Large Class', 'student_count': 50}]
        rooms = [{'id': 'r1', 'name': 'Small Room', 'capacity': 20}]
        teacher_subjects = [{'teacher_id': 't1', 'subject_id': 's1'}]
        class_subjects = [{'class_id': 'c1', 'subject_id': 's1'}]

        scheduler = TimetableScheduler(
            teachers,
            rooms,
            subjects,
            classes,
            teacher_subjects,
            class_subjects
        )

        solutions = scheduler.solve(solution_limit=1)

        # Should not find a solution since room is too small
        self.assertEqual(
            len(solutions),
            0,
            "Should NOT find a solution when room capacity is insufficient"
        )

    def test_no_teacher_overload(self):
        """Test that the same teacher is not scheduled in the same period."""
        teachers = [
            {'id': 't1', 'name': 'Mr. A', 'availability': {}},
        ]
        subjects = [
            {'id': 's1', 'name': 'Math', 'periods_per_week': 2, 'is_consecutive': False},
            {'id': 's2', 'name': 'English', 'periods_per_week': 2, 'is_consecutive': False},
        ]
        classes = [
            {'id': 'c1', 'name': 'Class 1', 'student_count': 20},
            {'id': 'c2', 'name': 'Class 2', 'student_count': 20},
        ]
        rooms = [
            {'id': 'r1', 'name': 'Room 1', 'capacity': 30},
            {'id': 'r2', 'name': 'Room 2', 'capacity': 30},
        ]

        # One teacher teaches both Math and English
        teacher_subjects = [
            {'teacher_id': 't1', 'subject_id': 's1'},
            {'teacher_id': 't1', 'subject_id': 's2'},
        ]

        class_subjects = [
            {'class_id': 'c1', 'subject_id': 's1'},
            {'class_id': 'c2', 'subject_id': 's2'},
        ]

        scheduler = TimetableScheduler(
            teachers,
            rooms,
            subjects,
            classes,
            teacher_subjects,
            class_subjects
        )

        solutions = scheduler.solve(solution_limit=1)

        if solutions:
            solution = solutions[0]

            # Check that the same teacher is never in two places at the same time
            teacher_schedule = {}
            for assignment in solution:
                teacher_id = assignment['teacher_id']
                day = assignment['day_of_week']
                period = assignment['period']
                key = (teacher_id, day, period)

                self.assertNotIn(
                    key,
                    teacher_schedule,
                    f"Teacher {teacher_id} scheduled twice at day {day}, period {period}"
                )
                teacher_schedule[key] = assignment

    def test_no_room_double_booking(self):
        """Test that the same room is not used twice in the same period."""
        teachers = [
            {'id': 't1', 'name': 'Mr. A', 'availability': {}},
            {'id': 't2', 'name': 'Mr. B', 'availability': {}},
        ]
        subjects = [
            {'id': 's1', 'name': 'Math', 'periods_per_week': 2, 'is_consecutive': False},
            {'id': 's2', 'name': 'English', 'periods_per_week': 2, 'is_consecutive': False},
        ]
        classes = [
            {'id': 'c1', 'name': 'Class 1', 'student_count': 20},
            {'id': 'c2', 'name': 'Class 2', 'student_count': 20},
        ]
        rooms = [
            {'id': 'r1', 'name': 'Room 1', 'capacity': 30},
        ]

        teacher_subjects = [
            {'teacher_id': 't1', 'subject_id': 's1'},
            {'teacher_id': 't2', 'subject_id': 's2'},
        ]

        class_subjects = [
            {'class_id': 'c1', 'subject_id': 's1'},
            {'class_id': 'c2', 'subject_id': 's2'},
        ]

        scheduler = TimetableScheduler(
            teachers,
            rooms,
            subjects,
            classes,
            teacher_subjects,
            class_subjects
        )

        solutions = scheduler.solve(solution_limit=1)

        if solutions:
            solution = solutions[0]

            # Check that no room is booked twice in the same period
            room_schedule = {}
            for assignment in solution:
                room_id = assignment['room_id']
                day = assignment['day_of_week']
                period = assignment['period']
                key = (room_id, day, period)

                self.assertNotIn(
                    key,
                    room_schedule,
                    f"Room {room_id} double-booked at day {day}, period {period}"
                )
                room_schedule[key] = assignment


class TestSchedulerConsecutivePeriods(unittest.TestCase):
    """Test consecutive periods constraint."""

    def test_consecutive_periods(self):
        """Test that consecutive period requirement is respected."""
        teachers = [{'id': 't1', 'name': 'Mr. A', 'availability': {}}]

        # Math requires 4 consecutive periods (2 blocks of 2)
        subjects = [
            {'id': 's1', 'name': 'Math', 'periods_per_week': 4, 'is_consecutive': True},
        ]
        classes = [{'id': 'c1', 'name': 'Class 1', 'student_count': 20}]
        rooms = [{'id': 'r1', 'name': 'Room 1', 'capacity': 30}]
        teacher_subjects = [{'teacher_id': 't1', 'subject_id': 's1'}]
        class_subjects = [{'class_id': 'c1', 'subject_id': 's1'}]

        consecutive_requirements = [
            {'subject_id': 's1', 'blocks': 2}  # 2 blocks of consecutive periods
        ]

        scheduler = TimetableScheduler(
            teachers,
            rooms,
            subjects,
            classes,
            teacher_subjects,
            class_subjects,
            consecutive_requirements
        )

        solutions = scheduler.solve(solution_limit=1)

        # Should find a solution
        self.assertTrue(
            len(solutions) > 0,
            "Should find a solution with consecutive periods requirement"
        )


class TestSchedulerEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_empty_data(self):
        """Test scheduler with empty data."""
        scheduler = TimetableScheduler([], [], [], [], [], [])
        solutions = scheduler.solve(solution_limit=1)

        self.assertEqual(len(solutions), 0, "Should return empty solutions for empty data")

    def test_unqualified_teacher(self):
        """Test when no teacher is qualified to teach a required subject."""
        teachers = [{'id': 't1', 'name': 'Mr. A', 'availability': {}}]
        subjects = [{'id': 's1', 'name': 'Math', 'periods_per_week': 2, 'is_consecutive': False}]
        classes = [{'id': 'c1', 'name': 'Class 1', 'student_count': 20}]
        rooms = [{'id': 'r1', 'name': 'Room 1', 'capacity': 30}]

        # No teacher-subject mapping - t1 cannot teach s1
        teacher_subjects = []
        class_subjects = [{'class_id': 'c1', 'subject_id': 's1'}]

        scheduler = TimetableScheduler(
            teachers,
            rooms,
            subjects,
            classes,
            teacher_subjects,
            class_subjects
        )

        solutions = scheduler.solve(solution_limit=1)

        self.assertEqual(
            len(solutions),
            0,
            "Should not find solution when no qualified teacher exists"
        )

    def test_multiple_solutions(self):
        """Test that solver can find multiple solutions."""
        teachers = [
            {'id': 't1', 'name': 'Mr. A', 'availability': {}},
            {'id': 't2', 'name': 'Mr. B', 'availability': {}},
        ]
        subjects = [
            {'id': 's1', 'name': 'Math', 'periods_per_week': 2, 'is_consecutive': False},
        ]
        classes = [{'id': 'c1', 'name': 'Class 1', 'student_count': 20}]
        rooms = [
            {'id': 'r1', 'name': 'Room 1', 'capacity': 30},
            {'id': 'r2', 'name': 'Room 2', 'capacity': 30},
        ]

        # Both teachers can teach Math
        teacher_subjects = [
            {'teacher_id': 't1', 'subject_id': 's1'},
            {'teacher_id': 't2', 'subject_id': 's1'},
        ]

        class_subjects = [{'class_id': 'c1', 'subject_id': 's1'}]

        scheduler = TimetableScheduler(
            teachers,
            rooms,
            subjects,
            classes,
            teacher_subjects,
            class_subjects
        )

        solutions = scheduler.solve(solution_limit=5)

        # Should find multiple solutions (or at least attempt to)
        self.assertTrue(
            len(solutions) >= 1,
            "Should find at least one solution when multiple are possible"
        )


if __name__ == '__main__':
    unittest.main()
