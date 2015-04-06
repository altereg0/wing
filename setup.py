from setuptools import setup

setup(
    name='falcon-wing',
    version='0.1.5',
    description='Falcon extension for building nice looking API',

    author='Vlad Bakin',

    install_requires=['falcon'],

    packages=[
        'wing',
        'wing.adapters',
        'wing.serialization',
    ]
)
