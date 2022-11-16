from functools import cache

# print("x y z w")
# for x in range(0, 2):
#     for y in range(0, 2):
#         for z in range(0, 2):
#             for w in range(0, 2):
#                 if not((x <= y) == (z <= w) or (x and w)):
#                     print(x, y, z, w)

# a = set()
# for t in range(10, 1001):
#     n = bin(t)[2:]
#     n = n[1:]
#     if n[1] == '0':
#         n = n[n.find('1'):]
#     if n == 0:
#         a.add(n)
#     else:
#         a.add(str(int(n, 2)))
# print(a)
# print(len(a))


# print(30*2/1.5/4)


# print((5+5+8*4)/8)
# print(6)
# print(6*25)


s = '9' * 1000
while ('999' in s) or ('888' in s):
    if '888' in s:
        s = s.replace('888', '9', 1)
    else:
        s = s.replace('999', '8', 1)
print(s)

s = '9' * 1000
while ('999' in s) or ('888' in s):
    if '888' in s:
        s = s.replace ('888', '9', 1)
    if '999' in s:
        s = s.replace ('999', '8', 1)
print(s)

# print(str(4**2020 + 2**2017 - 15).count('1'))


# def f(n):
#     if n == 1:
#         return 1
#     return f(n-1)+n
# print(f(40))


# f = open('17.txt')
# a = list(map(int, f.readlines()))
# n = len(a)
# s = [i for i in a if i % 2 == 0]
# m = sum(s) / len(s)
# b = []
# for i in range(n - 1):
#     if (a[i] % 3 == 0) or (a[i+1] % 3 == 0) and (a[i] < m or a[i+1] < m):
#         b.append(a[i] + a[i+1])
# print(len(b))
# print(max(b))


# f = open('24.txt')
# m = -10
# s = f.readline().split('XZZY')
# for i in s:
#     if len(i) > m:
#         m = len(i)
# print(m)


# f = open('26.txt')
# a = list(map(int, f.readlines()))
# b = [i for i in a if i % 2 != 0]
# s = 0
# x = 0
# y = 0
# c = []
# na = set(a)
# for i in range(1, len(b) - 1):
#     for j in range(i + 1, len(b)):
#         s = (b[i] + b[j]) // 2
#         if s in na:
#             c.append(s)
#
# print(len(c), max(c))


