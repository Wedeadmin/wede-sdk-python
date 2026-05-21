from setuptools import setup, find_packages

setup(
    name="wede-sdk",
    version="0.1.0",
    description="Official Python SDK for the Wede Technology platform",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Wede Technology",
    author_email="geral@wede.pt",
    url="https://github.com/Wedeadmin/wede-sdk-python",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
