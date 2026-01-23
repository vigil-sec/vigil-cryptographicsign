#!/usr/bin/env python3
"""Setup script for Vigil CLI."""

from setuptools import setup, find_packages

with open("PyPI_README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="vigil-cli",
    version="0.1.0",
    description="CLI wrapper for Vigil cryptographic proof service. Request and verify cryptographic proofs for agent actions.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Vigil Team",
    url="https://github.com/rom-mvp/vigil-cryptographicsign",
    project_urls={
        "Documentation": "https://github.com/rom-mvp/vigil-cryptographicsign#readme",
        "Source": "https://github.com/rom-mvp/vigil-cryptographicsign",
        "Tracker": "https://github.com/rom-mvp/vigil-cryptographicsign/issues",
    },
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
    ],
    entry_points={
        'console_scripts': [
            'vigil=cli.vigil:main',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security :: Cryptography",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
