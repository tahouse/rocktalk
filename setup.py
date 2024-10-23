from setuptools import setup, find_packages
from pathlib import Path

# Load packages from requirements.txt
BASE_DIR = Path(__file__).parent
with open(Path(BASE_DIR, "requirements.txt")) as file:
    required_packages = [ln.strip() for ln in file.readlines()]

setup(
    name="rocktalk",
    version="0.1",
    python_requires=">=3.11",
    packages=find_packages(),
    install_requires=required_packages,
)