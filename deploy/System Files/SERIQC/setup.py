"""
setup.py
"""
from pathlib import Path

from setuptools import setup, find_packages


HERE = Path(__file__).parent.resolve()
README = "TBD"
VERSION = "0.1.0"

with open("requirements.txt") as f:
    INSTALL_REQUIREMENTS = f.read().splitlines()


DEV_REQUIREMENTS = ["black", "pylint", "jupyter", "pipreqs"]
TEST_REQUIREMENTS = ["pytest", "pytest-cov"]
DOC_REQUIREMENTS = [
    "make",
    "ghp-import",
    "numpydoc",
    "pandoc",
    "sphinx",
    "myst-nb",
    "sphinx-book-theme",
]
DESCRIPTION = (
    "SERI QC is a python package for quality controlling of solar "
    "irradiance data."
)


setup(
    name="NREL-seriqc",
    version=VERSION,
    description=DESCRIPTION,
    long_description=README,
    author="Adam R. Jensen",
    maintainer_email="adam-r-j@hotmail.com",
    packages=find_packages(),
    package_dir={"seriqc": "seriqc"},
    zip_safe=False,
    keywords="seriqc",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering",
    ],
    entry_points={},
    test_suite="tests",
    install_requires=INSTALL_REQUIREMENTS,
    extras_require={
        "test": TEST_REQUIREMENTS,
        "dev": TEST_REQUIREMENTS + DEV_REQUIREMENTS,
        "docs": TEST_REQUIREMENTS + DEV_REQUIREMENTS + DOC_REQUIREMENTS,
    },
)
