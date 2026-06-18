from setuptools import setup, find_packages

setup(
    name='common_models',
    version='0.1',
    packages=find_packages(),  # Automatically find all packages in the 'common' directory
    include_package_data=True,
    install_requires=[
        'Django>=4.2.19',  
    ],
)