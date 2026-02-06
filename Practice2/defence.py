students = {
    "Али": 85,
    "Айша": 92,
    "Нурлан": 48,
    "Дана": 78,
    "Ержан": 95
}

def get_gpa(score):
    if score >= 95:
        return 4.0
    elif score >= 90:
        return 3.7
    elif score >= 85:
        return 3.3
    elif score >= 80:
        return 3.0
    elif score >= 75:
        return 2.7
    elif score >= 70:
        return 2.3
    elif score >= 65:
        return 2.0
    elif score >= 60:
        return 1.7
    elif score >= 55:
        return 1.3
    elif score >= 50:
        return 1.0
    else:
        return 0.0

for name, score in students.items():
    gpa = get_gpa(score)
    print(f"{name}: {score} -> GPA {gpa}")