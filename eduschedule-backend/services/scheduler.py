# services/scheduler.py
from ortools.sat.python import cp_model
from typing import List, Dict, Any, Optional, Set
import logging
from datetime import datetime, time

logger = logging.getLogger(__name__)

class TimetableSolutionCollector(cp_model.CpSolverSolutionCallback):
    """Collects multiple solutions found by the solver."""
    def __init__(self, assignments: Dict, limit: int = 5):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__assignments = assignments
        self.__solutions = []
        self.__limit = limit

    @property
    def solutions(self) -> List[List[Dict]]:
        return self.__solutions

    def on_solution_callback(self):
        """Called by the solver for each new solution found."""
        solution = []
        for (c, s, t, r, d, p), var in self.__assignments.items():
            if self.Value(var):
                solution.append({
                    "class_id": c,
                    "subject_id": s,
                    "teacher_id": t,
                    "room_id": r,
                    "day_of_week": d,
                    "period": p
                })
        self.__solutions.append(solution)

        if len(self.__solutions) >= self.__limit:
            self.StopSearch()

class TimetableScheduler:
    def __init__(self, teachers: List[Dict], rooms: List[Dict], subjects: List[Dict],
                 classes: List[Dict], teacher_subjects: List[Dict], class_subjects: List[Dict] = None):
        """
        Initialize the scheduler with all required data.

        Args:
            teachers: List of teacher records with availability preferences
            rooms: List of available rooms
            subjects: List of all subjects
            classes: List of all classes
            teacher_subjects: List mapping teachers to subjects they can teach
            class_subjects: List mapping classes to subjects they need (optional)
        """
        self.rooms = {r['id']: r for r in rooms}
        self.subjects = {s['id']: s for s in subjects}
        self.classes = {c['id']: c for c in classes}
        self.teachers = {t['id']: t for t in teachers}

        # Build teacher qualifications mapping
        self.teacher_qualifications = {}
        for ts in teacher_subjects:
            t_id = ts['teacher_id']
            s_id = ts['subject_id']
            self.teacher_qualifications.setdefault(t_id, []).append(s_id)

        # Build class-subject requirements (what subjects each class needs)
        self.class_subject_requirements = {}
        if class_subjects:
            for cs in class_subjects:
                c_id = cs['class_id']
                s_id = cs['subject_id']
                periods_per_week = cs.get('periods_per_week', 1)
                self.class_subject_requirements.setdefault(c_id, {})[s_id] = periods_per_week
        else:
            # Default: all classes need all subjects (legacy behavior)
            for c_id in self.classes:
                self.class_subject_requirements[c_id] = {s_id: 1 for s_id in self.subjects}

        # Parse teacher availability (hard constraints)
        self.teacher_availability = {}
        self.teacher_preferences = {}

        for t_id, teacher in self.teachers.items():
            # Parse availability (hard constraints)
            availability = teacher.get('availability', {})
            self.teacher_availability[t_id] = self._parse_availability(availability)

            # Parse preferences (soft constraints)
            preferences = teacher.get('preferences', {})
            self.teacher_preferences[t_id] = self._parse_preferences(preferences)

        # Scheduler parameters
        self.days = list(range(5))  # Monday to Friday (0-4)
        self.periods = list(range(8))  # 8 periods per day (0-7)

        # OR-Tools model
        self.model = cp_model.CpModel()
        self.assignments = {}

    def _parse_availability(self, availability: Dict) -> Dict[int, Set[int]]:
        """
        Parse teacher availability into day -> set of available periods mapping.

        Format expected:
        {
            "monday": {"unavailable": [0, 1], "available": [2,3,4,5,6,7]},
            "tuesday": {"unavailable": [7], "available": [0,1,2,3,4,5,6]},
            ...
        }

        Returns: {day_index: {available_periods}}
        """
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4
        }

        parsed = {}
        for day_name, day_data in availability.items():
            if day_name.lower() in day_mapping:
                day_idx = day_mapping[day_name.lower()]

                if isinstance(day_data, dict):
                    unavailable = set(day_data.get('unavailable', []))
                    available = set(day_data.get('available', self.periods))
                    # Remove unavailable periods from available
                    available = available - unavailable
                else:
                    # Legacy format: assume all periods available
                    available = set(self.periods)

                parsed[day_idx] = available

        # Default: all days/periods available if not specified
        for day in self.days:
            if day not in parsed:
                parsed[day] = set(self.periods)

        return parsed

    def _parse_preferences(self, preferences: Dict) -> Dict[str, Any]:
        """
        Parse teacher preferences (soft constraints for optimization).

        Format expected:
        {
            "preferred_days": ["monday", "tuesday"],
            "preferred_periods": [0, 1, 2],  # Morning periods
            "max_consecutive_periods": 3,
            "min_break_between_classes": 1,
            "preferred_rooms": ["room1", "room2"]
        }
        """
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4
        }

        parsed = {
            'preferred_days': set(),
            'preferred_periods': set(preferences.get('preferred_periods', [])),
            'max_consecutive': preferences.get('max_consecutive_periods', 4),
            'min_break': preferences.get('min_break_between_classes', 0),
            'preferred_rooms': set(preferences.get('preferred_rooms', []))
        }

        # Parse preferred days
        for day_name in preferences.get('preferred_days', []):
            if day_name.lower() in day_mapping:
                parsed['preferred_days'].add(day_mapping[day_name.lower()])

        return parsed

    def _create_variables(self):
        """
        Create decision variables only for valid combinations.
        Each variable represents: class c, subject s, teacher t, room r, day d, period p
        """
        logger.info("Creating decision variables...")

        for c_id in self.classes:
            required_subjects = self.class_subject_requirements.get(c_id, {})

            for s_id, periods_needed in required_subjects.items():
                # Find qualified teachers for this subject
                qualified_teachers = [
                    t_id for t_id, subjects in self.teacher_qualifications.items()
                    if s_id in subjects
                ]

                if not qualified_teachers:
                    logger.warning(f"No qualified teachers found for subject {s_id}")
                    continue

                # Create variables for each possible assignment
                for t_id in qualified_teachers:
                    for r_id in self.rooms:
                        for d in self.days:
                            # Check teacher availability (hard constraint)
                            available_periods = self.teacher_availability.get(t_id, {}).get(d, set())

                            for p in self.periods:
                                if p not in available_periods:
                                    continue  # Skip unavailable slots

                                # Create the decision variable
                                var_name = f'assign_{c_id}_{s_id}_{t_id}_{r_id}_{d}_{p}'
                                var = self.model.NewBoolVar(var_name)
                                self.assignments[(c_id, s_id, t_id, r_id, d, p)] = var

        logger.info(f"Created {len(self.assignments)} decision variables")

    def _add_constraints(self):
        """Add all scheduling constraints."""
        logger.info("Adding constraints...")

        self._add_class_requirements_constraints()
        self._add_teacher_conflicts_constraints()
        self._add_room_conflicts_constraints()
        self._add_class_conflicts_constraints()
        self._add_workload_constraints()

    def _add_class_requirements_constraints(self):
        """Ensure each class gets the required number of periods for each subject."""
        for c_id, required_subjects in self.class_subject_requirements.items():
            for s_id, periods_needed in required_subjects.items():
                # Sum all assignments for this class-subject combination
                relevant_vars = [
                    var for (c, s, t, r, d, p), var in self.assignments.items()
                    if c == c_id and s == s_id
                ]

                if relevant_vars:
                    self.model.Add(sum(relevant_vars) == periods_needed)

    def _add_teacher_conflicts_constraints(self):
        """A teacher can only be in one place at one time."""
        for t_id in self.teachers:
            for d in self.days:
                for p in self.periods:
                    # Find all assignments for this teacher at this time slot
                    conflicting_vars = [
                        var for (c, s, t, r, d_var, p_var), var in self.assignments.items()
                        if t == t_id and d_var == d and p_var == p
                    ]

                    if conflicting_vars:
                        # Teacher can be assigned to at most one class per time slot
                        self.model.Add(sum(conflicting_vars) <= 1)

    def _add_room_conflicts_constraints(self):
        """A room can only host one class at a time."""
        for r_id in self.rooms:
            for d in self.days:
                for p in self.periods:
                    # Find all assignments for this room at this time slot
                    conflicting_vars = [
                        var for (c, s, t, r, d_var, p_var), var in self.assignments.items()
                        if r == r_id and d_var == d and p_var == p
                    ]

                    if conflicting_vars:
                        # Room can host at most one class per time slot
                        self.model.Add(sum(conflicting_vars) <= 1)

    def _add_class_conflicts_constraints(self):
        """A class can only have one subject at a time."""
        for c_id in self.classes:
            for d in self.days:
                for p in self.periods:
                    # Find all assignments for this class at this time slot
                    conflicting_vars = [
                        var for (c, s, t, r, d_var, p_var), var in self.assignments.items()
                        if c == c_id and d_var == d and p_var == p
                    ]

                    if conflicting_vars:
                        # Class can have at most one subject per time slot
                        self.model.Add(sum(conflicting_vars) <= 1)

    def _add_workload_constraints(self):
        """Add reasonable workload limits for teachers."""
        for t_id in self.teachers:
            # Daily workload limit (max 6 periods per day)
            for d in self.days:
                daily_vars = [
                    var for (c, s, t, r, d_var, p_var), var in self.assignments.items()
                    if t == t_id and d_var == d
                ]
                if daily_vars:
                    self.model.Add(sum(daily_vars) <= 6)

            # Weekly workload limit (max 25 periods per week)
            weekly_vars = [
                var for (c, s, t, r, d, p), var in self.assignments.items()
                if t == t_id
            ]
            if weekly_vars:
                self.model.Add(sum(weekly_vars) <= 25)

    def _add_preferences(self):
        """Add soft constraints (preferences) to the objective function."""
        logger.info("Adding preference objectives...")

        preference_vars = []

        for t_id, prefs in self.teacher_preferences.items():
            # Preferred days bonus
            if prefs['preferred_days']:
                for d in prefs['preferred_days']:
                    day_vars = [
                        var for (c, s, t, r, d_var, p), var in self.assignments.items()
                        if t == t_id and d_var == d
                    ]
                    if day_vars:
                        bonus_var = self.model.NewIntVar(0, len(day_vars), f'day_pref_{t_id}_{d}')
                        self.model.Add(bonus_var == sum(day_vars))
                        preference_vars.append(bonus_var * 2)  # Weight: 2 points per preferred day assignment

            # Preferred periods bonus
            if prefs['preferred_periods']:
                for p in prefs['preferred_periods']:
                    period_vars = [
                        var for (c, s, t, r, d, p_var), var in self.assignments.items()
                        if t == t_id and p_var == p
                    ]
                    if period_vars:
                        bonus_var = self.model.NewIntVar(0, len(period_vars), f'period_pref_{t_id}_{p}')
                        self.model.Add(bonus_var == sum(period_vars))
                        preference_vars.append(bonus_var * 1)  # Weight: 1 point per preferred period

        # Minimize gaps in schedules (consecutive periods preferred)
        gap_penalty_vars = []
        for t_id in self.teachers:
            for d in self.days:
                for p in range(len(self.periods) - 1):
                    current_period_vars = [
                        var for (c, s, t, r, d_var, p_var), var in self.assignments.items()
                        if t == t_id and d_var == d and p_var == p
                    ]
                    next_period_vars = [
                        var for (c, s, t, r, d_var, p_var), var in self.assignments.items()
                        if t == t_id and d_var == d and p_var == p + 1
                    ]

                    if current_period_vars and next_period_vars:
                        # Penalty for gaps (teaching in period p but not p+1, then teaching again later)
                        gap_var = self.model.NewBoolVar(f'gap_{t_id}_{d}_{p}')
                        # This is a simplified gap detection - can be made more sophisticated
                        gap_penalty_vars.append(gap_var * 3)  # 3 point penalty per gap

        # Set objective: maximize preferences, minimize penalties
        if preference_vars or gap_penalty_vars:
            total_preference = sum(preference_vars) if preference_vars else 0
            total_penalty = sum(gap_penalty_vars) if gap_penalty_vars else 0
            self.model.Maximize(total_preference - total_penalty)

    def solve(self, solution_limit: int = 5, time_limit_seconds: int = 300) -> List[List[Dict]]:
        """
        Solve the timetabling problem and return multiple solutions.

        Args:
            solution_limit: Maximum number of solutions to find
            time_limit_seconds: Maximum solving time

        Returns:
            List of solutions, each containing assignment dictionaries
        """
        logger.info("Starting timetable generation...")

        # Validate input data
        if not self._validate_input_data():
            logger.error("Input data validation failed")
            return []

        try:
            # Build the model
            self._create_variables()

            if not self.assignments:
                logger.error("No valid assignments possible with current constraints")
                return []

            self._add_constraints()
            self._add_preferences()

            # Set up solver
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = time_limit_seconds
            solver.parameters.enumerate_all_solutions = True

            # Set up solution collector
            solution_collector = TimetableSolutionCollector(self.assignments, solution_limit)

            # Solve
            logger.info(f"Solving with {len(self.assignments)} variables...")
            status = solver.SolveWithSolutionCallback(self.model, solution_collector)

            # Process results
            if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
                solutions = solution_collector.solutions
                logger.info(f"Found {len(solutions)} solutions")
                return solutions
            else:
                logger.error(f"No solution found. Status: {solver.StatusName(status)}")
                return []

        except Exception as e:
            logger.error(f"Solver error: {str(e)}")
            raise

    def _validate_input_data(self) -> bool:
        """Validate that we have sufficient data to generate a timetable."""
        if not self.teachers:
            logger.error("No teachers provided")
            return False

        if not self.classes:
            logger.error("No classes provided")
            return False

        if not self.subjects:
            logger.error("No subjects provided")
            return False

        if not self.rooms:
            logger.error("No rooms provided")
            return False

        # Check that we have qualified teachers for all required subjects
        all_required_subjects = set()
        for c_id, subjects in self.class_subject_requirements.items():
            all_required_subjects.update(subjects.keys())

        all_qualified_subjects = set()
        for t_id, subjects in self.teacher_qualifications.items():
            all_qualified_subjects.update(subjects)

        unqualified_subjects = all_required_subjects - all_qualified_subjects
        if unqualified_subjects:
            logger.error(f"No qualified teachers for subjects: {unqualified_subjects}")
            return False

        return True

    def get_solution_metrics(self, solution: List[Dict]) -> Dict[str, Any]:
        """Calculate metrics for a given solution."""
        if not solution:
            return {}

        metrics = {
            'total_assignments': len(solution),
            'teachers_used': len(set(a['teacher_id'] for a in solution)),
            'rooms_used': len(set(a['room_id'] for a in solution)),
            'teacher_workload': {},
            'room_utilization': {},
            'preference_score': 0
        }

        # Calculate teacher workloads
        for assignment in solution:
            t_id = assignment['teacher_id']
            metrics['teacher_workload'][t_id] = metrics['teacher_workload'].get(t_id, 0) + 1

        # Calculate room utilization
        for assignment in solution:
            r_id = assignment['room_id']
            metrics['room_utilization'][r_id] = metrics['room_utilization'].get(r_id, 0) + 1

        # Calculate preference satisfaction score
        preference_score = 0
        for assignment in solution:
            t_id = assignment['teacher_id']
            day = assignment['day_of_week']
            period = assignment['period']

            prefs = self.teacher_preferences.get(t_id, {})

            # Preferred day bonus
            if day in prefs.get('preferred_days', set()):
                preference_score += 2

            # Preferred period bonus
            if period in prefs.get('preferred_periods', set()):
                preference_score += 1

        metrics['preference_score'] = preference_score

        return metrics
