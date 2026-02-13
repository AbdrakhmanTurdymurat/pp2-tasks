numbers = [1, 2, 3, 4]

print(list(map(lambda x: x * 2, numbers)))

print(list(map(lambda x: x ** 2, numbers)))

names = ["a", "b", "c"]
print(list(map(lambda x: x.upper(), names)))

values = [5, 10]
print(list(map(lambda x: x + 1, values)))
