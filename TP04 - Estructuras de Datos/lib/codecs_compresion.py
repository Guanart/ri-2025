from bitarray import bitarray
import math

# -------------------- VByte --------------------


def vbyte_encode_number(n: int) -> bytes:
    """
    Codifica un entero n >= 0 en VByte (Variable Byte).
    El entero se divide en bloques de 7 bits. Cada byte contiene 7 bits de datos y 1 bit de control (MSB):
    - Si el MSB=1, es el último byte del número.
    - Si el MSB=0, hay más bytes por venir.
    Ejemplo:  n = 130 -> [0b00000010, 0b10000001]
    """
    bytes_list = []
    while True:
        byte = n & 0b01111111  # Toma los 7 bits menos significativos de n  -> operador AND "&"
        n >>= 7  # Desplaza n 7 bits a la derecha (elimina los 7 bits ya codificados)
        if n:
            bytes_list.append(byte)  # MSB=0 (no es el último byte)
        else:
            bytes_list.append(byte | 0b10000000)  # MSB=1 (último byte)
            break
    # IMPORTANTE: los bytes se agregan en orden little-endian (primero los menos significativos)
    return bytes(bytes_list)


def vbyte_encode_list(nums: list[int]) -> bytes:
    """
    Codifica una lista de enteros usando VByte.
    Simplemente concatena la codificación VByte de cada número.
    """
    return b"".join(vbyte_encode_number(n) for n in nums)


def vbyte_decode_list(data: bytes) -> list[int]:
    """
    Decodifica una secuencia de bytes VByte a una lista de enteros.
    Lee byte a byte:
    - Si el MSB=1, es el último byte del número actual.
    - Si el MSB=0, sigue leyendo y acumulando los bits.
    El primer byte es el menos significativo, el último (con MSB=1) es el más significativo.
    """
    nums = []
    n = 0
    shift = 0
    for b in data:
        data_bits = b & 0b01111111
        n |= data_bits << shift
        if b & 0b10000000:  # Si el bit más significativo es 1, es el último byte
            nums.append(n)
            n = 0
            shift = 0
        else:
            shift += 7
    return nums


# -------------------- Elias-gamma --------------------


def Unary(x):
    """
    Codifica x en unario: (x-1) ceros seguidos de un 1.
    Ejemplo: x=4 -> '0001'
    """
    return (x - 1) * "0" + "1"


def Binary(x, length=1):
    """
    Codifica x en binario de longitud 'length' (rellenando con ceros a la izquierda si es necesario).
    Ejemplo: x=3, length=4 -> '0011'
    """
    s = "{0:0%db}" % length
    return s.format(x)


def elias_gamma_encode_number(n: int) -> bitarray:
    """
    Codifica un entero n >= 1 en Elias-gamma (bitarray).
    - Escribe el log2(n) en unario (cantidad de bits menos 1, en ceros, seguido de un 1).
    - Luego escribe los bits binarios de n sin el bit más significativo.
    Ejemplo: n=9 -> binario '1001' -> unario '0001' + binario '001' -> '0001001'
    """
    if n <= 0:
        raise ValueError("Elias-gamma solo para n >= 1")
    bin_len = int(math.log2(n))  # Cantidad de bits binarios menos 1
    b = n - 2**bin_len  # Parte binaria sin el bit más significativo
    unary = Unary(bin_len + 1)  # Codificación unaria
    binary = Binary(b, bin_len)  # Parte binaria
    bits = unary + binary  # Concatenar ambos
    return bitarray(bits)


def elias_gamma_encode_list(nums: list[int]) -> bitarray:
    """
    Codifica una lista de enteros en Elias-gamma, concatenando la codificación de cada uno.
    """
    ba = bitarray()
    for n in nums:
        ba.extend(elias_gamma_encode_number(n))
    return ba


def elias_gamma_decode_list(ba: bitarray) -> list[int]:
    """
    Decodifica una bitarray Elias-gamma a una lista de enteros.
    Para cada número:
    - Cuenta la cantidad de ceros hasta el primer 1 (unario).
    - Lee esa cantidad de bits binarios y los concatena al 1 inicial.
    - Reconstruye el número original.
    """
    nums = []
    i = 0
    n = len(ba)
    while i < n:
        # Leer unario: cuenta ceros hasta el primer 1
        unary_len = 0
        while i < n and not ba[i]:
            unary_len += 1
            i += 1
        if i >= n:
            break  # Si llegamos al final, salimos
        i += 1  # Saltar el 1
        # Leer binario de unary_len bits
        b = 0
        for j in range(unary_len):
            if i < n and ba[i]:
                b |= 1 << (unary_len - 1 - j)
            i += 1
        val = (1 << unary_len) + b  # Reconstruir el número original
        nums.append(val)
    return nums


# -------------------- DGaps --------------------


def compute_dgaps(nums: list[int]) -> list[int]:
    """
    Convierte una lista de enteros ordenados en DGaps (diferencias sucesivas).
    El primer elemento se mantiene igual, el resto es la diferencia con el anterior.
    Ejemplo: [3, 7, 10] -> [3, 4, 3]
    """
    if not nums:
        return []
    dgaps = [nums[0]]
    for i in range(1, len(nums)):
        dgaps.append(nums[i] - nums[i - 1])
    return dgaps


def restore_from_dgaps(dgaps: list[int]) -> list[int]:
    """
    Reconstruye la lista original a partir de DGaps.
    El primer elemento se mantiene igual, el resto se suma acumulativamente.
    Ejemplo: [3, 4, 3] -> [3, 7, 10]
    """
    if not dgaps:
        return []
    nums = [dgaps[0]]
    for d in dgaps[1:]:
        nums.append(nums[-1] + d)
    return nums

if __name__ == "__main__":
    # Test unitario de Elias-gamma
    from random import randint

    for L in [3, 10, 100, 1000]:
        original = [randint(1, 100) for _ in range(L)]
        ba = elias_gamma_encode_list(original)
        decoded = elias_gamma_decode_list(ba)
        if original != decoded:
            print(f"[ERROR] Elias-gamma falla para lista de largo {L}")
            print("Original:", original)
            print("Decodificado:", decoded)
        else:
            print(f"[OK] Elias-gamma correcto para lista de largo {L}")