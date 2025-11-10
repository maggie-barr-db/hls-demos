from setuptools import setup, find_packages

setup(
    name="faker_lib",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "Faker>=22.0.0",
    ],
    author="HLS Demo",
    author_email="demo@example.com",
    description="Faker library wrapper for HLS demos",
    python_requires=">=3.9",
)

