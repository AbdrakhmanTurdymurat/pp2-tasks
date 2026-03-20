from functools import reduce

numbers = [1, 2, 3, 4, 5]

# MAP
squared = list(map(lambda x: x**2, numbers))

# FILTER
evens = list(filter(lambda x: x % 2 == 0, numbers))

# REDUCE
total = reduce(lambda a, b: a + b, numbers)

print("Original:", numbers)
print("Squared:", squared)
print("Evens:", evens)
print("Sum:", total)