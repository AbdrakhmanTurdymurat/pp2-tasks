#1
a = int(input("Enter a number: "))
s = (i ** 2 for i in range(1, a + 1))

for i in s:
    print(i)

#2
n = int(input("Enter a number: "))
e = (i for i in range(0, n + 1) if i % 2 == 0)

print(",".join(str(i) for i in e))

#3
def d34(n):
    for i in range(0, n + 1):
        if i % 3 == 0 and i % 4 == 0:
            yield i

n = int(input("Enter a number: "))
for nb in d34(n):
    print(nb)
#4
def s(a, b):
    for i in range(a, b + 1):
        yield i ** 2

s = int(input("start: "))
e = int(input("end: "))

for v in s(s, e):
    print(v)
#5
n = int(input("Enter a number: "))
s = (i for i in range( n, -1, -1))

for i in s:
    print(i)