from setuptools import setup
from setuptools import find_packages

setup(
    name='duckdata',
    packages=find_packages(),
    install_requires=[
    "scipy==0.19.1",
    "Pillow==4.2.1"
    ]
    )
