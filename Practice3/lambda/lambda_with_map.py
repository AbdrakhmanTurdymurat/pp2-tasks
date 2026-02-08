numbers = [1, 2, 3, 4]

result = map(lambda x: x * 2, numbers)
print(list(result))


names = ["a", "b", "c"]
upper = map(lambda x: x.upper(), names)
print(list(upper))


values = [5, 10, 15]
squared = map(lambda x: x ** 2, values)
print(list(squared))
