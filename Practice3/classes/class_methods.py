class Car:
    def __init__(self, brand):
        self.brand = brand

    def drive(self):
        print(self.brand, "is driving")

car = Car("Toyota")
car.drive()
