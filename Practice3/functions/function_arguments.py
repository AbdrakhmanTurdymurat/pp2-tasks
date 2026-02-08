sdef student(name, age):
    print(name, age)

student("John", 18)


def country(name="Kazakhstan"):
    print(name)

country()
country("Japan")


def add(a, b, c):
    print(a + b + c)

add(1, 2, 3)


def print_list(items):
    for i in items:
        print(i)

print_list([1, 2, 3])
