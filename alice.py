from bb84.bb84 import *
from BitVector import BitVector
from Crypto.Cipher import AES
from Crypto import Random

key_size = 32
length = 3 * key_size
acceptable_error = 0.5
recipient = "Bob"


with CQCConnection("Alice") as Alice:
    print("Connection made")

    # Send bob key length
    Alice.sendClassical(recipient, length)
    confirmation = int.from_bytes(Alice.recvClassical(), byteorder="big")

    print("Conform message length {}: {}".format(length, confirmation == length))

    # Get key, encode key, send to bob
    key, qubits, bases = create_master_key(Alice, length)
    key_bit_vect = BitVector(intVal=key)
    print("Key:           {}".format(bin(key)))
    print("Bases:         {}".format(bin(int(bases))))

    # If we measaure in the standard basis on Bob's block, we should see the 0 numbers be correct
    for q in qubits:
        Alice.sendQubit(q, recipient)

    Alice.sendClassical(recipient, bases)

    # receive bases used by Bob
    bobs_bases = BitVector(bitlist=Alice.recvClassical())
    print("Bobs bases:    {}".format(bin(bobs_bases.int_val())))
    correct_bases = ~bobs_bases ^ bases
    print("Correct:       {}".format(bin(int(correct_bases))))
    print(type(correct_bases))

    # Send bob correct bases
    Alice.sendClassical(recipient, correct_bases[:])
    key = truncate_key(key, length, correct_bases)

    if validate_generated_key(length, acceptable_error, key) != OK:
        raise Exception("Poor error rate: {}".format(1 - (len(key) / length)))
        exit(0)

    expected_verify, key = break_into_parts(key, key_size)
    verification_bits = BitVector(bitlist=Alice.recvClassical())

    if expected_verify != verification_bits:
        Alice.sendClassical(recipient, TAMPERED)
        pass
    else:
        Alice.sendClassical(recipient, OK)

    # Test AES encoding a message
    message = "Hello bob!"
    encrypted = encrypt(message, key)
    print(encrypted)
    Alice.sendClassical(recipient, encrypted)
