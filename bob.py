from bb84.bb84 import *
from BitVector import BitVector

with CQCConnection("Bob") as Bob:
    print("Connection made")
    # Receive lenth and initialize varaiables
    length = int.from_bytes(Bob.recvClassical(), byteorder="big")
    key_length = length / 3
    Bob.sendClassical("Alice", length)
    print(length)
    qubits = [None] * length

    for i in range(length):
        qubits[i] = Bob.recvQubit()

    bases = BitVector(bitlist=Bob.recvClassical())

    key, bases = measure_random(qubits)
    print("Key:     {}".format(bin(key)))
    print("Bases:   {}".format(bin(bases.int_val())))

    # Since we can only send indiviual numbers from 0-256,
    # we have to split this up into a list of digits.
    # Use slice to extract list from bitvector
    Bob.sendClassical("Alice", bases[:])

    correct_bases = BitVector(bitlist=Bob.recvClassical())
    print("Correct: {}".format(bin(int(correct_bases))))

    # Remove all incorrectly measured bits
    key = truncate_key(key, length, correct_bases)

    # Break into verification bits and final key
    verification_bits, key = break_into_parts(key, key_length)
    Bob.sendClassical("Alice", verification_bits[:])

    response = Bob.recvClassical()

    if response == OK:
        print("Key OK to use")
    elif response == TAMPERED:
        print("Key compromised!")
        pass

    # Test decrypt message
    encrypted = Bob.recvClassical()
    message = decrypt(encrypted, int(key))
    print(message)
