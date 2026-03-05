import re

#task 1
pattern1 = r"ab*"
print(re.findall(pattern1, "a ab abb abbb ac"))

#task 2
pattern2 = r"ab{2,3}"
print(re.findall(pattern2, "ab abb abbb abbbb"))

#task 3
pattern3 = r"[a-z]+_[a-z]+"
print(re.findall(pattern3, "hello_world test_case Hello_world"))

#task 4
pattern4 = r"[A-Z][a-z]+"
print(re.findall(pattern4, "Hello World PYTHON Test"))

#task 5
pattern5 = r"a.*b"
print(re.findall(pattern5, "axxb a123b acb ahello b"))

#task 6
text = "Hello, world. Python is great"
result = re.sub(r"[ ,\.]", ":", text)
print(result)

#task 7
snake = "hello_world_example"
camel = re.sub(r"_([a-z])", lambda m: m.group(1).upper(), snake)
print(camel)

#task 8
text = "HelloWorldPython"
result = re.split(r"(?=[A-Z])", text)
print(result)

#task 9
text = "HelloWorldPython"
result = re.sub(r"([A-Z])", r" \1", text).strip()
print(result)

#task 10
camel = "helloWorldExample"
snake = re.sub(r"([A-Z])", r"_\1", camel).lower()
print(snake)