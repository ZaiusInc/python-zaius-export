from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='zaius_export',
    version='1.2',
    description='Zaius Export API Interface',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='http://github.com/zaiusinc/python-zaius-export',
    author='The Zaius Team',
    author_email='engineering@zaius.com',
    license='Apache 2.0',
    packages=find_packages(),
    install_requires=[
        'requests',
        'parsy',
        'boto3',
    ],
    test_suite='nose.collector',
    tests_require=['nose'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points = {
        'console_scripts': ['zaius-export=zaius.cli.main:main'],
    },
)
