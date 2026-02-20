class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def intro(self):
        return f"Hi, I'm {self.name}, I'm {self.age}"


class Student(Person):
    def __init__(self, name, age, year):
        super().__init__(name, age)
        self.year = year

    def grade(self):
        return f"Hi, I'm {self.year} year student, my name is {self.name}"


class Doctor(Person):
    def __init__(self, name, age, hname, major):
        super().__init__(name, age)
        self.hname = hname
        self.major = major

    def hospital(self):
        return f"Hi, I'm Dr. {self.name}, a {self.major}, working at {self.hname}"


p1 = Person("Ali", 18)
print(p1.intro())

p2 = Student("Sara", 20, 4)
print(p2.intro())
print(p2.grade())

p3 = Doctor("John", 35, "Hospital #14", "Surgeon")
print(p3.intro())
print(p3.hospital())