import os
from setuptools import setup, find_packages


base_packages = [
    "anywidget>=0.9.2"
]

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="wigglystuff",
    version="0.1.10",
    description="Collection of Anywidget Widgets",
    author="Vincent D. Warmerdam",
    packages=find_packages(exclude=["notebooks"]),
    package_data={"wigglystuff": ["static/*.js", "static/*.css"]},
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    install_requires=base_packages,
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering",
    ],
    license_files=["LICENSE"],
)
