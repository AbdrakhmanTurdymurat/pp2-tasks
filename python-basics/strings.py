print("Hello")
print('Hello')

a = """Lorem ipsum dolor sit amet,
consectetur adipiscing elit,
sed do eiusmod tempor incididunt
ut labore et dolore magna aliqua."""
print(a)

a = '''Lorem ipsum dolor sit amet,
consectetur adipiscing elit,
sed do eiusmod tempor incididunt
ut labore et dolore magna aliqua.'''
print(a)

#slicing 
b = "Hello, World!"
print(b[2:5])

b = "Hello, World!"
print(b[:5]) #slice from the start 

b = "Hello, World!"
print(b[2:]) #slice to the end

b = "Hello, World!"
print(b[-5:-2]) #negative indexing 

#The upper() method returns the string in upper case:
a = "Hello, World!"
print(a.upper())

#The lower() method returns the string in lower case:
a = "Hello, World!"
print(a.lower())

#The strip() method removes any whitespace from the beginning or the end:
a = " Hello, World! "
print(a.strip()) # returns "Hello, World!"

#The replace() method replaces a string with another string:
a = "Hello, World!"
print(a.replace("H", "J"))

#The split() method splits the string into substrings if it finds instances of the separator:
a = "Hello, World!"
print(a.split(",")) # returns ['Hello', ' World!']

#concatenate 
a = "Hello"
b = "World"
c = a + b
print(c)

#formating
age = 36
txt = f"My name is John, I am {age}"
print(txt)

#escape characters 
txt = "We are the so-called \"Vikings\" from the north."
print (txt)
