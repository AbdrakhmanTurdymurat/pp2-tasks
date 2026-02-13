class Bird:
    def sound(self):
        print("Bird sound")

class Sparrow(Bird):
    def sound(self):
        print("Chirp")

b = Sparrow()
b.sound()


class Parrot(Bird):
    def sound(self):
        print("Talk")

p = Parrot()
p.sound()
