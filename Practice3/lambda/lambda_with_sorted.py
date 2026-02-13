numbers = [3, 1, 4, 2]

print(sorted(numbers))

print(sorted(numbers, key=lambda x: -x))

words = ["apple", "kiwi", "banana"]
print(sorted(words, key=lambda x: len(x)))

students = [{"name": "Ali", "age": 20},
            {"name": "Dana", "age": 18}]
print(sorted(students, key=lambda x: x["age"]))
