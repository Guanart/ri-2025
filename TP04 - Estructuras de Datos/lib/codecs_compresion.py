from bitarray import bitarray
import math

# -------------------- VByte --------------------
def vbyte_encode_number(n: int) -> bytes:
    """Codifica un entero n >= 0 en VByte (devuelve bytes)."""
    bytes_list = []
    while True:
        byte = n & 0b01111111
        n >>= 7
        if n:
            bytes_list.append(byte)
        else:
            bytes_list.append(byte | 0b10000000)
            break
    return bytes(bytes_list)

def vbyte_encode_list(nums: list[int]) -> bytes:
    """Codifica una lista de enteros en VByte."""
    return b"".join(vbyte_encode_number(n) for n in nums)

def vbyte_decode_list(data: bytes) -> list[int]:
    """Decodifica una secuencia de bytes VByte a una lista de enteros."""
    nums = []
    n = 0
    shift = 0
    for b in data:
        if b & 0b10000000:
            n |= (b & 0b01111111) << shift
            nums.append(n)
            n = 0
            shift = 0
        else:
            n |= (b & 0b01111111) << shift
            shift += 7
    return nums

# -------------------- Elias-gamma --------------------
def Unary(x):
    """Codifica x en unario: (x-1) ceros seguidos de un 1."""
    return (x-1)*'0'+'1'

def Binary(x, length=1):
    """Codifica x en binario de longitud length (con ceros a la izquierda)."""
    s = '{0:0%db}' % length
    return s.format(x)

def elias_gamma_encode_number(n: int) -> bitarray:
    """Codifica un entero n >= 1 en Elias-gamma (bitarray, versión didáctica)."""
    if n <= 0:
        raise ValueError("Elias-gamma solo para n >= 1")
    bin_len = int(math.log2(n))
    b = n - 2**bin_len
    unary = Unary(bin_len+1)
    binary = Binary(b, bin_len)
    bits = unary + binary
    return bitarray(bits)

def elias_gamma_encode_list(nums: list[int]) -> bitarray:
    ba = bitarray()
    for n in nums:
        ba.extend(elias_gamma_encode_number(n))
    return ba

def elias_gamma_decode_list(ba: bitarray) -> list[int]:
    """Decodifica una bitarray Elias-gamma a una lista de enteros (versión didáctica)."""
    nums = []
    i = 0
    n = len(ba)
    while i < n:
        # Leer unario
        unary_len = 0
        while i < n and not ba[i]:
            unary_len += 1
            i += 1
        if i >= n:
            break
        i += 1  # saltar el 1
        # Leer binario de unary_len bits
        b = 0
        for j in range(unary_len):
            if i < n and ba[i]:
                b |= 1 << (unary_len-1-j)
            i += 1
        val = (1 << unary_len) + b
        nums.append(val)
    return nums

# -------------------- DGaps --------------------
def compute_dgaps(nums: list[int]) -> list[int]:
    """Convierte una lista de enteros ordenados en DGaps."""
    if not nums:
        return []
    dgaps = [nums[0]]
    for i in range(1, len(nums)):
        dgaps.append(nums[i] - nums[i-1])
    return dgaps

def restore_from_dgaps(dgaps: list[int]) -> list[int]:
    """Reconstruye la lista original a partir de DGaps."""
    if not dgaps:
        return []
    nums = [dgaps[0]]
    for d in dgaps[1:]:
        nums.append(nums[-1] + d)
    return nums
