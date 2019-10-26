# bb84

### To install:
`pip3 install git+https://github.com/athorp96/bb84.git`
If you're using a virtualenv, you will need to install cqc and simulaqron outside of the virtual env _as well_. if you know how to work around this feel free to let me know

### To run:
`alice.py` and `bob.py` are two example clients on how two parties would use the library.
You will have to configure simulaqron to have at least 3n qubits, where n is the number of bits in your key.
This can be done by running `simulaqron set max-qubits <number of qubits>` and stopping and starting simulaqron again.

