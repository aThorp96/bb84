from setuptools import setup

setup(
    name='bb84',    # This is the name of your PyPI-package.
    version='1.0',                          # Update the version number for new releases
    packages=['bb84'],
    scripts=['alice.py', 'bob.py'],
    install_requires=['bitvector', 'pycryptodome', 'cqc', 'simulaqron'],
    author='Andrew Thorp',
    author_email='andrew.thorp.dev@gmail.com',
    url='https://github.com/athorp96/bb84',
)

