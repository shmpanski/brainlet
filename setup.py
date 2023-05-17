from setuptools import setup, find_packages

required_packages = [
    "loguru~=0.7.0",
    "weaviate-client~=3.18.0",
    "fastapi~=0.95.2",
    "uvicorn~=0.22.0",
]

dev_packages = [
    "black~=23.3.0",
    "wikiextractor~=3.0.6",
    "pytest~=7.3.1",
    "httpx~=0.24.0",
]

setup(
    name="brainlet",
    version="0.0.1",
    author="Andrey Sokolov",
    python_requires=">=3.9",
    install_requires=required_packages,
    extras_require={"dev": dev_packages},
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
