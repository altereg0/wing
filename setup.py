from setuptools import setup

setup(
    name='falcon-wing',
    version='0.2.0',
    description='Falcon extension for building nice looking API',

    author='Vlad Bakin',

    install_requires=['falcon'],

    packages=[
        'wing',
        'wing.adapters',
        'wing.serialization',
    ]
)
