numbers = [10, 20, 30]
names = ["Alice", "Bob", "Charlie"]

# ENUMERATE
for index, value in enumerate(numbers):
    print(f"Index {index}: {value}")

# ZIP
combined = list(zip(names, numbers))
print("Zipped:", combined)

# SORTED
unsorted_list = [5, 2, 9, 1]
print("Sorted:", sorted(unsorted_list))

# TYPE CONVERSION
x = "123"
print("String to int:", int(x))
print("Int to float:", float(x))