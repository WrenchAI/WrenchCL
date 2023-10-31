import os
from setuptools import setup, find_packages

# Function to find a folder that ends with .egg-info
def find_egg_info_folder(path='.'):
    for folder_name in os.listdir(path):
        if folder_name.endswith('.egg-info'):
            return folder_name
    return None

# Read the long description from README.md
with open("README.md", "r") as f:
    long_description = f.read()

# First, attempt to read the dependencies from requirements.txt in the root directory
required = []
requirements_path = 'requirements.txt'
if os.path.exists(requirements_path):
    with open(requirements_path, "r") as f:
        required = f.read().splitlines()
else:
    # If requirements.txt is not found, locate the .egg-info folder and read requires.txt
    egg_info_folder = find_egg_info_folder()
    if egg_info_folder:
        requires_path = os.path.join(egg_info_folder, 'requires.txt')
        if os.path.exists(requires_path):
            with open(requires_path, "r") as f:
                required = f.read().splitlines()

setup(
    name='WrenchCL',
    version='1.2',
    author='willem@wrench.ai',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=required
)
