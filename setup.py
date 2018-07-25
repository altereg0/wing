import io
import os

from setuptools import setup, find_packages

# Package meta-data.
NAME = 'wing'
DESCRIPTION = 'Falcon extension for building nice looking API'
URL = 'https://github.com/altereg0/wing'
EMAIL = 'noemail@user.com'
AUTHOR = 'Vlad Bakin, altereg0'
REQUIRES_PYTHON = '>=3.5.0'
VERSION = '0.3.3'
KEYWORDS = "falcon peewee wing"
# What packages are required for this module to be executed?
REQUIRED = [
    'falcon',
    'peewee',
    'marshmallow',
    'marshmallow-jsonapi',
    'pyjwt'
]

# What packages are optional?
EXTRAS = {
}

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# Load the package's __version__.py module as a dictionary.
about = {}
if not VERSION:
    with open(os.path.join(here, NAME, '__version__.py')) as f:
        exec(f.read(), about)
else:
    about['__version__'] = VERSION

setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author=AUTHOR,
    author_email=EMAIL,
    keywords=KEYWORDS,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=['contrib', 'docs', 'test*']),
    # If your package is a single module, use this instead of 'packages':
    # py_modules=['mypackage'],
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    package_data={
        # If any package contains *.txt or *.rst files, include them:
        # '': ['*.txt', '*.rst'],
        # And include any *.msg files found in the 'hello' package, too:
        # 'hello': ['*.msg'],
    },
    data_files=[],

    entry_points={
        'console_scripts': [
            'wtestme = tests.run:main'
        ],
    },
)
