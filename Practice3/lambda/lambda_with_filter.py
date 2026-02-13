numbers = [1, 2, 3, 4, 5]

print(list(filter(lambda x: x % 2 == 0, numbers)))

print(list(filter(lambda x: x > 3, numbers)))

words = ["hi", "hello", "bye"]
print(list(filter(lambda w: len(w) > 2, words)))

values = [10, 20, 5]
print(list(filter(lambda x: x >= 10, values)))
