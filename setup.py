import os
import platform
from setuptools import setup, find_packages


# Function to find a folder that ends with .egg-info
def find_egg_info_folder(path='.'):
    for folder_name in os.listdir(path):
        if folder_name.endswith('.egg-info'):
            return folder_name
    return None


# Read the long description from README.md
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

# First, attempt to read the dependencies from requirements.txt in the root directory
required = []
requirements_path = 'requirements.txt'
if os.path.exists(requirements_path):
    with open(requirements_path, "r", encoding="utf-8") as f:
        required = f.read().splitlines()
else:
    # If requirements.txt is not found, locate the .egg-info folder and read requires.txt
    egg_info_folder = find_egg_info_folder()
    if egg_info_folder:
        requires_path = os.path.join(egg_info_folder, 'requires.txt')
        if os.path.exists(requires_path):
            with open(requires_path, "r", encoding="utf-8") as f:
                required = f.read().splitlines()

# Define the optional dependencies
extras = {'libmagic': ['python-magic-bin~=0.4.14']}

setup(name='WrenchCL', version='0.0.1.dev0', author='willem@wrench.ai',
      description='WrenchCL is a comprehensive library designed to facilitate seamless interactions with AWS services, OpenAI models, and various utility tools. This package aims to streamline the development process by providing robust components for database interactions, cloud storage, and AI-powered functionalities.',
      long_description=long_description, long_description_content_type="text/markdown",
      url='https://github.com/WrenchAI/WrenchCL', packages=find_packages(), install_requires=required,
      extras_require=extras, python_requires='>=3.11',
      classifiers=['Programming Language :: Python :: 3', 'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent', ], )
