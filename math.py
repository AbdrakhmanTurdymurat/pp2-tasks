#1
import math

d = float(input("Input degree: "))
r = d * (math.pi / 180)

print("Output radian:", round(radian, 6))

#2
h = float(input("Height: "))
bf= float(input("Base, first value: "))
bs= float(input("Base, second value: "))

out = ((bs + bf)/2)*h

print("Expected Output: ", out)

#3
import math

n = int(input("Input number of sides: "))
s = float(input("Input the length of a side: "))

area = (n * s**2) / (4 * math.tan(math.pi / n))

print("The area of the polygon is:", int(area))

#4
l = float(input("Length of base: "))
h = float(input("Height of parallelogram: "))

print("Expected Output: ", l * h)