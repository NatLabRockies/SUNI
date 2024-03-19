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
DOC_REQUIREMENTS = ["make", "ghp-import", "numpydoc", "pandoc"]
DESCRIPTION = (
    "National Renewable Energy Laboratory's (NREL's) Solar Uncertainty "
    "Analysis (SUNI) framework"
)


setup(
    name="NREL-suni",
    version=VERSION,
    description=DESCRIPTION,
    long_description=README,
    author="Paul Pinchuk",
    maintainer_email="ppinchuk@nrel.gov",
    packages=find_packages(),
    package_dir={"suni": "suni"},
    zip_safe=False,
    keywords="suni",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    entry_points={
        "console_scripts": ["suni=suni.cli:main"],
    },
    test_suite="tests",
    install_requires=INSTALL_REQUIREMENTS,
    extras_require={
        "test": TEST_REQUIREMENTS,
        "dev": TEST_REQUIREMENTS + DEV_REQUIREMENTS,
        "docs": TEST_REQUIREMENTS + DEV_REQUIREMENTS + DOC_REQUIREMENTS,
    },
)
