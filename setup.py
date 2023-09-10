from setuptools import setup, find_packages

# Read the long description from README.md or README.rst
with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name='wrench-code-library',
    version='1.0.0',
    author='willem@wrench.ai',
    long_description=long_description,
    long_description_content_type="text/markdown",  # or "text/x-rst" if you used reStructuredText
    packages=find_packages(),
    install_requires=[
        'colorama~=0.4.6',
        'pandas~=1.5.3',
        'requests~=2.29.0',
        'psycopg2~=2.9.6',
        'python-dotenv~=1.0.0',
        'openai~=0.27.4',
        'tenacity~=8.2.2',
    ],
)
