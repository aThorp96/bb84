from setuptools import setup, find_packages

setup(
    name='bb84',    # This is the name of your PyPI-package.
    version='1.0',                          # Update the version number for new releases
    packages=find_packages(),
    scripts=['alice.py', 'bob.py'],
    install_requires=['bitvector', 'pycrypto', 'cqc'],
    author='Andrew Thorp',
    author_email='andrew.thorp.dev@gmail.com',
    url='https://github.com/athorp96/bb84',
)

