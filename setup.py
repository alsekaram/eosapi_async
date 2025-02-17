import setuptools
from setuptools import find_packages


setuptools.setup(
    name="eosapi-async",
    version="2.0.2",  # Major version bump due to significant changes
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
        "aiohappyeyeballs==2.3.4",
        "aiohttp==3.10.1",
        "aiorpcX==0.23.1",
        "aiosignal==1.3.1",
        "attrs==24.1.0",
        "base58>=2.1.1",
        "certifi==2024.7.4",
        "charset-normalizer==3.3.2",
        "cryptos==2.0.9",
        "frozenlist==1.4.1",
        "idna==3.7",
        "janus==1.0.0",
        "multidict==6.0.5",
        "packaging==24.1",
        "pbkdf2==1.3",
        "pycryptodomex==3.20.0",
        "requests==2.32.3",
        "typing_extensions==4.12.2",
        "urllib3==2.2.2",
        "yarl==1.9.4",
        "pydantic~=2.8.2",
        "antelopy~=0.2.0",
        "setuptools~=72.1.0",
        "cachetools~=5.5.0",
    ],  # Вместо чтения из requirements.txt указываем зависимости прямо здесь
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
