import base64
from BitVector import BitVector
from Crypto.Cipher import AES
from Crypto import Random
import math
from time import sleep
import random

from cqc.pythonLib import CQCConnection, qubit, CQCNoQubitError

"""
BB84 protocol simulator
author: Andrew H. Thorp andrew.thorp.dev@gmail.com

Protocol:
    1.  Alice and Bob connect via quantum network simulator (simulaqron)
    2.  Alice generates n random bits; n > 3k, k = desired key size
    3.  Alice encodes the bits into qubits, randomly chosing to encode using one 
        of two orthoganal bases (Standard and Hadamard basis)
    4.  Alice sends the qubits to Bob
    5.  Bob measures each qubit using a random one of the two bases selected
    6.  Bob sends a bitvector of the bases used to measure to Alice over a classical channel
    7.  Alice responds with a bitvector of which bases were correct
    8.  Alice and Bob discard all qubits that were measured in the wrong basis
    9.  Bob sends Alice k/2 of the measurements to ensure the key was recieved without
        any eavesdropping
    10. Alice responds with whether or not the measured values were correct
    11. The values compared are discarded by both parties, and the rest of the bits are used as
        the key if there were no errors in the compared measurements
"""

# TODO: Abstract these methods into a q-register data type

###################
# Contants
###################
OK = 5
ERROR = 20
TAMPERED = 80

###################
# Opperations
###################
def initiate_keygen(
    key_size=32, name="Alice", recipient="Bob", acceptable_error=0.5, q_logger=print
):
    length = 3 * key_size
    q_logger("Begginning key initialization with {}".format(recipient))
    with get_CQCConnection(name) as conn:
        q_logger("init Connection made")

        # Send bob key length
        q_logger("sending length")
        conn.sendClassical(recipient, length)
        q_logger("Length sent, awaiting confirmation")
        confirmation = int.from_bytes(conn.recvClassical(), byteorder="big")
        q_logger("recieved length conformation")

        # Get key, encode key, send to bob
        key, qubits, bases = create_master_key(conn, length)
        key_bit_vect = BitVector(intVal=key)
        q_logger("Key:           {}".format(bin(key)))
        q_logger("Bases:         {}".format(bin(int(bases))))

        # Send all the qubits sequentially
        for q in qubits:
            conn.sendQubit(q, recipient)
        q_logger("sent qubits!")

        # receive bases used by Bob
        bobs_bases = BitVector(bitlist=conn.recvClassical())
        q_logger("Bobs bases:    {}".format(bin(bobs_bases.int_val())))
        correct_bases = ~bobs_bases ^ bases
        correctness = correct_bases.count_bits() / length
        q_logger("Correct:       {}".format(bin(int(correct_bases))))
        q_logger(correctness)

        # Send bob correct bases
        conn.sendClassical(recipient, correct_bases[:])
        key = truncate_key(key, length, correct_bases)

        if validate_generated_key(length, acceptable_error, key) != OK:
            raise Exception("Poor error rate: {}".format(1 - (len(key) / length)))
            exit(0)

        expected_verify, key = break_into_parts(key, key_size)
        verification_bits = BitVector(bitlist=conn.recvClassical())

        q_logger("Comparing verification bits")
        if expected_verify == verification_bits:
            q_logger("Verification bits OK")
            conn.sendClassical(recipient, OK)
        else:
            q_logger("Bits Tampered")
            conn.sendClassical(recipient, TAMPERED)

        if conn.recvClassical() != OK:
            # raise exception
            pass

        q_logger("Key generated: {}".format(hex(key)))
        return key


def target_keygen(name="Bob", initiator="Alice", q_logger=print):
    q_logger("Receiving keygen")
    with get_CQCConnection(name) as conn:
        q_logger("target Connection made")
        # Receive lenth and initialize varaiables
        length = int.from_bytes(conn.recvClassical(), byteorder="big")
        q_logger("Length recieved")
        conn.sendClassical(initiator, length)
        q_logger("Conformation sent")
        key_length = length / 3
        q_logger(length)
        qubits = [None] * length

        sleep(10)
        for i in range(length):
            qubits[i] = conn.recvQubit()

        q_logger("Recieved qubits!")

        key, bases = measure_random(qubits)
        q_logger("Key:     {}".format(bin(key)))
        q_logger("Bases:   {}".format(bin(bases.int_val())))

        # Since we can only send indiviual numbers from 0-256,
        # we have to split this up into a list of digits.
        # Use slice to extract list from bitvector
        conn.sendClassical(initiator, bases[:])

        correct_bases = BitVector(bitlist=conn.recvClassical())
        q_logger("Correct: {}".format(bin(int(correct_bases))))

        # Remove all incorrectly measured bits
        key = truncate_key(key, length, correct_bases)

        # Break into verification bits and final key
        verification_bits, key = break_into_parts(key, key_length)
        conn.sendClassical(initiator, verification_bits[:])

        response = conn.recvClassical()

        if response == OK:
            q_logger("Key OK to use")
            conn.sendClassical(initiator, OK)
            pass
        elif response == TAMPERED:
            q_logger("Key compromised!")
            pass
        conn.sendClassical(initiator, OK)

        return key


#############################
# Quantum helper functions
#############################


def get_CQCConnection(name):
    with CQCConnection(name) as n:
        return n


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


def validate_generated_key(full_length, acceptable_error, truncated_key):
    error_rate = 1 - (len(truncated_key) / full_length)
    if error_rate <= acceptable_error:
        return OK
    elif error_rate > (1.5 * acceptable_error):
        return TAMPERED
    else:
        return ERROR


"""
break_into_parts breaks the key into the true key and the verification bits.
The given key must be at least 1.5 * key_length bits long.

param key: The current bits generated through exchange
param key_length: The length of the final key

return verification: the first (key_length / 2) bits of the given key
return true_key: the last (key_length) bits of the given key

"""


def break_into_parts(key, key_length):
    # This should be inforced by the validate_generated_key function
    if len(key) < 1.5 * key_length:
        raise Exception("Bits not long enough to break into verification bits and key")

    verification = key[: int(key_length / 2)]
    true_key = key[int(len(key) - key_length) :]
    # print(type(key))
    return verification, key_length


BLOCK_SIZE = 16
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(
    BLOCK_SIZE - len(s) % BLOCK_SIZE
)
unpad = lambda s: s[: -ord(s[len(s) - 1 :])]


def encrypt(raw, key):
    raw = pad(raw)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(bytes(key), AES.MODE_CBC, iv)
    return base64.b64encode(iv + cipher.encrypt(raw))


def decrypt(enc, key):
    enc = base64.b64decode(enc)
    iv = enc[:16]
    cipher = AES.new(bytes(key), AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(enc[16:]))


def test():
    with get_CQCConnection("Alice") as Alice:
        key = random.randint(0, pow(2, 99) - 1)
        # print("Key:    {}".format(hex(key)))
        encoded, bases = encode_random(Alice, key)
        decoded = measure_given_basis(encoded, bases)
        # print("Basis': {}".format(hex(int(bases))))
        # print("Result: {}".format(hex(decoded)))
        # print("Correct:{}".format(key == decoded))
