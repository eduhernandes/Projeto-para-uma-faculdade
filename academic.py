from dataclasses import dataclass

@dataclass(frozen=True)
class AcademicSummary:
    average: float | None
    attendance_pct: float | None
    absences: int
    status: str


def calculate_summary(enrollment):
    graded = [g for g in enrollment.grades if g.score is not None and g.assessment.max_score > 0]
    total_weight = sum(g.assessment.weight for g in graded)
    if total_weight:
        normalized = sum((g.score / g.assessment.max_score) * 10 * g.assessment.weight for g in graded)
        average = round(normalized / total_weight, 2)
    else:
        average = None

    present = sum(1 for a in enrollment.attendance if a.status in {'present', 'justified'})
    absent = sum(1 for a in enrollment.attendance if a.status == 'absent')
    counted = present + absent
    pct = round(present / counted * 100, 2) if counted else None

    rules = enrollment.academic_class.semester
    required = rules.number_of_assessments
    enough_assessments = required is None or len(graded) >= required
    if average is None or pct is None or not enough_assessments:
        status = 'Pendente'
    else:
        status = 'Aprovado' if average >= rules.minimum_average and pct >= rules.minimum_attendance_pct and (rules.maximum_absences is None or absent <= rules.maximum_absences) else 'Reprovado'
    return AcademicSummary(average, pct, absent, status)
