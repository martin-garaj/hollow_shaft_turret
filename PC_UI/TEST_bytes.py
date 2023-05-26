
byteorder = 'big'

integer_k = 1
bytes_k = integer_k.to_bytes(length=2, byteorder=byteorder)
_integer_k = int.from_bytes(bytes=bytes_k, byteorder=byteorder, signed=False)


print(integer_k)
print(bytes_k)
print(_integer_k)

import time

print(time.time())


import collections

d = collections.deque(maxlen=10)
for i in range(20):
    d.append((time.time(), i))
    
print(d[0])
print(d[-1])


def fun(a, b, c=0):
    print(f"{a}-{b}-{c}")

# d = {'a':1, 'b':2, 'd':1}
d = {'a':1, 'b':2}

fun(**d)