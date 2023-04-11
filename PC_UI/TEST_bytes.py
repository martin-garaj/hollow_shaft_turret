
byteorder = 'big'

integer_k = 1
bytes_k = integer_k.to_bytes(length=2, byteorder=byteorder)
_integer_k = int.from_bytes(bytes=bytes_k, byteorder=byteorder, signed=False)


print(integer_k)
print(bytes_k)
print(_integer_k)