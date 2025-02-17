import setuptools
from setuptools import find_packages


setuptools.setup(
    name="eosapi-async",
    version="2.0.1",  # Major version bump due to significant changes
    author="alsekaram",
    author_email="git@awl.su",
    description="EOS API async client with modern Python support",
    long_description="""
    Fork of original eosapi with significant improvements:

    - Complete rework of async implementation
    - Modern Python versions support
    - Enhanced error handling
    - Performance optimizations
    - Updated documentation

    Original code by encoderlee (encoderlee@gmail.com)
    """,
    long_description_content_type="text/markdown",
    url="https://github.com/alsekaram/eosapi_async",
    install_requires=[
        "aiohttp>=3.8.0",
        "requests>=2.26.0",
        "cryptos==2.0.9",
        "base58==2.1.1",
        "cachetools==5.5.1",
        "pydantic==2.10.6",
        "antelopy==0.2.0",
    ],  # Вместо чтения из requirements.txt указываем зависимости прямо здесь
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
