<h1 align="center">Wrench Code Library</h1>

<p align="center">
    <img src="https://raw.githubusercontent.com/WrenchAI/WrenchCL/release/resources/img/logo.svg" alt="Logo" style="display: inline-block; vertical-align: middle; width: 90%; max-width: 800px;">
    <br><br>
    <a href="https://pypi.org/project/WrenchCL/" style="text-decoration: none;">
        <img alt="PyPI - Version" src="https://img.shields.io/pypi/v/WrenchCL?logo=pypi&logoColor=green&color=green">
    </a>
    <a href="https://github.com/Kydoimos97" style="text-decoration: none;">
        <img src="https://img.shields.io/badge/Kydoimos97-cb632b?label=Code%20Maintainer" alt="Maintainer" height="20"/>
    </a>
    <a href="https://github.com/WrenchAI/WrenchCL/actions/workflows/publish-to-pypi.yml" style="text-decoration: none;">
        <img alt="GitHub Workflow Status (with event)" src="https://img.shields.io/github/actions/workflow/status/WrenchAI/WrenchCL/publish-to-pypi.yml?event=push&logo=Github&label=Test%20%26%20Publish%20%F0%9F%90%8D%20to%20PyPI%20%F0%9F%93%A6">
    </a>
</p>

## [Read the Docs - Documentation](https://wrenchai.github.io/WrenchCL/)

## Description

WrenchCL is a comprehensive library designed to facilitate seamless interactions with AWS services, OpenAI models, and various utility tools. This package aims to streamline the development process by providing robust components for database interactions, cloud storage, and AI-powered functionalities.


**PyPI Link:** [WrenchCL on PyPI](https://pypi.org/project/WrenchCL/)

## Package Structure

- **_Internal**: Contains internal classes for configuration and SSH tunnel management.
- **Connect**: Provides gateways for AWS RDS and S3 services and the `AWSClientHub`.
- **Decorators**: Utility decorators for retry logic, singleton pattern, and method timing.
- **Models**: _Internal for interacting with OpenAI models.
- **Tools**: Miscellaneous utility tools such as coalescing values, file typing, image encoding, and a custom logger.
- **DataFlow**: Response focused tools to aid in returning values and generating logs based on status codes.

## Installation

To install the package, simply run the following command:

```bash
pip install WrenchCL
```

## Development

To locally develop the plugin, clone the repository locally and make your changes.

Open the console in your working directory; the building command is

```bash
python setup.py sdist bdist_wheel
```

You can then install the package with 

```bash
pip install ./dist/WrenchCL-0.0.1.dev0-py3-none-any.whl --force-reinstall
```

Use the `--no-dependencies flag` to reinstall quickly if there are no dependency changes

```bash
pip install ./dist/WrenchCL-0.0.1.dev0-py3-none-any.whl --force-reinstall --no-dependencies
```
