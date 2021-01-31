from setuptools import find_packages, setup

setup(
    name='pynamodb_utils',
    version='0.0.1',
    packages=find_packages(exclude=(
        'build',
        'tests',
    )),
    install_requires=[
        'marshmallow>=3.10.0',
        'pynamodb>=5.0.0'
    ],
    include_package_data=True,
)
