Development
===========

To locally develop the plugin, clone the repository locally and make your changes.

Open the console in your working directory; the building command is

.. code-block:: bash

   python setup.py sdist bdist_wheel

You can then install the package with

.. code-block:: bash

   pip install ./dist/WrenchCL-0.0.1.dev0-py3-none-any.whl --force-reinstall

Use the `--no-dependencies flag` to reinstall quickly if there are no dependency changes

.. code-block:: bash

   pip install ./dist/WrenchCL-0.0.1.dev0-py3-none-any.whl --force-reinstall --no-dependencies
