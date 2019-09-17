from BitVector import BitVector
import math
import random

from cqc.pythonLib import CQCConnection, qubit, CQCNoQubitError

"""
BB84 protocol simulator
author: Andrew H. Thorp andrew.thorp.dev@gmail.com

Protocol:
    1.  Alice and Bob connect via quantum network simulator (simulaqron)
    2.  Alice generates n random bits; n > 2m, m = desired key size
    3.  Alice encodes the bits into qubits, randomly chosing to encode using one 
        of two orthoganal bases (Standard and Hadamard basis)
    4.  Alice sends the qubits to Bob
    5.  Bob measures each qubit using a random one of the two bases selected
    6.  Bob sends a bitvector of the bases used to measure to Alice over a classical channel
    7.  Alice responds with a bitvector of which bases were correct
    8.  Alice and Bob discard all qubits that were measured in the wrong basis
    9.  Bob sends Alice a small number of the measurements to ensure the key was recieved without
        any eavesdropping
    10. Alice responds with whether or not the measured values were correct
    11. The values compared are discarded by both parties, and the rest of the bits are used as
        the key 
"""

# TODO: Abstract these methods into a q-register data type

"""
Quantum helper functions
"""

# Generate random-basis quantum-encoded key of length n
def create_master_key(connection, key_length):
    key = random.randint(0, pow(2, key_length) - 1)
    encoded, bases = encode_random(connection, key)
    return key, encoded, bases


# Return the length, in bits, needed to store a number (ceilinged to bytes)
def get_length(num):
    return math.ceil(num.bit_length() / 8) * 8


# Intake a CQCConnection and a number of arbitrary length
#
# Return an array of qubits encoding the number and a bitvector of the basis used for each bit
def encode_random(connection, number):
    length = get_length(number)
    bases = BitVector(size=length)
    encoded = [None] * length
    num_vector = BitVector(intVal=number, size=length)

    for i in range(length):
        encoded[i] = qubit(connection)
        if num_vector[i] != 0:
            encoded[i].X()  # Apply not gate

        # Randomly apply a quarter spin to put in Hadamard basis
        if random.randint(0, 1) == 1:
            encoded[i].H()
            # update bitvector of bases
            bases[i] = 1

    return encoded, bases


# Intake a q-encoded number and measure each qubit on a random basis
# return the bases chosen as a bitvector
def measure_random(encoded_num):
    length = len(encoded_num)
    decoded_num = BitVector(size=length, intVal=0)
    bases = BitVector(size=length)

    for i in range(length):
        # Randomly apply a quarter spin to put in Hadamard basis
        if random.randint(0, 1) == 1:
            encoded_num[i].H()
            # update bitvector of bases
            bases[i] = 1

        # Measure the bit and insert it into the decoded number
        measure = encoded_num[i].measure()
        decoded_num[i] = measure

    return int(decoded_num), bases


# Intake a q-encoded number and a bitvector of bases
# and measure each qubit per basis
def measure_given_basis(encoded_num, bases):
    length = len(encoded_num)
    decoded_num = 0

    for i in range(length):
        # If the basis is hadamard, apply the H gate to put it into standard basis
        if bases[i] > 0:
            encoded_num[i].H()

        # Measure the bit and insert it into the decoded number
        decoded_num |= (1 & encoded_num[i].measure()) << i

    return decoded_num


# Given a number, the number of bits to encode, and a connection to a CQC network,
# encode that number into an array of qubits and return the result
def encode_standard(connection, number):
    # Determine number of bits needed to store the number
    length = get_length(number)
    qubits = [None] * length
    for i in range(length):
        qubits[i] = qubit(connection)
        if (number & (1 << i)) != 0:
            qubits[i].X()
    return qubits


# Measure a q-register in the standard basis
def measure_standard(encoded_num):
    length = len(encoded_num)
    decoded_num = 0
    for i in range(length):
        bit = (1 & encoded_num[i].measure()) << i
        decoded_num |= bit
    return decoded_num


# Given a number, the number of bits to encode, and a connection to a CQC network,
# encode that number into an array of qubits using the Hadamard basis
def encode_hadamard(connection, number):
    # Determine number of bits needed to store the number
    length = get_length(number)
    qubits = [None] * length
    for i in range(length):
        qubits[i] = qubit(connection)
        if (number & (1 << i)) != 0:
            qubits[i].X()
        qubits[i].H()
    return qubits


# Measure a q-register in the Hadamard basis
def measure_hadamard(encoded_num):
    length = len(encoded_num)
    decoded_num = 0
    for i in range(length):
        encoded_num[i].H()
        bit = (1 & encoded_num[i].measure()) << i
        decoded_num |= bit
    return decoded_num


def truncate_key(key, length, correct_bases):
    key_bit_vect = BitVector(intVal=key, size=length)
    truncated_key = [key_bit_vect[i] for i in range(length) if correct_bases[i] is 1]
    return BitVector(bitlist=truncated_key)


def test():
    with CQCConnection("Alice") as Alice:
        key = random.randint(0, pow(2, 99) - 1)
        print("Key:    {}".format(hex(key)))
        encoded, bases = encode_random(Alice, key)
        decoded = measure_given_basis(encoded, bases)
        print("Basis': {}".format(hex(int(bases))))
        print("Result: {}".format(hex(decoded)))
        print("Correct:{}".format(key == decoded))
