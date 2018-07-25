from setuptools import setup

setup(
    name='falcon-wing',
    version='0.3.3',
    description='Falcon extension for building nice looking API',

    author='Vlad Bakin, altereg0',

    install_requires=['falcon'],

    packages=[
        'wing',
        'wing.adapters',
        'wing.serialization',
        'wing.falcon'
    ]
)
