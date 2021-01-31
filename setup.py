from setuptools import find_packages, setup

setup(
    name='pynamodb_utils',
    version='0.0.1',
    packages=find_packages(exclude=(
        'build',
        'tests',
    )),
    install_requires=[
        'marshmallow==3.3.0',
        'pynamodb==4.3.2',
        'boto3==1.12.5',
        'Flask==1.1.1'
    ],
    include_package_data=True,
)
