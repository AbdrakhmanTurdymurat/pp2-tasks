x = 4       # x is of type int
x = "Sally" # x is now of type str
print(x)

#Variables do not need to be declared
x = str(3)    # x will be '3'
y = int(3)    # y will be 3
z = float(3)  # z will be 3.0

#how to get the data type 
x = 5
y = "John"
print(type(x))
print(type(y))

#variable names
myvar = "John"
my_var = "John"
_my_var = "John"
myVar = "John"
MYVAR = "John"
myvar2 = "John"

#multiple variables in one line
x = y = z = "Orange"
print(x)
print(y)
print(z)

#unpacking
fruits = ["apple", "banana", "cherry"]
x, y, z = fruits
print(x)
print(y)
print(z)

#output variables 
x = "Python"
y = "is"
z = "awesome"
print(x)
print(x, y, z)
print(x + y + z)

#global variables
#ex 1
x = "awesome" #this is global variable 

def myfunc():
  x = "fantastic"
  print("Python is " + x)

myfunc()

print("Python is " + x)

#ex 2
x = "awesome"

def myfunc():
  global x #To change the value of a global variable inside a function
  x = "fantastic"

myfunc()

print("Python is " + x)