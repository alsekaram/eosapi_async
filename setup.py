import setuptools
from setuptools import find_packages

with open("README.md", "r") as file:
    description = file.read()
    file.close()

with open('requirements.txt') as f:
    requirements = [req for req in f.read().splitlines() if req]

setuptools.setup(
    name="eosapi",
    version="1.0.2",
    author="encoderlee",
    author_email="encoderlee@gmail.com",
    description="a simple, high-level and lightweight eosio sdk write by python",
    long_description=description,
    long_description_content_type="text/markdown",
    url="https://github.com/encoderlee/eosapi",
    packages=["eosapi"],
    install_requires=requirements,
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
