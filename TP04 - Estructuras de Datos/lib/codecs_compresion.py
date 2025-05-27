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
        byte = (
            n & 0b01111111
        )  # Toma los 7 bits menos significativos de n  -> operador AND "&"
        n >>= 7  # Desplaza n 7 bits a la derecha (elimina los 7 bits ya codificados)
        if n:
            bytes_list.append(byte)  # MSB=0 (no es el último byte)
            # Se guardan primero los bytes menos significativos
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


def elias_gamma_encode_number(n: int) -> bitarray:
    """
    Codifica un entero n >= 1 en Elias-gamma (bitarray).
    """
    if n <= 0:
        raise ValueError("Elias-gamma solo para n >= 1")
    bin_len = int(math.log2(n))  # redondea hacia abajo (numero base de la diapositiva)
    offset = n - 2**bin_len  # offset   # si k=17, entonces offset = 1
    ba = bitarray()
    # Unario: bin_len ceros y un 1
    ba.extend([0] * bin_len)
    ba.append(1)
    # Binario: los bits del offset en bin_len bits
    # Para cada posición de bit desde el más significativo al menos significativo
    for i in reversed(range(bin_len)):
        # si k=17, entonces offset = 1 = 0b0001
        # Extrae el bit en la posición 'i' de 'offset' y lo agrega a 'ba'
        ba.append(
            (offset >> i) & 0b00000001
        )  # Desplaza los bits de offset a la derecha i posiciones, y enmascara con 1 para obtener el bit menos significativo, para agregar los bits de mayor a menor peso
    return ba


def elias_gamma_encode_list(nums: list[int]) -> bytes:
    """
    Codifica una lista de enteros en Elias-gamma, concatenando la codificación de cada uno y retorna bytes.
    """
    ba = bitarray()
    for n in nums:
        ba.extend(elias_gamma_encode_number(n))
    return ba.tobytes()


def elias_gamma_decode_list(ba: bitarray) -> list[int]:
    """
    Decodifica una bitarray Elias-gamma a una lista de enteros.
    Para cada número:
    - Cuenta la cantidad de ceros hasta el primer 1 (unario).
    - Lee esa cantidad de bits binarios y los concatena al 1 inicial.
    - Reconstruye el número original.
    """
    nums: list[int] = []
    i = 0
    n = len(ba)
    while i < n:
        # Leer unario: cuenta ceros hasta el primer 1
        unary_len = 0
        while i < n and not ba[i]:  # cuando ba[i]=1 corta
            unary_len += 1
            i += 1
        if i >= n:
            break  # Si llegamos al final, salimos
        i += 1  # Saltar el 1 (el bit separador)
        # Leer binario de unary_len bits (el offset)
        b = 0  # Inicializamos el offset en 0
        for shift in reversed(range(unary_len)):
            # Recorremos los bits del offset de mayor a menor peso
            if i < n and ba[i]:
                b |= (
                    1 << shift
                )  # Si el bit está en 1, lo sumamos en la posición correspondiente
            i += 1
        # El número original es el 1 más significativo seguido del offset
        val = (1 << unary_len) | b  # Usamos OR para concatenar el 1 y el offset
        nums.append(val)
    return nums


# -------------------- DGaps --------------------


def compute_dgaps(nums: list[int]) -> list[int]:
    """
    Convierte una lista de enteros ordenados en DGaps.
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
        eg_bytes = elias_gamma_encode_list(original)
        ba = bitarray()
        ba.frombytes(eg_bytes)
        decoded = elias_gamma_decode_list(ba)
        if original != decoded:
            print(f"[ERROR] Elias-gamma falla para lista de largo {L}")
            print("Original:", original)
            print("Decodificado:", decoded)
        else:
            print(f"[OK] Elias-gamma correcto para lista de largo {L}")
