import codecs
import os.path

from setuptools import find_packages, setup

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    return codecs.open(os.path.join(HERE, *parts), "r").read()


setup(
    name="pynamodb_utils",
    version="1.3.6",
    author="Michal Murawski",
    author_email="mmurawski777@gmail.com",
    description="Utilities package for pynamodb.",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/micmurawski/pynamodb-utils/",
    package_dir={"": "src"},
    packages=find_packages(
        where="./src",
        exclude=(
            'build',
            'tests',
        )
    ),
    install_requires=["pynamodb>=5.0.0"],
    include_package_data=True,
    python_requires=">=3.6",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
