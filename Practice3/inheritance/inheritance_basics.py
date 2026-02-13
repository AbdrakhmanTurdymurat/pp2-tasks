class Animal:
    def speak(self):
        print("Animal sound")

class Dog(Animal):
    pass

dog = Dog()
dog.speak()


class Cat(Animal):
    pass

cat = Cat()
cat.speak()
