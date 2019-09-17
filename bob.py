from bb84.bb84 import *
from BitVector import BitVector

with CQCConnection("Bob") as Bob:
    print("Connection made")
    # Receive lenth and initialize varaiables
    length = int.from_bytes(Bob.recvClassical(), byteorder="big")
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
    send_val = bases[:]
    Bob.sendClassical("Alice", send_val)

    correct_bases = BitVector(bitlist=Bob.recvClassical())
    print("Correct: {}".format(bin(int(correct_bases))))

    truncated_key = truncate_key(key, length, correct_bases)

    print(hex(truncated_key.int_val()))
