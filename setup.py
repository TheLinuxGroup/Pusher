from setuptools import setup, find_packages

setup(
    name="pusher-l",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "cryptography",
    ],
    python_requires=">=3.7",
)
