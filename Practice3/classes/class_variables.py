class School:
    school_name = "High School"

    def __init__(self, student):
        self.student = student

s1 = School("Ali")
s2 = School("Dana")

print(s1.school_name)
print(s2.student)


School.school_name = "New School"
print(s1.school_name)
