from bb84.bb84 import *
from BitVector import BitVector

with CQCConnection("Alice") as Alice:
    print("Connection made")
    length = 32

    # Send bob key length
    Alice.sendClassical("Bob", length)
    confirmation = int.from_bytes(Alice.recvClassical(), byteorder="big")

    print("Conform key length: {}".format(confirmation == length))

    # Get key, encode key, send to bob
    key, qubits, bases = create_master_key(Alice, length)
    key_bit_vect = BitVector(intVal=key)
    print("Key:           {}".format(bin(key)))
    print("Bases:         {}".format(bin(int(bases))))

    # If we measaure in the standard basis on Bob's block, we should see the 0 numbers be correct
    for q in qubits:
        Alice.sendQubit(q, "Bob")

    Alice.sendClassical("Bob", bases)

    # receive bases used by Bob
    bobs_bases = BitVector(bitlist=Alice.recvClassical())
    print("Bobs bases:    {}".format(bin(bobs_bases.int_val())))
    correct_bases = ~bobs_bases ^ bases
    print("Correct:       {}".format(bin(int(correct_bases))))
    print(type(correct_bases))

    truncated_key = truncate_key(key, length, correct_bases)

    print(hex(truncated_key.int_val()))

    # Send bob correct bases
    Alice.sendClassical("Bob", correct_bases[:])
