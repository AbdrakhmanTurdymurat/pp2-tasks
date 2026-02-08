class A:
    def show(self):
        print("A")

class B:
    def display(self):
        print("B")

class C(A, B):
    pass

obj = C()
obj.show()
obj.display()
