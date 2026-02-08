numbers = [3, 1, 4, 2]
sorted_nums = sorted(numbers)
print(sorted_nums)


sorted_desc = sorted(numbers, key=lambda x: -x)
print(sorted_desc)


words = ["apple", "kiwi", "banana"]
sorted_words = sorted(words, key=lambda x: len(x))
print(sorted_words)
