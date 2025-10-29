from setuptools import setup, find_packages

setup(
    name="html2text_lib",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "html2text>=2020.1.16",
    ],
    python_requires=">=3.8",
    description="HTML to text converter library for serverless environments",
    author="Databricks",
)
