from ortools.sat.python import cp_model
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class TimetableSolutionCallback(cp_model.CpSolverSolutionCallback):
    """Collects multiple solutions found by the solver."""

    def __init__(self, limit: int = 5):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__solutions = []
        self.__limit = limit
        self.__solution_count = 0

    def on_solution_callback(self):
        self.__solution_count += 1
        # In a real scenario, you'd extract the variables here.
        # However, because variable mapping is complex, we often just count here
        # and extract variables after Solve() using the generic solver object
        # if we are not using a strictly custom printer.
        # For this implementation, we will just stop early.
        if self.__solution_count >= self.__limit:
            self.StopSearch()

    def solution_count(self):
        return self.__solution_count

class TimetableScheduler:
    def __init__(self, teachers: List[Dict], rooms: List[Dict], subjects: List[Dict],
                 classes: List[Dict], teacher_subjects: List[Dict],
                 class_subjects: List[Dict] = None,
                 consecutive_requirements: List[Dict] = None):

        self.teachers = {t['id']: t for t in teachers}
        self.rooms = {r['id']: r for r in rooms}
        self.subjects = {s['id']: s for s in subjects}
        self.classes = {c['id']: c for c in classes}

        # 1. Map Teachers to Subjects
        self.teacher_qualifications = {}
        for ts in teacher_subjects:
            self.teacher_qualifications.setdefault(ts['teacher_id'], []).append(ts['subject_id'])

        # 2. Map Classes to Subjects (Optimization: Only schedule needed subjects)
        self.class_requirements = {}
        if class_subjects:
            for cs in class_subjects:
                self.class_requirements.setdefault(cs['class_id'], []).append(cs['subject_id'])
        else:
            # Default: All classes take all subjects (Fallback)
            all_subject_ids = list(self.subjects.keys())
            for c_id in self.classes:
                self.class_requirements[c_id] = all_subject_ids

        # 3. Consecutive Requirements (e.g., {"subject_id": "math", "blocks": 2})
        self.consecutive_map = {}
        if consecutive_requirements:
            for req in consecutive_requirements:
                self.consecutive_map[req['subject_id']] = req.get('blocks', 1)

        self.days = list(range(5)) # 0=Mon, 4=Fri
        self.periods = list(range(8)) # 0-7 periods
        self.model = cp_model.CpModel()
        self.assignments = {}

    def _create_variables(self):
        """Creates decision variables with intelligent filtering."""
        for c_id, c_data in self.classes.items():
            # Only iterate subjects this class actually takes
            required_subjects = self.class_requirements.get(c_id, [])

            for s_id in required_subjects:
                # Get subject data safely
                s_data = self.subjects.get(s_id)
                if not s_data: continue

                # Find valid teachers for this subject
                valid_teachers = [t_id for t_id, subs in self.teacher_qualifications.items() if s_id in subs]

                for t_id in valid_teachers:
                    # Teacher Availability Check (Hard Constraint)
                    t_unavailable = self.teachers[t_id].get('availability', {}).get('unavailable', [])

                    for r_id, r_data in self.rooms.items():
                        # Room Capacity Check
                        if c_data.get('student_count', 0) > r_data.get('capacity', 0):
                            continue

                        for d in self.days:
                            for p in self.periods:
                                if [d, p] in t_unavailable:
                                    continue

                                name = f'{c_id}_{s_id}_{t_id}_{r_id}_{d}_{p}'
                                self.assignments[(c_id, s_id, t_id, r_id, d, p)] = self.model.NewBoolVar(name)

    def _apply_hard_constraints(self):
        """Applies physical reality constraints."""

        # 1. One Teacher, One Place
        for t in self.teachers:
            for d in self.days:
                for p in self.periods:
                    self.model.AddAtMostOne([v for (c, s, t_i, r, d_i, p_i), v in self.assignments.items()
                                           if t_i == t and d_i == d and p_i == p])

        # 2. One Class, One Room
        for c in self.classes:
            for d in self.days:
                for p in self.periods:
                    self.model.AddAtMostOne([v for (c_i, s, t, r, d_i, p_i), v in self.assignments.items()
                                           if c_i == c and d_i == d and p_i == p])

        # 3. One Room, One Class
        for r in self.rooms:
            for d in self.days:
                for p in self.periods:
                    self.model.AddAtMostOne([v for (c, s, t, r_i, d_i, p_i), v in self.assignments.items()
                                           if r_i == r and d_i == d and p_i == p])

        # 4. Subject Frequency & Consecutive Blocks
        for c_id in self.classes:
            required_subjects = self.class_requirements.get(c_id, [])

            for s_id in required_subjects:
                s_data = self.subjects[s_id]
                weekly_periods = s_data.get('periods_per_week', 4)

                # Gather all variables for this class-subject pair
                class_subject_vars = [v for (c, s, t, r, d, p), v in self.assignments.items()
                                      if c == c_id and s == s_id]

                if not class_subject_vars:
                    # If no valid slots exist (e.g. no teacher qualified), log warning
                    continue

                # Constraint: Total periods per week
                self.model.Add(sum(class_subject_vars) == weekly_periods)

                # --- Consecutive Logic Implementation ---
                block_size = self.consecutive_map.get(s_id, 1)
                if block_size > 1:
                    # Calculate how many blocks are needed (e.g., 4 periods / 2 = 2 blocks)
                    if weekly_periods % block_size != 0:
                        logger.warning(f"Subject {s_id} periods ({weekly_periods}) not divisible by block size {block_size}. detailed constraints may fail.")

                    num_blocks_needed = weekly_periods // block_size

                    # Create "Start Variables": block_starts[d][p] is True if a block starts here
                    block_starts = []

                    for d in self.days:
                        # We can't start a block if there isn't enough room left in the day
                        valid_start_periods = range(len(self.periods) - block_size + 1)

                        for p in valid_start_periods:
                            start_var = self.model.NewBoolVar(f'start_{c_id}_{s_id}_{d}_{p}')
                            block_starts.append(start_var)

                            # LOGIC: If a block starts at P, then the class MUST be assigned
                            # this subject for P, P+1, ... P+block_size-1
                            for offset in range(block_size):
                                target_p = p + offset
                                # Gather all assignment vars for this Class+Subject at Day+TargetP (across all teachers/rooms)
                                relevant_assignments = [
                                    v for (c, s, t, r, d_i, p_i), v in self.assignments.items()
                                    if c == c_id and s == s_id and d_i == d and p_i == target_p
                                ]

                                # If block starts, sum of assignments at P+offset must be 1
                                if relevant_assignments:
                                    self.model.Add(sum(relevant_assignments) == 1).OnlyEnforceIf(start_var)
                                else:
                                    # If no valid assignment exists at P+offset (e.g., restricted by teacher),
                                    # then a block CANNOT start here.
                                    self.model.Add(start_var == 0)

                    # LOGIC: The total number of started blocks must equal the required amount
                    if block_starts:
                        self.model.Add(sum(block_starts) == num_blocks_needed)

    def solve(self, solution_limit=5):
        self._create_variables()
        self._apply_hard_constraints()

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 60.0

        # Use the callback to stop after finding enough solutions
        callback = TimetableSolutionCallback(limit=solution_limit)
        status = solver.Solve(self.model, callback)

        solutions = []
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            # Extract ONE representative solution (since callback logic for extracting ALL is complex)
            # In a real app, you'd iterate `callback.solutions` if you stored them there.
            sol_data = []
            for (c, s, t, r, d, p), var in self.assignments.items():
                if solver.Value(var):
                    sol_data.append({
                        "class_id": c, "subject_id": s, "teacher_id": t,
                        "room_id": r, "day_of_week": d, "period": p
                    })
            solutions.append(sol_data)

        return solutions
