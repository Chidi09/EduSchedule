# services/scheduler.py
from ortools.sat.python import cp_model
from typing import List, Dict, Any

class TimetableSolutionCollector(cp_model.CpSolverSolutionCallback):
    """Collects solutions found by the solver."""
    def __init__(self, assignments: Dict, limit: int):
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
                    "class_id": c, "subject_id": s, "teacher_id": t,
                    "room_id": r, "day_of_week": d, "period": p
                })
        self.__solutions.append(solution)
        if len(self.__solutions) >= self.__limit:
            self.StopSearch()


class TimetableScheduler:
    def __init__(self, teachers: List[Dict], rooms: List[Dict], subjects: List[Dict], classes: List[Dict], teacher_subjects: List[Dict]):
        self.rooms = {r['id']: r for r in rooms}
        self.subjects = {s['id']: s for s in subjects}
        self.classes = {c['id']: c for c in classes}
        self.teachers = {t['id']: t for t in teachers} # Keep full teacher data
        
        self.teacher_qualifications = {}
        for ts in teacher_subjects:
            t_id = ts['teacher_id']
            s_id = ts['subject_id']
            self.teacher_qualifications.setdefault(t_id, []).append(s_id)

        self.days = list(range(5))
        self.periods = list(range(8))
        self.model = cp_model.CpModel()
        self.assignments = {}

    def _create_variables(self):
        """Create decision variables only for valid teacher-subject-class-room combinations."""
        for c_id, c_data in self.classes.items():
            for s_id, s_data in self.subjects.items():
                for t_id in self.teachers:
                    if s_id not in self.teacher_qualifications.get(t_id, []):
                        continue
                    for r_id, r_data in self.rooms.items():
                        if c_data['student_count'] > r_data['capacity']:
                            continue
                        if s_data.get('required_features'):
                           if not set(s_data['required_features']).issubset(set(r_data.get('features', []))):
                                continue
                        for d in self.days:
                            for p in self.periods:
                                key = (c_id, s_id, t_id, r_id, d, p)
                                self.assignments[key] = self.model.NewBoolVar(f'assign_{c_id}_{s_id}_{t_id}_{r_id}_{d}_{p}')
    
    def _apply_constraints(self):
        """Apply the fundamental rules of timetabling."""
        class_ids, subject_ids, teacher_ids, room_ids = self.classes.keys(), self.subjects.keys(), self.teachers.keys(), self.rooms.keys()
        for c in class_ids:
            for d in self.days:
                for p in self.periods:
                    self.model.AddExactlyOne(self.assignments.get((c, s, t, r, d, p), 0) for s in subject_ids for t in teacher_ids for r in room_ids)
        for t in teacher_ids:
            for d in self.days:
                for p in self.periods:
                    self.model.AddAtMostOne(self.assignments.get((c, s, t, r, d, p), 0) for c in class_ids for s in subject_ids for r in room_ids)
        for r in room_ids:
            for d in self.days:
                for p in self.periods:
                    self.model.AddAtMostOne(self.assignments.get((c, s, t, r, d, p), 0) for c in class_ids for s in subject_ids for t in teacher_ids)
        for c in class_ids:
            for s_id, s_data in self.subjects.items():
                self.model.Add(sum(self.assignments.get((c, s_id, t, r, d, p), 0) for t in teacher_ids for r in room_ids for d in self.days for p in self.periods) == s_data['periods_per_week'])

    def _apply_soft_constraints(self):
        """Applies teacher preferences as soft constraints with penalties."""
        penalties = []
        for t_id, teacher_data in self.teachers.items():
            preferences = teacher_data.get("preferences")
            if not preferences:
                continue

            # Penalty for teaching in the afternoon if morning is preferred
            if preferences.get("prefers_morning"):
                for d in self.days:
                    for p in range(4, 8): # Afternoon is periods 4, 5, 6, 7
                        for c_id in self.classes:
                            for s_id in self.subjects:
                                for r_id in self.rooms:
                                    key = (c_id, s_id, t_id, r_id, d, p)
                                    if key in self.assignments:
                                        penalties.append(self.assignments[key])

            # Penalty for teaching in the last period if it's avoided
            if preferences.get("avoids_last_period"):
                last_period = self.periods[-1]
                for d in self.days:
                    for c_id in self.classes:
                        for s_id in self.subjects:
                            for r_id in self.rooms:
                                key = (c_id, s_id, t_id, r_id, d, last_period)
                                if key in self.assignments:
                                    penalties.append(self.assignments[key])
        
        # Tell the solver to minimize the sum of all penalties
        if penalties:
            self.model.Minimize(sum(penalties))

    def solve(self, solution_limit=5):
        """Run the solver with hard and soft constraints."""
        self._create_variables()
        self._apply_constraints()
        self._apply_soft_constraints() # Apply the new preferences
        
        solver = cp_model.CpSolver()
        solution_collector = TimetableSolutionCollector(self.assignments, solution_limit)
        solver.Solve(self.model, solution_collector)
        
        return solution_collector.solutions