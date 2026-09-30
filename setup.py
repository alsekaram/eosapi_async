import setuptools
from setuptools import find_packages

setuptools.setup(
    name="eosapi-async",
    version="2.2.2",
    author="alsekaram",
    author_email="git@awl.su",
    description="EOS API async client with modern Python support",
    long_description="""
    Fork of original eosapi with significant improvements:

    - Complete rework of async implementation
    - Modern Python versions support
    - Enhanced error handling
    - Performance optimizations including shared HTTP session
    - Updated documentation
    - Fixed RIPEMD160 compatibility issues

    Original code by encoderlee (encoderlee@gmail.com)
    """,
    long_description_content_type="text/markdown",
    url="https://github.com/alsekaram/eosapi_async",
    python_requires=">=3.12",
    install_requires=[
        "aiohttp>=3.12.14",
        "requests>=2.32.4",
        "cryptos>=2.0.9,<3",
        "base58>=2.1.1,<3",
        "cachetools>=5.5,<8",
        "pydantic>=2.8,<3",
        "antelopy>=0.2.0,<0.3",
        "pycryptodome>=3.19.1",
    ],
    extras_require={
        # libsecp256k1 for ~27x faster signing; optional because coincurve
        # has no wheels for some platforms (e.g. Python 3.14 as of 21.0.0)
        "fast": ["coincurve>=21.0.0"],
        "test": ["pytest>=8"],
    },
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
