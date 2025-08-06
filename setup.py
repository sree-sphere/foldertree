
from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="treescaffold",
    version="1.4.2",
    description="Generate folder structures from various input formats (tree, YAML, simple indentation)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Sreeprad",
    author_email="sreeprad@gmail.com",
    license="MIT",
    url="https://github.com/sree-sphere/foldertree",
    packages=find_packages(where="."),
    include_package_data=True,
    package_data={"foldertree": ["py.typed"]},
    entry_points={
        "console_scripts": [
            "foldertree=foldertree.cli:main",
            "treescaffold=foldertree.cli:main",
        ],
    },
    python_requires=">=3.7",
    install_requires=["PyYAML>=5.4.0"],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.900",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Code Generators",
        "Topic :: System :: Filesystems",
        "Topic :: Utilities",
    ],
    keywords=["folder", "directory", "structure", "generator", "tree", "scaffold"],
)