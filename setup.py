from setuptools import setup, find_packages

# Read the long description from README.md
with open("README.md", "r") as f:
    long_description = f.read()

# Read the dependencies from requirements.txt
with open("requirements.txt", "r") as f:
    required = f.read().splitlines()

setup(
    name='WrenchCL',
    version='AUTO_BUMP_VERSION',
    author='willem@wrench.ai',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=required,
    extras_require={
        'optional': ['colorama>=0.4.6']
    }
)
