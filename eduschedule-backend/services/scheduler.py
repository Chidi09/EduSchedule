# eduschedule-backend/services/scheduler.py
from ortools.sat.python import cp_model
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, time
from core.logger import get_logger, PerformanceLogger, log_database_operation
import json

logger = get_logger(__name__)

class TimetableSolutionCollector(cp_model.CpSolverSolutionCallback):
    """Collects multiple solutions found by the solver."""

    def __init__(self, assignments: Dict, limit: int = 5, teachers: Dict = None):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__assignments = assignments
        self.__solutions = []
        self.__limit = limit
        self.__teachers = teachers or {}

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

        # Calculate solution quality metrics
        solution_metrics = self._calculate_solution_metrics(solution)
        solution_with_metrics = {
            'assignments': solution,
            'metrics': solution_metrics
        }

        self.__solutions.append(solution_with_metrics)
        logger.info(f"Found solution {len(self.__solutions)} with score {solution_metrics.get('total_score', 0)}")

        if len(self.__solutions) >= self.__limit:
            self.StopSearch()

    def _calculate_solution_metrics(self, solution: List[Dict]) -> Dict[str, Any]:
        """Calculate quality metrics for a solution."""
        metrics = {
            'total_assignments': len(solution),
            'teachers_used': len(set(a['teacher_id'] for a in solution)),
            'rooms_used': len(set(a['room_id'] for a in solution)),
            'teacher_workload': {},
            'preference_violations': 0,
            'gaps_count': 0,
            'total_score': 0
        }

        # Calculate teacher workloads
        teacher_schedules = {}
        for assignment in solution:
            t_id = assignment['teacher_id']
            day = assignment['day_of_week']
            period = assignment['period']

            if t_id not in teacher_schedules:
                teacher_schedules[t_id] = {}
            if day not in teacher_schedules[t_id]:
                teacher_schedules[t_id][day] = []

            teacher_schedules[t_id][day].append(period)
            metrics['teacher_workload'][t_id] = metrics['teacher_workload'].get(t_id, 0) + 1

        # Calculate gaps and preference violations
        for t_id, schedule in teacher_schedules.items():
            teacher_data = self.__teachers.get(t_id, {})
            preferences = teacher_data.get('preferences', {})

            for day, periods in schedule.items():
                periods.sort()

                # Count gaps
                for i in range(len(periods) - 1):
                    if periods[i + 1] - periods[i] > 1:
                        metrics['gaps_count'] += 1

                # Check preference violations
                preferred_periods = preferences.get('preferred_periods', [])
                if preferred_periods:
                    for period in periods:
                        if period not in preferred_periods:
                            metrics['preference_violations'] += 1

        # Calculate total score (higher is better)
        metrics['total_score'] = (
            metrics['total_assignments'] * 10
            - metrics['gaps_count'] * 5
            - metrics['preference_violations'] * 2
        )

        return metrics

class AdvancedTimetableScheduler:
    """
    Advanced timetable scheduler with support for:
    - Hard availability constraints (teacher cannot work certain times)
    - Consecutive periods (double lessons)
    - Teacher preferences (soft constraints)
    - Room capacity and feature requirements
    - Workload balancing
    """

    def __init__(self, teachers: List[Dict], rooms: List[Dict], subjects: List[Dict],
                 classes: List[Dict], teacher_subjects: List[Dict], class_subjects: List[Dict] = None,
                 consecutive_requirements: List[Dict] = None):
        """
        Initialize the advanced scheduler.

        Args:
            teachers: List of teacher records with availability and preferences
            rooms: List of room records with capacity and features
            subjects: List of subject records
            classes: List of class records with student counts
            teacher_subjects: Mapping of teachers to subjects they can teach
            class_subjects: Mapping of classes to subjects they need (with periods per week)
            consecutive_requirements: List of subjects that need consecutive periods
        """

        logger.info("Initializing Advanced Timetable Scheduler")

        # Store basic data
        self.rooms = {r['id']: r for r in rooms}
        self.subjects = {s['id']: s for s in subjects}
        self.classes = {c['id']: c for c in classes}
        self.teachers = {t['id']: t for t in teachers}

        # Build teacher qualifications
        self.teacher_qualifications = {}
        for ts in teacher_subjects:
            t_id = ts['teacher_id']
            s_id = ts['subject_id']
            self.teacher_qualifications.setdefault(t_id, []).append(s_id)

        logger.info(f"Teacher qualifications: {len(self.teacher_qualifications)} teachers qualified")

        # Build class-subject requirements
        self.class_subject_requirements = {}
        if class_subjects:
            for cs in class_subjects:
                c_id = cs['class_id']
                s_id = cs['subject_id']
                periods = cs.get('periods_per_week', 1)
                self.class_subject_requirements.setdefault(c_id, {})[s_id] = periods
        else:
            # Default: all classes need all subjects with 2 periods per week
            for c_id in self.classes:
                self.class_subject_requirements[c_id] = {s_id: 2 for s_id in self.subjects}

        # Build consecutive requirements
        self.consecutive_requirements = {}
        if consecutive_requirements:
            for cr in consecutive_requirements:
                s_id = cr['subject_id']
                c_id = cr.get('class_id', 'all')  # Apply to all classes if not specified
                consecutive_periods = cr.get('consecutive_periods', 2)

                if c_id == 'all':
                    for class_id in self.classes:
                        self.consecutive_requirements.setdefault(class_id, {})[s_id] = consecutive_periods
                else:
                    self.consecutive_requirements.setdefault(c_id, {})[s_id] = consecutive_periods

        # Parse teacher availability and preferences
        self.teacher_availability = {}
        self.teacher_preferences = {}

        for t_id, teacher in self.teachers.items():
            self.teacher_availability[t_id] = self._parse_availability(teacher.get('availability', {}))
            self.teacher_preferences[t_id] = self._parse_preferences(teacher.get('preferences', {}))

        # Time configuration
        self.days = list(range(5))  # Monday to Friday (0-4)
        self.periods = list(range(8))  # 8 periods per day (0-7)

        # OR-Tools model
        self.model = cp_model.CpModel()
        self.assignments = {}
        self.consecutive_vars = {}

        logger.info(f"Scheduler initialized: {len(self.classes)} classes, {len(self.subjects)} subjects, {len(self.teachers)} teachers, {len(self.rooms)} rooms")

    def _parse_availability(self, availability: Dict) -> Dict[int, Set[int]]:
        """
        Parse teacher availability into day -> set of available periods mapping.

        Format expected:
        {
            "monday": {"unavailable": [0, 1], "available": [2,3,4,5,6,7]},
            "tuesday": {"unavailable": [7], "available": [0,1,2,3,4,5,6]},
            "hard_constraints": {
                "never_monday_morning": true,
                "no_last_period": true
            }
        }
        """
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4,
            'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4
        }

        parsed = {}

        # Process day-specific availability
        for day_name, day_data in availability.items():
            if day_name.lower() in day_mapping:
                day_idx = day_mapping[day_name.lower()]

                if isinstance(day_data, dict):
                    unavailable = set(day_data.get('unavailable', []))
                    available = set(day_data.get('available', self.periods))
                    # Remove unavailable periods
                    available = available - unavailable
                elif isinstance(day_data, list):
                    # Assume it's a list of available periods
                    available = set(day_data)
                else:
                    available = set(self.periods)

                parsed[day_idx] = available

        # Process hard constraints
        hard_constraints = availability.get('hard_constraints', {})

        if hard_constraints.get('never_monday_morning'):
            parsed[0] = parsed.get(0, set(self.periods)) - {0, 1, 2}

        if hard_constraints.get('no_last_period'):
            for day in self.days:
                parsed[day] = parsed.get(day, set(self.periods)) - {max(self.periods)}

        if hard_constraints.get('no_early_morning'):
            for day in self.days:
                parsed[day] = parsed.get(day, set(self.periods)) - {0}

        # Default: all periods available if not specified
        for day in self.days:
            if day not in parsed:
                parsed[day] = set(self.periods)

        return parsed

    def _parse_preferences(self, preferences: Dict) -> Dict[str, Any]:
        """Parse teacher preferences (soft constraints)."""
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4,
            'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4
        }

        parsed = {
            'preferred_days': set(),
            'preferred_periods': set(preferences.get('preferred_periods', [])),
            'avoided_periods': set(preferences.get('avoided_periods', [])),
            'max_consecutive': preferences.get('max_consecutive_periods', 4),
            'min_break': preferences.get('min_break_between_classes', 0),
            'preferred_rooms': set(preferences.get('preferred_rooms', [])),
            'max_daily_load': preferences.get('max_daily_load', 6),
            'prefers_morning': preferences.get('prefers_morning', False),
            'prefers_afternoon': preferences.get('prefers_afternoon', False)
        }

        # Parse preferred days
        for day_name in preferences.get('preferred_days', []):
            if day_name.lower() in day_mapping:
                parsed['preferred_days'].add(day_mapping[day_name.lower()])

        return parsed

    def _create_variables(self):
        """Create decision variables for valid combinations only."""
        logger.info("Creating decision variables...")

        variable_count = 0

        for c_id in self.classes:
            required_subjects = self.class_subject_requirements.get(c_id, {})

            for s_id, periods_needed in required_subjects.items():
                # Find qualified teachers
                qualified_teachers = [
                    t_id for t_id, subjects in self.teacher_qualifications.items()
                    if s_id in subjects
                ]

                if not qualified_teachers:
                    logger.warning(f"No qualified teachers for subject {s_id}")
                    continue

                for t_id in qualified_teachers:
                    # Find suitable rooms
                    suitable_rooms = self._find_suitable_rooms(s_id, c_id)

                    if not suitable_rooms:
                        logger.warning(f"No suitable rooms for class {c_id}, subject {s_id}")
                        continue

                    for r_id in suitable_rooms:
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
                                variable_count += 1

        logger.info(f"Created {variable_count} decision variables")

        # Create consecutive period variables if needed
        self._create_consecutive_variables()

    def _find_suitable_rooms(self, subject_id: str, class_id: str) -> List[str]:
        """Find rooms suitable for a given subject and class."""
        suitable_rooms = []

        subject_data = self.subjects.get(subject_id, {})
        class_data = self.classes.get(class_id, {})

        required_features = subject_data.get('required_features', [])
        student_count = class_data.get('student_count', 0)

        for r_id, room_data in self.rooms.items():
            # Check capacity
            if student_count > room_data.get('capacity', 0):
                continue

            # Check required features
            room_features = room_data.get('features', [])
            if not set(required_features).issubset(set(room_features)):
                continue

            suitable_rooms.append(r_id)

        return suitable_rooms

    def _create_consecutive_variables(self):
        """Create variables for consecutive periods where required."""
        logger.info("Creating consecutive period variables...")

        for c_id, consecutive_subjects in self.consecutive_requirements.items():
            for s_id, consecutive_count in consecutive_subjects.items():
                for d in self.days:
                    for start_period in range(len(self.periods) - consecutive_count + 1):
                        # Create variable for consecutive block
                        var_name = f'consecutive_{c_id}_{s_id}_{d}_{start_period}_{consecutive_count}'
                        consecutive_var = self.model.NewBoolVar(var_name)

                        key = (c_id, s_id, d, start_period, consecutive_count)
                        self.consecutive_vars[key] = consecutive_var

    def _add_hard_constraints(self):
        """Add fundamental scheduling constraints."""
        logger.info("Adding hard constraints...")

        self._add_teacher_conflict_constraints()
        self._add_room_conflict_constraints()
        self._add_class_conflict_constraints()
        self._add_subject_frequency_constraints()
        self._add_consecutive_period_constraints()

    def _add_teacher_conflict_constraints(self):
        """A teacher can only be in one place at one time."""
        for t_id in self.teachers:
            for d in self.days:
                for p in self.periods:
                    conflicting_vars = [
                        var for (c, s, t, r, d_var, p_var), var in self.assignments.items()
                        if t == t_id and d_var == d and p_var == p
                    ]

                    if conflicting_vars:
                        self.model.AddAtMostOne(conflicting_vars)

    def _add_room_conflict_constraints(self):
        """A room can only host one class at a time."""
        for r_id in self.rooms:
            for d in self.days:
                for p in self.periods:
                    conflicting_vars = [
                        var for (c, s, t, r, d_var, p_var), var in self.assignments.items()
                        if r == r_id and d_var == d and p_var == p
                    ]

                    if conflicting_vars:
                        self.model.AddAtMostOne(conflicting_vars)

    def _add_class_conflict_constraints(self):
        """A class can only have one subject at a time."""
        for c_id in self.classes:
            for d in self.days:
                for p in self.periods:
                    conflicting_vars = [
                        var for (c, s, t, r, d_var, p_var), var in self.assignments.items()
                        if c == c_id and d_var == d and p_var == p
                    ]

                    if conflicting_vars:
                        self.model.AddAtMostOne(conflicting_vars)

    def _add_subject_frequency_constraints(self):
        """Ensure each class gets required periods for each subject."""
        for c_id, required_subjects in self.class_subject_requirements.items():
            for s_id, periods_needed in required_subjects.items():
                relevant_vars = [
                    var for (c, s, t, r, d, p), var in self.assignments.items()
                    if c == c_id and s == s_id
                ]

                if relevant_vars:
                    self.model.Add(sum(relevant_vars) == periods_needed)

    def _add_consecutive_period_constraints(self):
        """Link consecutive period variables with individual assignments."""
        for (c_id, s_id, d, start_period, consecutive_count), consecutive_var in self.consecutive_vars.items():
            # Get all assignments for this consecutive block
            block_vars = []
            for p in range(start_period, start_period + consecutive_count):
                period_vars = [
                    var for (c, s, t, r, d_var, p_var), var in self.assignments.items()
                    if c == c_id and s == s_id and d_var == d and p_var == p
                ]
                block_vars.extend(period_vars)

            if block_vars:
                # If consecutive_var is true, all periods in block must be assigned to same teacher/room
                # This is a simplified constraint - more complex logic needed for full implementation
                self.model.Add(sum(block_vars) == consecutive_count).OnlyEnforceIf(consecutive_var)

    def _add_workload_constraints(self):
        """Add teacher workload limits."""
        logger.info("Adding workload constraints...")

        for t_id, preferences in self.teacher_preferences.items():
            max_daily_load = preferences.get('max_daily_load', 6)

            # Daily workload constraint
            for d in self.days:
                daily_vars = [
                    var for (c, s, t, r, d_var, p), var in self.assignments.items()
                    if t == t_id and d_var == d
                ]
                if daily_vars:
                    self.model.Add(sum(daily_vars) <= max_daily_load)

            # Weekly workload constraint (max 30 periods)
            weekly_vars = [
                var for (c, s, t, r, d, p), var in self.assignments.items()
                if t == t_id
            ]
            if weekly_vars:
                self.model.Add(sum(weekly_vars) <= 30)

    def _add_preferences_objective(self):
        """Add soft constraints as objective terms."""
        logger.info("Adding preference objectives...")

        preference_terms = []
        penalty_terms = []

        for t_id, prefs in self.teacher_preferences.items():
            # Preferred days bonus
            if prefs['preferred_days']:
                for d in prefs['preferred_days']:
                    day_vars = [
                        var for (c, s, t, r, d_var, p), var in self.assignments.items()
                        if t == t_id and d_var == d
                    ]
                    if day_vars:
                        preference_terms.extend([var * 3 for var in day_vars])

            # Preferred periods bonus
            if prefs['preferred_periods']:
                for p in prefs['preferred_periods']:
                    period_vars = [
                        var for (c, s, t, r, d, p_var), var in self.assignments.items()
                        if t == t_id and p_var == p
                    ]
                    if period_vars:
                        preference_terms.extend([var * 2 for var in period_vars])

            # Avoided periods penalty
            if prefs['avoided_periods']:
                for p in prefs['avoided_periods']:
                    avoided_vars = [
                        var for (c, s, t, r, d, p_var), var in self.assignments.items()
                        if t == t_id and p_var == p
                    ]
                    if avoided_vars:
                        penalty_terms.extend([var * 5 for var in avoided_vars])

            # Morning preference
            if prefs['prefers_morning']:
                afternoon_vars = [
                    var for (c, s, t, r, d, p), var in self.assignments.items()
                    if t == t_id and p >= 4
                ]
                penalty_terms.extend([var * 2 for var in afternoon_vars])

            # Afternoon preference
            if prefs['prefers_afternoon']:
                morning_vars = [
                    var for (c, s, t, r, d, p), var in self.assignments.items()
                    if t == t_id and p < 4
                ]
                penalty_terms.extend([var * 2 for var in morning_vars])

        # Set objective: maximize preferences, minimize penalties
        if preference_terms or penalty_terms:
            total_preference = sum(preference_terms) if preference_terms else 0
            total_penalty = sum(penalty_terms) if penalty_terms else 0
            self.model.Maximize(total_preference - total_penalty)

    def solve(self, solution_limit: int = 5, time_limit_seconds: int = 300) -> List[Dict]:
        """
        Solve the advanced timetabling problem.

        Returns:
            List of solutions with assignments and quality metrics
        """
        logger.info(f"Starting advanced timetable generation (limit: {solution_limit}, timeout: {time_limit_seconds}s)")

        with PerformanceLogger(logger, "Advanced Timetable Generation"):
            try:
                # Build the model
                self._create_variables()

                if not self.assignments:
                    logger.error("No valid assignments possible with current constraints")
                    return []

                self._add_hard_constraints()
                self._add_workload_constraints()
                self._add_preferences_objective()

                # Configure solver
                solver = cp_model.CpSolver()
                solver.parameters.max_time_in_seconds = time_limit_seconds
                solver.parameters.enumerate_all_solutions = True

                # Set up solution collector
                solution_collector = TimetableSolutionCollector(
                    self.assignments,
                    solution_limit,
                    self.teachers
                )

                # Solve
                logger.info(f"Solving with {len(self.assignments)} variables and {len(self.consecutive_vars)} consecutive constraints...")
                status = solver.SolveWithSolutionCallback(self.model, solution_collector)

                # Process results
                if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
                    solutions = solution_collector.solutions
                    logger.info(f"Found {len(solutions)} high-quality solutions")

                    # Sort solutions by quality score
                    solutions.sort(key=lambda x: x['metrics'].get('total_score', 0), reverse=True)

                    return solutions
                else:
                    logger.error(f"No solution found. Status: {solver.StatusName(status)}")
                    return []

            except Exception as e:
                logger.error(f"Critical error in advanced scheduler: {str(e)}")
                raise

    def validate_solution(self, solution: Dict) -> Dict[str, Any]:
        """Validate a solution against all constraints."""
        assignments = solution.get('assignments', [])
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {
                'total_assignments': len(assignments),
                'teachers_used': len(set(a['teacher_id'] for a in assignments)),
                'rooms_used': len(set(a['room_id'] for a in assignments))
            }
        }

        # Check for conflicts
        time_slots = {}
        for assignment in assignments:
            t_id = assignment['teacher_id']
            r_id = assignment['room_id']
            c_id = assignment['class_id']
            d = assignment['day_of_week']
            p = assignment['period']

            slot_key = (d, p)

            # Check teacher conflicts
            if slot_key not in time_slots:
                time_slots[slot_key] = {'teachers': set(), 'rooms': set(), 'classes': set()}

            if t_id in time_slots[slot_key]['teachers']:
                validation_result['errors'].append(f"Teacher {t_id} conflict at day {d}, period {p}")
                validation_result['valid'] = False

            if r_id in time_slots[slot_key]['rooms']:
                validation_result['errors'].append(f"Room {r_id} conflict at day {d}, period {p}")
                validation_result['valid'] = False

            if c_id in time_slots[slot_key]['classes']:
                validation_result['errors'].append(f"Class {c_id} conflict at day {d}, period {p}")
                validation_result['valid'] = False

            time_slots[slot_key]['teachers'].add(t_id)
            time_slots[slot_key]['rooms'].add(r_id)
            time_slots[slot_key]['classes'].add(c_id)

        return validation_result

# Legacy compatibility
TimetableScheduler = AdvancedTimetableScheduler
