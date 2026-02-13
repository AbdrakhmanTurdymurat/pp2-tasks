class Student:
    def __init__(self, name, age):
        self.name = name
        self.age = age

s1 = Student("Alex", 18)
print(s1.name)


class Car:
    def __init__(self, brand):
        self.brand = brand

c = Car("Toyota")
print(c.brand)
