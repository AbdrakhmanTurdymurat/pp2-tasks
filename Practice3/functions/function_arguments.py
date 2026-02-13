def student(name, age):
    print(name, age)

student("John", 18)


def country(name="Kazakhstan"):
    print(name)

country()
country("Japan")


def keyword_example(first, second):
    print(first, second)

keyword_example(second="B", first="A")


def pass_list(items):
    for item in items:
        print(item)

pass_list([1, 2, 3])
