# bb84

### To install:
`pip3 install git+https://github.com/athorp96/bb84.git`
If you're using a virtualenv, you will need to install cqc and simulaqron outside of the virtual env __as well__ **if you know how to work around this feel free to let me know**

### To run:
`alice.py` and `bob.py` are two example clients on how two parties would use the library.
You will have to configure simulaqron to have at least 3n qubits, where n is the number of bits in your key.


##### Note
The Crypto library has been listed as having security vulnerabilities at version 2.6.1. I reccomend using the key without using my encrypt and decrypt functions. 
