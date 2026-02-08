numbers = [1, 2, 3, 4, 5]

even = filter(lambda x: x % 2 == 0, numbers)
print(list(even))


greater = filter(lambda x: x > 3, numbers)
print(list(greater))


words = ["hi", "hello", "bye"]
long_words = filter(lambda w: len(w) > 2, words)
print(list(long_words))
